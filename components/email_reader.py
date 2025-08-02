"""
Email Reader Component

Connects to Gmail via IMAP and fetches unread emails.
Extracts subject, sender, and full body content, then marks emails as read.
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailReader:
    """Gmail IMAP email reader for fetching newsletters."""
    
    def __init__(self, email_address: str, password: str):
        """
        Initialize the email reader.
        
        Args:
            email_address: Gmail address
            password: Gmail app password
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        
    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP server."""
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_address, self.password)
            logger.info("Successfully connected to Gmail IMAP")
            return imap
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            raise
    
    def safe_close(self, imap):
        """Safely close IMAP connection."""
        try:
            if imap.state == 'SELECTED':
                imap.close()
            imap.logout()
        except Exception as e:
            logger.warning(f"Error during IMAP cleanup: {e}")
    
    def decode_email_header(self, header: str) -> str:
        """Decode email header properly."""
        if header is None:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        
        return decoded_string
    
    def extract_email_content(self, msg) -> Dict[str, Any]:
        """Extract content from email message."""
        subject = self.decode_email_header(msg.get('Subject', ''))
        sender = self.decode_email_header(msg.get('From', ''))
        
        # Extract email body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
                elif content_type == "text/html":
                    try:
                        body = part.get_payload(decode=True).decode()
                        # Prefer plain text, but use HTML if no plain text found
                        if not body.strip():
                            continue
                    except:
                        continue
        else:
            # Not multipart
            content_type = msg.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    body = ""
        
        return {
            'subject': subject,
            'sender': sender,
            'body': body,
            'date': msg.get('Date', ''),
            'message_id': msg.get('Message-ID', '')
        }
    
    def fetch_unread_emails(self) -> List[Dict[str, Any]]:
        """
        Fetch all unread emails and mark them as read.
        
        Returns:
            List of email dictionaries with subject, sender, body, date
        """
        imap = self.connect()
        
        try:
            # Select the inbox
            imap.select('INBOX')
            
            # Search for unread emails
            _, message_numbers = imap.search(None, 'UNSEEN')
            
            if not message_numbers[0]:
                logger.info("No unread emails found")
                return []
            
            emails = []
            processed_message_ids = []
            
            for num in message_numbers[0].split():
                try:
                    # Fetch the email
                    _, msg_data = imap.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    email_content = self.extract_email_content(msg)
                    
                    # Only include emails with content
                    if email_content['body'].strip():
                        emails.append(email_content)
                        processed_message_ids.append(num)
                        logger.info(f"Processed unread email: {email_content['subject']}")
                    
                except Exception as e:
                    logger.error(f"Error processing email {num}: {e}")
                    continue
            
            # Mark all processed emails as read
            if processed_message_ids:
                try:
                    # Convert list of message IDs to comma-separated string
                    message_ids_str = b','.join(processed_message_ids)
                    imap.store(message_ids_str, '+FLAGS', '\\Seen')
                    logger.info(f"Marked {len(processed_message_ids)} emails as read")
                except Exception as e:
                    logger.error(f"Error marking emails as read: {e}")
            
            logger.info(f"Successfully fetched {len(emails)} unread emails")
            return emails
            
        finally:
            self.safe_close(imap)
    
    def fetch_emails(self) -> List[Dict[str, Any]]:
        """
        Alias for fetch_unread_emails for backward compatibility.
        
        Returns:
            List of email dictionaries with subject, sender, body, date
        """
        return self.fetch_unread_emails()
    
    def filter_newsletters(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter emails to only include newsletters and content-rich emails.
        Uses a more intelligent approach to identify valuable content.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Filtered list of newsletter emails
        """
        # Expanded newsletter indicators
        newsletter_keywords = [
            'newsletter', 'digest', 'weekly', 'daily', 'update',
            'news', 'insights', 'roundup', 'summary', 'report',
            'briefing', 'alert', 'insight', 'analysis', 'review',
            'trends', 'market', 'industry', 'tech', 'startup',
            'funding', 'acquisition', 'launch', 'release', 'update'
        ]
        
        # Known newsletter domains
        newsletter_domains = [
            'substack.com', 'revue.co', 'beehiiv.com', 'convertkit.com',
            'mailchimp.com', 'constantcontact.com', 'medium.com',
            'techcrunch.com', 'wired.com', 'theverge.com', 'arstechnica.com',
            'hackernews.com', 'producthunt.com', 'indiehackers.com'
        ]
        
        # Spam/transactional keywords to exclude
        spam_keywords = [
            'receipt', 'invoice', 'order confirmation', 'shipping',
            'password reset', 'account verification', 'unsubscribe',
            'confirm your email', 'verify your account', 'welcome to',
            'your order', 'payment received', 'shipping confirmation'
        ]
        
        filtered_emails = []
        rejected_emails = []
        
        for email_data in emails:
            subject = email_data['subject'].lower()
            sender = email_data['sender'].lower()
            body = email_data['body'].lower()
            
            # Skip obvious spam/transactional emails
            is_spam = any(keyword in subject for keyword in spam_keywords)
            if is_spam:
                rejected_emails.append(f"SPAM: {email_data['subject']} (from {email_data['sender']})")
                continue
            
            # Check if it's a newsletter by keywords
            is_newsletter = any(keyword in subject for keyword in newsletter_keywords)
            is_newsletter = is_newsletter or any(keyword in sender for keyword in newsletter_keywords)
            
            # Check known newsletter domains
            for domain in newsletter_domains:
                if domain in sender:
                    is_newsletter = True
                    break
            
            # Check if content is substantial (more than just a few words)
            content_length = len(body.split())
            is_substantial = content_length > 50  # At least 50 words
            
            # Check if it contains links (indicates content-rich email)
            has_links = 'http' in body or 'www.' in body
            
            # Include if it's a newsletter OR if it's substantial content with links
            if is_newsletter or (is_substantial and has_links):
                filtered_emails.append(email_data)
            else:
                rejected_emails.append(f"SHORT/NO LINKS: {email_data['subject']} (from {email_data['sender']}) - {content_length} words")
        
        logger.info(f"Filtered to {len(filtered_emails)} newsletters")
        logger.info(f"Rejected {len(rejected_emails)} emails:")
        for rejected in rejected_emails[:10]:  # Show first 10
            logger.info(f"  - {rejected}")
        if len(rejected_emails) > 10:
            logger.info(f"  ... and {len(rejected_emails) - 10} more")
        
        return filtered_emails