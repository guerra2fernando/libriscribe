# Framework Core Rules

## Invariants

1. **One stage at a time.** Only one workflow stage may be active for a book idea. Auto-advancement is prohibited.
2. **Approval gates are mandatory.** A stage may reach "complete" status but the `Current stage` field stays anchored until the user explicitly advances.
3. **No backward regression.** `Current stage` never moves to a lower-numbered stage. Earlier-stage amendments are applied in place; downstream impact is noted in status metadata.
4. **Stages must be completed in order.** Stages 1 -> 2 -> 3 -> 4 are mandatory and cannot be skipped. Stage 5 (review) is optional. Stage 6 finalizes. A user may not jump from stage 1 to stage 4 without completing 2 and 3 first.
5. **Stage 4 is the first chapter-implementation stage.** Stage 3 produces final content design (plot, chapter summaries, diagrams), and only `4-chapter-writer` may produce chapter prose files.
6. **Force flags never bypass approval gates.** `--force` controls file overwrite/reset behavior, not stage progression.
7. **Chapter files are user-owned.** Framework never overwrites files under `<book-slug>/chapters/`.
8. **Finalization cleanup is irreversible.** Explicit user confirmation is required before any directory is deleted; cleanup cannot be silently skipped.
9. **Missing predecessor files trigger a creation notice.** If a stage attempts to start but the previous stage's output file is missing, the active tool must tell the user: "Stage X file (0X-xxx.md) is missing. I will create it from the available context before proceeding to stage Y."
10. **Lazy stage-file creation only.** Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`. Later numbered stage files are created only when that stage starts after explicit user approval.
11. **No burst stage creation.** Outside initialization, create at most two numbered stage files in a single pass: a missing predecessor needed for recovery and the current stage file being started now.
12. **Stage 5 (review) is optional.** The user may advance directly from stage 4 to stage 6. If skipped, note it in `00-current-status.md` and set stage 5 in `incompletedStages`.

## Stage Ownership

| Stage | May write |
|---|---|
| `1-book-init` | `01-init.md`, `state.json`, `00-current-status.md` |
| `2-book-planner` | `02-plan.md`, `state.json`, `00-current-status.md` |
| `3-book-designer` | `03-design.md`, `state.json`, `00-current-status.md` |
| `4-chapter-writer` | `<book-slug>/chapters/*.md`, `assets/chapter-memory.json`, `04-implementation.md` |
| `5-book-reviewer` | `05-review.md`, `state.json`, `00-current-status.md` |
| `6-publish-assembler` | `manuscript-*-final.md`, `06-finalization.md`, cleanup only |

## Amendment Rule

Requests to add, modify, or clarify content inside the current stage are treated as **in-place amendments**, not advancement. The stage file is updated; `Current stage` does not change.

## Conflict Rule

When spec and code/content conflict, spec takes priority. Reconcile by updating the content to match the spec, then note the change in the current stage file.
