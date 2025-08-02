"""
Digest Composer Component

Sorts all summaries by importance (descending) and formats into a digest.
"""

from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DigestComposer:
    """Compose ranked digest from processed newsletters."""
    
    def __init__(self):
        """Initialize the digest composer."""
        self.digest_template = """
# Newsletter Digest - {date}

## Summary
- Total newsletters processed: {total_count}
- High importance (4-5): {high_count}
- Medium importance (3): {medium_count}
- Low importance (1-2): {low_count}

## Top Stories (Score 4-5)
{high_importance_section}

## Medium Priority (Score 3)
{medium_importance_section}

## Lower Priority (Score 1-2)
{low_importance_section}

---
*Generated automatically by Newsletter Digest Bot*
"""
    
    def sort_by_importance(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort emails by importance score (descending).
        
        Args:
            emails: List of email data
            
        Returns:
            Sorted list of emails
        """
        return sorted(
            emails, 
            key=lambda x: x.get('importance_score', 0), 
            reverse=True
        )
    
    def group_by_importance(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group emails by importance level.
        
        Args:
            emails: List of email data
            
        Returns:
            Dictionary with grouped emails
        """
        groups = {
            'high': [],    # Score 4-5
            'medium': [],  # Score 3
            'low': []      # Score 1-2
        }
        
        for email in emails:
            score = email.get('importance_score', 3)
            
            if score >= 4:
                groups['high'].append(email)
            elif score == 3:
                groups['medium'].append(email)
            else:
                groups['low'].append(email)
        
        return groups
    
    def format_newsletter_entry(self, email: Dict[str, Any]) -> str:
        """
        Format a single newsletter entry.
        
        Args:
            email: Email data
            
        Returns:
            Formatted newsletter entry
        """
        subject = email.get('subject', 'Unknown')
        sender = email.get('sender', 'Unknown')
        score = email.get('importance_score', 3)
        category = email.get('category', 'News')
        summary_points = email.get('summary_points', ['', '', ''])
        links = email.get('extracted_links', [])
        
        # Format summary points
        summary_text = ""
        for i, point in enumerate(summary_points, 1):
            if point.strip():
                summary_text += f"• {point}\n"
        
        # Format links
        links_text = ""
        if links:
            links_text = "\n**Links:**\n"
            for link in links[:3]:  # Limit to 3 links
                links_text += f"- {link}\n"
        
        entry = f"""
### {subject} (Score: {score}/5)
**From:** {sender} | **Category:** {category}

{summary_text}{links_text}
"""
        return entry
    
    def compose_digest(self, emails: List[Dict[str, Any]]) -> str:
        """
        Compose a complete digest from processed emails.
        
        Args:
            emails: List of processed email data
            
        Returns:
            Formatted digest string
        """
        if not emails:
            return "No newsletters found for today."
        
        # Sort by importance
        sorted_emails = self.sort_by_importance(emails)
        
        # Group by importance
        groups = self.group_by_importance(sorted_emails)
        
        # Format each section
        high_section = self._format_section(groups['high'])
        medium_section = self._format_section(groups['medium'])
        low_section = self._format_section(groups['low'])
        
        # Get counts
        total_count = len(emails)
        high_count = len(groups['high'])
        medium_count = len(groups['medium'])
        low_count = len(groups['low'])
        
        # Compose digest
        digest = self.digest_template.format(
            date=datetime.now().strftime("%B %d, %Y"),
            total_count=total_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            high_importance_section=high_section,
            medium_importance_section=medium_section,
            low_importance_section=low_section
        )
        
        logger.info(f"Composed digest with {total_count} newsletters")
        return digest
    
    def _format_section(self, emails: List[Dict[str, Any]]) -> str:
        """
        Format a section of emails.
        
        Args:
            emails: List of emails for the section
            
        Returns:
            Formatted section string
        """
        if not emails:
            return "*No newsletters in this category*"
        
        section_text = ""
        for email in emails:
            section_text += self.format_newsletter_entry(email)
        
        return section_text
    
    def create_notion_entries(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create Notion database entries from processed emails.
        
        Args:
            emails: List of processed email data
            
        Returns:
            List of Notion entry dictionaries
        """
        notion_entries = []
        
        for email in emails:
            entry = {
                'title': email.get('subject', 'Unknown'),
                'summary': self._format_summary_for_notion(email),
                'importance': email.get('importance_score', 3),
                'category': email.get('category', 'News'),
                'link': self._get_primary_link(email),
                'date': datetime.now().isoformat(),
                'sender': email.get('sender', 'Unknown')
            }
            
            notion_entries.append(entry)
        
        logger.info(f"Created {len(notion_entries)} Notion entries")
        return notion_entries
    
    def _format_summary_for_notion(self, email: Dict[str, Any]) -> str:
        """
        Format summary for Notion database.
        
        Args:
            email: Email data
            
        Returns:
            Formatted summary string
        """
        summary_points = email.get('summary_points', ['', '', ''])
        
        # Filter out empty points
        valid_points = [point for point in summary_points if point.strip()]
        
        if valid_points:
            return '\n'.join([f"• {point}" for point in valid_points])
        else:
            return "No summary available"
    
    def _get_primary_link(self, email: Dict[str, Any]) -> str:
        """
        Get the primary link from email data.
        
        Args:
            email: Email data
            
        Returns:
            Primary link URL or empty string
        """
        links = email.get('extracted_links', [])
        
        if links:
            # Return the first link
            return links[0]
        
        return ""
    
    def get_digest_stats(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the digest.
        
        Args:
            emails: List of processed emails
            
        Returns:
            Dictionary with digest statistics
        """
        if not emails:
            return {
                'total_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'categories': {},
                'average_score': 0
            }
        
        # Count by importance
        groups = self.group_by_importance(emails)
        
        # Count by category
        categories = {}
        for email in emails:
            category = email.get('category', 'News')
            categories[category] = categories.get(category, 0) + 1
        
        # Calculate average score
        scores = [email.get('importance_score', 3) for email in emails]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_count': len(emails),
            'high_count': len(groups['high']),
            'medium_count': len(groups['medium']),
            'low_count': len(groups['low']),
            'categories': categories,
            'average_score': round(average_score, 2)
        } 