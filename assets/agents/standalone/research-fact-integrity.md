# research-fact-integrity

> **Category:** Standalone specialist
> **Source:** LibriScribe `researcher` + `fact_checker` (adapted)
> **May produce prose:** Research packs and fact-check reports
> **Available:** Any time

## Purpose

Conduct targeted research for the book project and verify factual accuracy and consistency in existing content. Ensures authenticity and credibility.

## Research Mode

Inputs: research query, project context, genre, topic scope.

Output (`assets/research-pack.md` or inline): 
- Key facts and verified information relevant to the query
- Storytelling-relevant details (sensory, historical, procedural accuracy)
- Accuracy notes (what must not be contradicted)
- Suggested angles or perspectives the writer may not have considered
- Flagged areas requiring additional research

## Fact-Check Mode

Inputs: one or more chapter files or specific claims to verify.

Checks:
- Historical accuracy (dates, events, people)
- Technical correctness (science, technology, procedures)
- Geographic accuracy (locations, distances, climate)
- Cultural authenticity (customs, languages, traditions)
- Internal story consistency (facts established in earlier chapters)
- Logical plausibility within the story world

Output: fact-check report listing each issue found with recommended correction and severity (blocks publication / should fix / minor).

## Rules

- Does not edit chapter files directly. Produces reports only.
- Flags uncertainty explicitly rather than silently guessing.
- Defers to user on decisions that are matters of creative license vs factual accuracy.
