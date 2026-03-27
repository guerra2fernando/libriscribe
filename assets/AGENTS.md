# book-producer - Agent Entry Point

This repository uses **book-producer**, a multi-tool book creation framework installed via npm or GitHub Packages.

## How to Read This

Before acting on any request:

1. Read this file (`AGENTS.md`) first.
2. Read `.book-framework/framework/01-core-rules.md` and follow the framework reading order.
3. Read `.book-framework/framework/09-orchestration-policy.md` and the matching file under `.book-framework/tooling/` for the active tool.
4. Read the relevant stage agent file from `.book-framework/agents/` for the current stage.
5. Read the active book-idea state from `.spec/<book-idea-name>/state.json` and `00-current-status.md`.
6. For specialist work, read the relevant standalone agent from `.book-framework/agents/standalone/`.

## Repo Layout

- `.book-framework/` is the installed framework package inside the user's repository.
- `.spec/<book-idea-name>/` stores the book workflow memory and stage specs.
- `<book-idea-name>/` at the repository root stores chapter files and the final manuscript.

Stage files are created lazily:

- Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`.
- Later stage files are created only when that stage starts after explicit user approval.
- Outside initialization, create at most two numbered stage files in one pass: a missing predecessor for recovery and the current stage file being started.

## Book-Idea-Scoped Workflow

This framework organizes all work around **book ideas** - named book projects stored under `.spec/<book-idea-name>/`. Branch mapping is used to resolve which book is active on the current branch.

Framework is dormant after `book-producer install` until the user explicitly runs `book-producer init`.

## Six-Stage Book Workflow

| Stage | Agent | What happens |
|---|---|---|
| 1 | `1-book-init` | Capture book concept, audience, category, constraints, publishing intent |
| 2 | `2-book-planner` | Build execution plan: milestones, chapter list, dependencies |
| 3 | `3-book-designer` | Produce final book design package: full plot summary, chapter summaries, and Mermaid story diagrams |
| 4 | `4-chapter-writer` | Create `<book>/chapters/` and implement one chapter file per design chapter |
| 5 | `5-book-reviewer` | Spell, grammar, editorial, and quality pass with actionable suggestions |
| 6 | `6-publish-assembler` | Concatenate chapter files as-is into the final manuscript; cleanup on confirmed finalization |

**User approval is mandatory after every stage. No auto-advancement.**

## Standalone Specialists

Available at any time. See `.book-framework/agents/standalone/` for role contracts.

`book-project-manager` · `concept-architect` · `book-outliner` · `developmental-editor` · `line-editor` · `character-world-designer` · `research-fact-integrity` · `chapter-arc-architect` · `continuity-checker` · `book-blurb-writer` · `sensitivity-reader`

## Tool Adapters

- Claude may use parallel packets created with `book-producer orchestrate ... --tool claude`.
- Copilot, Cursor, Antigravity, and other tools must stay sequential and use the matching `book-producer orchestrate` tool option.
- Tool entrypoints in the repo root must point back to `.book-framework/` and must not replace it as the canonical source.

## Core Rules Summary

- One stage active at a time.
- Current stage stays anchored until user explicitly advances.
- Only `4-chapter-writer` may produce prose files.
- Only `6-publish-assembler` may assemble the final manuscript and run cleanup.
- Force flags never bypass approval gates.
- See `.book-framework/framework/01-core-rules.md` for complete rules.
