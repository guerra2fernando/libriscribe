# 5 — Book Reviewer

> **Stage:** 5 (optional — recommended strongly, but the user may choose to advance directly to stage 6)
> **May produce prose:** No — produces review notes only
> **Updates:** `05-review.md`, `state.json`, `00-current-status.md`
> **Prerequisites:** All chapters in `status: approved`

## Purpose

Perform the full quality pass before finalization: spell-check, grammar, clarity, style consistency, continuity, and actionable improvement suggestions.

## Behavior

- Read ALL chapter files in order.
- Read `assets/chapter-memory.json` for cross-chapter consistency verification.
- Read `02-plan.md` to verify that the manuscript matches the approved outline.
- Do NOT edit chapters directly. All issues are documented in `05-review.md` as actionable items.
- If issues are found, present them to the user; allow selective chapter revisions before finalization.
- Keep `Current stage = 5-book-reviewer` until review is approved by user.

## Review Dimensions

1. **Structural** — overall arc, chapter order, pacing, completeness vs outline
2. **Continuity** — character consistency, timeline, established facts, terminology
3. **Editorial** — clarity, coherence, transition quality, argument flow (non-fiction)
4. **Voice** — consistency of tone and register across chapters
5. **Completeness** — all open threads from `chapter-memory.json` addressed or deliberately unresolved
6. **Language Quality** — spelling, grammar, punctuation, repetition, readability
7. **Improvement Suggestions** — high-value suggestions for stronger wording and impact

## Required Output (`05-review.md`)

- **Summary** — overall manuscript quality assessment (1 paragraph)
- **Issues list** — each issue with: chapter reference, dimension, severity (critical / major / minor), description, recommended fix
- **Language corrections** — concrete spelling/grammar fixes by chapter
- **Style suggestions** — optional quality improvements that preserve meaning
- **Strengths** — what works well
- **Resolved items** — updated as issues are addressed
- **Sign-off** — explicit user approval statement before stage 6 begins
