"""
Notion Writer Component

Sends digest entries to a Notion database using the Notion API.
"""

import requests
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotionWriter:
    """Write newsletter digest entries to Notion database."""
    
    def __init__(self, token: str, database_id: str):
        """
        Initialize the Notion writer.
        
        Args:
            token: Notion integration token
            database_id: Notion database ID
        """
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def test_connection(self) -> bool:
        """
        Test the connection to Notion API.
        
        Returns:
            True if connection is successful
        """
        try:
            response = requests.get(
                f"{self.base_url}/databases/{self.database_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                logger.info("Successfully connected to Notion API")
                return True
            else:
                logger.error(f"Failed to connect to Notion API: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Notion connection: {e}")
            return False
    
    def create_page(self, entry: Dict[str, Any]) -> bool:
        """
        Create a new page in the Notion database.
        
        Args:
            entry: Dictionary with page data
            
        Returns:
            True if page was created successfully
        """
        try:
            # Prepare the page data
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": self._format_properties(entry),
                "children": self._format_content(entry)
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                logger.info(f"Created Notion page: {entry.get('title', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to create Notion page: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return False
    
    def _format_properties(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format entry data for Notion properties.
        
        Args:
            entry: Entry data
            
        Returns:
            Formatted properties for Notion
        """
        properties = {}
        
        # Title property - use rich_text instead of title
        if entry.get('title'):
            properties["Title"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": entry['title']
                        }
                    }
                ]
            }
        
        # Summary property
        if entry.get('summary'):
            properties["Summary"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": entry['summary']
                        }
                    }
                ]
            }
        
        # Importance property
        if entry.get('importance'):
            properties["Importance"] = {
                "number": entry['importance']
            }
        
        # Category property
        if entry.get('category'):
            properties["Category"] = {
                "select": {
                    "name": entry['category']
                }
            }
        
        # Link property
        if entry.get('link'):
            properties["Link"] = {
                "url": entry['link']
            }
        
        # Date property
        if entry.get('date'):
            try:
                date_obj = datetime.fromisoformat(entry['date'].replace('Z', '+00:00'))
                properties["Date"] = {
                    "date": {
                        "start": date_obj.isoformat()
                    }
                }
            except:
                # Use current date if parsing fails
                properties["Date"] = {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
        
        return properties
    
    def _format_content(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format content for Notion page body.
        
        Args:
            entry: Entry data
            
        Returns:
            Formatted content blocks for Notion
        """
        content_blocks = []
        
        # Add sender information
        if entry.get('sender'):
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"From: {entry['sender']}"
                            }
                        }
                    ]
                }
            })
        
        # Add summary content
        if entry.get('summary'):
            # Split summary into paragraphs
            summary_lines = entry['summary'].split('\n')
            
            for line in summary_lines:
                if line.strip():
                    content_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": line.strip()
                                    }
                                }
                            ]
                        }
                    })
        
        # Add link if available
        if entry.get('link'):
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Link: {entry['link']}"
                            }
                        }
                    ]
                }
            })
        
        return content_blocks
    
    def batch_create_pages(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Create multiple pages in batch.
        
        Args:
            entries: List of entry data
            
        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0
        
        for entry in entries:
            try:
                if self.create_page(entry):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                logger.error(f"Error creating page for {entry.get('title', 'Unknown')}: {e}")
                failure_count += 1
        
        result = {
            'success_count': success_count,
            'failure_count': failure_count,
            'total_count': len(entries)
        }
        
        logger.info(f"Batch creation complete: {success_count} successful, {failure_count} failed")
        return result
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get the database schema to verify required properties exist.
        
        Returns:
            Database schema information
        """
        try:
            response = requests.get(
                f"{self.base_url}/databases/{self.database_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('properties', {})
            else:
                logger.error(f"Failed to get database schema: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return {}
    
    def validate_schema(self) -> bool:
        """
        Validate that the database has the required properties.
        
        Returns:
            True if schema is valid
        """
        schema = self.get_database_schema()
        
        required_properties = ['Title', 'Summary', 'Importance', 'Category', 'Link']
        
        for prop in required_properties:
            if prop not in schema:
                logger.error(f"Missing required property: {prop}")
                return False
        
        logger.info("Database schema validation passed")
        return True
    
    def create_digest_page(self, digest_content: str, stats: Dict[str, Any]) -> bool:
        """
        Create a summary page with the complete digest.
        
        Args:
            digest_content: Complete digest content
            stats: Digest statistics
            
        Returns:
            True if page was created successfully
        """
        try:
            # Create a summary entry with minimal required properties
            summary_entry = {
                'title': f"Newsletter Digest - {datetime.now().strftime('%B %d, %Y')}",
                'summary': f"Total: {stats.get('total_count', 0)} | High: {stats.get('high_count', 0)} | Medium: {stats.get('medium_count', 0)} | Low: {stats.get('low_count', 0)}",
                'importance': min(max(stats.get('average_score', 3), 1), 5),  # Ensure score is between 1-5
                'category': 'News'
            }
            
            # Format properties safely
            properties = self._format_properties(summary_entry)
            
            # Limit content to exactly 2000 characters (Notion's limit)
            limited_content = digest_content[:1999]  # Leave room for potential encoding issues
            
            # Create the page with digest content
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": limited_content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                logger.info("Created digest summary page")
                return True
            else:
                # Log the actual error response for debugging
                try:
                    error_data = response.json()
                    logger.error(f"Failed to create digest page: {response.status_code} - {error_data}")
                except:
                    logger.error(f"Failed to create digest page: {response.status_code} - {response.text}")
            
            # Try creating without children (just the properties)
            try:
                page_data_simple = {
                    "parent": {"database_id": self.database_id},
                    "properties": properties
                }
                
                response_simple = requests.post(
                    f"{self.base_url}/pages",
                    headers=self.headers,
                    json=page_data_simple
                )
                
                if response_simple.status_code == 200:
                    logger.info("Created digest summary page (without content)")
                    return True
                else:
                    logger.error(f"Failed to create digest page even without content: {response_simple.status_code}")
                    return False
                    
            except Exception as e2:
                logger.error(f"Error creating digest page without content: {e2}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating digest page: {e}")
            return False