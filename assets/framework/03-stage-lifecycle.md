# Stage Lifecycle

## Progression Rules

1. Stages advance strictly in order: 1 -> 2 -> 3 -> 4 -> 5 -> 6.
2. Each stage requires explicit user approval before the next begins.
3. Initialization creates `00-current-status.md` and `01-init.md`. Later stage files (`02-plan.md` -> `06-finalization.md`) are created lazily when that stage starts.
4. `Current stage` stays anchored to the active stage until the user explicitly advances.
5. Do not create a higher-numbered stage file during the current stage unless the user explicitly requests it.
6. Outside initialization, create at most two numbered stage files in one pass: the missing predecessor required for recovery and the current stage file being started.
7. **Stages 1, 2, 3, 4, and 6 are mandatory.** Stage 5 (review) is optional. No other stage may be skipped or bypassed.
8. **Missing predecessor file check:** Before starting any stage N, verify that the stage N-1 file exists. If it is missing, tell the user: "Stage N-1 file (0N-1-xxx.md) is missing. I will reconstruct it from available context before advancing." Create the file with a recovery notice at the top before continuing.

## Within-Stage Lifecycle

```text
stage created -> in-progress -> complete (anchored) -> user advances -> next stage
```

"Complete" is a status note, not a state transition. The stage remains current.

## Review Stage (Optional)

Stage 5 (`5-book-reviewer`) is the only stage that may be skipped. If the user explicitly advances from stage 4 to stage 6 without review:

- Move stage 5 to `incompletedStages` in `state.json`.
- Note it in `00-current-status.md` with a warning that the manuscript has not been editorially reviewed.
- Proceed to stage 6.

## Finalization Close

After `6-publish-assembler` assembles the manuscript and the user explicitly confirms closure, set:

- `currentStage`: `"none"`
- `finalized`: `true`
- `nextRecommendedStep`: `"none"`

If the finalized branch receives more work, reopen stage 6 as the active stage and require final approval again after the new work.

## Stage File Schema

Each numbered stage file (`01-init.md` -> `06-finalization.md`) must contain at minimum:

- **Book idea / problem statement**
- **Inputs**
- **Constraints**
- **Scope (in / out)**
- **Deliverables**
- **Status**
