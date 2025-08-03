# Newsletter Classification Prompt

Classify this newsletter content into one of these categories.

## Categories

- **News**: Industry updates, company announcements, market changes, new product launches
- **Tool**: Software, apps, resources, tutorials, how-to guides, productivity tips
- **Opinion**: Commentary, analysis, predictions, thought leadership, personal insights

## Input Variables

- `{content}` - Newsletter content

## Template

```
Classify this newsletter content into one of these categories:

- News: Industry updates, company announcements, market changes, new product launches
- Tool: Software, apps, resources, tutorials, how-to guides, productivity tips
- Opinion: Commentary, analysis, predictions, thought leadership, personal insights

Content:
{content}

Respond with only the category name: News, Tool, or Opinion
```
