"""
Newsletter Digest Pipeline

Orchestrates the entire pipeline to process newsletters and create a digest.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsletterDigestPipeline:
    """Main pipeline for processing newsletter emails."""
    
    def __init__(self):
        """Initialize the pipeline components."""
        load_dotenv()
        
        # Validate environment
        self._validate_environment()
        
        # Initialize components
        self.email_reader = EmailReader(
            email_address=os.getenv('EMAIL'),
            password=os.getenv('EMAIL_PASSWORD')
        )
        
        self.content_cleaner = ContentCleaner()
        self.cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        self.summarizer = Summarizer(api_key=self.cerebras_api_key)
        self.scorer = Scorer(api_key=self.cerebras_api_key)
        self.digest_composer = DigestComposer()
        self.notion_writer = NotionWriter(
            token=os.getenv('NOTION_TOKEN'),
            database_id=os.getenv('NOTION_DATABASE_ID')
        )
    
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
    
    def process_single_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email through the entire pipeline.
        
        Args:
            email_data: Raw email data
            
        Returns:
            Processed email data with summary, score, etc.
        """
        try:
            subject = email_data.get('subject', 'Unknown')
            logger.info(f"Processing email: {subject}")
            
            # Step 1: Clean content
            logger.info(f"Step 1: Cleaning content for '{subject}'")
            cleaned_email = self.content_cleaner.clean_email_content(email_data)
            
            if not cleaned_email.get('cleaned_body', '').strip():
                logger.warning(f"Skipping '{subject}' - no clean content found")
                return None
            
            # Step 2: Summarize content
            logger.info(f"Step 2: Summarizing '{subject}'")
            summarized_email = self.summarizer.summarize_content(cleaned_email)
            
            # Step 3: Score importance
            logger.info(f"Step 3: Scoring '{subject}'")
            scored_email = self.scorer.score_newsletter(summarized_email)
            
            # Step 4: Create Notion entry
            logger.info(f"Step 4: Creating Notion entry for '{subject}'")
            notion_entry = self.digest_composer.prepare_notion_entry(scored_email)
            
            success = self.notion_writer.create_page(notion_entry)
            if success:
                logger.info(f"Successfully processed and stored: {subject}")
                return scored_email
            else:
                logger.error(f"Failed to create Notion entry for: {subject}")
                return scored_email  # Return processed data even if Notion fails
                
        except Exception as e:
            logger.error(f"Error processing email '{email_data.get('subject', 'Unknown')}': {e}")
            return None
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete pipeline processing emails one at a time.
        
        Returns:
            Pipeline results with statistics
        """
        logger.info("Starting newsletter digest pipeline")
        
        try:
            # Step 1: Fetch unread emails
            logger.info("Step 1: Fetching unread emails")
            emails = self.email_reader.fetch_unread_emails()
            
            if not emails:
                logger.info("No unread emails found")
                return {
                    'total_emails': 0,
                    'processed_emails': 0,
                    'successful_entries': 0,
                    'failed_entries': 0,
                    'digest_created': False
                }
            
            logger.info(f"Found {len(emails)} unread emails")
            
            # Step 2: Filter newsletters
            logger.info("Step 2: Filtering newsletters")
            filtered_emails = self.email_reader.filter_newsletters(emails)
            
            if not filtered_emails:
                logger.info("No newsletters found after filtering")
                return {
                    'total_emails': len(emails),
                    'processed_emails': 0,
                    'successful_entries': 0,
                    'failed_entries': 0,
                    'digest_created': False
                }
            
            logger.info(f"Filtered to {len(filtered_emails)} newsletters")
            
            # Step 3: Process each email individually
            logger.info("Step 3: Processing emails one by one")
            processed_emails = []
            successful_entries = 0
            failed_entries = 0
            
            for i, email_data in enumerate(filtered_emails, 1):
                logger.info(f"Processing email {i}/{len(filtered_emails)}")
                
                processed_email = self.process_single_email(email_data)
                
                if processed_email:
                    processed_emails.append(processed_email)
                    successful_entries += 1
                else:
                    failed_entries += 1
            
            # Step 4: Create digest if we have processed emails
            digest_created = False
            if processed_emails:
                logger.info("Step 4: Creating digest summary")
                
                # Filter by minimum score
                min_score_emails = self.scorer.filter_by_score(processed_emails, min_score=1)
                
                if min_score_emails:
                    # Create digest content
                    digest_content = self.digest_composer.compose_digest(min_score_emails)
                    
                    # Create digest statistics
                    stats = self.digest_composer.get_digest_stats(min_score_emails)
                    
                    # Create digest page in Notion
                    digest_created = self.notion_writer.create_digest_page(digest_content, stats)
                    
                    if digest_created:
                        logger.info("Successfully created digest summary page")
                    else:
                        logger.warning("Failed to create digest summary page")
                else:
                    logger.info("No emails met minimum score threshold")
            
            # Return results
            results = {
                'total_emails': len(emails),
                'filtered_emails': len(filtered_emails),
                'processed_emails': len(processed_emails),
                'successful_entries': successful_entries,
                'failed_entries': failed_entries,
                'min_score_emails': len(min_score_emails) if processed_emails else 0,
                'digest_created': digest_created
            }
            
            logger.info("Pipeline completed successfully")
            logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'error': str(e),
                'total_emails': 0,
                'processed_emails': 0,
                'successful_entries': 0,
                'failed_entries': 0,
                'digest_created': False
            }
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all external connections."""
        results = {}
        
        # Test Gmail connection
        try:
            imap = self.email_reader.connect()
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
    """Main entry point."""
    try:
        pipeline = NewsletterDigestPipeline()
        
        # Test connections first
        logger.info("Testing connections...")
        connection_results = pipeline.test_connections()
        
        if not all(connection_results.values()):
            logger.error("Some connections failed. Please check your configuration.")
            return
        
        # Run the pipeline
        results = pipeline.run()
        
        if 'error' in results:
            logger.error(f"Pipeline failed: {results['error']}")
        else:
            logger.info("Pipeline completed successfully!")
            
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")

if __name__ == "__main__":
    main()