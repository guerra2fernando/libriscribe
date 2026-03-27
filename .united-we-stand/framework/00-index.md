# Framework Index

This directory is the canonical framework layer for **united-we-stand**.

## Purpose

Provide reusable, deterministic rules for spec-driven AI development across repositories, languages, and project shapes.

## Reading Order

1. `01-core-rules.md`
2. `02-state-model.md`
3. `03-stage-lifecycle.md`
4. `04-command-routing.md`
5. `05-conflict-resolution.md`
6. `06-spec-writing-standard.md`
7. `07-definition-of-done.md`
8. `08-skip-force-policy.md`
9. `09-traceability-model.md`
10. `10-review-model.md`
11. `11-glossary.md`

Then read:

- selected profile files under `profiles/`
- repo steering docs under `../steering/`
- role contracts under `../agents/`
- branch files under `.spec-driven/<sanitized-current-branch>/`
- branch-routing exceptions in `.spec-driven/.branch-routing.json` when present

## Canonical Ownership Map

- Workflow invariants and permissions: `01-core-rules.md`
- Status field semantics and stage categories: `02-state-model.md`
- Stage progression lifecycle: `03-stage-lifecycle.md`
- NL command routing and ambiguity handling: `04-command-routing.md`
- Spec-vs-code conflict handling and precedence: `05-conflict-resolution.md`
- Stage file schemas and required sections: `06-spec-writing-standard.md`
- Completion criteria: `07-definition-of-done.md`
- Skip/force behavior: `08-skip-force-policy.md`
- Requirement mapping across stages: `09-traceability-model.md`
- Review dimensions, deep checks, and outputs: `10-review-model.md`
- Shared definitions: `11-glossary.md`

## Design Goals

- Preserve durable branch memory.
- Keep `.united-we-stand/` reinstallable and template-only during runtime.
- Keep runtime branch memory isolated under `.spec-driven/`.
- Keep rules deterministic across chats and tools.
- Avoid contradictory duplication.
- Keep language-specific implementation guidance in profiles.
- Keep repo-specific behavior in steering.
