---
sidebar_position: 18
---

# Pacing Agent

The Pacing Agent analyses cross-chapter arc quality across 5 axes and injects actionable guidance into the Editor Agent prompt for the current chapter.

## Overview

After each chapter is written in AI-review mode, the Pacing Agent receives all chapters written so far and scores the manuscript's pacing. Any axis scoring below **0.70** contributes a line to a `PACING GUIDANCE:` block that is prepended to the editor prompt, directing the editor to address cross-chapter arc problems during this editing pass.

## Quality Axes

| Axis | Description | Score 1.0 means |
|------|-------------|-----------------|
| `tension_escalation` | Stakes/tension rise meaningfully from chapter to chapter | Sustained upward arc |
| `act_structure` | Inciting incident (~ch1-2), midpoint (~50%), dark night (~75%), climax (~90%) structurally clear | Clean three-act shape |
| `chapter_length_consistency` | Chapter word-counts are within 30% of each other | Uniform lengths |
| `emotional_beat_variety` | Consecutive chapters vary emotional register (tense, tender, comic, tragic) | No 3+ identical beats in a row |
| `narrative_momentum` | Each chapter ends with a hook or open question | All chapters have forward pull |

## Report Schema

```json
{
    "chapter_numbers": [1, 2, 3],
    "overall_score": 0.72,
    "priority_fix": "Raise stakes at the end of this chapter with an unresolved threat.",
    "axes": [
        {
            "name": "tension_escalation",
            "score": 0.50,
            "chapter_assessments": [
                "Ch1 tension good",
                "Ch3 tension drops after battle resolves cleanly"
            ],
            "recommendation": "Raise stakes at the end of this chapter with an unresolved threat."
        }
    ]
}
```

## Output Files

| File | Description |
|------|-------------|
| `pacing_report.json` | Full report with per-axis scores, chapter assessments, and recommendations |

## Pipeline Placement

```
ChapterWriter → ContentReviewer → NarrativeGraph → NarrativeViolations
  → PacingAgent (analyses all chapters written so far)
  → EditorAgent (receives PACING GUIDANCE block prepended to prompt)
  → StyleEditor
```

PacingAgent only runs in **AI review mode** (`review_preference == "AI"`). Human review mode skips it.

## PACING GUIDANCE Block

When one or more axes score below 0.70, the block below is prepended to the editor's prompt (axes sorted lowest-score-first):

```
PACING GUIDANCE (cross-chapter arc issues to address in this chapter):
- [tension_escalation score=0.50] Raise stakes at the end of this chapter with an unresolved threat.
  Context: Ch1 tension good
  Context: Ch3 tension drops after battle resolves cleanly
- [emotional_beat_variety score=0.60] Follow this grief beat with a moment of unexpected humour or relief.
```

If all axes score >= 0.70, the block is omitted and the editor prompt runs unchanged.

## Threshold

`_PACING_THRESHOLD = 0.70` in `pacing_agent.py`. Axes at or above this value are not reported.

## Error Handling

- No readable chapter files: returns `None`; pipeline continues without pacing guidance.
- LLM response unparseable: logs error, returns `None`; editor runs without pacing guidance.
- `pacing_report.json` write failure: does not abort chapter writing.

## Python API

```python
from libriscribe.agents.pacing_agent import PacingAgent

agent = PacingAgent(llm_client)

# Analyse chapters 1-3 already written
report = agent.execute(project_knowledge_base, chapter_numbers=[1, 2, 3])

if report:
    guidance = PacingAgent.get_editor_guidance(report)
    print(f"Overall pacing: {report.overall_score:.2f}")
    print(f"Priority fix: {report.priority_fix}")
```
