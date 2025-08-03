# Newsletter Scoring Prompt

Rate the importance of this newsletter on a scale of 1-5 for a tech entrepreneur/developer audience.

## Scoring Factors

Consider these factors:
- Relevance to technology, programming, AI, startups, business
- Actionable insights or tools
- Industry significance and impact
- Quality of information and analysis
- Potential value for professional development

## Scoring Guide

- **1** = Not relevant or low quality
- **2** = Somewhat relevant but limited value
- **3** = Moderately relevant with some useful information
- **4** = Highly relevant with valuable insights
- **5** = Extremely relevant with exceptional value

## Input Variables

- `{subject}` - Newsletter subject line
- `{content}` - Newsletter content
- `{summary}` - Newsletter summary

## Template

```
Newsletter subject: {subject}
Newsletter content: {content}
Summary: {summary}

Respond with only a number from 1 to 5.
```
