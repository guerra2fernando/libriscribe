# 6 - Finalizer

> **Category:** Framework agent (optional)
> **May change code:** No (documentation-only updates allowed)
> **Updates:** `06-finalization.md`, `00-current-status.md`

## Purpose

Close branch workflow with final summary, gaps, and documentation updates.

## Canonical References

- Core rules: `../framework/01-core-rules.md`
- State model: `../framework/02-state-model.md`
- Spec schema: `../framework/06-spec-writing-standard.md`
- Done criteria: `../framework/07-definition-of-done.md`

## Prerequisites

- Step `4-implementer` complete unless explicit bypass/force behavior applies.

## Behavior

- Summarize delivered scope and unresolved gaps.
- Compare the recorded specs against the implemented result and identify meaningful changes that are present in code/docs but not yet captured in the branch specs.
- Surface those mismatches or uncaptured changes to the user before treating finalization as clean.
- Ask the user to confirm whether the finalization is acceptable after those observations are presented.
- If the user requests changes, keep finalization open and route the needed follow-up work without silently closing the branch.
- Never consider finalization definitively done by the agent alone.
- Only treat finalization as definitively closed after the user explicitly confirms that the final state is acceptable.
- Update relevant docs (for example README/module docs) when needed.
- Keep closure notes traceable and actionable.
- If the user asks to modify finalization notes, update `06-finalization.md` in place.
- While waiting for user approval, keep `Current stage = 6-finalizer`.
- After explicit user closure confirmation, move `6-finalizer` to completed state, set `Current stage = none`, and mark the workflow closed/finalized.
- If the workflow was already closed and the user later requests more changes, reopen `6-finalizer` as the current stage and require finalization approval again after the new work is reflected.

## Required Output (`06-finalization.md`)

- Final summary
- Delivered scope
- Spec/code mismatches or uncaptured implementation changes
- Known gaps
- Recommended next actions
- Documentation updates performed
- User closure confirmation status

## Next-Step Status Rules

- Unfinished -> continue `6-finalizer`.
- Skipped/forced -> move to `Incompleted stages`, set explicit new current stage per user request.
- Ready for approval -> keep `Current stage = 6-finalizer`, present final observations, and request explicit user confirmation.
- Confirmed/closed -> move `6-finalizer` into completed state, set `Current stage = none`, set `Next recommended step = none`, and treat the workflow as closed until a new user request reopens it.
