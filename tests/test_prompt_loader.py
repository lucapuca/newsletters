"""
Tests for the PromptLoader utility.
"""

import unittest
import tempfile
import os
from pathlib import Path
from utils.prompt_loader import PromptLoader


class TestPromptLoader(unittest.TestCase):
    """Test cases for PromptLoader functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_loader = PromptLoader(self.temp_dir)
        
        # Create a sample prompt file
        self.sample_prompt_content = """# Test Prompt

This is a test prompt for unit testing.

## Template

```
Test prompt with {variable} placeholder.
Respond with test data.
```
"""
        
        with open(Path(self.temp_dir) / "test_prompt.md", 'w') as f:
            f.write(self.sample_prompt_content)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_prompt_success(self):
        """Test successful prompt loading."""
        prompt = self.prompt_loader.load_prompt('test_prompt')
        expected = "Test prompt with {variable} placeholder.\nRespond with test data."
        self.assertEqual(prompt, expected)
    
    def test_load_prompt_file_not_found(self):
        """Test loading non-existent prompt file."""
        with self.assertRaises(FileNotFoundError):
            self.prompt_loader.load_prompt('nonexistent_prompt')
    
    def test_prompt_caching(self):
        """Test that prompts are cached after first load."""
        # Load prompt twice
        prompt1 = self.prompt_loader.load_prompt('test_prompt')
        prompt2 = self.prompt_loader.load_prompt('test_prompt')
        
        # Should be the same object (cached)
        self.assertEqual(prompt1, prompt2)
        self.assertIn('test_prompt', self.prompt_loader._prompt_cache)
    
    def test_reload_prompt(self):
        """Test reloading prompt bypasses cache."""
        # Load prompt first time
        prompt1 = self.prompt_loader.load_prompt('test_prompt')
        
        # Modify the file
        new_content = """# Modified Prompt

## Template

```
Modified prompt content.
```
"""
        with open(Path(self.temp_dir) / "test_prompt.md", 'w') as f:
            f.write(new_content)
        
        # Reload should get new content
        prompt2 = self.prompt_loader.reload_prompt('test_prompt')
        self.assertNotEqual(prompt1, prompt2)
        self.assertEqual(prompt2, "Modified prompt content.")
    
    def test_list_available_prompts(self):
        """Test listing available prompt files."""
        # Create additional prompt file
        with open(Path(self.temp_dir) / "another_prompt.md", 'w') as f:
            f.write("# Another prompt\n\n## Template\n\n```\nAnother test.\n```")
        
        prompts = self.prompt_loader.list_available_prompts()
        self.assertIn('test_prompt', prompts)
        self.assertIn('another_prompt', prompts)
        self.assertEqual(len(prompts), 2)
    
    def test_clear_cache(self):
        """Test clearing the prompt cache."""
        # Load a prompt to populate cache
        self.prompt_loader.load_prompt('test_prompt')
        self.assertIn('test_prompt', self.prompt_loader._prompt_cache)
        
        # Clear cache
        self.prompt_loader.clear_cache()
        self.assertEqual(len(self.prompt_loader._prompt_cache), 0)
    
    def test_extract_template_fallback(self):
        """Test template extraction fallback methods."""
        # Test content without code blocks
        content_without_blocks = """# Test Prompt

## Template

This is template content without code blocks.
Variable: {test}
"""
        
        with open(Path(self.temp_dir) / "fallback_prompt.md", 'w') as f:
            f.write(content_without_blocks)
        
        prompt = self.prompt_loader.load_prompt('fallback_prompt')
        self.assertIn("This is template content", prompt)
        self.assertIn("{test}", prompt)


if __name__ == '__main__':
    unittest.main()
