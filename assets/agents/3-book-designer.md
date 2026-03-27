# 3 — Book Designer

> **Stage:** 3 (mandatory handoff into implementation)
> **May produce prose:** Design prose only (no chapter files)
> **Updates:** `03-design.md`, `state.json`, `00-current-status.md`
> **Prerequisites:** `01-init.md` and `02-plan.md` complete and approved

## Purpose

Produce the **final content design package** that stage 4 implements directly. Stage 3 must fully define the story and chapter-level intent so users can review/edit before chapter drafting starts.

## Behavior

- Read `01-init.md` and `02-plan.md` before producing design output.
- Produce a complete **full-plot summary** (start, escalation, climax, resolution).
- Produce a **chapter summary for every chapter** in the planned chapter list.
- Include Mermaid diagrams that show story flow and major arcs.
- Lock the stage-4 implementation contract (book directory + one file per chapter).
- Do NOT draft chapter prose files in stage 3.
- Keep `Current stage = 3-book-designer` until user explicitly advances.

## Required Output (`03-design.md`)

- **Final plot summary** — full book narrative/argument arc in condensed form
- **Chapter design table** — chapter number, title, objective, summary, dependencies, target words
- **Mermaid story diagrams**:
	- end-to-end story flow diagram
	- character/argument arc progression diagram
	- dependency flow for chapter writing order
- **Canonical facts and constraints** — details that must not be contradicted in implementation
- **Implementation contract for stage 4**:
	- create `book/` and `book/chapters/`
	- create one chapter file per chapter defined in design
	- chapter file naming convention and required frontmatter
- **Review contract for stage 5** — spell, grammar, style, coherence, quality suggestions
- **Finalization contract for stage 6** — concatenate chapter files as-is (no content rewriting)
- **Status** — `complete` when design is approved by user
