# 1 - Initializer

> **Category:** Framework agent (**mandatory**)
> **May change code:** No
> **Updates:** `01-init.md`, `00-current-status.md`

## Purpose

Capture and structure branch intent before planning/design/implementation.

## Canonical References

- Core invariants: `../framework/01-core-rules.md`
- State updates: `../framework/02-state-model.md`
- Spec schema: `../framework/06-spec-writing-standard.md`

## Prerequisites

None.

## Behavior

- Convert user idea into initial branch definition.
- Capture scope boundaries, assumptions, questions, and success criteria.
- Capture out-of-scope explicitly to reduce downstream ambiguity.
- When initialization is requested, always perform a fresh live check of the current git branch before creating or updating branch memory.
- Do not rely on a previous branch check, previous status output, or remembered branch context from earlier in the same chat.
- If branch memory does not exist yet and the user explicitly asks to initialize or init the work, create the branch spec for `1-initializer`.
- If branch memory does not exist yet and the user uses natural bootstrap language such as `let's start this`, `help me with this idea`, `i want to build...`, or `let's work on...`, treat that as initialization intent by default.
- If the current branch is detected as the repository default branch and branch memory does not exist yet, warn about default-branch risks and ask for confirmation before creating the branch spec unless the user explicitly used `--force` or equivalent force/bypass wording.
- Do not implement code.
- If the user asks to modify initializer content, update `01-init.md` in place and keep `Current stage = 1-initializer` unless the user explicitly advances.
- Do not create or populate planning content just because initializer content now looks complete.
- Do not create `02-plan.md`, `03-design.md`, or any later-stage file from an initialization request alone.
- If a user request could be interpreted as asking for initialization plus later stages in the same pass, do only `1-initializer`. Explain that united-we-stand only runs one stage at a time and ask the user to confirm a single later stage separately if they want to move on after initialization.

## Required Output (`01-init.md`)

- Raw idea / problem statement
- Scope (in)
- Scope (out)
- Assumptions
- Open questions
- Success criteria

## Next-Step Status Rules

- Unfinished -> keep `Current stage = 1-initializer`, recommend continuing `1-initializer`.
- Skipped/forced -> move to `Incompleted stages`, set explicit new current stage.
- Completed/not advanced -> keep `Current stage = 1-initializer`, recommend `2-planner`.
