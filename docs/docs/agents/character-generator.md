---
sidebar_position: 4
---

# Character Generator Agent

The Character Generator Agent creates detailed character profiles for your book, including their backgrounds, personalities, motivations, and relationships.

## Overview

This agent specializes in creating well-rounded, believable characters that fit your story's genre and themes. It generates a complete cast of characters with detailed profiles that can be referenced throughout the writing process.

## Character Profile Structure

Each character profile includes:

```json
{
    "name": "Character Name",
    "role": "Protagonist/Antagonist/Supporting",
    "background": {
        "age": "Character's age",
        "occupation": "Current occupation",
        "history": "Detailed background story"
    },
    "personality": {
        "traits": ["List", "of", "key", "traits"],
        "strengths": ["Character's", "strengths"],
        "weaknesses": ["Character's", "flaws"]
    },
    "relationships": {
        "character_name": "Relationship description",
        "other_character": "Another relationship"
    },
    "goals": {
        "main_goal": "Primary character motivation",
        "secondary_goals": ["Additional", "character", "objectives"]
    },
    "arc": "Character's development journey"
}
```

## Key Features

### Personality Development
- Creates distinct personality profiles
- Balances strengths and weaknesses
- Ensures realistic character traits
- Develops unique voice and mannerisms

### Relationship Mapping
- Establishes character connections
- Defines relationship dynamics
- Creates conflict potential
- Maps character networks

### Character Arc Planning
- Designs character growth trajectories
- Plans development milestones
- Aligns with plot points
- Creates meaningful change

## Integration

The Character Generator works with:
- Concept Generator for thematic alignment
- Outliner for character arc integration
- Chapter Writer for consistent portrayal
- Content Reviewer for character consistency

## Usage

```bash
# Through the CLI
libriscribe characters
```

Character generation is usually triggered from guided setup or by the Project Manager during a project workflow.

## Best Practices

1. **Character Balance**
   - Ensure diverse cast
   - Balance screen time
   - Create meaningful conflicts
   - Develop distinct voices

2. **Consistency Checks**
   - Verify background logic
   - Check relationship consistency
   - Align with story themes
   - Maintain character voice

3. **Development Planning**
   - Map character arcs
   - Plan key moments
   - Track relationships
   - Monitor growth