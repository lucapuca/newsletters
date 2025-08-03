# Simple Newsletter Scoring Prompt

Rate this newsletter's importance (1-5) for a tech audience.

## Input Variables

- `{subject}` - Newsletter subject line
- `{summary}` - Newsletter summary

## Scoring Scale

- **1** = Not relevant
- **2** = Somewhat relevant
- **3** = Moderately relevant
- **4** = Highly relevant
- **5** = Extremely relevant

## Template

```
Subject: {subject}
Summary: {summary}

1=Not relevant, 2=Somewhat relevant, 3=Moderately relevant, 4=Highly relevant, 5=Extremely relevant

Respond with only a number from 1 to 5.
```
