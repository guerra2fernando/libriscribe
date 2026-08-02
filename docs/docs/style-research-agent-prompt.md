---
sidebar_position: 99
---

# Implementation Prompt: StyleResearchAgent

> **Purpose:** Hand this document to the next AI engineer (or AI coding agent) as a complete, self-contained specification for implementing `StyleResearchAgent` in the LibriScribe pipeline.

---

## Background

LibriScribe users can set an `inspired_by` field (e.g. `"Cormac McCarthy"`, `"The Road"`, `"Brandon Sanderson's Stormlight Archive"`). Currently this raw string is passed verbatim into LLM prompts and the model is expected to infer style from its training data. This approach has two problems:

1. The model's style knowledge is implicit and inconsistent across providers.
2. There is no deterministic record of *which* style attributes were actually applied.

`StyleResearchAgent` fixes this by running a focused LLM research pass *before* the pipeline starts, extracting concrete, labelled style attributes from the `inspired_by` value, persisting them in the `ProjectKnowledgeBase`, and injecting them as explicit constraints into every downstream agent prompt.

---

## Scope

- **New file:** `src/libriscribe/agents/style_research.py`
- **Modified:** `src/libriscribe/knowledge_base.py` — add `StyleProfile` model and `style_profile` field to PKB
- **Modified:** `src/libriscribe/utils/prompts_context.py` — add `{style_profile_block}` placeholder to `OUTLINE_PROMPT` and `SCENE_PROMPT`; add `format_style_profile_block()` helper
- **Modified:** `src/libriscribe/agents/outliner.py` — pass `style_profile_block` when formatting `OUTLINE_PROMPT`
- **Modified:** `src/libriscribe/agents/chapter_writer.py` — pass `style_profile_block` when formatting `SCENE_PROMPT`; add to `prefix_parts`
- **Modified:** `src/libriscribe/main.py` (or `project_manager.py`) — call `StyleResearchAgent.execute()` once, early, when `pkb.inspired_by` is set and `pkb.style_profile` is empty

Do **not** modify `character_generator.py` or `concept_generator.py` — they already receive the raw `inspired_by` field and that is sufficient for their purposes.

---

## StyleProfile Data Model

Add to `src/libriscribe/knowledge_base.py`, alongside the existing Pydantic models:

```python
class StyleProfile(BaseModel):
    """Extracted style attributes from an inspired_by reference."""

    source: str = ""
    """The raw inspired_by value this profile was derived from."""

    point_of_view: str = ""
    """e.g. 'close third-person', 'first-person unreliable narrator'"""

    sentence_length: str = ""
    """e.g. 'short declarative sentences, rarely exceeding 15 words'"""

    pacing: str = ""
    """e.g. 'slow burn with sudden violent accelerations'"""

    dialogue_style: str = ""
    """e.g. 'sparse, unattributed, subtext-heavy'"""

    prose_tone: str = ""
    """e.g. 'bleak, lyrical, biblical cadence'"""

    structural_patterns: str = ""
    """e.g. 'non-linear timeline, chapter-length vignettes'"""

    thematic_preoccupations: str = ""
    """e.g. 'violence, grace, fate, the American West'"""

    what_to_avoid: str = ""
    """e.g. 'purple prose, extended exposition, comic relief'"""
```

Add to `ProjectKnowledgeBase`:

```python
style_profile: Optional[StyleProfile] = None
```

---

## StyleResearchAgent

Create `src/libriscribe/agents/style_research.py`:

```python
"""StyleResearchAgent: extracts concrete style attributes from an inspired_by reference."""

import json
import logging
import re
from typing import Optional

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import ProjectKnowledgeBase, StyleProfile
from libriscribe.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

_RESEARCH_PROMPT = """\
You are a literary critic and style analyst.

The author of a book project says they want their writing to be inspired by:
  "{inspired_by}"

Extract concrete, actionable style attributes from this reference. If the reference is an author name, base your analysis on their most well-known published work. If it is a specific book title, base your analysis on that book.

Return a JSON object with EXACTLY these keys — no extras, no omissions:

{{
  "point_of_view": "...",
  "sentence_length": "...",
  "pacing": "...",
  "dialogue_style": "...",
  "prose_tone": "...",
  "structural_patterns": "...",
  "thematic_preoccupations": "...",
  "what_to_avoid": "..."
}}

Rules:
- Each value must be a concrete, specific description (1-2 sentences maximum).
- Do NOT write vague answers like "varies" or "depends on the scene".
- Do NOT include JSON keys other than the eight listed above.
- Do NOT include markdown fences or any text outside the JSON object.
"""


class StyleResearchAgent(Agent):
    """Runs once pre-pipeline to extract style attributes from inspired_by."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__("StyleResearchAgent", llm_client)

    def execute(self, project_knowledge_base: ProjectKnowledgeBase) -> None:
        """Populate pkb.style_profile if inspired_by is set and profile not yet built."""
        inspired_by: str = getattr(project_knowledge_base, "inspired_by", "") or ""
        if not inspired_by.strip():
            return

        if project_knowledge_base.style_profile is not None:
            self.logger.info("Style profile already present; skipping research.")
            return

        self.logger.info("Running style research for: %s", inspired_by)
        prompt = _RESEARCH_PROMPT.format(inspired_by=inspired_by)

        try:
            raw = self.llm_client.generate_content(prompt, max_tokens=600)
        except Exception:
            self.logger.exception("Style research LLM call failed; continuing without style profile.")
            return

        profile = self._parse_profile(raw, inspired_by)
        if profile:
            project_knowledge_base.style_profile = profile
            self.logger.info("Style profile populated for: %s", inspired_by)

    def _parse_profile(self, raw: Optional[str], source: str) -> Optional[StyleProfile]:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                self.logger.warning("Could not parse style research JSON; skipping.")
                return None
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                self.logger.warning("Could not parse style research JSON after extraction; skipping.")
                return None

        valid_keys = set(StyleProfile.model_fields) - {"source"}
        return StyleProfile(source=source, **{k: str(v) for k, v in data.items() if k in valid_keys})
```

---

## Prompt Helper

Add to `src/libriscribe/utils/prompts_context.py`:

```python
def format_style_profile_block(style_profile) -> str:
    """Return a STYLE REFERENCE block string, or empty string if profile is None."""
    if style_profile is None:
        return ""
    sp = style_profile
    lines = []
    for label, value in [
        ("Point of view", sp.point_of_view),
        ("Sentence length", sp.sentence_length),
        ("Pacing", sp.pacing),
        ("Dialogue style", sp.dialogue_style),
        ("Prose tone", sp.prose_tone),
        ("Structural patterns", sp.structural_patterns),
        ("Thematic preoccupations", sp.thematic_preoccupations),
        ("Avoid", sp.what_to_avoid),
    ]:
        if value and value.strip():
            lines.append(f"  - {label}: {value}")
    if not lines:
        return ""
    return "STYLE REFERENCE (inspired by: " + sp.source + "):\n" + "\n".join(lines)
```

Add `{style_profile_block}` placeholder to both `OUTLINE_PROMPT` and `SCENE_PROMPT` (after the language/tone block). The value is `""` when absent so no layout change occurs.

---

## Outliner Integration

In `src/libriscribe/agents/outliner.py`, in both `execute()` and `generate_scene_outline()`:

```python
from libriscribe.utils.prompts_context import format_style_profile_block

style_profile_block = format_style_profile_block(project_knowledge_base.style_profile)
# Pass to OUTLINE_PROMPT.format(..., style_profile_block=style_profile_block)
```

---

## Chapter Writer Integration

In `src/libriscribe/agents/chapter_writer.py`, in `_write_scene()`:

```python
from libriscribe.utils.prompts_context import format_style_profile_block

style_profile_block = format_style_profile_block(project_knowledge_base.style_profile)
# Add to prefix_parts alongside constraint_block, style_block, dq_block, etc.
prefix_parts = [p for p in [constraint_block, style_block, style_profile_block, dq_block, char_profiles_block, worldbuilding_block] if p]
```

Also pass to `SCENE_PROMPT.format(..., style_profile_block=style_profile_block)`.

---

## Pipeline Call Point

In the orchestration layer (`src/libriscribe/main.py` or `project_manager.py`), call once before any other agent:

```python
from libriscribe.agents.style_research import StyleResearchAgent

if pkb.inspired_by:
    StyleResearchAgent(llm_client).execute(pkb)
```

This must run **before** `OutlinerAgent.execute()` and **before** `ChapterWriterAgent.execute()`.

---

## Acceptance Criteria

1. When `inspired_by = "Cormac McCarthy"`, `pkb.style_profile` is populated with non-empty values for all eight fields after `StyleResearchAgent.execute()` runs.
2. When `inspired_by` is empty or `None`, `execute()` returns without error and `pkb.style_profile` remains `None`.
3. When `pkb.style_profile` is already set (resumed run), `execute()` is a no-op — no extra LLM call.
4. When the LLM returns malformed JSON, the agent logs a warning, sets no profile, and the pipeline continues normally.
5. The `STYLE REFERENCE` block appears in `OutlinerAgent`'s prompt and in every `ChapterWriterAgent` scene prompt when a profile is present.
6. When `inspired_by` is absent, `style_profile_block` is `""` and no `STYLE REFERENCE` block appears.
7. All existing tests pass (`python -m pytest tests/ -q`). No new dependencies introduced.
8. `StyleProfile` serialises cleanly to/from `project_data.json` via Pydantic's existing save/load path.

---

## Implementation Notes

- `StyleProfile` uses `str` fields with `""` defaults (not `Optional[str]`) so Pydantic serialisation is lossless across resumed runs.
- `max_tokens=600` is intentional — style profiles should be dense, not verbose. Do not increase without justification.
- The JSON self-healing fallback mirrors the pattern already in `LLMClient`; keep it minimal.
- Do not store the raw LLM response. Store only the parsed `StyleProfile`.
- `what_to_avoid` is the most actionable field for the quality rewrite loop. Future work can feed it directly into `ContentQualityAgent._build_style_hints()`.
- **Do not** add style research to any other agent. One agent, one pre-pipeline call, one PKB field. Keep it simple.
