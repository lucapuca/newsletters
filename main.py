"""
Main Newsletter Digest Pipeline

Orchestrates all components to process newsletters and send them to Notion.
Uses Cerebras for AI processing.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from components.email_reader import EmailReader
from components.content_cleaner import ContentCleaner
from components.summarizer import Summarizer
from components.scorer import Scorer
from components.digest_composer import DigestComposer
from components.notion_writer import NotionWriter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('newsletter_digest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsletterDigestPipeline:
    """Main pipeline for processing newsletters."""
    
    def __init__(self):
        """Initialize the pipeline with all components."""
        # Load environment variables
        self.email_address = os.getenv('EMAIL')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Validate required environment variables
        self._validate_environment()
        
        # Initialize components
        self.email_reader = EmailReader(self.email_address, self.email_password)
        self.content_cleaner = ContentCleaner()
        self.summarizer = Summarizer(api_key=self.cerebras_api_key)
        self.scorer = Scorer(api_key=self.cerebras_api_key)
        self.digest_composer = DigestComposer()
        self.notion_writer = NotionWriter(self.notion_token, self.notion_database_id)
    
    def _validate_environment(self):
        """Validate that all required environment variables are set."""
        required_vars = [
            'EMAIL', 'EMAIL_PASSWORD', 'CEREBRAS_API_KEY', 
            'NOTION_TOKEN', 'NOTION_DATABASE_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete newsletter digest pipeline.
        
        Returns:
            Dictionary with pipeline results and statistics
        """
        logger.info("Starting Newsletter Digest Pipeline")
        
        try:
            # Step 1: Fetch emails
            logger.info("Step 1: Fetching emails from Gmail")
            emails = self.email_reader.fetch_emails()
            
            if not emails:
                logger.warning("No emails found")
                return self._create_empty_result()
            
            # Step 2: Filter newsletters
            logger.info("Step 2: Filtering newsletters")
            newsletters = self.email_reader.filter_newsletters(emails)
            
            if not newsletters:
                logger.warning("No newsletters found")
                return self._create_empty_result()
            
            # Step 3: Clean content
            logger.info("Step 3: Cleaning email content")
            cleaned_newsletters = []
            for newsletter in newsletters:
                cleaned = self.content_cleaner.clean_email_content(newsletter)
                if self.content_cleaner.is_valid_content(cleaned.get('cleaned_body', '')):
                    cleaned_newsletters.append(cleaned)
            
            if not cleaned_newsletters:
                logger.warning("No valid newsletters after cleaning")
                return self._create_empty_result()
            
            # Step 4: Summarize content
            logger.info("Step 4: Summarizing newsletters")
            summarized_newsletters = self.summarizer.batch_summarize(cleaned_newsletters)
            
            # Step 5: Score importance
            logger.info("Step 5: Scoring newsletter importance")
            scored_newsletters = self.scorer.batch_score(summarized_newsletters)
            
            # Step 6: Filter by minimum score
            logger.info("Step 6: Filtering by importance score")
            filtered_newsletters = self.scorer.filter_by_score(scored_newsletters, min_score=1)
            
            if not filtered_newsletters:
                logger.warning("No newsletters meet minimum importance score")
                return self._create_empty_result()
            
            # Step 7: Compose digest
            logger.info("Step 7: Composing digest")
            digest_content = self.digest_composer.compose_digest(filtered_newsletters)
            digest_stats = self.digest_composer.get_digest_stats(filtered_newsletters)
            
            # Step 8: Create Notion entries
            logger.info("Step 8: Creating Notion entries")
            notion_entries = self.digest_composer.create_notion_entries(filtered_newsletters)
            
            # Step 9: Write to Notion
            logger.info("Step 9: Writing to Notion database")
            notion_results = self.notion_writer.batch_create_pages(notion_entries)
            
            # Step 10: Create digest summary page
            logger.info("Step 10: Creating digest summary page")
            self.notion_writer.create_digest_page(digest_content, digest_stats)
            
            # Compile results
            results = {
                'success': True,
                'total_emails': len(emails),
                'total_newsletters': len(newsletters),
                'valid_newsletters': len(cleaned_newsletters),
                'processed_newsletters': len(filtered_newsletters),
                'notion_results': notion_results,
                'digest_stats': digest_stats,
                'digest_content': digest_content,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Pipeline completed successfully")
            logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result when no newsletters are found."""
        return {
            'success': True,
            'total_emails': 0,
            'total_newsletters': 0,
            'valid_newsletters': 0,
            'processed_newsletters': 0,
            'notion_results': {'success_count': 0, 'failure_count': 0, 'total_count': 0},
            'digest_stats': {
                'total_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'categories': {},
                'average_score': 0
            },
            'digest_content': "No newsletters found for today.",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_connections(self) -> Dict[str, bool]:
        """
        Test all external connections.
        
        Returns:
            Dictionary with connection test results
        """
        results = {}
        
        # Test Gmail connection
        try:
            imap = self.email_reader.connect()
            # Use the safe_close method instead of direct close/logout
            self.email_reader.safe_close(imap)
            results['gmail'] = True
            logger.info("Gmail connection test: PASSED")
        except Exception as e:
            results['gmail'] = False
            logger.error(f"Gmail connection test: FAILED - {e}")
        
        # Test Cerebras connection
        try:
            results['cerebras'] = self.summarizer.test_connection()
            if results['cerebras']:
                logger.info("Cerebras connection test: PASSED")
            else:
                logger.error("Cerebras connection test: FAILED")
        except Exception as e:
            results['cerebras'] = False
            logger.error(f"Cerebras connection test: FAILED - {e}")
        
        # Test Notion connection
        try:
            results['notion'] = self.notion_writer.test_connection()
            if results['notion']:
                logger.info("Notion connection test: PASSED")
            else:
                logger.error("Notion connection test: FAILED")
        except Exception as e:
            results['notion'] = False
            logger.error(f"Notion connection test: FAILED - {e}")
        
        return results

def main():
    """Main entry point for the newsletter digest pipeline."""
    try:
        pipeline = NewsletterDigestPipeline()
        
        # Test connections first
        logger.info("Testing connections...")
        connection_results = pipeline.test_connections()
        
        if not all(connection_results.values()):
            logger.error("Some connections failed. Please check your configuration.")
            for service, status in connection_results.items():
                logger.error(f"{service}: {'PASSED' if status else 'FAILED'}")
            return
        
        # Run the pipeline
        results = pipeline.run()
        
        if results['success']:
            logger.info("Pipeline completed successfully!")
            print(f"\n📧 Newsletter Digest Complete!")
            print(f"�� Processed {results['processed_newsletters']} newsletters")
            print(f"📈 Notion entries created: {results['notion_results']['success_count']}")
            print(f"⭐ Average importance score: {results['digest_stats']['average_score']}")
        else:
            logger.error("Pipeline failed!")
            print(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()