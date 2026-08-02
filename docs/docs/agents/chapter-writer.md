---
sidebar_position: 6
---

# Chapter Writer Agent

The Chapter Writer Agent generates the first draft of each chapter scene by scene, with automatic narrative constraint injection and an inline prose quality loop.

## Overview

This agent transforms the outline into fully-written chapters. For each scene it:

1. Checks narrative invariants (dead characters, injured limbs, destroyed locations) and prepends any violations as hard constraints in the prompt.
2. Injects style hints from the prior chapter's quality report to prevent recurring clichés and tell-not-show patterns.
3. Generates the scene prose via the configured LLM.
4. Scores the generated prose across 5 quality axes; if the overall score is below 0.65, fires one targeted rewrite pass preserving all plot facts.
5. After all scenes are written, triggers `NarrativeGraphBuilder` to extract and persist new narrative facts.

## Quality Pipeline

### Option A — Preventive Style Injection

Before writing chapter N, the agent reads `quality_chapter_{N-1}.json`. Any quality axis scoring below **0.70** contributes a line to a `STYLE CONSTRAINTS:` block that is prepended to every scene prompt in the chapter. This costs zero extra LLM calls.

Example injected block:
```
STYLE CONSTRAINTS (patterns to avoid from prior chapter quality analysis):
- [cliche_density] Replace opening atmospheric sentences with a concrete sensory detail or action.
  Avoid phrases like: "The air was thick with tension"
  Avoid phrases like: "he let out a breath he didn't know he was holding"
```

### Option B — Reactive Rewrite Loop

After each scene is generated, `ContentQualityAgent.score_prose()` evaluates it. If `overall_score < 0.65`:

- The lowest-scoring axes are collected.
- A rewrite prompt is built listing only the specific problems to fix, with strict instructions to preserve all character names, locations, events, and injuries.
- One rewrite pass fires against the LLM (max 2 000 tokens).
- If the rewrite fails or returns output shorter than half the original, the original scene is kept without error.

The threshold is configurable via `_QUALITY_REWRITE_THRESHOLD` in `chapter_writer.py` (default `0.65`).

## Narrative Graph Update

After all scenes in the chapter are written, the agent calls `NarrativeGraphBuilder.extract_from_chapter()`. Failure is caught and logged; existing facts in `narrative_graph.json` are never lost.

## Input Requirements

1. Chapter outline (scenes, characters, setting, goal, emotional beat)
2. Character profiles from the knowledge base
3. Worldbuilding information
4. Project metadata (title, genre, language)
5. `narrative_graph.json` (auto-created if missing)
6. `quality_chapter_{N-1}.json` (used for Option A; silently skipped if missing)

## Output Files

| File | Description |
|------|-------------|
| `chapter_{N}.md` | Written chapter in Markdown |
| `narrative_graph.json` | Updated with facts extracted from this chapter |

## CLI Usage

The chapter writer is invoked automatically during guided setup. It can also be triggered directly:

```bash
libriscribe write --chapter-number 1
```

## Error Handling

- Missing chapter in knowledge base: a default chapter is created and logged.
- Empty LLM response for a scene: placeholder text is inserted; chapter writing continues.
- Narrative graph update failure: existing graph is preserved; chapter writing is not aborted.
- Quality scoring or rewrite failure: original scene content is kept; chapter writing continues.

## Output Format

```markdown
## Chapter 1: Chapter Title

**Scene 1: Scene summary...**

[Scene prose...]

**Scene 2: Scene summary...**

[Scene prose...]
```
