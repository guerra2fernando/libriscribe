# Architecture

## Overview

`book-producer` is a repo-scoped CLI package for installing a persistent AI-assisted book workflow into any repository.

The architecture separates three concerns:

1. **Package code** - the CLI and implementation in this repository
2. **Installed framework assets** - reusable workflow rules written into `.book-framework/`
3. **Book-specific state and content** - `.spec/<book-slug>/` plus `<book-slug>/` at repo root

## Target repository structure

After `book-producer install`:

```text
.book-framework/
  agents/
  framework/
  templates/
  tooling/
  AGENTS.md
  CHAT-WORKFLOW.md
AGENTS.md
CLAUDE.md
.github/copilot-instructions.md
.cursor/rules/book-producer.mdc
.agents/workflows/book-producer.md
```

After `book-producer init "My Book"`:

```text
.spec/
  .branch-mapping.json
  my-book/
    state.json
    00-current-status.md
    01-init.md
    assets/
      chapter-memory.json
my-book/
  chapters/
```

Later stage files are created lazily as stages start.

## Orchestration

- Claude may use parallel chapter and research packets.
- Copilot, Cursor, Antigravity, and other tools are serialized.
- `book-producer orchestrate ...` writes the latest plan to `.spec/<book-slug>/assets/orchestration/`.

## Verification model

- `npm run build`
- `npm test`
- `npm run lint`
- `npm audit --omit=dev`
- `npm pack ./.release/npm`
- `npm pack ./.release/github`
