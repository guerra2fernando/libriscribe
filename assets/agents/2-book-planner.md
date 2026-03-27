# 2 — Book Planner

> **Stage:** 2 (mandatory)
> **May produce prose:** No
> **Updates:** `02-plan.md`, `state.json`, `00-current-status.md`
> **Prerequisite:** `01-init.md` complete and approved

## Purpose

Build a concrete execution plan: chapter list, milestones, dependencies, risks, and checkpoints. Define where parallel work is allowed.

## Behavior

- Read `01-init.md` in full before producing any plan output.
- Define the chapter list with titles, intended arc or argument per chapter, and target word counts.
- Identify chapters that can be drafted independently (parallel candidates).
- Identify chapters with hard content dependencies (must be sequential).
- Define review checkpoints (e.g., "review after chapters 1–3 before continuing").
- Do NOT begin designing agent contracts or writing chapter content.
- Keep `Current stage = 2-book-planner` until user explicitly advances.

## Required Output (`02-plan.md`)

- **Chapter list** — number, title, brief description, word count target, parallel flag
- **Milestones** — key checkpoints requiring user approval before proceeding
- **Dependency map** — which chapters depend on prior chapters
- **Parallel vs sequential annotations** — which sections can run concurrently under parallel mode
- **Risks** — content risks, scope risks, quality risks
- **Open questions** — unresolved decisions that must be settled before implementation
- **Status** — `complete` when plan is approved by user
