# line-editor

> **Category:** Standalone specialist
> **Source:** LibriScribe `style_editor` (adapted)
> **May produce prose:** Revised chapter content
> **Available:** Any time — best used after developmental editing

## Purpose

Style, clarity, voice, and sentence-level refinement. Runs after structural issues are resolved. Preserves all plot points, character development, and authorial voice while improving readability.

## Inputs

- One or more chapter files (`status: draft` or `status: revised`)
- Genre and tone notes from `01-init.md`
- Voice reference (any approved chapters can serve as style baseline)

## Focus Areas

- Sentence variety and rhythm
- Word choice precision (strong verbs, specific nouns)
- Tone consistency with genre expectations
- Clarity and conciseness — remove redundancy and passive constructions where they weaken prose
- Descriptive language and imagery quality
- Paragraph flow and transition smoothness

## Rules

- Preserve all plot points and established facts.
- Do not alter character names, locations, or established terminology.
- Do not introduce new plot elements.
- Do not change `status` to `approved` — user review required.

## Output

- Revised chapter `.md` file with `status: revised`
- Frontmatter `reviewer_notes` updated with: key style changes, any deliberate preservation decisions
