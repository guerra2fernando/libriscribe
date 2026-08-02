---
sidebar_position: 14
---

# Narrative Graph Builder

The Narrative Graph Builder extracts structured narrative facts from written chapters and persists them in a JSON-based narrative graph used by the Invariant Checker and the Quality Layer.

## Overview

After each chapter is written, this agent reads the chapter Markdown file and calls the LLM with a structured JSON prompt to extract narrative facts. Facts describe entities (characters, objects, locations, events), their predicates, and current values. Negated facts (e.g. "is_alive = false") cancel prior contradicting facts when the active fact set is computed.

## Fact Schema

Each extracted fact has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `fact_id` | `str` | SHA-1 hash of entity+predicate+value (first 8 chars) |
| `entity` | `str` | Name of the entity (e.g. "Mira") |
| `entity_type` | `str` | One of: `character`, `object`, `location`, `event` |
| `predicate` | `str` | The property being stated (e.g. "has_left_hand") |
| `value` | `str` | The value of the property (e.g. "false") |
| `chapter` | `int` | Chapter number where this fact was established |
| `evidence_quote` | `str` | Short quote from the chapter supporting this fact |
| `negated` | `bool` | If true, this fact cancels prior facts with the same entity+predicate |

## Deduplication

Before appending new facts, the builder computes SHA-1 IDs for each extracted fact and skips any that already exist in the graph. This makes re-running `extract_from_chapter` idempotent.

## Persistence

Facts are saved to `narrative_graph.json` using Pydantic's `model_dump_json(indent=4)`. If extraction fails partway through (LLM error, JSON parse error), the existing graph on disk is not modified.

## CLI Usage

```bash
# Rebuild the narrative graph from all chapters in a project
libriscribe narrative rebuild --project my_project
```

This iterates all chapters in order and calls `extract_from_chapter` for each one.

## Python API

```python
from libriscribe.narrative.graph_builder import NarrativeGraphBuilder

builder = NarrativeGraphBuilder(llm_client, project_dir, project_knowledge_base)
new_facts = builder.extract_from_chapter(chapter_number=1)
print(f"Extracted {len(new_facts)} new facts")
```

## Output

Facts are persisted in `narrative_graph.json`:

```json
{
    "project_name": "my_project",
    "last_chapter_processed": 2,
    "facts": [
        {
            "fact_id": "a3f8b2c1",
            "entity": "Mira",
            "entity_type": "character",
            "predicate": "has_left_hand",
            "value": "false",
            "chapter": 1,
            "evidence_quote": "her left arm ending abruptly at the elbow",
            "negated": true
        }
    ]
}
```
