"""
Prompt Loader Utility

Loads AI prompts from markdown files for easy maintenance and updates.
"""

import os
import re
from typing import Dict, Optional
from pathlib import Path

class PromptLoader:
    """Utility class to load and manage AI prompts from markdown files."""
    
    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt markdown files
        """
        if prompts_dir is None:
            # Default to prompts directory relative to this file
            current_dir = Path(__file__).parent.parent
            prompts_dir = current_dir / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache = {}
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt from its markdown file.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
            
        Returns:
            The prompt template string
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.md"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the template section from the markdown
        template = self._extract_template(content)
        
        # Cache the prompt
        self._prompt_cache[prompt_name] = template
        
        return template
    
    def _extract_template(self, markdown_content: str) -> str:
        """
        Extract the template section from markdown content.
        
        Args:
            markdown_content: Full markdown file content
            
        Returns:
            The template string
        """
        # Look for the template section (usually the last code block)
        # Pattern: ```\n(template content)\n```
        template_pattern = r'```\n(.*?)\n```'
        matches = re.findall(template_pattern, markdown_content, re.DOTALL)
        
        if matches:
            # Return the last template block (most complete one)
            return matches[-1].strip()
        
        # Fallback: if no template block found, return the content after "## Template"
        template_section = re.search(r'## Template\s*\n\n(.*)', markdown_content, re.DOTALL)
        if template_section:
            # Remove any remaining markdown formatting
            content = template_section.group(1).strip()
            # Remove code block markers if present
            content = re.sub(r'^```.*?\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'\n```$', '', content)
            return content.strip()
        
        # Final fallback: return the whole content (shouldn't happen with our format)
        return markdown_content.strip()
    
    def reload_prompt(self, prompt_name: str) -> str:
        """
        Reload a prompt from disk, bypassing cache.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
            
        Returns:
            The prompt template string
        """
        # Clear from cache and reload
        if prompt_name in self._prompt_cache:
            del self._prompt_cache[prompt_name]
        
        return self.load_prompt(prompt_name)
    
    def list_available_prompts(self) -> list:
        """
        List all available prompt files.
        
        Returns:
            List of prompt names (without .md extension)
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = list(self.prompts_dir.glob("*.md"))
        return [f.stem for f in prompt_files]
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._prompt_cache.clear()


# Global instance for easy access
_prompt_loader = None

def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader

def load_prompt(prompt_name: str) -> str:
    """
    Convenience function to load a prompt.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        
    Returns:
        The prompt template string
    """
    return get_prompt_loader().load_prompt(prompt_name)
