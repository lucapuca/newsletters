"""
Tests for the Scorer component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the parent directory to the path so we can import components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.scorer import Scorer
from tests.fixtures import (
    SAMPLE_CLEANED_EMAIL, SAMPLE_SCORED_EMAIL, 
    MOCK_SCORING_RESPONSE, MOCK_CEREBRAS_SUCCESS_RESPONSE
)


class TestScorer(unittest.TestCase):
    """Test cases for Scorer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'CEREBRAS_API_KEY': 'test_cerebras_key',
            'OPENROUTER_API_KEY': 'test_openrouter_key'
        })
        self.env_patcher.start()
        
        # Mock the AIClient
        self.ai_client_patcher = patch('components.scorer.create_ai_client')
        self.mock_ai_client_factory = self.ai_client_patcher.start()
        self.mock_ai_client = Mock()
        self.mock_ai_client_factory.return_value = self.mock_ai_client
        
        # Mock prompt loader
        self.prompt_patcher = patch('components.scorer.load_prompt')
        self.mock_load_prompt = self.prompt_patcher.start()
        self.mock_load_prompt.side_effect = self._mock_prompt_loader
        
        self.scorer = Scorer()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.ai_client_patcher.stop()
        self.prompt_patcher.stop()
    
    def _mock_prompt_loader(self, prompt_name):
        """Mock prompt loader responses."""
        prompts = {
            'scoring_prompt': 'Rate this newsletter (1-5). Subject: {subject}, Content: {content}, Summary: {summary}. Respond with only a number.',
            'simple_scoring_prompt': 'Rate this newsletter (1-5). Subject: {subject}, Summary: {summary}. Respond with only a number.'
        }
        return prompts.get(prompt_name, 'Mock prompt')
    
    def test_scorer_initialization(self):
        """Test scorer initialization."""
        self.assertIsNotNone(self.scorer.api_key)
        self.assertIsNotNone(self.scorer.openrouter_key)
        self.assertEqual(self.scorer.model, "qwen-3-coder-480b")
        self.assertEqual(self.scorer.openrouter_model, "z-ai/glm-4.5-air:free")
    
    @patch('components.scorer.requests.post')
    def test_score_newsletter_success(self):
        """Test successful newsletter scoring."""
        # Mock AIClient response
        self.mock_ai_client.chat_completion.return_value = "4"
        
        result = self.scorer.score_newsletter(SAMPLE_CLEANED_EMAIL.copy())
        
        self.assertEqual(result['importance_score'], 4)
        self.mock_ai_client.chat_completion.assert_called_once()
    
    def test_score_newsletter_with_fallback(self):
        """Test scoring with AIClient handling fallback automatically."""
        # Mock AIClient response (it handles fallback internally)
        self.mock_ai_client.chat_completion.return_value = "3"
        
        result = self.scorer.score_newsletter(SAMPLE_CLEANED_EMAIL.copy())
        
        self.assertEqual(result['importance_score'], 3)
        self.mock_ai_client.chat_completion.assert_called_once()
    
    def test_score_newsletter_api_failure(self):
        """Test behavior when AIClient fails."""
        # Mock AIClient failure
        self.mock_ai_client.chat_completion.side_effect = Exception("API Error")
        
        result = self.scorer.score_newsletter(SAMPLE_CLEANED_EMAIL.copy())
        
        # Should return default score
        self.assertEqual(result['importance_score'], 3)
    
    def test_parse_score_valid_numbers(self):
        """Test parsing valid score responses."""
        test_cases = [
            ("4", 4),
            ("Score: 5", 5),
            ("The score is 2 out of 5", 2),
            ("1", 1),
            ("five", 5),
            ("three", 3)
        ]
        
        for response_text, expected_score in test_cases:
            with self.subTest(response=response_text):
                score = self.scorer._parse_score(response_text)
                self.assertEqual(score, expected_score)
    
    def test_parse_score_invalid_input(self):
        """Test parsing invalid score responses."""
        test_cases = [
            "no numbers here",
            "",
            "6",  # Out of range
            "0",  # Out of range
            None
        ]
        
        for response_text in test_cases:
            with self.subTest(response=response_text):
                score = self.scorer._parse_score(str(response_text) if response_text is not None else "")
                self.assertEqual(score, 3)  # Default score
    
    def test_choose_appropriate_prompt(self):
        """Test prompt selection based on available content."""
        # Test with full content (should use detailed prompt)
        email_with_content = {
            'subject': 'Test Subject',
            'cleaned_body': 'This is test content',
            'summary_points': ['Point 1', 'Point 2', 'Point 3']
        }
        
        # Mock Cerebras response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "4"
        self.mock_cerebras_client.chat.completions.create.return_value = mock_response
        
        result = self.scorer.score_newsletter(email_with_content)
        
        # Verify the call was made (indicating prompt was chosen)
        self.mock_cerebras_client.chat.completions.create.assert_called_once()
        call_args = self.mock_cerebras_client.chat.completions.create.call_args
        
        # The prompt should contain content and summary
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        self.assertIn('Test Subject', user_message)
        self.assertIn('This is test content', user_message)
    
    def test_batch_score(self):
        """Test batch scoring functionality."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "4"
        self.mock_cerebras_client.chat.completions.create.return_value = mock_response
        
        emails = [SAMPLE_CLEANED_EMAIL.copy(), SAMPLE_CLEANED_EMAIL.copy()]
        results = self.scorer.batch_score(emails)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('importance_score', result)
            self.assertEqual(result['importance_score'], 4)
    
    def test_filter_by_score(self):
        """Test filtering emails by minimum score."""
        emails = [
            {'subject': 'Email 1', 'importance_score': 5},
            {'subject': 'Email 2', 'importance_score': 3},
            {'subject': 'Email 3', 'importance_score': 2},
            {'subject': 'Email 4', 'importance_score': 4}
        ]
        
        # Filter with min_score=3
        filtered = self.scorer.filter_by_score(emails, min_score=3)
        self.assertEqual(len(filtered), 3)
        
        # Filter with min_score=4
        filtered = self.scorer.filter_by_score(emails, min_score=4)
        self.assertEqual(len(filtered), 2)
    
    def test_get_score_description(self):
        """Test score description mapping."""
        descriptions = {
            1: "Not relevant",
            2: "Somewhat relevant",
            3: "Moderately relevant", 
            4: "Highly relevant",
            5: "Extremely relevant"
        }
        
        for score, expected_desc in descriptions.items():
            with self.subTest(score=score):
                desc = self.scorer.get_score_description(score)
                self.assertEqual(desc, expected_desc)
        
        # Test invalid score
        desc = self.scorer.get_score_description(10)
        self.assertEqual(desc, "Unknown")


if __name__ == '__main__':
    unittest.main()
