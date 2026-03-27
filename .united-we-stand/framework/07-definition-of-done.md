# Definition of Done

Framework-level completion criteria apply to all repos and stacks.

## Stage Completion Gate

A stage is done when all are true:

1. Designated stage file exists.
2. Required sections for that stage are present (`06-spec-writing-standard.md`).
3. Content truthfully reflects current branch state.
4. `00-current-status.md` is updated consistently.
5. Known blockers/gaps are explicitly documented.
6. `Next recommended step` is set according to state model.

## Role-Specific Completion Expectations

- **Initializer**: goal, scope, assumptions, open questions, and success criteria captured.
- **Planner**: objectives, tasks, dependencies, and risks are actionable.
- **Designer**: architecture, boundaries, and implementation guidance are clear.
- **Implementer**: changes, rationale, tests, and validation are recorded.
- **Code Reviewer**: quality, security, and optimization findings, severity, scope, and recommendations are explicit.
- **Finalizer**: delivered scope, known gaps, uncaptured spec/code differences, doc impact, and user closure confirmation status are clear; the workflow is only closed after explicit user confirmation.

## Implementation and Review Quality Gates

These gates must be applied through profile + review-model rules:

- naming is descriptive and readable
- required code comments from repo/profile guidance are present
- functions are kept small enough to be easy to scan and do not carry avoidable multiple responsibilities
- no avoidable duplication or dead code
- error handling and logging are intentional
- tests are proportionate and meaningful
- security boundaries are reviewed
- dependency/security checks are run when dependency changes occur
- available lint/parser/static-analysis checks relevant to the changed scope were run, or their absence/non-execution is explicitly disclosed

Profile-specific mandates (for example JS/TS style, audit commands, JSDoc practices) must be enforced via selected profile docs.

## Not Done If

- stage file lacks critical sections
- status categories are contradictory
- prerequisites were bypassed without explicit traceability
- documented behavior contradicts actual implementation state
- finalization claimed closure without surfacing meaningful spec/code differences or without explicit user confirmation that the final state is acceptable
- workflow remained anchored to `6-finalizer` after explicit closure confirmation instead of entering closed state
- a stage was auto-advanced without explicit user advancement
- workflow metadata regressed backward to an earlier stage because of later amendment work
- a higher-numbered stage was created or populated from an in-stage amendment request alone
- mandatory coding-steering requirements were skipped in the implemented code
