"""
Scorer Component

Uses Cerebras to assign importance scores (1-5) to newsletters based on relevance to tech audience.
Falls back to OpenRouter.ai if Cerebras returns 429 rate limit errors.
"""

import os
from typing import Dict, Any, List
import logging
import requests
from cerebras.cloud.sdk import Cerebras

# OpenRouter API endpoint
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

logger = logging.getLogger(__name__)

class Scorer:
    """AI-powered newsletter importance scorer with Cerebras primary and OpenRouter fallback."""
    
    def __init__(self, api_key: str = None, model: str = "qwen-3-coder-480b", openrouter_key: str = None, openrouter_model: str = None):
        """
        Initialize the scorer.
        
        Args:
            api_key: Cerebras API key (optional, uses env var if not provided)
            model: Cerebras model to use
            openrouter_key: OpenRouter.ai API key (optional, uses env var if not provided)
            openrouter_model: OpenRouter.ai model to use (optional)
        """
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.openrouter_model = openrouter_model or "z-ai/glm-4.5-air:free"
        self.client = Cerebras(api_key=self.api_key)
        
        # Scoring prompt template
        self.scoring_prompt = """
Rate the importance of this newsletter on a scale of 1-5 for a tech entrepreneur/developer audience.

Consider these factors:
- Relevance to technology, programming, AI, startups, business
- Actionable insights or tools
- Industry significance and impact
- Quality of information and analysis
- Potential value for professional development

Scoring guide:
1 = Not relevant or low quality
2 = Somewhat relevant but limited value
3 = Moderately relevant with some useful information
4 = Highly relevant with valuable insights
5 = Extremely relevant with exceptional value

Newsletter subject: {subject}
Newsletter content: {content}
Summary: {summary}

Respond with only a number from 1 to 5.
"""
        
        # Alternative scoring prompt for when we have limited content
        self.simple_scoring_prompt = """
Rate this newsletter's importance (1-5) for a tech audience:

Subject: {subject}
Summary: {summary}

1=Not relevant, 2=Somewhat relevant, 3=Moderately relevant, 4=Highly relevant, 5=Extremely relevant

Respond with only a number from 1 to 5.
"""
    
    def score_newsletter(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a newsletter's importance using Cerebras.
        
        Args:
            email_data: Email data with content and summary
            
        Returns:
            Email data with added importance score
        """
        try:
            subject = email_data.get('subject', '')
            content = email_data.get('cleaned_body', '')
            summary = email_data.get('full_summary', '')
            
            if not content and not summary:
                logger.warning("No content to score")
                return email_data
            
            # Choose appropriate prompt based on available content
            if content:
                prompt = self.scoring_prompt.format(
                    subject=subject,
                    content=content[:2000],  # Limit content length
                    summary=summary
                )
            else:
                prompt = self.simple_scoring_prompt.format(
                    subject=subject,
                    summary=summary
                )
            
            # Call Cerebras
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content evaluator. Respond with only a number from 1 to 5."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                stream=False,
                max_completion_tokens=5,
                temperature=0.1,
                top_p=0.8
            )
            
            score_text = response.choices[0].message.content.strip()
            score = self._parse_score(score_text)
            
            # Update email data
            scored_email = email_data.copy()
            scored_email['importance_score'] = score
            
            logger.info(f"Scored '{subject}': {score}/5")
            
            return scored_email
            
        except Exception as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.warning("Cerebras rate limit exceeded. Falling back to OpenRouter.ai.")
                return self._score_with_openrouter(email_data, prompt)
            else:
                logger.error(f"Error scoring newsletter: {e}")
                # Return with default score
                email_data['importance_score'] = 3  # Default middle score
                return email_data
    
    def _score_with_openrouter(self, email_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Fallback scoring using OpenRouter.ai"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Newsletter Digest Bot"
            }
            
            # Verify API key is present
            if not self.openrouter_key or not self.openrouter_key.strip():
                logger.error("OpenRouter API key is missing or empty")
                return {'score': 1, 'reasoning': 'OpenRouter API key missing - using default score'}
            data = {
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a content evaluator. Respond with only a number from 1 to 5."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 5,
                "temperature": 0.1,
                "top_p": 0.8
            }
            
            response = requests.post(OPENROUTER_ENDPOINT, 
                                   headers=headers, json=data, timeout=30)
            
            logger.info(f"OpenRouter response status: {response.status_code}")
            logger.info(f"OpenRouter response headers: {dict(response.headers)}")
            logger.info(f"OpenRouter response text: {response.text[:500]}...")
            
            response.raise_for_status()
            
            if not response.text.strip():
                logger.error("OpenRouter returned empty response")
                return {'score': 1, 'reasoning': 'OpenRouter fallback failed - using default score'}
            
            # Check if response is HTML (authentication failure)
            if response.text.strip().startswith('<!DOCTYPE html>'):
                logger.error("OpenRouter returned HTML instead of JSON - likely authentication failure")
                logger.error("Please verify your OpenRouter API key is valid and not expired")
                return {'score': 1, 'reasoning': 'OpenRouter authentication failed - using default score'}
            
            try:
                score_text = response.json()["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Failed to parse OpenRouter response: {e}")
                logger.error(f"Response content: {response.text[:200]}...")
                return {'score': 1, 'reasoning': 'OpenRouter response parsing failed - using default score'}
            score = self._parse_score(score_text)
            
            # Update email data
            scored_email = email_data.copy()
            scored_email['importance_score'] = score
            
            logger.info(f"Scored with OpenRouter: {email_data.get('subject', '')} -> {score}/5")
            
            return scored_email
            
        except Exception as e:
            logger.error(f"Error scoring newsletter with OpenRouter: {e}")
            # Return with default score
            email_data['importance_score'] = 3  # Default middle score
            return email_data
    
    def _parse_score(self, score_text: str) -> int:
        """
        Parse the score from Cerebras response.
        
        Args:
            score_text: Raw score text from Cerebras
            
        Returns:
            Parsed score (1-5)
        """
        try:
            # Extract numbers from the response
            import re
            numbers = re.findall(r'\d+', score_text)
            
            if numbers:
                score = int(numbers[0])
                # Ensure score is within valid range
                if 1 <= score <= 5:
                    return score
            
            # If no valid number found, try to interpret the text
            score_text_lower = score_text.lower()
            if 'five' in score_text_lower or '5' in score_text_lower:
                return 5
            elif 'four' in score_text_lower or '4' in score_text_lower:
                return 4
            elif 'three' in score_text_lower or '3' in score_text_lower:
                return 3
            elif 'two' in score_text_lower or '2' in score_text_lower:
                return 2
            elif 'one' in score_text_lower or '1' in score_text_lower:
                return 1
            
            # Default to middle score
            return 3
            
        except Exception as e:
            logger.error(f"Error parsing score '{score_text}': {e}")
            return 3  # Default middle score
    
    def batch_score(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score multiple newsletters in batch.
        
        Args:
            emails: List of email data
            
        Returns:
            List of scored email data
        """
        scored_emails = []
        
        for email_data in emails:
            try:
                scored_email = self.score_newsletter(email_data)
                scored_emails.append(scored_email)
            except Exception as e:
                logger.error(f"Error scoring email {email_data.get('subject', 'Unknown')}: {e}")
                # Add default score
                email_data['importance_score'] = 3
                scored_emails.append(email_data)
        
        return scored_emails
    
    def get_score_description(self, score: int) -> str:
        """
        Get a description for a score.
        
        Args:
            score: Importance score (1-5)
            
        Returns:
            Description of the score
        """
        descriptions = {
            1: "Not relevant",
            2: "Somewhat relevant", 
            3: "Moderately relevant",
            4: "Highly relevant",
            5: "Extremely relevant"
        }
        
        return descriptions.get(score, "Unknown")
    
    def filter_by_score(self, emails: List[Dict[str, Any]], min_score: int = 3) -> List[Dict[str, Any]]:
        """
        Filter emails by minimum importance score.
        
        Args:
            emails: List of email data
            min_score: Minimum score to include (default: 3)
            
        Returns:
            Filtered list of emails
        """
        filtered_emails = [
            email for email in emails 
            if email.get('importance_score', 0) >= min_score
        ]
        
        logger.info(f"Filtered to {len(filtered_emails)} emails with score >= {min_score}")
        return filtered_emails