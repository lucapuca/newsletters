# Newsletter Digest Bot

An intelligent Python application that automatically reads unread email newsletters from Gmail, summarizes them using Cerebras AI, and sends ranked digests to a Notion database.

## Features

- 📧 **Smart Email Reader**: Connects to Gmail via IMAP and processes unread emails, marking them as read
- 🧹 **Content Cleaner**: Removes email headers, footers, and boilerplate content
- 🤖 **AI Summarization**: Uses Cerebras AI to summarize newsletters in 3 bullet points
- 🔄 **OpenRouter Fallback**: Automatically falls back to OpenRouter.ai (z-ai/glm-4.5-air:free) when Cerebras hits rate limits (429 errors)
- 🏷️ **Content Classification**: Categorizes content as News, Tool, or Opinion
- ⭐ **Importance Scoring**: Rates newsletters 1-5 based on relevance to tech audience
- 📊 **Notion Integration**: Sends individual entries and digest summaries to a Notion database
- ⏰ **Scheduled Execution**: Can be run daily via cron
- 🔄 **Individual Processing**: Processes emails one at a time for better error handling
- 📈 **Real-time Progress**: Shows processing status for each email

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Test Dependencies (Optional)

For running the test suite:

```bash
pip install -r requirements-test.txt
```

### 3. Environment Configuration

Copy the environment template and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual credentials:

- **Cerebras API Key**: Get from [Cerebras Cloud](https://cloud.cerebras.net/)
- **OpenRouter API Key**: Get from [OpenRouter.ai](https://openrouter.ai/) (uses z-ai/glm-4.5-air:free model as fallback for rate limits)
- **Gmail Credentials**: Use an App Password for Gmail 2FA
- **Notion Token**: Create an integration at [Notion Developers](https://developers.notion.com)
- **Notion Database ID**: The ID of your target database

### 4. Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password in your `.env` file (not your regular password)

### 5. Notion Database Setup

Create a Notion database with these columns:
- **Title** (Text) - Email subject
- **Summary** (Text) - AI-generated summary
- **Importance** (Number) - Score 1-5
- **Category** (Select: News, Tool, Opinion)
- **Link** (URL) - Extracted links
- **Date** (Date) - Processing date

### 5. Run the Application

```bash
# Run the main pipeline
python main.py

# Run with test data
python test_pipeline.py

# Run the scheduler
python scheduler.py
```

## Project Structure

```
newsletters/
├── components/
│   ├── __init__.py
│   ├── email_reader.py      # Gmail IMAP connection & unread email processing
│   ├── content_cleaner.py   # Email content extraction & cleaning
│   ├── summarizer.py        # AI summarization with fallback
│   ├── scorer.py           # Importance scoring with fallback
│   ├── digest_composer.py  # Digest formatting & Notion entry preparation
│   └── notion_writer.py    # Notion API integration
├── utils/
│   ├── __init__.py
│   ├── prompt_loader.py     # Dynamic prompt loading from markdown
│   └── ai_client.py        # Shared AI client (Cerebras + OpenRouter)
├── prompts/
│   ├── scoring_prompt.md           # Detailed scoring prompt
│   ├── simple_scoring_prompt.md    # Simple scoring prompt
│   ├── summarization_prompt.md     # Summarization prompt
│   └── classification_prompt.md    # Content classification prompt
├── tests/
│   ├── fixtures.py          # Test data and mock responses
│   ├── test_prompt_loader.py # Prompt loading tests
│   ├── test_scorer.py       # Scoring component tests
│   ├── test_summarizer.py   # Summarization component tests
│   ├── test_pipeline.py     # Integration tests
│   └── test_runner.py       # Custom test runner
├── main.py                  # Main pipeline orchestrator
├── scheduler.py             # Cron scheduler
├── requirements.txt         # Production dependencies
├── requirements-test.txt    # Test dependencies
├── pytest.ini             # Test configuration
├── env.example             # Environment template
└── README.md              # This file
```

## Testing

**🧪 Always run tests before running the app to ensure everything is working correctly!**

### Running Tests

```bash
# Run all tests (recommended)
python3 -m pytest tests/ -v

# Run specific test files
python3 -m pytest tests/test_prompt_loader.py -v
python3 -m pytest tests/test_scorer.py -v
python3 -m pytest tests/test_summarizer.py -v

# Run tests quietly (less verbose)
python3 -m pytest tests/

# Use the custom test runner
python3 tests/test_runner.py

# Run tests with coverage (if pytest-cov installed)
python3 -m pytest tests/ --cov=components --cov=utils
```

### Test Structure

```
tests/
├── fixtures.py           # Test data and mock responses
├── test_prompt_loader.py  # Prompt loading utility tests
├── test_scorer.py        # Newsletter scoring tests
├── test_summarizer.py    # AI summarization tests
├── test_pipeline.py      # Integration tests
└── test_runner.py        # Custom test runner
```

### What Tests Cover

- ✅ **Prompt Loading**: Dynamic loading from markdown files
- ✅ **AI Scoring**: Newsletter importance scoring (1-5)
- ✅ **AI Summarization**: Content summarization and classification
- ✅ **API Fallbacks**: Cerebras → OpenRouter fallback logic
- ✅ **Error Handling**: Graceful degradation when APIs fail
- ✅ **Pipeline Integration**: End-to-end workflow testing

## Usage

### Recommended Workflow

```bash
# 1. First, run tests to ensure everything works
python3 -m pytest tests/ -v

# 2. If tests pass, run the app
python3 main.py
```

### Daily Execution

Add to your crontab for daily execution:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM (with testing)
0 9 * * * cd /path/to/newsletters && python3 -m pytest tests/ -q && python3 main.py
```

### Manual Execution

```bash
# Run the complete pipeline
python3 main.py
```

## How It Works

### 1. Email Processing
- Fetches all unread emails from Gmail
- Marks them as read after processing
- Filters for newsletters and content-rich emails
- Processes each email individually

### 2. Content Analysis
- Cleans email content (removes boilerplate, headers, footers)
- Extracts meaningful text and links
- Uses Cerebras AI for summarization and classification
- Scores importance (1-5) for tech audience

### 3. Notion Integration
- Creates individual Notion entries for each processed email
- Generates a digest summary page with statistics
- Handles API errors gracefully with fallback mechanisms

## Configuration

### Email Filters

The system intelligently filters emails based on:
- Newsletter keywords (newsletter, digest, weekly, etc.)
- Known newsletter domains (Substack, Revue, etc.)
- Content quality (substantial text with links)
- Spam detection (excludes transactional emails)

### AI Model

**Primary**: Cerebras Cloud with the `qwen-3-coder-480b` model for:
- Summarization (3 bullet points)
- Classification (News/Tool/Opinion)
- Importance scoring (1-5 scale)

**Fallback**: OpenRouter.ai with `z-ai/glm-4.5-air:free` model
- Automatically activates when Cerebras returns 429 rate limit errors
- Uses the same prompts and scoring criteria as Cerebras
- Completely free tier model (no cost)
- Endpoint: `https://openrouter.ai/v1/chat/completions`
- Seamless fallback - processing continues without interruption

### Scoring Criteria

The AI evaluates newsletters based on:
- Relevance to tech/startup audience
- Actionable insights and tools
- Industry news and trends
- Innovation and business value

## Troubleshooting

### Common Issues

1. **Gmail Connection Failed**: 
   - Ensure App Password is correct (not regular password)
   - Verify 2FA is enabled on Gmail
   - Check IMAP is enabled in Gmail settings

2. **Cerebras API Error**: 
   - Verify your API key is valid
   - Check your Cerebras Cloud account status
   - Ensure you have sufficient credits
   - **Note**: 429 rate limit errors automatically trigger OpenRouter fallback

3. **OpenRouter Fallback Issues**:
   - Verify your OpenRouter API key is set in `.env`
   - Check OpenRouter account status at [openrouter.ai](https://openrouter.ai/)
   - Model used: `z-ai/glm-4.5-air:free` (completely free)
   - Endpoint: `https://openrouter.ai/v1/chat/completions`

4. **Notion Permission Error**: 
   - Verify your integration has access to the database
   - Check database column names match exactly
   - Ensure integration token is correct

5. **Empty Results**: 
   - Check if you have unread emails
   - Verify email filtering criteria
   - Look at debug logs for rejected emails

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export DEBUG=1
python main.py
```

### Log Analysis

The system provides detailed logging:
- Shows which emails are being processed
- Lists rejected emails with reasons
- Tracks Notion API success/failures
- Reports processing statistics

## Recent Updates

### v2.0 - Individual Email Processing
- **Sequential Processing**: Each email is processed completely before moving to the next
- **Better Error Handling**: One bad email won't break the entire pipeline
- **Real-time Progress**: See exactly which email is being processed
- **Atomic Operations**: Each email is fully processed before marking as read

### v1.5 - Cerebras AI Integration
- **Switched from OpenAI**: Now uses Cerebras Cloud for free AI processing
- **Improved Link Extraction**: Better identification of relevant links
- **Enhanced Filtering**: More intelligent email filtering criteria

### v1.0 - Core Features
- **Gmail Integration**: IMAP connection with unread email processing
- **Content Cleaning**: Removes boilerplate and extracts meaningful content
- **AI Summarization**: 3-bullet point summaries with classification
- **Notion Integration**: Database entries with digest summaries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 