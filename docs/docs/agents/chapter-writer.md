---
sidebar_position: 6
---

# Chapter Writer Agent

The Chapter Writer Agent generates the first draft of each chapter based on the outline, character profiles, and worldbuilding details.

## Overview

This agent transforms your outline into fully-written chapters, incorporating character development, world details, and maintaining narrative consistency throughout the writing process.

## Features

### Chapter Creation
- Generates complete chapter drafts
- Follows outline structure
- Incorporates character voices
- Maintains narrative flow
- Implements world details

### Content Integration
- Uses character profiles
- Implements worldbuilding elements
- Follows plot points
- Maintains story continuity

### Writing Elements
- Dialogue generation
- Scene description
- Action sequences
- Character introspection
- Setting details

## Input Requirements

The Chapter Writer requires:
1. Chapter outline
2. Character profiles
3. Worldbuilding information
4. Project metadata
5. Chapter number

## Process Flow

1. **Preparation**
   - Loads chapter outline
   - References character data
   - Accesses worldbuilding details
   - Verifies project settings

2. **Content Generation**
   - Creates chapter structure
   - Develops scenes
   - Writes dialogue
   - Adds descriptions
   - Incorporates details

3. **Output Processing**
   - Formats content
   - Adds chapter headers
   - Implements styling
   - Saves to file

## Usage

```bash
# Through the CLI
libriscribe write --chapter-number 1
```

The chapter writer is most commonly invoked through the guided setup flow or through the Project Manager.
Direct agent usage is primarily relevant for contributors working inside the codebase.

## Best Practices

1. **Preparation**
   - Review chapter outline
   - Check character references
   - Verify world details
   - Confirm story progression

2. **Quality Control**
   - Monitor narrative flow
   - Check character consistency
   - Verify plot progression
   - Maintain pacing

3. **Integration**
   - Follow outline structure
   - Use character voices
   - Include world details
   - Maintain continuity

## Error Handling

The agent handles:
- Missing input files
- Invalid chapter numbers
- Content generation issues
- File system errors

## Output Format

Chapters are generated in Markdown format:

```markdown
# Chapter [Number]: [Title]

[Chapter content with proper formatting]

## Scene breaks where appropriate

[Continued content...]
```