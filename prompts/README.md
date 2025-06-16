# LibriScribe Prompt Templates

## Structure
- `templates/` - YAML files with prompt templates
- `configs/` - Model and cost configurations per prompt type

## Benefits
- User transparency - see what AI is asked to do
- Custom prompts - optimize for specific genres/styles
- Cost visibility - track token usage per operation
- A/B testing - compare prompt variations
- Model optimization - use appropriate models per task

## Template Customization

### Genre-Specific Prompts
Create specialized templates:
- Copy existing template: `cp templates/editor.yml templates/mystery-editor.yml`
- Modify for your genre's needs
- Add genre-specific focus areas

### Cost Optimization Examples
```yaml
# Budget-friendly settings
settings:
  max_tokens: 3000        # Reduced from default
  suggested_models:
    - "gpt-4o-mini"       # 83% cheaper than gpt-4o
    - "claude-3-haiku"    # Fast and economical

# Quality-focused settings
settings:
  max_tokens: 10000       # Increased for detailed output
  suggested_models:
    - "claude-3.5-sonnet" # Premium quality
    - "gpt-4o"            # Advanced reasoning
```

### Integration
Templates are automatically loaded by enhanced agents:
```python
agent = EnhancedEditorAgent(llm_client)
# Automatically uses prompts/templates/editor.yml if available
# Falls back to hardcoded prompts if template not found
```
