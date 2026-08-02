---
sidebar_position: 15
---

# Invariant Checker

The Invariant Checker validates upcoming scenes against the narrative graph before writing begins, catching continuity errors before they reach the LLM.

## Overview

Before each scene is generated, `InvariantChecker.check_scene()` queries the narrative graph for active facts about the scene's characters and setting. It detects:

- **Dead characters reappearing** — a character whose `is_alive` fact is `false` appearing as an active participant.
- **Injured characters performing physical actions** — e.g. a character missing a limb picking something up with that limb.
- **Destroyed or inaccessible locations** — scenes set in locations the graph marks as destroyed or sealed.

## Violation Schema

Each violation has:

| Field | Type | Description |
|-------|------|-------------|
| `severity` | `str` | `"hard"` (blocks scene logic) or `"soft"` (advisory) |
| `description` | `str` | Human-readable description of the conflict |
| `entity` | `str` | The entity involved |
| `fact` | `NarrativeFact` | The fact that was violated |

## Constraint Injection

Violations are formatted as a `NARRATIVE CONSTRAINTS:` block and prepended to the scene prompt:

```
NARRATIVE CONSTRAINTS:
- [HARD] Mira's left hand was severed in Chapter 1 — she cannot pick up objects with her left hand.
- [SOFT] The Grand Atheneum vault was sealed after Chapter 1 — confirm accessibility.
```

Hard violations are also logged to the console as `INVARIANT WARNING` so they are visible during chapter writing.

## CLI Usage

```bash
# Check narrative violations for all scenes in chapter 2
libriscribe narrative check my_project --chapter 2
```

## Python API

```python
from libriscribe.narrative.invariant_checker import InvariantChecker
from libriscribe.narrative.models import NarrativeGraph

graph = NarrativeGraph.load(project_dir / "narrative_graph.json")
checker = InvariantChecker(graph)
violations = checker.check_scene(scene, chapter_number, project_knowledge_base)
block = checker.format_violations_for_prompt(violations)
```

## Integration

`InvariantChecker` is called by `ChapterWriterAgent` for every scene before generation. The constraint block is prepended alongside the `STYLE CONSTRAINTS:` block from the Quality Layer (Option A). No extra LLM calls are made.
