---
sidebar_position: 5
---

# Worldbuilding Agent

The Worldbuilding Agent creates detailed and coherent world information for your book, including history, culture, geography, and other setting-specific elements.

## Overview

This agent specializes in creating rich, detailed worlds that enhance your story's setting. It generates comprehensive worldbuilding details that maintain internal consistency and support your narrative.

## Worldbuilding Categories

The agent generates content across multiple categories based on your book's needs:

### Physical World
- Geography and climate
- Natural resources
- Flora and fauna
- Physical laws (for speculative fiction)

### Society & Culture
- Social structure
- Cultural norms
- Religious beliefs
- Political systems
- Economic systems

### History & Timeline
- Major historical events
- Cultural development
- Political changes
- Technological advancement

### Technology & Magic
- Available technology
- Magical systems
- Scientific advancement
- Technological limitations

## Output Format

The worldbuilding details are stored in a structured JSON format:

```json
{
    "physical_world": {
        "geography": {...},
        "climate": {...},
        "nature": {...}
    },
    "society": {
        "structure": {...},
        "culture": {...},
        "politics": {...}
    },
    "history": {
        "timeline": [...],
        "major_events": [...]
    },
    "systems": {
        "magic": {...},
        "technology": {...}
    }
}
```

## Integration

The Worldbuilding Agent works closely with:
- Concept Generator for setting alignment
- Character Generator for cultural context
- Chapter Writer for setting consistency
- Content Reviewer for world consistency

## Usage

```bash
# Through the CLI
libriscribe worldbuilding
```

Worldbuilding can also be generated automatically during guided setup when the project requires it.

## Best Practices

1. **Consistency Management**
   - Track established facts
   - Maintain internal logic
   - Document rule systems
   - Verify timeline consistency

2. **Detail Balance**
   - Focus on story-relevant details
   - Avoid excessive complexity
   - Maintain reader accessibility
   - Support narrative needs

3. **Integration Planning**
   - Connect to character backgrounds
   - Support plot elements
   - Create narrative opportunities
   - Enable natural exposition

## Genre-Specific Features

The agent adapts its worldbuilding based on genre:

### Fantasy
- Magic systems
- Mythological elements
- Unique races/species
- Alternative physics

### Science Fiction
- Technology systems
- Future history
- Scientific principles
- Space/time mechanics

### Historical Fiction
- Period accuracy
- Cultural details
- Historical events
- Period terminology

### Contemporary
- Real-world accuracy
- Current events
- Social systems
- Modern technology