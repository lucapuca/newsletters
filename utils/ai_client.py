"""
AI Client Utility

Shared client for Cerebras and OpenRouter API calls with fallback logic.
Reduces code duplication across Scorer and Summarizer components.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from cerebras.cloud.sdk import Cerebras

logger = logging.getLogger(__name__)

# OpenRouter API endpoint
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class AIClient:
    """Unified AI client with Cerebras primary and OpenRouter fallback."""
    
    def __init__(self, 
                 cerebras_key: str = None, 
                 openrouter_key: str = None,
                 cerebras_model: str = "qwen-3-coder-480b",
                 openrouter_model: str = "z-ai/glm-4.5-air:free"):
        """
        Initialize the AI client.
        
        Args:
            cerebras_key: Cerebras API key (optional, uses env var if not provided)
            openrouter_key: OpenRouter API key (optional, uses env var if not provided)
            cerebras_model: Cerebras model to use
            openrouter_model: OpenRouter model to use
        """
        self.cerebras_key = cerebras_key or os.environ.get("CEREBRAS_API_KEY")
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY")
        self.cerebras_model = cerebras_model
        self.openrouter_model = openrouter_model
        
        # Initialize Cerebras client
        if self.cerebras_key:
            self.cerebras_client = Cerebras(api_key=self.cerebras_key)
        else:
            self.cerebras_client = None
            logger.warning("Cerebras API key not found")
    
    def _get_openrouter_headers(self) -> Dict[str, str]:
        """Get standard OpenRouter API headers."""
        return {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000",
            "X-Title": "Newsletter Digest Bot"
        }
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit (429) error."""
        return hasattr(error, 'status_code') and error.status_code == 429
    
    def chat_completion(self, 
                       messages: list, 
                       system_prompt: str = None,
                       max_tokens: int = 1000,
                       temperature: float = 0.1) -> str:
        """
        Perform chat completion with fallback logic.
        
        Args:
            messages: List of message dictionaries
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If both Cerebras and OpenRouter fail
        """
        # Prepare messages with system prompt if provided
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages
        
        # Try Cerebras first
        try:
            if self.cerebras_client:
                response = self.cerebras_client.chat.completions.create(
                    messages=full_messages,
                    model=self.cerebras_model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            else:
                raise Exception("Cerebras client not available")
                
        except Exception as e:
            if self._is_rate_limit_error(e):
                logger.warning("Cerebras rate limit exceeded. Falling back to OpenRouter.")
                return self._chat_completion_openrouter(full_messages, max_tokens, temperature)
            else:
                logger.error(f"Cerebras API error: {e}")
                # Try OpenRouter as fallback for any Cerebras error
                return self._chat_completion_openrouter(full_messages, max_tokens, temperature)
    
    def _chat_completion_openrouter(self, 
                                   messages: list, 
                                   max_tokens: int = 1000,
                                   temperature: float = 0.1) -> str:
        """
        Fallback chat completion using OpenRouter.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If OpenRouter fails
        """
        if not self.openrouter_key or not self.openrouter_key.strip():
            raise Exception("OpenRouter API key is missing or empty")
        
        headers = self._get_openrouter_headers()
        
        data = {
            "model": self.openrouter_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                OPENROUTER_ENDPOINT, 
                headers=headers, 
                json=data, 
                timeout=30
            )
            response.raise_for_status()
            
            # Check if response is HTML (authentication failure)
            if 'text/html' in response.headers.get('content-type', ''):
                raise Exception("OpenRouter authentication failed (received HTML response)")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter request failed: {e}")
            raise Exception(f"OpenRouter API request failed: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"OpenRouter response parsing failed: {e}")
            raise Exception(f"OpenRouter response format error: {e}")
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Test connections to both AI services.
        
        Returns:
            Dictionary with connection status for each service
        """
        results = {
            "cerebras": False,
            "openrouter": False
        }
        
        # Test Cerebras
        try:
            if self.cerebras_key and self.cerebras_client:
                # Simple test message
                test_messages = [{"role": "user", "content": "Hello"}]
                self.cerebras_client.chat.completions.create(
                    messages=test_messages,
                    model=self.cerebras_model,
                    max_tokens=10
                )
                results["cerebras"] = True
                logger.info("Cerebras connection test passed")
        except Exception as e:
            logger.error(f"Cerebras connection test failed: {e}")
        
        # Test OpenRouter
        try:
            if self.openrouter_key:
                test_messages = [{"role": "user", "content": "Hello"}]
                self._chat_completion_openrouter(test_messages, max_tokens=10)
                results["openrouter"] = True
                logger.info("OpenRouter connection test passed")
        except Exception as e:
            logger.error(f"OpenRouter connection test failed: {e}")
        
        return results


def create_ai_client(**kwargs) -> AIClient:
    """Factory function to create an AI client with standard configuration."""
    return AIClient(**kwargs)
