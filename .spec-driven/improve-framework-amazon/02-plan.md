# 02-plan

## Goals
- Build a distributable npm package (`book-framework`) with `install` command for setup.
- After install, entire workflow runs **conversationally in Claude**: agent reads/writes `.spec/<book-idea>/` files directly; no additional CLI commands needed.
- Enforce book-idea-scoped workflow memory under `.spec/<book-idea-name>/` with explicit initialization (CLI or chat-based).
- Implement stage lifecycle: initialize -> plan -> design -> implement -> review -> finalize (publish-assembly finalization).
- Enforce approval gate after every stage (explicit user confirmation in chat).
- Support tool-aware orchestration:
  - Chat/Claude default: parallel-capable orchestration.
  - Other tools (if used): sequential orchestration.
- Ensure implementation stage is the chapter-writing execution stage where `.spec/<book-idea>/book/chapters/` is materialized.
- Ensure finalization stage assembles one editable final manuscript file without rewriting chapter content.
- Include final cleanup requirement: optionally remove any temporary local reference directories when finalization is approved.
- Optional: CLI convenience commands (`init`, `list`, `use`, `doctor`, `refresh`) for terminal-first users; none are required in chat workflow.

## Dependencies
- Existing initialization direction captured in `01-init.md`.
- Reference behavior from https://github.com/mrudinal/united-we-stand-framework (package/CLI/template model).
- Reference orchestration style from https://github.com/guerra2fernando/libriscribe (approval-gated collaboration).
- Node 18+ runtime for package tooling and CLI distribution.

## Risks / unknowns
- Destructive finalization cleanup can remove useful historical references if run without an explicit safety check.
- Book-idea matching heuristics may produce false positives unless similarity logic is conservative.
- Cross-tool behavior consistency may drift if pointer instructions are ambiguous.
- Parallel orchestration may create merge conflicts in book-idea artifacts if write ownership is not serialized.
- Final manuscript assembly quality depends on chapter format normalization rules.

## Suggested execution order
1. Define book-idea memory architecture and naming/matching policy.
2. Define CLI commands and command contracts.
3. Define installed framework assets and agent/stage instructions.
4. Define orchestration policy (parallel/sequential + gate rules).
5. Implement package scaffold and CLI runtime.
6. Implement book-idea lifecycle commands.
7. Implement stage templates and runtime state management.
8. Implement finalization assembly and cleanup behavior.
9. Validate with unit/integration tests and dry-run safety checks.
10. Prepare publishing flow and migration notes.

## Detailed task list
### Workstream A: Book-idea-scoped runtime model
- Create spec memory model under `.spec/<book-idea-name>/` (workflow files only).
- Create book content directory `<book-idea-name>/` at repo root (chapters, manuscript).
- Define machine state schema for book-idea lifecycle (includes `bookContentDir` pointer).
- Implement book-idea-name sanitization and collision handling.
- Implement book-idea matching lookup:
  - exact match check,
  - optional close-match suggestions,
  - explicit user choice to continue or create new.

### Workstream B: CLI command surface
- Define and implement command set:
  - `book-framework install`
  - `book-framework init`
  - `book-framework status [slug]` ← NEW
  - `book-framework list`
  - `book-framework use`
  - `book-framework doctor`
  - `book-framework refresh`
- Ensure install is passive (no automatic stage activation).
- Ensure `init` is the only workflow bootstrap entrypoint.
- `status` command: output current stage, chapter progress, active branches, last-updated timestamp.
- Add `--force` support where destructive/overwrite behavior is relevant.

### Workstream B.2: Branch Mapping
- Implement `.spec/.branch-mapping.json` to track which books are worked on per branch.
- Mapping entries:
  - `branches`: map of branch name → list of book slugs
  - `books`: map of book slug → displayName, branch list, createdAt
- On `init`: detect current git branch and update mapping.
- On `status` (CLI or chat): read mapping to show which branches are active for a book.
- Branch resolution policy (for chat context resolution):
  - 0 books on branch → list all books, ask
  - 1 book on branch → auto-select unless user specifies different
  - Multiple books on branch → ask (unless user mentions book name in chat message)
  - User mentions book name → use it directly, no confirmation needed

### Workstream B.1: Force policy and safety model
- Define a shared force policy document for command/runtime consistency.
- Require explicit warning text before any destructive force action.
- Keep dry-run support compatible with force paths to preview impact.
- Ensure force never bypasses mandatory user approval gates for stage transitions.
- Ensure finalization cleanup force path still requires explicit user confirmation before directory deletion.

### Workstream C: Stage and approval engine
- Encode six-stage workflow for book context.
- Enforce one-stage-at-a-time progression.
- Require explicit user approval between stages.
- Keep stage ownership/write boundaries deterministic.

### Workstream D: Multi-tool orchestration policy
- Add explicit instruction blocks for Claude/Cursor/VS Code/Codex style agents.
- Set default execution mode by tool:
  - Claude parallel-capable,
  - all others sequential.
- Add fallback sequencing rules when dependencies or approvals require serialized execution.

### Workstream E: Book pipeline semantics
- Stage 4 implementer: execute full chapter writing according to approved design.
- Stage 5 review: structural and editorial quality review pass.
- Stage 6 finalizer (publish-assembly):
  - gather all approved chapters,
  - produce one final editable manuscript file,
  - record finalization summary.

### Workstream F: Finalization cleanup requirement
- Add explicit finalization action to delete any user-specified temporary/reference directories after successful approved finalization.
- Add safety controls:
  - only execute cleanup in finalizer stage,
  - require explicit user final approval before deletion,
  - log deleted paths in finalization report.

### Workstream G: Testing and verification
- Unit tests for book-idea init/matching/routing.
- Tests for stage transitions and approval gate enforcement.
- Tests for orchestration mode selection by tool.
- Tests for final manuscript assembly.
- Tests for cleanup trigger conditions and safe-path deletion.
- Tests for `--force` command semantics and overwrite/reset behavior parity.

### Workstream H: Package and release
- Prepare package metadata, bin mapping, and files list.
- Ensure install templates are complete for supported tools.
- Add docs for install, init, and workflow usage.
- Validate npm publish flow (dry-run, package inspection, and release checklist).

## Status
- Stage planning is complete at specification level.
- Ready for `3-designer` after explicit user advancement.