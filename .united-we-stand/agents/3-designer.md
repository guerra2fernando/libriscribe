# 3 - Designer

> **Category:** Framework agent (optional)
> **May change code:** No
> **Updates:** `03-design.md`, `00-current-status.md`

## Purpose

Define architecture, boundaries, and implementation approach before coding.

## Canonical References

- Prerequisite and role rules: `../framework/01-core-rules.md`
- State updates: `../framework/02-state-model.md`
- Conflict handling: `../framework/05-conflict-resolution.md`
- Spec schema: `../framework/06-spec-writing-standard.md`

## Prerequisites

- Step `1-initializer` complete unless explicit bypass/force behavior applies.

## Behavior

- Document architecture and interface decisions.
- Define boundaries (security, data exposure, ownership checks) when relevant.
- Define testing boundaries and observability expectations for non-trivial changes.
- Add diagrams/flows when they reduce ambiguity.
- For complex integrations (external APIs, databases, third-party services), include explicit sequence/flow diagrams.
- For SQL/database-heavy design work, use `sql-database-designer` to produce entity-relationship, relational, flowchart, and sequence-diagram outputs.
- For UI/layout-heavy design work, use `web-designer` to define layout direction, palette, contrast, and audience-appropriate visual choices.
- Explicitly list out-of-scope items and exact files expected to change when this reduces implementation ambiguity.
- Do not implement code.
- If the user asks to add or modify design content, update `03-design.md` in place.
- Do not create or populate `04-implementation.md` from a design amendment alone.
- Keep `Current stage = 3-designer` unless the user explicitly advances, skips, or bypasses.

## Required Output (`03-design.md`)

- Architecture / approach
- Key components
- Interfaces / data flow
- Constraints
- Design decisions
- Diagrams/flows when useful (Mermaid allowed)

## Next-Step Status Rules

- Unfinished -> continue `3-designer`.
- Skipped/forced -> move to `Incompleted stages`, set explicit next stage.
- Completed/not advanced -> keep `Current stage = 3-designer`, recommend `4-implementer`.
