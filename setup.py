#!/usr/bin/env python3
"""
Setup script for Newsletter Digest Bot

Helps users install dependencies and set up the project.
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template."""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if not os.path.exists('env.example'):
        print("❌ env.example file not found")
        return False
    
    try:
        shutil.copy('env.example', '.env')
        print("✅ Created .env file from template")
        print("📝 Please edit .env with your actual credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import openai
        import requests
        import schedule
        from bs4 import BeautifulSoup
        from dotenv import load_dotenv
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Newsletter Digest Bot Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Test imports
    if not test_imports():
        return
    
    # Create .env file
    if not create_env_file():
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your credentials:")
    print("   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys")
    print("   - EMAIL & EMAIL_PASSWORD: Your Gmail credentials (use App Password)")
    print("   - NOTION_TOKEN: Get from https://developers.notion.com")
    print("   - NOTION_DATABASE_ID: Your Notion database ID")
    print("\n2. Test the pipeline:")
    print("   python test_pipeline.py")
    print("\n3. Run the main pipeline:")
    print("   python main.py")
    print("\n4. Set up scheduling:")
    print("   python scheduler.py --daily 09:00")

if __name__ == "__main__":
    main() 