# Versions

## 0.1.0

`0.1.0` is the initial published version of `book-producer`.

This version establishes the package as a repo-scoped AI book writing framework distributed as a CLI. It is designed to be installed into an existing git repository so an AI assistant can work with persistent, branch-aware writing context instead of relying only on chat memory.

### What this version does

This version provides:

- a CLI named `book-producer`
- installable framework assets under `.book-framework/`
- managed tool entrypoints that point back to `.book-framework/`
- per-book workflow memory under `.spec/<book-slug>/`
- book content (chapters, manuscript) at `<book-slug>/` in the repository root
- deterministic markdown-based workflow guidance for AI-assisted book creation
- six numbered stage agents covering the full book creation lifecycle
- specialist agents for continuity, arc planning, editing, research, and worldbuilding

The main idea in `0.1.0` is that the framework separates:

- reusable framework rules in `.book-framework/`
- book-specific working memory in `.spec/<book-slug>/`
- actual book content in `<book-slug>/` at the repository root

That means a repository can refresh or reset framework assets while keeping book progress and chapter content separate.

### CLI commands in 0.1.0

#### `book-producer install`

Installs the framework files into a target git repository.

Writes: `.book-framework/agents/`, `.book-framework/framework/`, `.book-framework/templates/`, `.book-framework/tooling/`, `.book-framework/AGENTS.md`, `.book-framework/CHAT-WORKFLOW.md`, plus managed tool entrypoints in the repository root and tool-specific folders.

Supports `--force` to overwrite all managed files with package defaults.

#### `book-producer status`

Prints the current book status: stage, completed steps, approved chapters, next recommended step.

#### `book-producer list`

Lists all book slugs found in `.spec/` with their current stage.

### Workflow model in 0.1.0

Six numbered workflow stages:

1. `1-book-init` — capture concept, audience, genre, publishing intent
2. `2-book-planner` — chapter list, word targets, milestones, dependency map
3. `3-book-designer` — full-plot arc, per-chapter design, character sheets, worldbuilding
4. `4-chapter-writer` — implement one chapter file per designed chapter
5. `5-book-reviewer` — editorial review pass (optional)
6. `6-publish-assembler` — assemble final manuscript

Stages 1, 2, 3, 4, and 6 are mandatory and cannot be skipped. Stage 5 is optional. Stages advance only on explicit user approval.

### Chapter file format in 0.1.0

Canonical chapter frontmatter:

```markdown
---
chapter: N
title: "Chapter N: Chapter Title"
status: draft
word_count_target: 3000
word_count_actual: 0
assigned_agent: chapter-writer
reviewer_notes: ""
---
```

The `chapter: N` field is the sort key. The `title: "Chapter N: ..."` format provides human-readable order confirmation. The assembler validates gaps, duplicates, and title format before producing the manuscript.

### Error handling in 0.1.0

- `state.json` read failures print a descriptive recovery message
- `state.json` JSON parse failures include the file path and recovery steps
- `.branch-mapping.json` read or parse errors return an empty mapping rather than crashing
- All destructive CLI operations require explicit confirmation

### Summary of 0.1.0

Version `0.1.0` is the foundational release of the project. It includes a usable CLI, full six-stage workflow, branch-aware book tracking, chapter assembly with validation, defensive error handling, a complete test suite, and full user-facing and maintainer documentation.
