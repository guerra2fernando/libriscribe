# 4 - Implementer

> **Category:** Framework agent (**mandatory**)
> **May change code:** Yes (first framework stage allowed to change code)
> **Updates:** `04-implementation.md`, `00-current-status.md`

## Purpose

Implement branch changes while preserving traceability and quality.

## Canonical References

- Core invariants: `../framework/01-core-rules.md`
- State updates: `../framework/02-state-model.md`
- Conflict policy: `../framework/05-conflict-resolution.md`
- Spec schema: `../framework/06-spec-writing-standard.md`
- Done criteria: `../framework/07-definition-of-done.md`
- Profile selection: `../framework/profiles/00-profile-selection.md`
- Repo coding rules: `../steering/coding-steering.md`

## Prerequisites

- If branch memory does not exist yet, do not treat the request as automatic entry into `4-implementer`. Continue helping with the implementation request normally unless the user explicitly asks to initialize or explicitly asks for framework-stage behavior.
- Step `1-initializer` complete unless explicit bypass/force behavior applies.
- If `2-planner`/`3-designer` are missing, warn and get confirmation before direct implementation.

## Behavior

- Update specs first when user intent changes.
- If branch memory is missing and the user did not ask to initialize, do not mention missing framework setup or create stage metadata from ordinary implementation requests.
- Implement code changes and add/update tests proportionate to risk.
- Apply selected profiles (language + project-type) for coding/testing specifics.
- Treat `../steering/coding-steering.md` as mandatory for every code change.
- Follow repository linting, parser-based analysis, and static-analysis rules during implementation instead of treating them as review-only concerns.
- When repo commands or configured tools exist for linting or parser/static-analysis checks, use them during implementation close and fix straightforward violations in the changed scope before considering the implementation ready for review.
- Add the required file-level/function/block comments from coding steering during implementation instead of leaving them for review cleanup.
- Do not leave large multi-responsibility functions behind when they can be split into smaller helpers during the implementation step.
- If code/spec drift exists, reconcile using canonical conflict policy.
- If the user asks to add or modify implementation notes, update `04-implementation.md` in place.
- Do not create or populate `05-code-review.md` from an implementation amendment alone.
- Keep `Current stage = 4-implementer` unless the user explicitly advances, skips, or bypasses.

## Required Output (`04-implementation.md`)

- What changed
- Why it changed
- Files touched
- Validation and tests executed
- Lint/parser/static-analysis checks executed for the changed scope, or an explicit note when such checks were not available
- Remaining gaps / follow-ups

## Next-Step Status Rules

- Unfinished -> continue `4-implementer`.
- Skipped/forced -> move to `Incompleted stages`, set explicit next stage.
- Completed/not advanced -> keep `Current stage = 4-implementer`, recommend `5-code-reviewer`.
