# Newsletter Digest Bot

An intelligent Python application that automatically reads email newsletters from Gmail, summarizes them using OpenAI, and sends ranked digests to a Notion database.

## Features

- 📧 **Email Reader**: Connects to Gmail via IMAP and fetches newsletters from the last 24 hours
- 🧹 **Content Cleaner**: Removes email headers, footers, and boilerplate content
- 🤖 **AI Summarization**: Uses OpenAI to summarize newsletters in 3 bullet points
- 🏷️ **Content Classification**: Categorizes content as News, Tool, or Opinion
- ⭐ **Importance Scoring**: Rates newsletters 1-5 based on relevance to tech audience
- 📊 **Notion Integration**: Sends ranked digests to a Notion database
- ⏰ **Scheduled Execution**: Can be run daily via cron

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

- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Gmail Credentials**: Use an App Password for Gmail 2FA
- **Notion Token**: Create an integration at [Notion Developers](https://developers.notion.com)
- **Notion Database ID**: The ID of your target database

### 3. Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password in your `.env` file

### 4. Notion Database Setup

Create a Notion database with these columns:
- **Title** (Text)
- **Summary** (Text)
- **Importance** (Number)
- **Category** (Select: News, Tool, Opinion)
- **Link** (URL)
- **Date** (Date)

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
│   ├── email_reader.py      # Gmail IMAP connection
│   ├── content_cleaner.py   # Email content extraction
│   ├── summarizer.py        # OpenAI summarization
│   ├── scorer.py           # Importance scoring
│   ├── digest_composer.py  # Digest formatting
│   └── notion_writer.py    # Notion API integration
├── main.py                 # Main pipeline
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

## Configuration

### Email Filters

Modify `components/email_reader.py` to filter specific senders or subjects:

```python
# Example: Only process emails from specific newsletters
ALLOWED_SENDERS = [
    'newsletter@example.com',
    'tech@example.com'
]
```

### Scoring Criteria

Adjust the scoring prompt in `components/scorer.py` to match your preferences:

```python
SCORING_PROMPT = """
Rate the importance of this newsletter on a scale of 1-5 for a tech entrepreneur.
Consider relevance to: AI, startups, programming, business, innovation.
"""
```

## Troubleshooting

### Common Issues

1. **Gmail Connection Failed**: Ensure App Password is correct and 2FA is enabled
2. **OpenAI API Error**: Check your API key and billing status
3. **Notion Permission Error**: Verify your integration has access to the database
4. **Empty Results**: Check email filters and date range settings

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export DEBUG=1
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 