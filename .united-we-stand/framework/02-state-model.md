# State Model

`00-current-status.md` is the canonical branch status file, stored under `.spec-driven/<sanitized-current-branch>/`.
`state.json` is the machine-readable runtime companion file in the same folder.

## Required Fields

- `Current branch`
- `Current stage`
- `Completed steps`
- `Incompleted stages`
- `Next recommended step`
- `Status note`
- `Blockers / warnings`
- `Last updated by`
- `Last updated at`

## Anchored Current Stage Model

1. `Current stage` is the active stage anchor.
2. A stage remains in `Current stage` until explicit user advancement, explicit skip, or force bypass.
3. Completing work does not automatically move a stage to `Completed steps`.
4. `Completed steps` records stages explicitly left behind after user advancement.
5. If user moves forward without completion, move prior stage to `Incompleted stages`.
6. `Current stage` must never move backward to an earlier numbered stage.
7. `Current stage` must match the highest existing numbered stage file in the branch folder among `01-init.md` through `06-finalization.md`.

## Closed Workflow State

- A branch may enter an explicitly closed workflow state only after `6-finalizer` presents final observations and the user explicitly confirms closure.
- In that closed state:
  - `Current stage = none`
  - `Next recommended step = none`
  - `6-finalizer` appears in `Completed steps`
  - workflow is considered closed/finalized rather than actively anchored to a numbered stage
- If the user later requests more work on that branch, reopen `6-finalizer` as the current stage and clear the closed/finalized state before continuing.

## In-Stage Amendment Rule

- If the user asks to add, modify, remove, clarify, or fix content in the current stage, update that stage in place.
- Do not auto-advance because the edited stage now looks complete.
- Keep `Current stage` anchored to the same stage unless the user explicitly says to advance, skip, or bypass.
- Set `Next recommended step` according to reality:
  - if the stage is still unfinished, recommend the same stage
  - if the stage is now complete but not advanced, keep the same `Current stage` and recommend the next logical stage

## Cross-Stage Amendment Rule

- If the user explicitly asks to modify a different stage file, treat that as an amendment request for the named stage file.
- Update the targeted stage file in place without treating the request as workflow advancement by itself.
- Do not create, populate, or advance into a higher-numbered stage just because an earlier stage was amended.
- Preserve the existing `Current stage` unless the user explicitly says to advance, skip, or bypass.

## Backward Work Rule

- If the workflow is already in a later stage and the user requests work that belongs to an earlier stage, perform the work without regressing state categories.
- Update the relevant earlier-stage files in place.
- Keep `Current stage`, `Completed steps`, and `Incompleted stages` unchanged unless the user is moving forward or invoking skip/force semantics.
- Update `Status note` and `Blockers / warnings` to record that earlier-stage work changed after later-stage progress, so downstream work can be refreshed consciously.
- Set `Next recommended step` to the nearest forward-looking corrective action, usually re-running or refreshing the current stage.

## Advancement Bookkeeping Rule

- Only explicit user advancement changes `Current stage`.
- When the user explicitly advances from one stage to another:
  - move the stage being left behind to `Completed steps` if it is complete
  - move the stage being left behind to `Incompleted stages` if it is unfinished and the user still wants to move on
  - keep any earlier explicitly used stages in `Completed steps` if they were already completed and are no longer current
  - ensure every recorded completed or incompleted stage has its corresponding stage document present in `.spec-driven/<branch>/`

## One-Stage-At-A-Time Rule

- Never infer permission to cross two or more stages from broad outcome wording alone.
- If a request could mean `do planning, design, and implementation` or any other multi-stage jump, do not run multiple stages.
- Explain that united-we-stand only runs one stage at a time.
- Ask the user to confirm one single stage, suggesting the next recommended numbered stage first.
- Without that single-stage confirmation, keep `Current stage` anchored and perform only the nearest safe in-stage work.

## Category Invariants

- A stage can appear in exactly one category at a time:
  - `Current stage`
  - `Completed steps`
  - `Incompleted stages`
- No duplicates within a category.
- `Current stage` must never be empty while workflow is active.
- `Current stage` may be `none` only when the workflow is explicitly closed after user-confirmed finalization.
- While workflow is active, `Current stage` must match the highest existing stage file present in the branch folder.
- In closed workflow state, `06-finalization.md` must exist and `6-finalizer` must be recorded as completed.

## Next Recommended Step Rules

- If current stage is unfinished:
  - recommend continuing the same stage.
- If current stage is complete but not advanced:
  - keep current stage anchored and point `Next recommended step` to next logical numbered stage.
- If stage was skipped/forced past:
  - set `Next recommended step` to explicit user-selected target or next valid path after bypass.
- If current stage is `6-finalizer` and final observations have been prepared but the user has not yet confirmed closure:
  - keep `Current stage = 6-finalizer`
  - set `Next recommended step` to explicit user confirmation or requested follow-up changes
- If workflow is explicitly closed after finalizer confirmation:
  - set `Current stage = none`
  - set `Next recommended step = none`

## Status Note Rules

`Status note` must be plain-language and include:

- what stage is active
- whether it is complete
- what should happen next
- whether earlier-stage work changed after later-stage progress when that affects downstream confidence
- for finalization, whether user closure confirmation is still pending
- when workflow is closed, that the branch is finalized and waiting for a new user request to reopen work

## Completion Reflection Rule

If any stage file changes and status is stale, update `00-current-status.md` to match reality.
If status auto-correction is made, report that correction briefly in chat output.
Keep `state.json` synchronized with the same status state.

## `state.json` Schema Rule

Use the exact machine-readable keys below in `state.json`:

- `branchName`
- `sanitizedBranchName`
- `branchMemoryFolder`
- `currentStage`
- `completedSteps`
- `incompletedStages`
- `nextRecommendedStep`
- `lastUpdatedBy`
- `lastUpdatedAt`
- `initialized`
- `finalized`

Do not invent alternate key names such as snake_case variants.

## Auto-Correction Scope

Status checker may auto-correct status-category contradictions (for example duplicated stage labels across categories) when correction is deterministic.
If ambiguity remains, warn and request user confirmation before destructive status edits.
