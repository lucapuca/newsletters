"""
Tests for the main NewsletterDigestPipeline.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the parent directory to the path so we can import components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import NewsletterDigestPipeline
from tests.fixtures import (
    SAMPLE_EMAIL_DATA, SAMPLE_CLEANED_EMAIL, 
    SAMPLE_SUMMARIZED_EMAIL, SAMPLE_SCORED_EMAIL
)


class TestNewsletterDigestPipeline(unittest.TestCase):
    """Test cases for NewsletterDigestPipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock all environment variables
        self.env_patcher = patch.dict(os.environ, {
            'CEREBRAS_API_KEY': 'test_cerebras_key',
            'OPENROUTER_API_KEY': 'test_openrouter_key',
            'EMAIL': 'test@example.com',
            'EMAIL_PASSWORD': 'test_password',
            'NOTION_TOKEN': 'test_notion_token',
            'NOTION_DATABASE_ID': 'test_database_id'
        })
        self.env_patcher.start()
        
        # Mock all component classes
        self.email_reader_patcher = patch('main.EmailReader')
        self.content_cleaner_patcher = patch('main.ContentCleaner')
        self.summarizer_patcher = patch('main.Summarizer')
        self.scorer_patcher = patch('main.Scorer')
        self.digest_composer_patcher = patch('main.DigestComposer')
        self.notion_writer_patcher = patch('main.NotionWriter')
        
        self.mock_email_reader = self.email_reader_patcher.start()
        self.mock_content_cleaner = self.content_cleaner_patcher.start()
        self.mock_summarizer = self.summarizer_patcher.start()
        self.mock_scorer = self.scorer_patcher.start()
        self.mock_digest_composer = self.digest_composer_patcher.start()
        self.mock_notion_writer = self.notion_writer_patcher.start()
        
        # Set up mock instances
        self.mock_email_reader_instance = Mock()
        self.mock_content_cleaner_instance = Mock()
        self.mock_summarizer_instance = Mock()
        self.mock_scorer_instance = Mock()
        self.mock_digest_composer_instance = Mock()
        self.mock_notion_writer_instance = Mock()
        
        self.mock_email_reader.return_value = self.mock_email_reader_instance
        self.mock_content_cleaner.return_value = self.mock_content_cleaner_instance
        self.mock_summarizer.return_value = self.mock_summarizer_instance
        self.mock_scorer.return_value = self.mock_scorer_instance
        self.mock_digest_composer.return_value = self.mock_digest_composer_instance
        self.mock_notion_writer.return_value = self.mock_notion_writer_instance
        
        self.pipeline = NewsletterDigestPipeline()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.email_reader_patcher.stop()
        self.content_cleaner_patcher.stop()
        self.summarizer_patcher.stop()
        self.scorer_patcher.stop()
        self.digest_composer_patcher.stop()
        self.notion_writer_patcher.stop()
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        self.assertIsNotNone(self.pipeline.email_reader)
        self.assertIsNotNone(self.pipeline.content_cleaner)
        self.assertIsNotNone(self.pipeline.summarizer)
        self.assertIsNotNone(self.pipeline.scorer)
        self.assertIsNotNone(self.pipeline.digest_composer)
        self.assertIsNotNone(self.pipeline.notion_writer)
    
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        # Should not raise any exception
        try:
            self.pipeline._validate_environment()
        except SystemExit:
            self.fail("Environment validation failed unexpectedly")
    
    def test_validate_environment_missing_vars(self):
        """Test environment validation with missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                self.pipeline._validate_environment()
    
    def test_test_connections_all_pass(self):
        """Test connection testing when all connections pass."""
        # Mock all connections to return True
        self.mock_email_reader_instance.test_connection.return_value = True
        self.mock_summarizer_instance.test_connection.return_value = True
        self.mock_notion_writer_instance.test_connection.return_value = True
        
        results = self.pipeline.test_connections()
        
        self.assertTrue(results['gmail'])
        self.assertTrue(results['cerebras'])
        self.assertTrue(results['notion'])
    
    def test_test_connections_some_fail(self):
        """Test connection testing when some connections fail."""
        # Mock mixed connection results
        self.mock_email_reader_instance.test_connection.return_value = True
        self.mock_summarizer_instance.test_connection.return_value = False
        self.mock_notion_writer_instance.test_connection.return_value = True
        
        results = self.pipeline.test_connections()
        
        self.assertTrue(results['gmail'])
        self.assertFalse(results['cerebras'])
        self.assertTrue(results['notion'])
    
    def test_run_pipeline_success(self):
        """Test successful pipeline execution."""
        # Mock the entire pipeline flow
        self.mock_email_reader_instance.fetch_unread_emails.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_email_reader_instance.filter_newsletters.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_content_cleaner_instance.clean_email.return_value = SAMPLE_CLEANED_EMAIL
        self.mock_summarizer_instance.summarize_content.return_value = SAMPLE_SUMMARIZED_EMAIL
        self.mock_scorer_instance.score_newsletter.return_value = SAMPLE_SCORED_EMAIL
        self.mock_scorer_instance.filter_by_score.return_value = [SAMPLE_SCORED_EMAIL]
        self.mock_digest_composer_instance.compose_digest.return_value = "Test digest"
        self.mock_notion_writer_instance.create_page.return_value = True
        self.mock_notion_writer_instance.create_digest_page.return_value = True
        
        results = self.pipeline.run()
        
        # Verify results
        self.assertEqual(results['total_emails'], 1)
        self.assertEqual(results['filtered_emails'], 1)
        self.assertEqual(results['processed_emails'], 1)
        self.assertEqual(results['successful_entries'], 1)
        self.assertEqual(results['failed_entries'], 0)
        self.assertTrue(results['digest_created'])
        
        # Verify all components were called
        self.mock_email_reader_instance.fetch_unread_emails.assert_called_once()
        self.mock_email_reader_instance.filter_newsletters.assert_called_once()
        self.mock_content_cleaner_instance.clean_email.assert_called_once()
        self.mock_summarizer_instance.summarize_content.assert_called_once()
        self.mock_scorer_instance.score_newsletter.assert_called_once()
        self.mock_notion_writer_instance.create_page.assert_called_once()
        self.mock_notion_writer_instance.create_digest_page.assert_called_once()
    
    def test_run_pipeline_no_emails(self):
        """Test pipeline execution with no emails."""
        # Mock no emails found
        self.mock_email_reader_instance.fetch_unread_emails.return_value = []
        self.mock_email_reader_instance.filter_newsletters.return_value = []
        
        results = self.pipeline.run()
        
        # Verify results
        self.assertEqual(results['total_emails'], 0)
        self.assertEqual(results['filtered_emails'], 0)
        self.assertEqual(results['processed_emails'], 0)
        self.assertEqual(results['successful_entries'], 0)
        self.assertEqual(results['failed_entries'], 0)
        self.assertFalse(results['digest_created'])
        
        # Verify early exit - summarizer and scorer should not be called
        self.mock_summarizer_instance.summarize_content.assert_not_called()
        self.mock_scorer_instance.score_newsletter.assert_not_called()
    
    def test_run_pipeline_processing_errors(self):
        """Test pipeline execution with processing errors."""
        # Mock email fetch success but processing failures
        self.mock_email_reader_instance.fetch_unread_emails.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_email_reader_instance.filter_newsletters.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_content_cleaner_instance.clean_email.return_value = SAMPLE_CLEANED_EMAIL
        self.mock_summarizer_instance.summarize_content.side_effect = Exception("Summarization failed")
        self.mock_scorer_instance.filter_by_score.return_value = []
        
        results = self.pipeline.run()
        
        # Should handle errors gracefully
        self.assertEqual(results['total_emails'], 1)
        self.assertEqual(results['filtered_emails'], 1)
        self.assertEqual(results['failed_entries'], 1)
        self.assertEqual(results['successful_entries'], 0)
    
    def test_run_pipeline_notion_failures(self):
        """Test pipeline execution with Notion API failures."""
        # Mock successful processing but Notion failures
        self.mock_email_reader_instance.fetch_unread_emails.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_email_reader_instance.filter_newsletters.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_content_cleaner_instance.clean_email.return_value = SAMPLE_CLEANED_EMAIL
        self.mock_summarizer_instance.summarize_content.return_value = SAMPLE_SUMMARIZED_EMAIL
        self.mock_scorer_instance.score_newsletter.return_value = SAMPLE_SCORED_EMAIL
        self.mock_scorer_instance.filter_by_score.return_value = [SAMPLE_SCORED_EMAIL]
        self.mock_notion_writer_instance.create_page.side_effect = Exception("Notion API failed")
        
        results = self.pipeline.run()
        
        # Should handle Notion failures
        self.assertEqual(results['processed_emails'], 1)
        self.assertEqual(results['failed_entries'], 1)
        self.assertEqual(results['successful_entries'], 0)
    
    def test_run_pipeline_filtered_out_by_score(self):
        """Test pipeline execution where emails are filtered out by score."""
        # Mock successful processing but low scores
        self.mock_email_reader_instance.fetch_unread_emails.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_email_reader_instance.filter_newsletters.return_value = [SAMPLE_EMAIL_DATA]
        self.mock_content_cleaner_instance.clean_email.return_value = SAMPLE_CLEANED_EMAIL
        self.mock_summarizer_instance.summarize_content.return_value = SAMPLE_SUMMARIZED_EMAIL
        
        # Mock low score that gets filtered out
        low_score_email = SAMPLE_SCORED_EMAIL.copy()
        low_score_email['importance_score'] = 1
        self.mock_scorer_instance.score_newsletter.return_value = low_score_email
        self.mock_scorer_instance.filter_by_score.return_value = []  # Filtered out
        
        results = self.pipeline.run()
        
        # Should process but not create entries due to low score
        self.assertEqual(results['processed_emails'], 1)
        self.assertEqual(results['min_score_emails'], 0)
        self.assertFalse(results['digest_created'])
        
        # Notion should not be called for individual entries
        self.mock_notion_writer_instance.create_page.assert_not_called()
    
    def test_run_pipeline_partial_success(self):
        """Test pipeline execution with partial success."""
        # Mock multiple emails with mixed results
        emails = [SAMPLE_EMAIL_DATA, SAMPLE_EMAIL_DATA.copy()]
        self.mock_email_reader_instance.fetch_unread_emails.return_value = emails
        self.mock_email_reader_instance.filter_newsletters.return_value = emails
        
        # Mock first email success, second email failure
        def clean_side_effect(email):
            if email == emails[0]:
                return SAMPLE_CLEANED_EMAIL
            else:
                raise Exception("Cleaning failed")
        
        self.mock_content_cleaner_instance.clean_email.side_effect = clean_side_effect
        self.mock_summarizer_instance.summarize_content.return_value = SAMPLE_SUMMARIZED_EMAIL
        self.mock_scorer_instance.score_newsletter.return_value = SAMPLE_SCORED_EMAIL
        self.mock_scorer_instance.filter_by_score.return_value = [SAMPLE_SCORED_EMAIL]
        self.mock_notion_writer_instance.create_page.return_value = True
        self.mock_notion_writer_instance.create_digest_page.return_value = True
        self.mock_digest_composer_instance.compose_digest.return_value = "Test digest"
        
        results = self.pipeline.run()
        
        # Should have partial success
        self.assertEqual(results['total_emails'], 2)
        self.assertEqual(results['successful_entries'], 1)
        self.assertEqual(results['failed_entries'], 1)
        self.assertTrue(results['digest_created'])


if __name__ == '__main__':
    unittest.main()
