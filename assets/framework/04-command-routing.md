# Command Routing

## Routing Defaults

| Request type | Routed to |
|---|---|
| Status / progress question | `0-status-checker` behavior (read and report state) |
| Concept shaping | `concept-architect` |
| Outline / chapter planning | `book-outliner` |
| Stage 1 work | `1-book-init` |
| Stage 2 work | `2-book-planner` |
| Stage 3 work | `3-book-designer` |
| Chapter writing | `4-chapter-writer` |
| Review request | `5-book-reviewer` |
| Finalization / assembly | `6-publish-assembler` |
| Editing request | `developmental-editor` or `line-editor` |
| Character / world work | `character-world-designer` |
| Research / fact-check | `research-fact-integrity` |
| Chapter arc planning | `chapter-arc-architect` |
| Continuity check | `continuity-checker` |
| Blurb / listing copy | `book-blurb-writer` |
| Sensitivity review | `sensitivity-reader` |

## Ambiguity Handling

If a request could mean advancing through two or more stages, do not infer permission. Explain that only one stage runs at a time, suggest the next recommended stage, and ask the user to confirm.

## In-Place vs Advancement

Requests to amend, clarify, or fix content in the current stage = **in-place amendment** (update stage file, do not advance).  
Requests explicitly stating "start", "begin", "advance", "next step", or similar = **advancement** (requires previous stage to be complete).

## Standalone Specialists

Standalone agents may be invoked at any time without affecting `Current stage`. They do not update numbered stage files unless explicitly asked.
