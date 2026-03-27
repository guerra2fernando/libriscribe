# Conflict Resolution

## Core Principle

Preserve user intent and user-authored code while keeping specs truthful and traceable.

## Canonical Rules

1. If user gives a new instruction that changes intent:
   - update relevant spec files first
   - then update code if active role allows

2. If code conflicts with spec and user did **not** request code rollback/change:
   - do not silently overwrite user-authored code
   - update spec to match actual implementation
   - clearly inform user of mismatch and reconciliation

3. If user explicitly asks to restore behavior from spec, preserve spec and align code accordingly.

4. If mismatch is risky or ambiguous:
   - warn user before destructive edits
   - choose least destructive action
   - capture decision in relevant stage file(s)

5. Review stages should report discrepancies by default:
   - do not rewrite older stages unless user explicitly requests persistent correction

## Resolution Priority

1. Latest confirmed user intent
2. Actual repository code state
3. Persisted branch specs
4. Historical chat memory

## Required Documentation

Whenever meaningful conflict is resolved:

- document resolution in relevant stage file(s)
- update `00-current-status.md` if state changed
- keep traceability references current