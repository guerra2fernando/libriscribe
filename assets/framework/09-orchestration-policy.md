# Orchestration Policy

## Mode Detection

Orchestration mode is detected once at `book-producer init` time and stored in `state.json` as `orchestrationMode`.
The `book-producer orchestrate` command follows the requested tool adapter when it generates work packets, while still reporting the stored state mode for traceability.

| Signal | Mode |
|---|---|
| `ANTHROPIC_API_KEY` env var set | `parallel` |
| Any `CLAUDE_*` env var present | `parallel` |
| `.claude/` directory exists in repo root | `parallel` |
| None of the above | `sequential` |

Override: `book-producer init --mode [parallel|sequential]`

## Tool Adapters

Installed tool entrypoints point back to the framework:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/book-producer.mdc`
- `.agents/workflows/book-producer.md`

These files must direct the active tool to `.book-framework/AGENTS.md` plus the matching file under `.book-framework/tooling/`.

## Parallel Mode (Claude)

Allowed for:

- Independent chapter drafts (different chapter numbers with no content dependency)
- Per-chapter review passes
- Research pack generation for non-overlapping topics

Drive these packets with:

- `book-producer orchestrate chapters <slug> --tool claude --chapters 1,2`
- `book-producer orchestrate research <slug> --tool claude --topics "topic one,topic two"`

Always sequential even in parallel mode:

- concept -> outline -> chapter plan (hard dependency chain)
- Any step that requires prior approval output as input
- Finalization assembly (single writer, single output file)

**Write-ownership rule:** No two agent calls may write to the same chapter file simultaneously. `book-project-manager` is the serialization authority for parallel chapter writes.

## Sequential Mode (Copilot, Cursor, Antigravity, Codex, others)

All tasks run one at a time. Parallel gates are disabled. The workflow proceeds linearly through stages and chapters.

Drive these packets with the matching tool name:

- `book-producer orchestrate chapters <slug> --tool cursor --chapters 1,2`
- `book-producer orchestrate research <slug> --tool copilot --topics "topic one,topic two"`

## Fallback

Even in parallel mode, execution falls back to sequential when:

- A task depends on the output of another in-progress task.
- An approval gate is pending.
- The user has not explicitly confirmed readiness to continue.
