"""
Test Pipeline Script

Simulates the newsletter digest pipeline using example emails.
Uses Cerebras for AI processing (free API credits available).
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestNewsletterPipeline:
    """Test pipeline using sample newsletter data."""
    
    def __init__(self):
        """Initialize the test pipeline."""
        self.cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Initialize components
        self.content_cleaner = ContentCleaner()
        self.summarizer = Summarizer(api_key=self.cerebras_api_key)
        self.scorer = Scorer(api_key=self.cerebras_api_key)
        self.digest_composer = DigestComposer()
        
        # Initialize Notion writer if credentials are available
        if self.notion_token and self.notion_database_id:
            self.notion_writer = NotionWriter(self.notion_token, self.notion_database_id)
        else:
            self.notion_writer = None
            logger.warning("Notion credentials not provided - skipping Notion integration")
    
    def get_sample_newsletters(self) -> List[Dict[str, Any]]:
        """Get sample newsletter data for testing."""
        return [
            {
                'subject': 'TechCrunch Newsletter - Latest Startup News',
                'sender': 'newsletter@techcrunch.com',
                'body': '''
                <html>
                <body>
                <h1>TechCrunch Newsletter</h1>
                <p>Here are the top stories from this week:</p>
                <ul>
                <li>OpenAI releases GPT-5 with improved reasoning capabilities</li>
                <li>Microsoft acquires AI startup for $2 billion</li>
                <li>New funding round for autonomous vehicle company</li>
                </ul>
                <p>Read more at <a href="https://techcrunch.com">TechCrunch</a></p>
                <div class="footer">
                <p>Unsubscribe here</p>
                </div>
                </body>
                </html>
                ''',
                'date': '2024-01-15',
                'message_id': 'test1@example.com'
            },
            {
                'subject': 'Product Hunt Daily - Amazing New Tools',
                'sender': 'hello@producthunt.com',
                'body': '''
                <html>
                <body>
                <h2>Today's Top Products</h2>
                <p>Check out these amazing new tools:</p>
                <ul>
                <li>Notion AI - AI-powered note-taking assistant</li>
                <li>Cursor - AI-powered code editor</li>
                <li>Midjourney v6 - Advanced image generation</li>
                </ul>
                <p>Visit <a href="https://producthunt.com">Product Hunt</a> for more</p>
                <div class="footer">
                <p>Manage your preferences</p>
                </div>
                </body>
                </html>
                ''',
                'date': '2024-01-15',
                'message_id': 'test2@example.com'
            },
            {
                'subject': 'Paul Graham Essays - Startup Advice',
                'sender': 'essays@paulgraham.com',
                'body': '''
                <html>
                <body>
                <h1>Latest Essay: How to Build a Great Company</h1>
                <p>In this essay, I discuss the key principles for building successful startups:</p>
                <ol>
                <li>Focus on solving real problems</li>
                <li>Build for users, not investors</li>
                <li>Stay lean and iterate quickly</li>
                </ol>
                <p>Read the full essay at <a href="http://paulgraham.com">paulgraham.com</a></p>
                <div class="footer">
                <p>© 2024 Paul Graham</p>
                </div>
                </body>
                </html>
                ''',
                'date': '2024-01-15',
                'message_id': 'test3@example.com'
            },
            {
                'subject': 'Hacker News Digest - Top Stories',
                'sender': 'digest@hackernews.com',
                'body': '''
                <html>
                <body>
                <h2>Top Hacker News Stories</h2>
                <p>Here are the most discussed stories:</p>
                <ul>
                <li>Rust 2.0 released with major improvements</li>
                <li>New study shows AI can predict protein structures</li>
                <li>GitHub introduces AI-powered code review</li>
                </ul>
                <p>View all stories at <a href="https://news.ycombinator.com">Hacker News</a></p>
                <div class="footer">
                <p>Unsubscribe from this digest</p>
                </div>
                </body>
                </html>
                ''',
                'date': '2024-01-15',
                'message_id': 'test4@example.com'
            },
            {
                'subject': 'Spam Newsletter - Click Here Now!',
                'sender': 'spam@example.com',
                'body': '''
                <html>
                <body>
                <h1>URGENT: Limited Time Offer!</h1>
                <p>Click here to claim your free money!</p>
                <p>Act now before it's too late!</p>
                <p>Make money fast from home!</p>
                <div class="footer">
                <p>Click here to unsubscribe</p>
                </div>
                </body>
                </html>
                ''',
                'date': '2024-01-15',
                'message_id': 'test5@example.com'
            }
        ]
    
    def run_test_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete test pipeline.
        
        Returns:
            Dictionary with test results and statistics
        """
        logger.info("Starting Test Newsletter Pipeline")
        
        try:
            # Step 1: Get sample newsletters
            logger.info("Step 1: Loading sample newsletters")
            sample_newsletters = self.get_sample_newsletters()
            
            # Step 2: Clean content
            logger.info("Step 2: Cleaning email content")
            cleaned_newsletters = []
            for newsletter in sample_newsletters:
                cleaned = self.content_cleaner.clean_email_content(newsletter)
                if self.content_cleaner.is_valid_content(cleaned.get('cleaned_body', '')):
                    cleaned_newsletters.append(cleaned)
                    logger.info(f"Cleaned: {cleaned.get('subject', 'Unknown')}")
                else:
                    logger.info(f"Skipped invalid content: {cleaned.get('subject', 'Unknown')}")
            
            if not cleaned_newsletters:
                logger.warning("No valid newsletters after cleaning")
                return self._create_empty_result()
            
            # Step 3: Summarize content
            logger.info("Step 3: Summarizing newsletters")
            summarized_newsletters = self.summarizer.batch_summarize(cleaned_newsletters)
            
            # Step 4: Score importance
            logger.info("Step 4: Scoring newsletter importance")
            scored_newsletters = self.scorer.batch_score(summarized_newsletters)
            
            # Step 5: Filter by minimum score
            logger.info("Step 5: Filtering by importance score")
            filtered_newsletters = self.scorer.filter_by_score(scored_newsletters, min_score=2)
            
            if not filtered_newsletters:
                logger.warning("No newsletters meet minimum importance score")
                return self._create_empty_result()
            
            # Step 6: Compose digest
            logger.info("Step 6: Composing digest")
            digest_content = self.digest_composer.compose_digest(filtered_newsletters)
            digest_stats = self.digest_composer.get_digest_stats(filtered_newsletters)
            
            # Step 7: Create Notion entries (if available)
            notion_results = {'success_count': 0, 'failure_count': 0, 'total_count': 0}
            if self.notion_writer:
                logger.info("Step 7: Creating Notion entries")
                notion_entries = self.digest_composer.create_notion_entries(filtered_newsletters)
                notion_results = self.notion_writer.batch_create_pages(notion_entries)
            else:
                logger.info("Step 7: Skipping Notion integration (no credentials)")
            
            # Compile results
            results = {
                'success': True,
                'total_newsletters': len(sample_newsletters),
                'valid_newsletters': len(cleaned_newsletters),
                'processed_newsletters': len(filtered_newsletters),
                'notion_results': notion_results,
                'digest_stats': digest_stats,
                'digest_content': digest_content,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Test pipeline completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Test pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result when no newsletters are found."""
        return {
            'success': True,
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
            'digest_content': "No newsletters found for testing.",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_components(self) -> Dict[str, bool]:
        """
        Test individual components.
        
        Returns:
            Dictionary with component test results
        """
        results = {}
        
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
        
        # Test Notion connection (if available)
        if self.notion_writer:
            try:
                results['notion'] = self.notion_writer.test_connection()
                if results['notion']:
                    logger.info("Notion connection test: PASSED")
                else:
                    logger.error("Notion connection test: FAILED")
            except Exception as e:
                results['notion'] = False
                logger.error(f"Notion connection test: FAILED - {e}")
        else:
            results['notion'] = False
            logger.warning("Notion connection test: SKIPPED (no credentials)")
        
        return results
    
    def print_digest(self, digest_content: str):
        """Print the digest content to console."""
        print("\n" + "="*60)
        print("NEWSLETTER DIGEST")
        print("="*60)
        print(digest_content)
        print("="*60)

def main():
    """Main entry point for the test pipeline."""
    try:
        pipeline = TestNewsletterPipeline()
        
        # Test connections first
        logger.info("Testing connections...")
        connection_results = pipeline.test_components()
        
        if not connection_results.get('cerebras', False):
            logger.error("Cerebras connection failed. Please check your API key.")
            print("\n🔧 To get Cerebras API key:")
            print("1. Visit https://cloud.cerebras.net")
            print("2. Sign up for free account")
            print("3. Get your API key from the dashboard")
            print("4. Add CEREBRAS_API_KEY to your .env file")
            return
        
        # Run the test pipeline
        results = pipeline.run_test_pipeline()
        
        if results['success']:
            logger.info("Test pipeline completed successfully!")
            print(f"\n🧪 Test Pipeline Complete!")
            print(f"�� Processed {results['processed_newsletters']} newsletters")
            print(f"📈 Notion entries created: {results['notion_results']['success_count']}")
            print(f"⭐ Average importance score: {results['digest_stats']['average_score']}")
            
            # Print the digest
            pipeline.print_digest(results['digest_content'])
        else:
            logger.error("Test pipeline failed!")
            print(f"❌ Test pipeline failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()