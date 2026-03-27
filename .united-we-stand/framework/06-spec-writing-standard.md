# Spec Writing Standard

This file defines canonical structure for branch markdown files so multiple AI tools behave consistently.

Branch files are runtime memory under `.spec-driven/<sanitized-current-branch>/`.
Machine-readable runtime state lives in `.spec-driven/<sanitized-current-branch>/state.json`.

## General Writing Rules

1. Prefer explicit structured sections over freeform prose.
2. Separate confirmed facts from assumptions and open questions.
3. If information is unknown, write `Unknown` rather than inventing details.
4. If section is not applicable, write `Not applicable`.
5. Update existing structure in place unless change-log style is explicitly needed.
6. Keep files truthful to current branch state.

## Cross-File Section Schema

For consistency and reuse, every stage or appendix file should contain the sections below when relevant:

- Purpose
- Inputs
- Constraints
- Decisions
- Open questions
- Out of scope
- Dependencies
- Status

Stage-specific required sections below remain mandatory even if this schema is adapted.

## `00-current-status.md` Standard

Required fields:

- Current branch
- Current stage
- Completed steps
- Incompleted stages
- Next recommended step
- Status note
- Blockers / warnings
- Last updated by
- Last updated at

## Stage File Minimum Sections

### `01-init.md`

- Raw idea / problem statement
- Scope (in)
- Scope (out)
- Assumptions
- Open questions
- Success criteria

### `02-plan.md`

- Objectives
- Dependencies
- Risks / unknowns
- Suggested execution order
- Detailed task list
- Status

### `03-design.md`

- Architecture / approach
- Key components
- Interfaces / data flow
- Constraints
- Design decisions
- Diagrams/flows when useful (Mermaid allowed)

### `04-implementation.md`

- What changed
- Why it changed
- Files touched
- Validation and tests executed
- Remaining gaps / follow-ups

### `05-code-review.md`

- Quality & maintainability findings
- Security / boundary findings
- Optimization findings
- Severity / priority
- Recommended fixes
- Reviewed scope and non-reviewed scope

### `06-finalization.md`

- Final summary
- Delivered scope
- Known gaps
- Recommended next actions
- Documentation updates performed

## Appendix File Standards

### `07-decisions.md`

- Date
- Decision
- Rationale
- Alternatives considered
- Impact

### `08-traceability.md`

- Requirement
- Source
- Plan reference
- Design reference
- Implementation reference
- Review reference
- Final status

### `09-risks-issues.md`

- Risk/issue description
- Impact
- Likelihood
- Mitigation
- Owner
- Status

### `10-test-strategy.md`

- Test scope
- Test levels
- Critical cases
- Environment/tooling notes
- Exit criteria

### `11-change-log.md`

- Chronological meaningful changes to branch spec intent/state

### `12-handoff.md`

- Current state
- Immediate next action
- Required context for next chat/engineer

### `13-retrospective.md`

- What worked
- What did not
- Improvement actions

## Subfolder Standards

- `modules/`: module-specific design/implementation notes
- `api/`: contracts, endpoints, auth boundaries
- `data/`: schema notes, migrations, boundaries
- `ux/`: flows, screen states, copy notes
