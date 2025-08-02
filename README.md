# Newsletter Digest Bot

An intelligent Python application that automatically reads unread email newsletters from Gmail, summarizes them using Cerebras AI, and sends ranked digests to a Notion database.

## Features

- 📧 **Smart Email Reader**: Connects to Gmail via IMAP and processes unread emails, marking them as read
- 🧹 **Content Cleaner**: Removes email headers, footers, and boilerplate content
- 🤖 **AI Summarization**: Uses Cerebras AI to summarize newsletters in 3 bullet points
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

### 2. Environment Configuration

Copy the environment template and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual credentials:

- **Cerebras API Key**: Get from [Cerebras Cloud](https://cloud.cerebras.net/)
- **Gmail Credentials**: Use an App Password for Gmail 2FA
- **Notion Token**: Create an integration at [Notion Developers](https://developers.notion.com)
- **Notion Database ID**: The ID of your target database

### 3. Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password in your `.env` file (not your regular password)

### 4. Notion Database Setup

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
│   ├── summarizer.py        # Cerebras AI summarization
│   ├── scorer.py           # Importance scoring
│   ├── digest_composer.py  # Digest formatting & Notion entry preparation
│   └── notion_writer.py    # Notion API integration
├── main.py                 # Main pipeline with individual email processing
├── test_pipeline.py        # Test script
├── scheduler.py            # Cron scheduler
├── requirements.txt        # Dependencies
├── env.example            # Environment template
└── README.md             # This file
```

## Usage

### Daily Execution

Add to your crontab for daily execution:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/newsletters && python main.py
```

### Manual Execution

```bash
# Run the complete pipeline
python main.py

# Test with sample data
python test_pipeline.py
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

Currently uses Cerebras Cloud with the `qwen-3-coder-480b` model for:
- Summarization (3 bullet points)
- Classification (News/Tool/Opinion)
- Importance scoring (1-5 scale)

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

3. **Notion Permission Error**: 
   - Verify your integration has access to the database
   - Check database column names match exactly
   - Ensure integration token is correct

4. **Empty Results**: 
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