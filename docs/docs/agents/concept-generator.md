---
sidebar_position: 2
---

# Concept Generator Agent

The Concept Generator Agent is responsible for creating the initial book concept, including title, logline, and detailed description.

## Overview

This agent takes basic project parameters such as genre and category and generates a cohesive book concept. It's typically the first creative agent involved in the book writing process.

## Output Format

The Concept Generator produces a JSON object containing:

```json
{
    "title": "Your Book Title",
    "logline": "A compelling one-sentence summary",
    "description": "A detailed 200-300 word description"
}
```

## Key Features

### Title Generation
- Creates memorable, genre-appropriate titles
- Considers market trends and target audience
- Ensures uniqueness and searchability

### Logline Creation
- Distills the book's core concept into one sentence
- Captures the main conflict and stakes
- Highlights unique selling points

### Description Development
- Expands the concept into a detailed description
- Includes key plot points and themes
- Maintains genre conventions
- Targets specific reader demographics

## Integration

The Concept Generator integrates with:
- Project Manager for initial setup
- Outliner Agent for detailed plot development
- Character Generator for character concept alignment
- Worldbuilding Agent for setting consistency

## Usage

The Concept Generator is normally invoked by the guided `libriscribe start` workflow rather than through a standalone top-level CLI command.

For contributors working inside the codebase, it is triggered through the Project Manager and agent layer.

## Error Handling

The agent includes robust error handling for:
- Invalid project data
- JSON parsing errors
- API response validation
- Content generation failures

## Best Practices

When working with the Concept Generator:
1. Provide clear genre and category information
2. Include any specific themes or elements you want to incorporate
3. Review and iterate on generated concepts
4. Save preferred concepts before proceeding to outline generation