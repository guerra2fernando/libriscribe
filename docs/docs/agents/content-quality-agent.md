---
sidebar_position: 16
---

# Content Quality Agent

The Content Quality Agent scores chapter or scene prose across 5 literary quality axes and drives both the preventive style injection (Option A) and the reactive rewrite loop (Option B) inside `ChapterWriterAgent`.

## Overview

Quality scoring uses a structured LLM prompt that returns a JSON object with one entry per axis. Scores range from 0.0 (worst) to 1.0 (best). Reports are saved to `quality_chapter_{N}.json` and are read by the next chapter's writer to inject style hints.

## Quality Axes

| Axis | What it measures | Score 1.0 means |
|------|-----------------|-----------------|
| `cliche_density` | Frequency of AI-obvious or overused phrases | No clichés found |
| `show_dont_tell_ratio` | Direct emotion statements vs. demonstrated through action/dialogue | Everything is shown, not told |
| `dialogue_voice_consistency` | Whether each character's dialogue matches their established voice | All voices consistent |
| `sentence_variety` | Variation in sentence length and structure | High structural variety |
| `scene_function_clarity` | Whether each scene clearly advances plot, character, or theme | All scenes earn their place |

## Report Schema

```json
{
    "chapter_number": 1,
    "overall_score": 0.77,
    "priority_fix": "Replace opening atmospheric sentences with a concrete sensory detail.",
    "axes": [
        {
            "name": "cliche_density",
            "score": 0.50,
            "flagged_excerpts": [
                "The air was thick with tension",
                "he let out a breath he didn't know he was holding"
            ],
            "recommendation": "Replace opening atmospheric sentences with a concrete sensory detail or action."
        }
    ]
}
```

## Option A — Preventive Style Injection

`ChapterWriterAgent._build_style_hints()` reads `quality_chapter_{N-1}.json` before writing chapter N. Axes with score below **0.70** become lines in a `STYLE CONSTRAINTS:` block prepended to every scene prompt. Zero extra LLM calls.

## Option B — Reactive Rewrite Loop

`ContentQualityAgent.score_prose()` accepts raw prose text (no file I/O) and returns a `QualityReport`. `ChapterWriterAgent._maybe_rewrite_scene()` calls this after each scene is generated. If `overall_score < 0.65`:

1. The lowest-scoring axes are extracted.
2. A targeted rewrite prompt is built, listing exact problems and constraining the LLM to preserve all plot facts.
3. One rewrite pass runs (max 2 000 tokens).
4. If the rewrite output is less than half the original length, the original is kept.

Failures at any step fall back to the original scene without aborting chapter writing.

## CLI Usage

```bash
# Analyze prose quality for chapter 1 and print a score bar-chart
libriscribe quality my_project --chapter 1
```

## Python API

```python
from libriscribe.agents.content_quality import ContentQualityAgent

qa = ContentQualityAgent(llm_client)

# Full chapter analysis (reads chapter_{N}.md, saves quality_chapter_{N}.json)
report = qa.execute(project_knowledge_base, chapter_number=1)

# Inline prose scoring (no file I/O — used by Option B rewrite loop)
report = qa.score_prose(prose_text, scene_label="ch1_scene2")
```

## Output Files

| File | Description |
|------|-------------|
| `quality_chapter_{N}.json` | Full quality report for chapter N |

The report is read by `ChapterWriterAgent` when writing chapter N+1 (Option A).
