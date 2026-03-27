# Skip and Force Policy

## Normal Rule

Follow stages in order unless user explicitly requests skip/bypass.

## Force and Bypass Semantics

`--force` means explicit override of normal prerequisite/progression behavior.

Force/bypass must never be inferred from broad delivery language alone.
If a request could imply skipping or combining two or more stages, explain the one-stage-at-a-time rule and require the user to confirm one exact target stage before proceeding.

When force/bypass is applied:

- document bypass in stage file and status note
- move unfinished skipped stage(s) to `Incompleted stages`
- set new `Current stage` explicitly
- update `Next recommended step` accordingly

## Direct Work Before Initialization

If branch memory does not exist yet, direct repo work without explicit initialization is separate from force/bypass:

- continue helping with the requested work normally
- do not create `.spec-driven/...` files unless the user explicitly asks to initialize
- do not interrupt to explain framework setup unless the user explicitly asks to initialize or explicitly mentions the framework

## Default Branch Initialization Warning

If the current branch is detected as the repository default branch and the user asks to initialize framework memory:

- warn about the risks of anchoring branch-specific workflow state on the default branch
- ask for explicit confirmation before creating `.spec-driven/...` files
- only skip that confirmation when the user explicitly uses `--force` or equivalent force/bypass wording

## Mandatory Stage Warning

If user bypasses a mandatory stage (`1-initializer` or `4-implementer`):

- warn clearly about risk and missing guarantees
- proceed only if user confirms bypass intent

## Traceability Requirement

Bypass never erases history. Bypassed state must remain visible in:

- `00-current-status.md`
- relevant stage file notes
- traceability/risk appendices when impacted
