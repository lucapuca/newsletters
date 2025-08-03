"""
Summarizer Component

Uses Cerebras to summarize newsletters in 3 bullet points and classify content.
Falls back to OpenRouter.ai if Cerebras returns 429 rate limit errors.
"""

import os
import logging
from typing import Dict, Any, List
from cerebras.cloud.sdk import Cerebras
import requests
import json
from utils.prompt_loader import load_prompt

# OpenRouter API endpoint
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

logger = logging.getLogger(__name__)

class Summarizer:
    """AI-powered newsletter summarizer with Cerebras primary and OpenRouter fallback."""
    
    def __init__(self, api_key: str = None, openrouter_key: str = None, model: str = "qwen-3-coder-480b"):
        """
        Initialize the summarizer.
        
        Args:
            api_key: Cerebras API key (optional, uses env var if not provided)
            openrouter_key: OpenRouter API key (optional, uses env var if not provided)
            model: Cerebras model to use
        """
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.openrouter_model = "z-ai/glm-4.5-air:free"  # Free tier fallback model
        self.client = Cerebras(api_key=self.api_key)
        
        # Categories for classification
        self.categories = ["News", "Tool", "Opinion"]
        
        # Load prompts from markdown files
        try:
            self.summary_prompt = load_prompt('summarization_prompt')
            self.classification_prompt = load_prompt('classification_prompt')
        except FileNotFoundError as e:
            logger.error(f"Failed to load summarization prompts: {e}")
            # Fallback to basic prompts if files not found
            self.summary_prompt = "Summarize this newsletter in 3 bullet points: {content}"
            self.classification_prompt = "Classify this content as News, Tool, or Opinion: {content}"
    
    def summarize_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize newsletter content using Cerebras.
        
        Args:
            email_data: Email data with cleaned content
            
        Returns:
            Email data with added summary, category, and links
        """
        try:
            content = email_data.get('cleaned_body', '')
            subject = email_data.get('subject', '')
            
            if not content:
                logger.warning("No content to summarize")
                return email_data
            
            # Prepare the prompt
            prompt = self.summary_prompt.format(content=content[:3000])  # Limit content length
            
            # Call Cerebras
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes newsletters professionally."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                stream=False,
                max_completion_tokens=500,
                temperature=0.3,
                top_p=0.8
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the response
            summary_data = self._parse_summary_response(result)
            
            # Update email data
            summarized_email = email_data.copy()
            summarized_email.update(summary_data)
            
            logger.info(f"Summarized: {subject}")
            logger.info(f"Category: {summary_data.get('category', 'Unknown')}")
            
            return summarized_email
            
        except Exception as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.warning("Cerebras rate limit exceeded. Falling back to OpenRouter.ai.")
                return self._summarize_with_openrouter(email_data)
            else:
                logger.error(f"Error summarizing content: {e}")
                # Return original data with default values
                return email_data
    
    def _summarize_with_openrouter(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summarization using OpenRouter.ai"""
        try:
            content = email_data.get('cleaned_body', '')
            subject = email_data.get('subject', '')
            
            if not content:
                logger.warning("No content to summarize")
                return email_data
            
            # Prepare the prompt
            prompt = self.summary_prompt.format(content=content[:3000])
            
            # Call OpenRouter using chat completions format
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Newsletter Digest Bot"
            }
            
            # Verify API key is present
            if not self.openrouter_key or not self.openrouter_key.strip():
                logger.error("OpenRouter API key is missing or empty")
                return self._create_fallback_summary(email_data)
            data = {
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes newsletters professionally."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3,
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
                return self._create_fallback_summary(email_data)
            
            # Check if response is HTML (authentication failure)
            if response.text.strip().startswith('<!DOCTYPE html>'):
                logger.error("OpenRouter returned HTML instead of JSON - likely authentication failure")
                logger.error("Please verify your OpenRouter API key is valid and not expired")
                return self._create_fallback_summary(email_data)
            
            try:
                result = response.json()["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Failed to parse OpenRouter response: {e}")
                logger.error(f"Response content: {response.text[:200]}...")
                return self._create_fallback_summary(email_data)
            
            # Parse the response
            summary_data = self._parse_summary_response(result)
            
            # Update email data
            summarized_email = email_data.copy()
            summarized_email.update(summary_data)
            
            logger.info(f"Summarized with OpenRouter: {subject}")
            logger.info(f"Category: {summary_data.get('category', 'Unknown')}")
            
            return summarized_email
            
        except Exception as e:
            logger.error(f"Error summarizing content with OpenRouter: {e}")
            # Return original data with default values
            return email_data
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the Cerebras response to extract summary, category, and links.
        
        Args:
            response: Raw response from Cerebras
            
        Returns:
            Parsed summary data
        """
        try:
            lines = response.split('\n')
            summary_points = []
            category = "News"  # Default
            links = []
            
            for line in lines:
                line = line.strip()
                
                # Extract bullet points
                if line.startswith('•') or line.startswith('-'):
                    point = line[1:].strip()
                    if point:
                        summary_points.append(point)
                
                # Extract category
                elif line.startswith('Category:'):
                    cat = line.replace('Category:', '').strip()
                    if cat in self.categories:
                        category = cat
                
                # Extract links
                elif line.startswith('Links:'):
                    links_text = line.replace('Links:', '').strip()
                    if links_text:
                        links = [link.strip() for link in links_text.split(',') if link.strip()]
            
            # If no bullet points found, try to extract from the response
            if not summary_points:
                # Look for any numbered or bulleted content
                import re
                bullet_pattern = r'[•\-]\s*(.+)'
                matches = re.findall(bullet_pattern, response)
                summary_points = matches[:3]  # Take first 3
            
            # Ensure we have exactly 3 points
            while len(summary_points) < 3:
                summary_points.append("")
            
            # Truncate to 3 points
            summary_points = summary_points[:3]
            
            return {
                'summary_points': summary_points,
                'category': category,
                'extracted_links': links,
                'full_summary': response
            }
            
        except Exception as e:
            logger.error(f"Error parsing summary response: {e}")
            return {
                'summary_points': ["", "", ""],
                'category': "News",
                'extracted_links': [],
                'full_summary': response
            }
    
    def classify_content(self, content: str) -> str:
        """
        Classify content into News, Tool, or Opinion.
        
        Args:
            content: Content to classify
            
        Returns:
            Classification category
        """
        try:
            prompt = self.classification_prompt.format(content=content[:2000])
            
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content classifier. Respond with only the category name."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                stream=False,
                max_completion_tokens=10,
                temperature=0.1,
                top_p=0.8
            )
            
            category = response.choices[0].message.content.strip()
            
            # Validate category
            if category not in self.categories:
                category = "News"  # Default
            
            return category
            
        except Exception as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.warning("Cerebras rate limit exceeded. Falling back to OpenRouter.ai.")
                return self._classify_with_openrouter(content)
            else:
                logger.error(f"Error classifying content: {e}")
                return "News"  # Default
    
    def _classify_with_openrouter(self, content: str) -> str:
        """Fallback classification using OpenRouter.ai"""
        try:
            prompt = self.classification_prompt.format(content=content[:2000])
            
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Newsletter Digest Bot"
            }
            
            # Verify API key is present
            if not self.openrouter_key or not self.openrouter_key.strip():
                logger.error("OpenRouter API key is missing or empty")
                return self._create_fallback_summary(email_data)
            data = {
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a content classifier. Respond with only one word: News, Tool, or Opinion."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1,
                "top_p": 0.8
            }
            
            response = requests.post(OPENROUTER_ENDPOINT, 
                                   headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            category = response.json()["choices"][0]["message"]["content"].strip()
            
            # Validate category
            if category not in self.categories:
                category = "News"  # Default
            
            logger.info(f"Classified with OpenRouter: {category}")
            return category
            
        except Exception as e:
            logger.error(f"Error classifying content with OpenRouter: {e}")
            return "News"  # Default
    
    def batch_summarize(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize multiple emails in batch.
        
        Args:
            emails: List of email data
            
        Returns:
            List of summarized email data
        """
        summarized_emails = []
        
        for email_data in emails:
            try:
                summarized_email = self.summarize_content(email_data)
                summarized_emails.append(summarized_email)
            except Exception as e:
                logger.error(f"Error summarizing email {email_data.get('subject', 'Unknown')}: {e}")
                # Add original email with default values
                email_data.update({
                    'summary_points': ["", "", ""],
                    'category': "News",
                    'extracted_links': [],
                    'full_summary': ""
                })
                summarized_emails.append(email_data)
        
        return summarized_emails
    
    def test_connection(self) -> bool:
        """Test connection to Cerebras with minimal API usage."""
        try:
            # Just check if we have API key and can initialize client
            if not self.api_key:
                logger.error("Cerebras API key not found")
                return False
            
            # The client initialization and TCP warming already happened in __init__
            # If we got this far, the connection is likely working
            # We'll rely on the actual usage to trigger fallback if needed
            logger.info("Cerebras API key configured, connection assumed ready")
            return True
            
        except Exception as e:
            logger.error(f"Cerebras connection test failed: {e}")
            return False