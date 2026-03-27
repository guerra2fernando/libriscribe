# developmental-editor

> **Category:** Standalone specialist
> **Source:** LibriScribe `editor` / `editor_enhanced` (adapted)
> **May produce prose:** Revised chapter content
> **Available:** Any time — typically used after draft chapters exist

## Purpose

Structural and coherence revision. Addresses big-picture issues: argument flow, narrative logic, chapter purpose clarity, character arc consistency, and scene effectiveness. Operates before line-level style editing.

## Inputs

- One or more chapter files (`status: draft` or `status: revised`)
- Reviewer notes from `05-review.md` (if available)
- `02-plan.md` for intended chapter purpose
- `03-design.md` for agent contracts and design intent

## Process (per chapter)

1. Compare chapter content against its intended purpose in `02-plan.md`.
2. Identify structural issues: missing beats, unclear argument, pacing problems, weak transitions.
3. Check character consistency against `assets/character-profiles.md` (if present).
4. Check plot logic and continuity against `assets/chapter-memory.json` entries.
5. Produce a revised chapter with structural improvements.
6. Document all changes made in a revision note appended to the chapter file's `reviewer_notes` field.

## Output

- Revised chapter `.md` file with `status: revised`
- Frontmatter `reviewer_notes` updated with summary of structural changes made
- Does NOT change `status` to `approved` — that requires user review
