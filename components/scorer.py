"""
Scorer Component

Uses AI to assign importance scores (1-5) to newsletters based on relevance to tech audience.
Uses shared AIClient with Cerebras primary and OpenRouter fallback.
"""

import logging
from typing import Dict, Any, List
from utils.prompt_loader import load_prompt
from utils.ai_client import create_ai_client

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
        # Initialize shared AI client
        self.ai_client = create_ai_client(
            cerebras_key=api_key,
            openrouter_key=openrouter_key,
            cerebras_model=model,
            openrouter_model=openrouter_model or "z-ai/glm-4.5-air:free"
        )
        
        # Load prompts from markdown files
        try:
            self.scoring_prompt = load_prompt('scoring_prompt')
            self.simple_scoring_prompt = load_prompt('simple_scoring_prompt')
        except FileNotFoundError as e:
            logger.error(f"Failed to load scoring prompts: {e}")
            # Fallback to basic prompts if files not found
            self.scoring_prompt = "Rate this newsletter (1-5) for tech audience. Subject: {subject}, Content: {content}, Summary: {summary}. Respond with only a number."
            self.simple_scoring_prompt = "Rate this newsletter (1-5) for tech audience. Subject: {subject}, Summary: {summary}. Respond with only a number."
    
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
            
            # Choose appropriate prompt based on content availability
            prompt = self._choose_appropriate_prompt(email_data)
            
            # Make API call using shared client (handles fallback automatically)
            messages = [{
                "role": "user",
                "content": prompt
            }]
            
            system_prompt = "You are an expert at rating newsletter importance for tech professionals. Respond with only a number from 1-5."
            
            score_text = self.ai_client.chat_completion(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            score = self._parse_score(score_text)
            
            # Update email data
            scored_email = email_data.copy()
            scored_email['importance_score'] = score
            
            logger.info(f"Scored '{subject}': {score}/5")
            
            return scored_email
            
        except Exception as e:
            logger.error(f"Error scoring newsletter: {e}")
            # Return with default score
            email_data['importance_score'] = 3  # Default middle score
            return email_data
    
    def _choose_appropriate_prompt(self, email_data: Dict[str, Any]) -> str:
        subject = email_data.get('subject', '')
        content = email_data.get('cleaned_body', '')
        summary = email_data.get('full_summary', '')
        
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
        
        return prompt
    

    
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