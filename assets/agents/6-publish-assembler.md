# 6 — Publish Assembler

> **Stage:** 6 — Publish-Assembly Finalization
> **May produce prose:** No — assembles existing approved chapters only
> **Updates:** `manuscript-<name>-final.md`, `06-finalization.md`
> **Prerequisites:** Stage 4 complete (all chapters approved). Stage 5 (review) is optional but recommended before assembly.

## Purpose

Concatenate chapter files into one final, editable Markdown manuscript file **without modifying chapter content**. Record a finalization summary. On explicit user confirmation, run cleanup.

## Assembly Flow

```
1. Read all chapter files under .spec/<book-idea>/book/chapters/
2. Sort by chapter frontmatter.chapter number
3. Concatenate chapter files exactly as written (copy/paste behavior, no rewriting)
6. Write: .spec/<book-idea>/manuscript-<book-idea-name>-final.md
7. Write finalization summary to 06-finalization.md
8. Log: included chapters and word counts
9. STOP — print summary and AWAIT explicit user confirmation before any cleanup
10. On confirmation: delete any user-specified temporary/reference directories that are not part of the shipped framework
11. Log deleted paths (or "skipped: not found") in 06-finalization.md cleanup section
12. Update state.json: finalized=true, currentStage="none"
```

## Output Format

- Plain Markdown — no custom shortcodes, no embedded HTML
- Amazon KDP copy-paste friendly
- Concatenated chapter files with original content preserved

## Behavior Rules

- Never rewrite, clean, or normalize chapter content during assembly.
- Cleanup (step 10–11) is irreversible. Print the list of affected paths and require `y/n` confirmation.
- If cleanup directories do not exist, log `skipped: not found` — no error.
- After finalization, `currentStage` is set to `"none"` and `finalized` to `true`.

## Required Output (`06-finalization.md`)

- Manuscript file path
- Chapter list: number, title, word count, status
- Total word count
- Cleanup log (paths deleted or skipped)
- Finalization timestamp and explicit user confirmation record
