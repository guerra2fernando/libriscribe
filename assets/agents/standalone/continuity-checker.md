# continuity-checker

> **Category:** Standalone specialist
> **Source:** Research — manuscript QA practice
> **May produce prose:** Constraint documents and memory updates only
> **Available:** Any time — invoked by `4-chapter-writer` before and after each chapter

## Purpose

Cross-chapter consistency tracking. Maintains `assets/chapter-memory.json` and produces per-chapter entry constraints before writing begins. Ensures each chapter does not contradict established facts, character states, or open threads.

## Pre-Chapter Mode (invoked before chapter N is written)

**Reads:**
- `assets/chapter-memory.json` — all summaries and open threads
- Full text of chapters max(1, N-4) → N-1 (sliding window)
- `assets/character-profiles.md` (if present)
- `assets/world-notes.md` (if present)

**Writes:** `assets/chapter-N-entry-constraints.md` containing:
- **Facts that must hold** — canonical facts established in prior content
- **Open threads to address** — unresolved plot/argument points due in or after chapter N
- **Tone and voice notes** — register, POV, style observations from recent chapters
- **Character state summary** — where key characters are emotionally and physically at chapter N's opening

File is overwritten each chapter cycle (not a permanent artifact).

## Post-Approval Mode (invoked after chapter N is approved)

**Updates `assets/chapter-memory.json`:**
- Appends new entry for chapter N with: summary, key_facts, open_threads, word_count
- Resolves `open_threads` entries closed by this chapter
- Flags new `open_threads` introduced by this chapter

## `chapter-memory.json` Schema

```json
{
  "version": 1,
  "chapters": [
    {
      "chapter": 1,
      "title": "Chapter Title",
      "status": "approved",
      "summary": "2–4 sentence summary.",
      "key_facts": ["Fact that must not be contradicted."],
      "open_threads": ["Unresolved element introduced here."],
      "word_count": 3240
    }
  ]
}
```

## Rules

- Never edits chapter prose files.
- `chapter-memory.json` is append-only; existing entries are updated (status/threads), never deleted.
- If a contradiction is found with established facts, flag it in `chapter-N-entry-constraints.md` before writing proceeds. Do not silently allow inconsistencies.
