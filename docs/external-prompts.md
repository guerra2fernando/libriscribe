# External Prompt Templates

LibriScribe supports external YAML prompt templates, giving you full control over AI behavior.

## Quick Start

### View Available Templates
```bash
ls prompts/templates/
# Shows: editor.yml, concept_generator.yml, chapter_writer.yml, etc.
```

### Customize a Template
1. Copy: `cp prompts/templates/editor.yml prompts/templates/my-editor.yml`
2. Edit the template text and settings
3. Templates are automatically detected and used

## Template Structure
```yaml
name: "Chapter Editor"
cost_tier: "high"           # high/medium/low
template: |
  Your custom prompt with {variables}
settings:
  max_tokens: 8000
  suggested_models: ["gpt-4o-mini"]
```

## Available Templates
- **editor.yml** - Chapter editing and refinement (high cost)
- **concept_generator.yml** - Book concept creation (medium cost)
- **chapter_writer.yml** - Chapter content generation (high cost)
- **character_generator.yml** - Character profile creation (medium cost)
- **worldbuilding.yml** - World and setting details (medium cost)
- **outliner.yml** - Story structure and chapter planning (medium cost)

## Cost Management
Each template includes cost optimization:
- `max_tokens`: Response length limits
- `cost_tier`: Operation expense category
- `suggested_models`: Efficient model recommendations

## Example: Custom Genre Editor
```yaml
name: "Mystery Editor"
template: |
  Expert mystery editor: enhance this chapter for suspense and intrigue.
  
  Focus on:
  - Clue placement and pacing
  - Red herrings and misdirection
  - Character suspicion levels
  - Plot revelation timing
  
  Chapter: {chapter_content}
  Review: {review_feedback}
```
