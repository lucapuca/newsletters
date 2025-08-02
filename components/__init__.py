"""
Newsletter Digest Components

This package contains all the components for the newsletter digest pipeline:
- Email Reader: Gmail IMAP connection
- Content Cleaner: Email content extraction
- Summarizer: OpenAI summarization
- Scorer: Importance scoring
- Digest Composer: Digest formatting
- Notion Writer: Notion API integration
"""

from .email_reader import EmailReader
from .content_cleaner import ContentCleaner
from .summarizer import Summarizer
from .scorer import Scorer
from .digest_composer import DigestComposer
from .notion_writer import NotionWriter

__all__ = [
    'EmailReader',
    'ContentCleaner', 
    'Summarizer',
    'Scorer',
    'DigestComposer',
    'NotionWriter'
] 