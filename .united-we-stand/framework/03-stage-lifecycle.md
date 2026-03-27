# Stage Lifecycle

Each framework stage moves through deterministic lifecycle states.

## Lifecycle States

### 1. Not started
Stage has not begun in current branch context.

### 2. Active and unfinished
Stage is current anchor and still needs work.

### 3. Active and completed
Stage work is complete, but stage remains anchored until explicit advancement.

### 4. Completed and advanced
Stage was explicitly advanced and moved to `Completed steps`.

### 5. Incompleted / bypassed
Stage was active but unfinished and explicitly skipped or forced past.

### 6. Closed after finalizer confirmation
Workflow is no longer actively anchored to a numbered stage because the user explicitly approved finalization.

## Advancement Triggers

Advancement occurs only when one of the following is true:

- user explicitly requests next step
- user explicitly requests skip/bypass
- `--force` semantics are applied per framework policy

Completion alone is not an advancement trigger.
Editing or enriching a stage file is not an advancement trigger.
Broad "get it ready", "take it all the way", or outcome-oriented phrasing is not by itself an advancement trigger across multiple stages.
Explicit user closure confirmation after `6-finalizer` is the trigger that moves workflow from active finalization to closed state.

## Amendment Behavior

- A request such as `add this in planning`, `change the initializer`, or `update design` is an amendment to that stage file.
- Amendment requests must not be interpreted as permission to create or fill the next stage.
- If the amended stage becomes complete, it remains `Active and completed` until the user explicitly advances.

## Backward-Stage Requests

- A request that targets earlier-stage work after the workflow has already moved forward is a backward-stage request.
- Backward-stage requests do not change lifecycle category placement for the current stage.
- Execute the requested earlier-stage work, update the relevant stage files, and mark downstream state as needing refresh in status metadata when applicable.
- The workflow continues from its existing later-stage anchor unless the user explicitly advances forward again, skips, or bypasses.

## Multi-Stage Requests

- Never auto-advance, even if the next stage seems obvious.
- If a request could be read as advancing through two or more stages at once, do not run multiple stages.
- Explain that united-we-stand only runs one stage at a time.
- Suggest the next recommended numbered stage first.
- Ask the user to confirm one single stage to run now.
- Until the user confirms that single stage, keep the workflow anchored in the current stage.

## Resumption Inputs

When resuming work, consult:

- `Current stage`
- `Next recommended step`
- `Status note`
- `Blockers / warnings`

If the workflow is closed (`Current stage = none`), treat any new branch-change request as a reopen signal for `6-finalizer`.
