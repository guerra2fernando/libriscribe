---
sidebar_position: 9
---

# Style Research Agent

The Style Research Agent runs a focused LLM research pass **before** outlining begins, extracting concrete, labelled style attributes from the `inspired_by` field and persisting them in the `ProjectKnowledgeBase`.

## Overview

When a user sets `inspired_by` (e.g. `"Cormac McCarthy"`, `"The Road"`, `"Brandon Sanderson's Stormlight Archive"`), this agent converts that raw string into a structured `StyleProfile` — eight specific, actionable style constraints that every downstream agent can act on.

Without this agent, style knowledge is implicit and inconsistent across LLM providers. With it, there is a deterministic record of exactly which style attributes were applied.

## When It Runs

`StyleResearchAgent` is called once by the Project Manager **inside `generate_outline()`**, before the Outliner runs. It is a no-op when:

- `inspired_by` is empty or whitespace
- `pkb.style_profile` is already set (resumed run — no extra LLM call)

## StyleProfile Fields

| Field | Description | Example |
|---|---|---|
| `point_of_view` | Narrative perspective | `"Close third-person limited, single protagonist"` |
| `sentence_length` | Sentence rhythm | `"Short declarative sentences, rarely exceeding 15 words"` |
| `pacing` | Story tempo | `"Slow burn with sudden violent accelerations"` |
| `dialogue_style` | How characters speak | `"Sparse, unattributed, subtext-heavy"` |
| `prose_tone` | Overall voice | `"Bleak, lyrical, biblical cadence"` |
| `structural_patterns` | Chapter/section structure | `"Non-linear timeline, chapter-length vignettes"` |
| `thematic_preoccupations` | Recurring themes | `"Violence, grace, fate, the American West"` |
| `what_to_avoid` | Anti-patterns | `"Purple prose, extended exposition, comic relief"` |

## Pipeline Integration

Once populated, `pkb.style_profile` is injected as a `STYLE REFERENCE` block into:

- **OutlinerAgent** — both the chapter outline prompt and individual scene outline prompts
- **ChapterWriterAgent** — every scene prompt via `SCENE_PROMPT.format(style_profile_block=...)` and the `prefix_parts` prepend block

When `inspired_by` is absent, `style_profile_block` is `""` and no `STYLE REFERENCE` block appears.

## Persistence

`StyleProfile` is a Pydantic model stored as a nested object in `project_data.json`. It survives save/load round-trips via the existing PKB serialisation path — no migration needed.

## Error Handling

- **Malformed JSON:** A regex extraction fallback attempts to find a `{...}` block in the LLM response before giving up.
- **LLM failure:** Logs an exception and continues. The pipeline never stops because of a missing style profile.
- **Partial JSON keys:** Extra keys from the LLM are silently ignored. Missing keys default to `""`.

## Usage

The agent is invoked automatically. No standalone CLI command is needed. To trigger it, set `inspired_by` during **Advanced Mode** setup or in an expert config file:

```yaml
inspired_by: "Cormac McCarthy"
```

## Integration

Works with:
- **Project Manager** — registers and calls `StyleResearchAgent` before outlining
- **Outliner Agent** — receives `STYLE REFERENCE` block in chapter and scene outline prompts
- **Chapter Writer** — receives `STYLE REFERENCE` in every scene prompt and `prefix_parts`
