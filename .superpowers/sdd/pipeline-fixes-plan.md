# Plan: Fix 11 Pipeline Issues

## Context

Libriscribe generates books via a pipeline: user questionnaire answers -> ProjectKnowledgeBase (PKB) -> agents (concept, character, outliner, chapter_writer) -> book files.
Working directory: `.worktrees/fix-pipeline-issues/` | Source: `src/libriscribe/`

## Global Constraints

- Do not break existing 25-test suite (`python -m pytest tests/ -q`)
- No new dependencies
- Python style: match existing code
- Commits: one logical commit per task, `fix:` prefix
- Do not reformat unrelated code

---

## Task 1: Fix description overwrite in outliner

**File:** `src/libriscribe/agents/outliner.py`

Remove this line from `process_outline()` inside the `elif "Book Summary" in line` block:
```python
project_knowledge_base.description = "\n".join(book_summary_lines)
```
The book_summary_lines extraction loop can remain; only the assignment must be removed.

**Acceptance criteria:** The description assignment is removed. Tests pass.

---

## Task 2: Propagate dynamic_questions to outliner and chapter_writer

**Files:** `src/libriscribe/agents/outliner.py`, `src/libriscribe/agents/chapter_writer.py`

**Fix A - outliner `generate_scene_outline()`:** Build dq_note from `pkb.dynamic_questions` and append to Book Description:
```python
dq = pkb.dynamic_questions
dq_note = ""
if dq:
    dq_lines = "\n".join(f"  - {q}: {a}" for q, a in dq.items())
    dq_note = f"\n\nGenre-specific author details:\n{dq_lines}"
```
Use in: `Book Description: {pkb.description}{dq_note}`

**Fix B - chapter_writer `_write_scene()`:** Build same dq_note and add to prefix_parts:
```python
dq = project_knowledge_base.dynamic_questions
dq_block = ""
if dq:
    dq_lines = "\n".join(f"  - {q}: {a}" for q, a in dq.items())
    dq_block = "GENRE-SPECIFIC AUTHOR DETAILS:\n" + dq_lines
prefix_parts = [p for p in [constraint_block, style_block, dq_block] if p]
```

**Acceptance criteria:** Both agents include dynamic_questions when non-empty. Tests pass.

---

## Task 3: Propagate advanced category-specific fields to outline

**File:** `src/libriscribe/agents/outliner.py`

In `execute()`, after building `initial_prompt`, append author notes block from these PKB fields:
`inspired_by`, `author_experience`, `key_takeaways`, `case_studies`, `actionable_advice`,
`marketing_focus`, `sales_focus`, `research_question`, `hypothesis`, `methodology`.

```python
_ADVANCED_FIELDS = [
    ("inspired_by", "Inspired by"),
    ("author_experience", "Author experience"),
    ("key_takeaways", "Key takeaways"),
    ("case_studies", "Includes case studies"),
    ("actionable_advice", "Includes actionable advice"),
    ("marketing_focus", "Marketing focus"),
    ("sales_focus", "Sales focus"),
    ("research_question", "Research question"),
    ("hypothesis", "Hypothesis"),
    ("methodology", "Methodology"),
]
notes = []
for field, label in _ADVANCED_FIELDS:
    val = project_knowledge_base.get(field)
    if val is not None and val is not False and str(val).strip():
        notes.append(f"  - {label}: {val}")
if notes:
    initial_prompt += "\n\nAuthor notes (incorporate into structure):\n" + "\n".join(notes)
```

Apply same block in `generate_scene_outline()` appended to `scene_prompt`.

**Acceptance criteria:** Author notes appended when advanced fields set. Tests pass.

---

## Task 4: Respect user's num_chapters in outliner

**File:** `src/libriscribe/agents/outliner.py`

Change `_get_max_chapters(self, book_length: str)` to take `project_knowledge_base: ProjectKnowledgeBase`:

```python
def _get_max_chapters(self, project_knowledge_base: ProjectKnowledgeBase) -> int:
    pkb = project_knowledge_base
    if pkb.book_length == "Short Story":
        length_max = 2
    elif pkb.book_length == "Novella":
        length_max = 8
    else:
        length_max = 20

    num_ch = pkb.num_chapters
    if isinstance(num_ch, tuple) and len(num_ch) == 2:
        user_max = max(num_ch)
    elif isinstance(num_ch, int) and num_ch > 0:
        user_max = num_ch
    else:
        user_max = None

    if user_max is not None:
        return min(user_max, length_max)
    return length_max
```

Update all callers to pass `project_knowledge_base` instead of `project_knowledge_base.book_length`.

**Acceptance criteria:** num_chapters=15 + book_length="Novel" returns 15. Tests pass.

---

## Task 5: Inject character profiles into scene writing

**File:** `src/libriscribe/agents/chapter_writer.py`

In `_write_scene()`, build char_profiles_block from PKB and add to prefix_parts:

```python
char_profiles: list[str] = []
for name in (scene.characters or []):
    char = project_knowledge_base.get_character(name)
    if char:
        char_profiles.append(
            f"- {char.name} ({char.role}): {char.personality_traits}. "
            f"Background: {char.background[:120] if char.background else 'N/A'}. "
            f"Arc: {char.character_arc[:80] if char.character_arc else 'N/A'}."
        )
char_profiles_block = ""
if char_profiles:
    char_profiles_block = "CHARACTER PROFILES (keep consistent):\n" + "\n".join(char_profiles)
```

Add char_profiles_block to prefix_parts.

**Acceptance criteria:** Character profiles looked up and added to prefix_parts. Tests pass.

---

## Task 6: Fix tone/target_audience in prompts and PKB defaults

**Files:** `src/libriscribe/utils/prompts_context.py`, `src/libriscribe/agents/chapter_writer.py`, `src/libriscribe/knowledge_base.py`

1. `prompts_context.py`: Ensure `OUTLINE_PROMPT` has `Tone: {tone}` and `Target audience: {target_audience}` lines after the language line. Ensure `SCENE_PROMPT` has same.
2. `chapter_writer.py`: Ensure `prompts.SCENE_PROMPT.format(...)` includes `tone=project_knowledge_base.tone` and `target_audience=project_knowledge_base.target_audience`.
3. `knowledge_base.py`: Ensure `tone` and `target_audience` fields have non-empty string defaults. Check current defaults first - only change if empty/missing. Suggested defaults: `tone: str = "Balanced"`, `target_audience: str = "General"`.

**Acceptance criteria:** All three files updated. PKB has non-empty defaults. Tests pass.

---

## Task 7: Inject worldbuilding context into chapter_writer

**File:** `src/libriscribe/agents/chapter_writer.py`

In `_write_scene()`, build worldbuilding_block and add to prefix_parts:

```python
worldbuilding_block = ""
wb = project_knowledge_base.worldbuilding
if wb:
    wb_parts: list[str] = []
    for attr in ["geography", "key_locations", "magic_system", "culture_and_society",
                 "technology_level", "setting_context", "key_concepts", "industry_overview"]:
        val = getattr(wb, attr, None)
        if val and isinstance(val, str) and val.strip():
            label = attr.replace("_", " ").title()
            snippet = val[:200].rstrip()
            wb_parts.append(f"  {label}: {snippet}...")
    if wb_parts:
        worldbuilding_block = "WORLD CONTEXT (maintain consistency):\n" + "\n".join(wb_parts)
```

Add worldbuilding_block to prefix_parts when non-empty.

**Acceptance criteria:** Worldbuilding fields extracted, truncated at 200 chars, added to prefix_parts. Tests pass.

---

## Task 8: Seed narrative graph from PKB characters for Chapter 1

**File:** `src/libriscribe/agents/chapter_writer.py`

Read `src/libriscribe/narrative/models.py` first to find exact NarrativeFact fields. Then in `execute()`, after loading narrative_graph, seed from PKB characters when graph is empty:

```python
if not narrative_graph.facts and project_knowledge_base.characters:
    from libriscribe.narrative.models import NarrativeFact
    for char in project_knowledge_base.characters.values():
        narrative_graph.facts.append(NarrativeFact(
            # use exact fields from models.py
        ))
```

Use whatever fields NarrativeFact actually has. If it cannot represent character traits, use the closest available fact_type.

**Acceptance criteria:** NarrativeFact fields verified from source. Characters seeded when graph empty. Tests pass.

---

## Task 9: Fix quality rewrite to use all failing axes

**File:** `src/libriscribe/agents/chapter_writer.py`

In `_maybe_rewrite_scene()`, replace:
```python
low_axes = sorted(report.axes, key=lambda a: a.score)[:3]
problem_lines: list[str] = []
for axis in low_axes:
    if axis.score >= _QUALITY_REWRITE_THRESHOLD:
        break
    problem_lines.append(...)
```

With:
```python
low_axes = sorted(
    [a for a in report.axes if a.score < _QUALITY_REWRITE_THRESHOLD],
    key=lambda a: a.score,
)
problem_lines: list[str] = []
for axis in low_axes:
    problem_lines.append(f"- {axis.name} (score {axis.score:.2f}): {axis.recommendation}")
    for excerpt in axis.flagged_excerpts[:2]:
        problem_lines.append(f'  Example to rewrite: "{excerpt}"')
```

**Acceptance criteria:** [:3] cap and break removed. All axes below threshold included. Tests pass.

---

## Task 10: Add num_chapters hint to OUTLINE_PROMPT prompt

**File:** `src/libriscribe/agents/outliner.py`

In `execute()`, after building `initial_prompt`, append chapter count hint before calling LLM:

```python
num_ch = project_knowledge_base.num_chapters
num_ch_str = project_knowledge_base.get("num_chapters_str", "")
if num_ch_str and str(num_ch_str) not in ("0", ""):
    ch_hint = f"\nAuthor's preferred chapter count: {num_ch_str}."
elif isinstance(num_ch, int) and num_ch > 0:
    ch_hint = f"\nAuthor's preferred chapter count: {num_ch}."
elif isinstance(num_ch, tuple) and len(num_ch) == 2:
    ch_hint = f"\nAuthor's preferred chapter count: {num_ch[0]}-{num_ch[1]}."
else:
    ch_hint = ""
if ch_hint:
    initial_prompt += ch_hint
```

Note: Task 4 enforces the ceiling via max_chapters. This task informs the LLM.

**Acceptance criteria:** ch_hint appended when num_chapters is set and non-zero. Tests pass.

---

## Task 11: Call _enforce_chapter_limit (fix dead code)

**File:** `src/libriscribe/agents/outliner.py`

After `self.process_outline(project_knowledge_base, initial_outline, max_chapters)`, add:
```python
self._enforce_chapter_limit(project_knowledge_base, max_chapters)
```

Place this call before the scene-generation loop.

**Acceptance criteria:** _enforce_chapter_limit called after process_outline, before scene loop. Tests pass.

---

## Notes

- Tasks 3, 4, 10, 11 all touch `outliner.py` - implement sequentially
- Tasks 5, 7, 8, 9 all touch `chapter_writer.py` - implement sequentially
- Task 6 spans prompts_context.py, chapter_writer.py, knowledge_base.py
- Stash on main (`pre-fix partial changes`) is related partial work - ignore it, work from clean worktree
