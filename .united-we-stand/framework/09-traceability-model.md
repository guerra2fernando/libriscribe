# Traceability Model

Traceability maps user requirements through the full stage lifecycle.

## Requirement Flow

A requirement should be traceable across:

- `01-init.md`
- `02-plan.md`
- `03-design.md`
- `04-implementation.md`
- `05-code-review.md`
- `06-finalization.md`

## Required Traceability Behavior

- Do not drop user-requested goals silently.
- If requirement changes, update earlier specs first.
- If requirement is deferred/skipped/partial, mark explicitly with rationale.
- Keep implementation and review linked to requirement IDs/labels.

## Canonical Tracking File

Use `08-traceability.md` with columns:

- Requirement ID/label
- Source
- Planned in
- Designed in
- Implemented in
- Reviewed in
- Final status

## Cross-File References

When possible, include direct anchors or headings for faster navigation.
