"""
Test fixtures and sample data for the newsletter digest system.
"""

# Sample email data for testing
SAMPLE_EMAIL_DATA = {
    "subject": "Weekly Tech Newsletter - AI Breakthroughs",
    "from": "newsletter@techcompany.com",
    "body": """
    <html>
    <body>
    <h1>This Week in Tech</h1>
    <p>Welcome to our weekly newsletter covering the latest in technology!</p>
    
    <h2>AI News</h2>
    <p>OpenAI released a new model that shows significant improvements in reasoning capabilities. 
    The model demonstrates better performance on complex mathematical problems and coding tasks.</p>
    
    <h2>Developer Tools</h2>
    <p>GitHub announced a new feature for automated code reviews using AI. This tool can help 
    identify potential bugs and suggest improvements before code is merged.</p>
    
    <h2>Startup News</h2>
    <p>TechStartup Inc. raised $50M in Series B funding to expand their AI platform. 
    The company plans to use the funding to hire more engineers and expand globally.</p>
    
    <p>Links:</p>
    <ul>
        <li><a href="https://openai.com/news">OpenAI News</a></li>
        <li><a href="https://github.com/features">GitHub Features</a></li>
        <li><a href="https://techcrunch.com/startup-funding">TechCrunch Funding</a></li>
    </ul>
    
    <p>Thanks for reading!</p>
    <p>Unsubscribe | Privacy Policy</p>
    </body>
    </html>
    """,
    "date": "2024-01-15 10:30:00",
    "uid": 12345
}

SAMPLE_CLEANED_EMAIL = {
    "subject": "Weekly Tech Newsletter - AI Breakthroughs",
    "from": "newsletter@techcompany.com",
    "cleaned_body": """This Week in Tech

Welcome to our weekly newsletter covering the latest in technology!

AI News
OpenAI released a new model that shows significant improvements in reasoning capabilities. 
The model demonstrates better performance on complex mathematical problems and coding tasks.

Developer Tools
GitHub announced a new feature for automated code reviews using AI. This tool can help 
identify potential bugs and suggest improvements before code is merged.

Startup News
TechStartup Inc. raised $50M in Series B funding to expand their AI platform. 
The company plans to use the funding to hire more engineers and expand globally.

Links:
- OpenAI News
- GitHub Features  
- TechCrunch Funding""",
    "extracted_links": [
        "https://openai.com/news",
        "https://github.com/features", 
        "https://techcrunch.com/startup-funding"
    ],
    "date": "2024-01-15 10:30:00",
    "uid": 12345
}

SAMPLE_SUMMARIZED_EMAIL = {
    **SAMPLE_CLEANED_EMAIL,
    "summary_points": [
        "OpenAI released a new model with improved reasoning capabilities for math and coding tasks",
        "GitHub launched AI-powered automated code review feature to identify bugs and suggest improvements", 
        "TechStartup Inc. raised $50M Series B funding to expand their AI platform and hire engineers"
    ],
    "category": "News",
    "full_summary": "• OpenAI released a new model with improved reasoning capabilities for math and coding tasks\n• GitHub launched AI-powered automated code review feature to identify bugs and suggest improvements\n• TechStartup Inc. raised $50M Series B funding to expand their AI platform and hire engineers\n\nCategory: News\nLinks: https://openai.com/news, https://github.com/features"
}

SAMPLE_SCORED_EMAIL = {
    **SAMPLE_SUMMARIZED_EMAIL,
    "importance_score": 4
}

# Sample AI responses for mocking
MOCK_SUMMARIZATION_RESPONSE = """• OpenAI released a new model with improved reasoning capabilities for math and coding tasks
• GitHub launched AI-powered automated code review feature to identify bugs and suggest improvements  
• TechStartup Inc. raised $50M Series B funding to expand their AI platform and hire engineers

Category: News
Links: https://openai.com/news, https://github.com/features"""

MOCK_SCORING_RESPONSE = "4"

MOCK_CLASSIFICATION_RESPONSE = "News"

# Sample newsletter variations for different test cases
TOOL_NEWSLETTER = {
    "subject": "New Python Library for Data Science",
    "cleaned_body": "Introducing DataWiz, a new Python library that simplifies data analysis workflows. Features include automated data cleaning, visualization tools, and machine learning integration. Available on PyPI with comprehensive documentation.",
    "category": "Tool"
}

OPINION_NEWSLETTER = {
    "subject": "The Future of Remote Work",
    "cleaned_body": "Remote work is here to stay, but companies need to adapt their management strategies. Based on my experience leading distributed teams, here are the key challenges and solutions for effective remote collaboration.",
    "category": "Opinion"
}

# Test data for edge cases
EMPTY_EMAIL = {
    "subject": "",
    "cleaned_body": "",
    "extracted_links": []
}

MALFORMED_EMAIL = {
    "subject": "Test Subject",
    "cleaned_body": None,
    "extracted_links": None
}

# Mock API responses
MOCK_CEREBRAS_SUCCESS_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": MOCK_SUMMARIZATION_RESPONSE
            }
        }
    ]
}

MOCK_OPENROUTER_SUCCESS_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": MOCK_SUMMARIZATION_RESPONSE
            }
        }
    ]
}
