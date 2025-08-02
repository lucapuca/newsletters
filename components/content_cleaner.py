"""
Content Cleaner Component

Removes email headers, footers, unsubscribe links, and boilerplate content.
Extracts main body text and links.
"""

import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ContentCleaner:
    """Clean and extract meaningful content from email bodies."""
    
    def __init__(self):
        """Initialize the content cleaner."""
        # Common patterns to remove
        self.unsubscribe_patterns = [
            r'unsubscribe',
            r'opt.?out',
            r'click here to unsubscribe',
            r'to stop receiving',
            r'manage your preferences',
            r'update your preferences',
            r'email preferences',
            r'preferences center'
        ]
        
        self.footer_patterns = [
            r'©\s*\d{4}',
            r'all rights reserved',
            r'powered by',
            r'sent with',
            r'this email was sent to',
            r'you received this email because',
            r'add us to your address book',
            r'view this email in your browser'
        ]
        
        self.header_patterns = [
            r'view this email in your browser',
            r'web version',
            r'view online',
            r'email not displaying correctly'
        ]
        
        # Social media and contact patterns
        self.social_patterns = [
            r'follow us on',
            r'connect with us',
            r'find us on',
            r'facebook',
            r'twitter',
            r'linkedin',
            r'instagram',
            r'youtube'
        ]
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML content and extract text.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        if not html_content:
            return ""
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove common newsletter elements
            self._remove_newsletter_elements(soup)
            
            # Extract text
            text = soup.get_text()
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            # Fallback to regex cleaning
            return self._clean_with_regex(html_content)
    
    def _remove_newsletter_elements(self, soup: BeautifulSoup):
        """Remove common newsletter elements from HTML."""
        # Remove elements with common newsletter class names
        newsletter_classes = [
            'footer', 'header', 'unsubscribe', 'social', 'share',
            'newsletter-footer', 'email-footer', 'email-header'
        ]
        
        for class_name in newsletter_classes:
            elements = soup.find_all(class_=re.compile(class_name, re.I))
            for element in elements:
                element.decompose()
        
        # Remove elements with common newsletter IDs
        newsletter_ids = [
            'footer', 'header', 'unsubscribe', 'social'
        ]
        
        for id_name in newsletter_ids:
            elements = soup.find_all(id=re.compile(id_name, re.I))
            for element in elements:
                element.decompose()
    
    def _clean_with_regex(self, content: str) -> str:
        """
        Clean content using regex patterns as fallback.
        
        Args:
            content: Raw content to clean
            
        Returns:
            Cleaned content
        """
        # Convert HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove patterns
        all_patterns = (
            self.unsubscribe_patterns + 
            self.footer_patterns + 
            self.header_patterns + 
            self.social_patterns
        )
        
        for pattern in all_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def extract_links(self, html_content: str) -> List[str]:
        """
        Extract links from HTML content.
        
        Args:
            html_content: HTML content to extract links from
            
        Returns:
            List of extracted URLs
        """
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Filter out common newsletter links
                if not any(pattern in href.lower() for pattern in [
                    'unsubscribe', 'preferences', 'manage', 'update'
                ]):
                    links.append(href)
            
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            # Fallback regex extraction
            url_pattern = r'https?://[^\s<>"]+'
            return re.findall(url_pattern, html_content)
    
    def clean_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean email content and extract meaningful information.
        
        Args:
            email_data: Email data with subject, sender, body
            
        Returns:
            Cleaned email data with extracted content and links
        """
        body = email_data.get('body', '')
        
        # Determine if content is HTML or plain text
        is_html = '<html' in body.lower() or '<body' in body.lower() or '<div' in body.lower()
        
        if is_html:
            cleaned_text = self.clean_html(body)
            links = self.extract_links(body)
        else:
            cleaned_text = self._clean_with_regex(body)
            # Extract URLs from plain text
            url_pattern = r'https?://[^\s]+'
            links = re.findall(url_pattern, cleaned_text)
        
        # Remove the extracted links from the text
        for link in links:
            cleaned_text = cleaned_text.replace(link, '')
        
        # Final cleanup
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        # Update email data
        cleaned_email = email_data.copy()
        cleaned_email['cleaned_body'] = cleaned_text
        cleaned_email['links'] = links
        cleaned_email['is_html'] = is_html
        
        logger.info(f"Cleaned email: {email_data.get('subject', 'Unknown')}")
        logger.info(f"Extracted {len(links)} links")
        
        return cleaned_email
    
    def is_valid_content(self, cleaned_content: str) -> bool:
        """
        Check if cleaned content is valid and meaningful.
        
        Args:
            cleaned_content: Cleaned text content
            
        Returns:
            True if content is valid and meaningful
        """
        if not cleaned_content:
            return False
        
        # Check minimum length (at least 50 characters)
        if len(cleaned_content) < 50:
            return False
        
        # Check for meaningful content (not just whitespace and punctuation)
        meaningful_chars = len(re.sub(r'[^\w]', '', cleaned_content))
        if meaningful_chars < 20:
            return False
        
        # Check for common spam indicators
        spam_indicators = [
            'click here', 'limited time', 'act now', 'urgent',
            'free money', 'make money fast', 'work from home'
        ]
        
        content_lower = cleaned_content.lower()
        spam_score = sum(1 for indicator in spam_indicators if indicator in content_lower)
        
        if spam_score > 2:
            return False
        
        return True 