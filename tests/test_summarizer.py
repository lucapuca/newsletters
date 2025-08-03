"""
Tests for the Summarizer component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the parent directory to the path so we can import components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.summarizer import Summarizer
from tests.fixtures import (
    SAMPLE_CLEANED_EMAIL, SAMPLE_SUMMARIZED_EMAIL,
    MOCK_SUMMARIZATION_RESPONSE, MOCK_CLASSIFICATION_RESPONSE,
    TOOL_NEWSLETTER, OPINION_NEWSLETTER
)


class TestSummarizer(unittest.TestCase):
    """Test cases for Summarizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'CEREBRAS_API_KEY': 'test_cerebras_key',
            'OPENROUTER_API_KEY': 'test_openrouter_key'
        })
        self.env_patcher.start()
        
        # Mock the AIClient
        self.ai_client_patcher = patch('components.summarizer.create_ai_client')
        self.mock_ai_client_factory = self.ai_client_patcher.start()
        self.mock_ai_client = Mock()
        self.mock_ai_client_factory.return_value = self.mock_ai_client
        
        # Mock prompt loader
        self.prompt_patcher = patch('components.summarizer.load_prompt')
        self.mock_load_prompt = self.prompt_patcher.start()
        self.mock_load_prompt.side_effect = self._mock_prompt_loader
        
        self.summarizer = Summarizer()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.ai_client_patcher.stop()
        self.prompt_patcher.stop()
    
    def _mock_prompt_loader(self, prompt_name):
        """Mock prompt loader responses."""
        prompts = {
            'summarization_prompt': 'Summarize this newsletter in 3 bullet points: {content}',
            'classification_prompt': 'Classify this content as News, Tool, or Opinion: {content}'
        }
        return prompts.get(prompt_name, 'Mock prompt')
    
    def test_summarizer_initialization(self):
        """Test summarizer initialization."""
        self.assertIsNotNone(self.summarizer.api_key)
        self.assertIsNotNone(self.summarizer.openrouter_key)
        self.assertEqual(self.summarizer.model, "qwen-3-coder-480b")
        self.assertEqual(self.summarizer.categories, ["News", "Tool", "Opinion"])
    
    def test_summarize_content_success(self):
        """Test successful content summarization."""
        # Mock AIClient response
        self.mock_ai_client.chat_completion.return_value = MOCK_SUMMARIZATION_RESPONSE
        
        result = self.summarizer.summarize_content(SAMPLE_CLEANED_EMAIL.copy())
        
        self.assertIn('summary_points', result)
        self.assertIn('category', result)
        self.assertIn('extracted_links', result)
        self.assertIn('full_summary', result)
        
        # Verify summary points
        self.assertEqual(len(result['summary_points']), 3)
        self.assertEqual(result['category'], 'News')
    
    def test_summarize_content_cerebras_rate_limit(self):
        """Test fallback to OpenRouter when Cerebras hits rate limit."""
        # Mock Cerebras rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        self.mock_ai_client.chat_completion.side_effect = rate_limit_error
        
        # Mock OpenRouter response
        with patch('components.summarizer.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": MOCK_SUMMARIZATION_RESPONSE}}]
            }
            mock_response.text = MOCK_SUMMARIZATION_RESPONSE
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = self.summarizer.summarize_content(SAMPLE_CLEANED_EMAIL.copy())
            
            # Verify OpenRouter was called
            mock_post.assert_called_once()
            # Since OpenRouter fallback is implemented, should have summary data
            self.assertIn('summary_points', result)
            self.assertEqual(result['category'], 'News')
    
    def test_summarize_content_both_apis_fail(self):
        """Test handling when both Cerebras and OpenRouter fail."""
        # Mock Cerebras failure
        self.mock_ai_client.chat_completion.side_effect = Exception("API Error")
        
        result = self.summarizer.summarize_content(SAMPLE_CLEANED_EMAIL.copy())
        
        # Should return original data (graceful degradation)
        self.assertEqual(result['subject'], SAMPLE_CLEANED_EMAIL['subject'])
        self.assertEqual(result['cleaned_body'], SAMPLE_CLEANED_EMAIL['cleaned_body'])
    
    def test_parse_summary_response(self):
        """Test parsing of summarization response."""
        response = MOCK_SUMMARIZATION_RESPONSE
        parsed = self.summarizer._parse_summary_response(response)
        
        self.assertIn('summary_points', parsed)
        self.assertIn('category', parsed)
        self.assertIn('extracted_links', parsed)
        self.assertIn('full_summary', parsed)
        
        # Verify summary points
        self.assertEqual(len(parsed['summary_points']), 3)
        self.assertTrue(all(point.strip() for point in parsed['summary_points']))
        
        # Verify category
        self.assertIn(parsed['category'], self.summarizer.categories)
    
    def test_parse_summary_response_malformed(self):
        """Test parsing of malformed response."""
        malformed_responses = [
            "Just some text without proper format",
            "• Only one bullet point\nCategory: News",
            "",
            "No bullets or category here"
        ]
        
        for response in malformed_responses:
            with self.subTest(response=response):
                parsed = self.summarizer._parse_summary_response(response)
                
                # Should have default structure
                self.assertIn('summary_points', parsed)
                self.assertIn('category', parsed)
                self.assertEqual(len(parsed['summary_points']), 3)
                self.assertEqual(parsed['category'], 'News')  # Default
    
    def test_classify_content_success(self):
        """Test successful content classification."""
        # Mock AIClient response
        self.mock_ai_client.chat_completion.return_value = "Tool"
        
        result = self.summarizer.classify_content("This is about a new development tool")
        
        self.assertEqual(result, "Tool")
        self.mock_ai_client.chat_completion.assert_called_once()
    
    def test_classify_content_invalid_category(self):
        """Test classification with invalid category response."""
        # Mock Cerebras response with invalid category
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "InvalidCategory"
        self.mock_ai_client.chat_completion.return_value = mock_response
        
        category = self.summarizer.classify_content("Some content")
        self.assertEqual(category, "News")  # Should default to News
    
    def test_classify_content_rate_limit_fallback(self):
        """Test classification fallback to OpenRouter."""
        # Mock Cerebras rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        self.mock_cerebras_client.chat.completions.create.side_effect = rate_limit_error
        
        # Mock OpenRouter response
        with patch('components.summarizer.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Opinion"}}]
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            category = self.summarizer.classify_content(OPINION_NEWSLETTER['cleaned_body'])
            
            # Verify OpenRouter was called
            mock_post.assert_called_once()
            self.assertEqual(category, "Opinion")
    
    def test_batch_summarize(self):
        """Test batch summarization functionality."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = MOCK_SUMMARIZATION_RESPONSE
        self.mock_cerebras_client.chat.completions.create.return_value = mock_response
        
        emails = [SAMPLE_CLEANED_EMAIL.copy(), SAMPLE_CLEANED_EMAIL.copy()]
        results = self.summarizer.batch_summarize(emails)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('summary_points', result)
            self.assertIn('category', result)
            self.assertEqual(len(result['summary_points']), 3)
    
    def test_batch_summarize_with_failures(self):
        """Test batch summarization with some failures."""
        # Mock mixed responses - first succeeds, second fails
        def side_effect(*args, **kwargs):
            if not hasattr(side_effect, 'call_count'):
                side_effect.call_count = 0
            side_effect.call_count += 1
            
            if side_effect.call_count == 1:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = MOCK_SUMMARIZATION_RESPONSE
                return mock_response
            else:
                raise Exception("API Error")
        
        self.mock_cerebras_client.chat.completions.create.side_effect = side_effect
        
        emails = [SAMPLE_CLEANED_EMAIL.copy(), SAMPLE_CLEANED_EMAIL.copy()]
        results = self.summarizer.batch_summarize(emails)
        
        # Should still return 2 results (graceful degradation)
        self.assertEqual(len(results), 2)
        
        # First should be summarized, second should be original
        self.assertIn('summary_points', results[0])
        self.assertEqual(results[1]['subject'], SAMPLE_CLEANED_EMAIL['subject'])
    
    def test_graceful_degradation_on_failure(self):
        """Test graceful degradation when AI fails completely."""
        # Mock both Cerebras and OpenRouter failures
        self.mock_cerebras_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('components.summarizer.requests.post') as mock_post:
            mock_post.side_effect = Exception("OpenRouter failed")
            
            result = self.summarizer.summarize_content(SAMPLE_CLEANED_EMAIL.copy())
            
            # Should return original data (graceful degradation)
            self.assertEqual(result['subject'], SAMPLE_CLEANED_EMAIL['subject'])
            self.assertEqual(result['cleaned_body'], SAMPLE_CLEANED_EMAIL['cleaned_body'])
    
    def test_test_connection(self):
        """Test connection testing functionality."""
        # Test with valid API key
        connection_ok = self.summarizer.test_connection()
        self.assertTrue(connection_ok)
        
        # Test with missing API key
        self.summarizer.api_key = None
        connection_failed = self.summarizer.test_connection()
        self.assertFalse(connection_failed)


if __name__ == '__main__':
    unittest.main()
