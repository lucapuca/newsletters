# Newsletter Digest Bot - Project Structure

## 📁 Complete Project Structure

```
newsletters/
├── components/                    # Core components
│   ├── __init__.py              # Package initialization
│   ├── email_reader.py          # Gmail IMAP connection & email fetching
│   ├── content_cleaner.py       # Email content extraction & cleaning
│   ├── summarizer.py            # OpenAI summarization & classification
│   ├── scorer.py                # Importance scoring (1-5)
│   ├── digest_composer.py       # Digest formatting & Notion entry creation
│   └── notion_writer.py         # Notion API integration
├── main.py                      # Main pipeline orchestrator
├── test_pipeline.py             # Test script with sample data
├── scheduler.py                 # Cron-like scheduler
├── setup.py                     # Setup script for dependencies
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # Project documentation
└── PROJECT_STRUCTURE.md         # This file
```

## 🔧 Core Components

### 1. Email Reader (`components/email_reader.py`)
- **Purpose**: Connects to Gmail via IMAP and fetches emails from the last 24 hours
- **Features**:
  - IMAP SSL connection to Gmail
  - Email header decoding (subject, sender, date)
  - Body content extraction (HTML and plain text)
  - Newsletter filtering based on keywords and domains
  - Date range filtering (last 24 hours)

### 2. Content Cleaner (`components/content_cleaner.py`)
- **Purpose**: Removes email boilerplate and extracts meaningful content
- **Features**:
  - HTML parsing with BeautifulSoup
  - Removal of unsubscribe links, footers, headers
  - Social media link filtering
  - Spam detection and filtering
  - Link extraction from HTML content
  - Content validation (minimum length, meaningful content)

### 3. Summarizer (`components/summarizer.py`)
- **Purpose**: Uses OpenAI to summarize newsletters and classify content
- **Features**:
  - 3-bullet point summarization
  - Content classification (News, Tool, Opinion)
  - Link extraction from summaries
  - Batch processing for multiple newsletters
  - Error handling and fallback responses

### 4. Scorer (`components/scorer.py`)
- **Purpose**: Assigns importance scores (1-5) based on relevance to tech audience
- **Features**:
  - AI-powered scoring using OpenAI
  - Scoring criteria for tech entrepreneurs/developers
  - Score validation and parsing
  - Filtering by minimum score threshold
  - Score descriptions and statistics

### 5. Digest Composer (`components/digest_composer.py`)
- **Purpose**: Formats and organizes processed newsletters into digests
- **Features**:
  - Sorting by importance score (descending)
  - Grouping by importance level (high/medium/low)
  - Markdown digest formatting
  - Notion entry creation
  - Digest statistics and analytics

### 6. Notion Writer (`components/notion_writer.py`)
- **Purpose**: Sends digest entries to Notion database
- **Features**:
  - Notion API integration
  - Database schema validation
  - Page creation with properties and content
  - Batch processing
  - Connection testing and error handling

## 🚀 Main Scripts

### 1. Main Pipeline (`main.py`)
- **Purpose**: Orchestrates the complete newsletter processing pipeline
- **Features**:
  - Step-by-step processing workflow
  - Connection testing (Gmail, OpenAI, Notion)
  - Comprehensive error handling
  - Detailed logging and statistics
  - Environment variable validation

### 2. Test Pipeline (`test_pipeline.py`)
- **Purpose**: Tests the pipeline with sample newsletter data
- **Features**:
  - Sample newsletter data (TechCrunch, Product Hunt, etc.)
  - Component testing without real email access
  - Digest preview and formatting
  - Connection testing for OpenAI and Notion
  - Detailed test results and statistics

### 3. Scheduler (`scheduler.py`)
- **Purpose**: Runs the pipeline on a schedule
- **Features**:
  - Daily, weekly, and hourly scheduling
  - Command-line argument support
  - Continuous operation with graceful shutdown
  - Schedule information and management
  - Immediate execution option

### 4. Setup Script (`setup.py`)
- **Purpose**: Helps users set up the project
- **Features**:
  - Dependency installation
  - Python version checking
  - Environment file creation
  - Import testing
  - Setup instructions

## 📋 Configuration Files

### 1. Requirements (`requirements.txt`)
```
openai==1.3.0
langchain==0.0.350
langchain-openai==0.0.2
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
email-validator==2.0.0
schedule==1.2.0
```

### 2. Environment Template (`env.example`)
```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Gmail Configuration
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Notion Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
```

## 🔄 Pipeline Flow

1. **Email Fetching**: Connect to Gmail and fetch emails from last 24 hours
2. **Newsletter Filtering**: Filter emails to identify newsletters
3. **Content Cleaning**: Remove boilerplate and extract meaningful content
4. **AI Summarization**: Generate 3-bullet summaries and classify content
5. **Importance Scoring**: Rate newsletters 1-5 for tech audience relevance
6. **Score Filtering**: Filter out low-importance newsletters
7. **Digest Composition**: Sort and format newsletters by importance
8. **Notion Integration**: Create database entries for each newsletter
9. **Summary Creation**: Create digest summary page in Notion

## 🎯 Key Features

- **Modular Design**: Each component is independent and testable
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Environment-based configuration
- **Testing**: Built-in test pipeline with sample data
- **Scheduling**: Flexible scheduling options
- **Documentation**: Comprehensive README and setup instructions
- **Security**: Secure credential management with .env files

## 🚀 Quick Start

1. **Setup**: `python setup.py`
2. **Configure**: Edit `.env` with your credentials
3. **Test**: `python test_pipeline.py`
4. **Run**: `python main.py`
5. **Schedule**: `python scheduler.py --daily 09:00`

This project provides a complete, production-ready solution for automated newsletter processing and digest creation. 