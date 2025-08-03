# Newsletter Summarization Prompt

Summarize this newsletter in exactly 3 bullet points. Focus on the most important and actionable information.

## Input Variables

- `{content}` - Newsletter content

## Instructions

- Provide exactly 3 bullet points
- Each bullet should be concise but informative
- Focus on key insights, tools, or news
- Use clear, professional language
- Avoid marketing language and fluff
- Extract the most relevant and interesting links from the content

## Output Format

```
• [First bullet point]
• [Second bullet point] 
• [Third bullet point]

Category: [Choose one: News, Tool, or Opinion]
Links: [List the most relevant and interesting links mentioned in the content, separated by commas. Focus on links to articles, tools, or resources that are specifically mentioned as important or interesting. If no relevant links are found, leave this empty.]
```

## Template

```
Newsletter content:
{content}

Instructions:
- Provide exactly 3 bullet points
- Each bullet should be concise but informative
- Focus on key insights, tools, or news
- Use clear, professional language
- Avoid marketing language and fluff
- Extract the most relevant and interesting links from the content

Format your response as:
• [First bullet point]
• [Second bullet point] 
• [Third bullet point]

Category: [Choose one: News, Tool, or Opinion]
Links: [List the most relevant and interesting links mentioned in the content, separated by commas. Focus on links to articles, tools, or resources that are specifically mentioned as important or interesting. If no relevant links are found, leave this empty.]
```
