"""
Summarizer Component

Uses Cerebras to summarize newsletters in 3 bullet points and classify content.
"""

import os
from typing import Dict, Any, List
import logging
from cerebras.cloud.sdk import Cerebras

logger = logging.getLogger(__name__)

class Summarizer:
    """Cerebras-powered newsletter summarizer."""
    
    def __init__(self, api_key: str = None, model: str = "qwen-3-coder-480b"):
        """
        Initialize the summarizer.
        
        Args:
            api_key: Cerebras API key (optional, uses env var if not provided)
            model: Cerebras model to use
        """
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        self.model = model
        self.client = Cerebras(api_key=self.api_key)
        
        # Categories for classification
        self.categories = ["News", "Tool", "Opinion"]
        
        # Summarization prompt template
        self.summary_prompt = """
Summarize this newsletter in exactly 3 bullet points. Focus on the most important and actionable information.

Newsletter content:
{content}

Instructions:
- Provide exactly 3 bullet points
- Each bullet should be concise but informative
- Focus on key insights, tools, or news
- Use clear, professional language
- Avoid marketing language and fluff
- Extract the most relevant and interesting links from the content

Format your response as:
• [First bullet point]
• [Second bullet point] 
• [Third bullet point]

Category: [Choose one: News, Tool, or Opinion]
Links: [List the most relevant and interesting links mentioned in the content, separated by commas. Focus on links to articles, tools, or resources that are specifically mentioned as important or interesting. If no relevant links are found, leave this empty.]
"""
        
        # Classification prompt
        self.classification_prompt = """
Classify this newsletter content into one of these categories:

- News: Industry updates, company announcements, market changes, new product launches
- Tool: Software, apps, resources, tutorials, how-to guides, productivity tips
- Opinion: Commentary, analysis, predictions, thought leadership, personal insights

Content:
{content}

Respond with only the category name: News, Tool, or Opinion
"""
    
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
            logger.error(f"Error summarizing content: {e}")
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
            logger.error(f"Error classifying content: {e}")
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
        """Test connection to Cerebras."""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                model=self.model,
                stream=False,
                max_completion_tokens=5,
                temperature=0.1
            )
            return True
        except Exception as e:
            logger.error(f"Cerebras connection test failed: {e}")
            return False