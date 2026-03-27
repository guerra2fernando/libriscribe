# 4 — Chapter Writer

> **Stage:** 4 (mandatory)
> **May produce prose:** Yes — this is the only stage that produces chapter files
> **Updates:** `book/chapters/*.md`, `assets/chapter-memory.json`, `04-implementation.md`
> **Prerequisites:** Stages 1–3 complete and approved (no stage may be skipped)

## Purpose

Implement the final book design from stage 3 by materializing one chapter file per designed chapter in `book/chapters/`, while preserving design intent and continuity.

## Implementation Setup (mandatory)

Before writing chapter text:
- Ensure `book/` directory exists under the book-idea folder.
- Ensure `book/chapters/` directory exists.
- Create one markdown file per chapter defined in `03-design.md`.
- File naming format: `NN-<slug>.md` (e.g., `01-opening-hook.md`).
- Chapter frontmatter title **must** follow the format `"Chapter N: <chapter name>"` so assembly order can be verified visually (e.g., `"Chapter 13: The Final Hour"`). The `chapter:` number field is the primary sort key; the title format is the human-readable confirmation.

## Pre-Write Loop (run before each chapter)

**Step 1 — Continuity check (delegate to `continuity-checker`):**
- Read `assets/chapter-memory.json` (all summaries + open threads)
- Read full text of chapters max(1, N-4) → N-1
- Output: `assets/chapter-N-entry-constraints.md` containing:
  - Facts that must hold in chapter N
  - Open threads that must be addressed or explicitly deferred
  - Tone and voice notes from recent chapters

**Step 2 — Arc planning (delegate to `chapter-arc-architect`):**
- Read `02-plan.md` chapter N description
- Read `assets/chapter-N-entry-constraints.md`
- Output: chapter N beat sheet (appended to `04-implementation.md`)

**Step 3 — Write chapter:**
- Read `assets/chapter-N-entry-constraints.md`
- Read chapter N beat sheet
- Read full text of chapters max(1, N-4) → N-1
- Read `assets/chapter-memory.json` summaries for chapters 1 → N-5
- Write `book/chapters/NN-<slug>.md` (status: draft)

## Post-Approval Update

After the user approves chapter N:
- Delegate to `continuity-checker` to update `assets/chapter-memory.json`:
  - Append summary entry for chapter N
  - Resolve any `open_threads` closed by this chapter
  - Flag any new `open_threads` introduced
- Update chapter frontmatter to `status: approved`

## Implementation Summary (required)

`04-implementation.md` must contain:
- Per-chapter implementation record: design summary vs implemented result
- Chapter file path and final word count
- Deviations from stage-3 design (if any) with reason
- Blockers and quality notes

## Chapter File Format

```markdown
---
chapter: N
title: "Chapter N: Chapter Title"
status: draft
word_count_target: 3000
word_count_actual: 0
assigned_agent: chapter-writer
reviewer_notes: ""
---

# Chapter N: Chapter Title

<!-- prose body -->
```

## Behavior Rules

- Never write two chapters simultaneously to the same file.
- Never overwrite a chapter with `status: approved` without user instruction.
- `04-implementation.md` receives a log entry for each chapter: beat sheet, word count, status changes.
- Keep `Current stage = 4-chapter-writer` until all designed chapter files exist, all chapters are approved, and user advances.
