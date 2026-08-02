---
sidebar_position: 3
---

# Outliner Agent

The Outliner Agent creates comprehensive chapter-by-chapter outlines for your book project, providing a detailed roadmap for the writing process.

## Overview

The Outliner Agent takes the initial book concept and expands it into a structured outline, breaking down the story into chapters and key scenes. It ensures proper pacing, plot development, and narrative structure.

## Features

### Chapter Structure
- Creates detailed chapter summaries
- Establishes clear story beats
- Maintains proper pacing
- Ensures narrative flow

### Plot Development
- Develops main plot and subplots
- Places major plot points
- Tracks character arcs
- Maintains story tension

### Content Organization
- Generates chapter titles
- Creates scene breakdowns
- Includes key story elements
- Tags important plot points

## Output Format

The outline is generated in Markdown format:

```markdown
# Chapter 1: Title
- Opening scene description
- Key plot points
- Character interactions
- Scene objectives

# Chapter 2: Title
...
```

## Integration

The Outliner works closely with:
- Concept Generator for initial story direction
- Character Generator for character arc integration
- Worldbuilding Agent for setting integration
- Chapter Writer for detailed chapter development

## Usage

```bash
# Through the CLI
libriscribe outline
```

The Outliner is also run automatically during guided setup after concept generation.

## Best Practices

1. **Review and Iteration**
   - Review the generated outline
   - Make necessary adjustments
   - Ensure all plot threads are addressed
   - Verify pacing and structure

2. **Chapter Balance**
   - Check chapter lengths
   - Verify plot point distribution
   - Ensure proper character focus
   - Maintain narrative momentum

3. **Integration Points**
   - Mark character development moments
   - Note worldbuilding elements
   - Identify research needs
   - Tag emotional beats

## Error Handling

The Outliner Agent includes error handling for:
- Invalid project data
- File system operations
- Content generation issues
- Format validation

## Pipeline Context Propagation

These behaviours were added to ensure every user answer reaches the outline.

### User Chapter Count Respected

`_get_max_chapters()` now reads `num_chapters_str` from the PKB to detect whether the user explicitly set a chapter count. When set, the user's preference is enforced (capped by length tier: Short Story ≤ 2, Novella ≤ 8, Novel ≤ 20). When not set (default `num_chapters=1`), the length-tier ceiling alone governs — the default is never mistaken for a user preference.

A chapter count hint is also injected into the LLM prompt so the model targets the right number.

### Author Notes Injected Into Prompts

Both `execute()` (outline-level) and `generate_scene_outline()` (scene-level) append an **Author notes** block when any of these Advanced-mode PKB fields are set:

| Field | Label |
|---|---|
| `inspired_by` | Inspired by |
| `author_experience` | Author experience |
| `key_takeaways` | Key takeaways |
| `case_studies` | Includes case studies |
| `actionable_advice` | Includes actionable advice |
| `marketing_focus` | Marketing focus |
| `sales_focus` | Sales focus |
| `research_question` | Research question |
| `hypothesis` | Hypothesis |
| `methodology` | Methodology |

### Dynamic Questions Propagated

Genre-specific Q&A collected during Advanced setup (`pkb.dynamic_questions`) is appended to the Book Description in `generate_scene_outline()` so scene-level prompts reflect the author's genre-specific intentions.

### Chapter Limit Enforced

`_enforce_chapter_limit()` is called after `process_outline()` to strip any extra chapters the LLM may have generated beyond `max_chapters`.

### Description Never Overwritten

The user's original book description is never replaced by any LLM-generated summary. The internal `book_summary_lines` extraction loop still runs for parsing purposes but the assignment `project_knowledge_base.description = …` was removed.