# Shared Tool Adapter

Use this file for tool-agnostic `book-producer` workflow rules.

## Canonical files

1. Read `.book-framework/AGENTS.md` first.
2. Read `.book-framework/framework/01-core-rules.md` and `.book-framework/framework/03-stage-lifecycle.md`.
3. Read `.book-framework/framework/09-orchestration-policy.md`.
4. Resolve the active book from `.spec/.branch-mapping.json` when present.
5. Read `.spec/<book-slug>/state.json` and `00-current-status.md`.
6. Read the current stage agent from `.book-framework/agents/`.

## Repo layout

- `.book-framework/` contains installed framework assets and adapter docs.
- `.spec/<book-slug>/` contains workflow memory and book-stage specs.
- `<book-slug>/` at repo root contains chapter drafts and the assembled manuscript.

## Stage-file creation policy

- Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`.
- Later numbered stage files are created lazily when a stage starts after explicit user approval.
- Outside initialization, create at most two numbered stage files in one pass: a missing predecessor for recovery and the current stage file you are starting now.

## Orchestration

- Use `book-producer orchestrate chapters ...` or `book-producer orchestrate research ...` to generate tool-specific work packets.
- Only tool adapters for Claude may emit parallel packets.
- All other tool adapters must serialize work and avoid concurrent writes.
