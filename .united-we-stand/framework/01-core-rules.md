# Core Rules

This file is the canonical source for global framework invariants.

## Non-Negotiable Rules

1. **Spec-driven development**
   Branch specs are authoritative working memory for workflow state.

2. **User intent precedence (User is King and Spec is Truth)**
   Latest confirmed user intent has highest authority. When intent changes direction, update relevant specs first, then update code if role allows.

3. **Branch-aware operation**
   All framework work is branch-aware and uses `.spec-driven/<sanitized-current-branch>/`.

4. **Persistent context over chat memory**
   Persisted framework files outrank remembered chat state when conflict exists.

5. **No silent stage jumps**
   Respect prerequisites and anchored stage model. Optional stages may be skipped only with explicit user instruction or `--force` behavior.

6. **No hallucinated completion**
   Missing stage files are not proof of completed work.

7. **Role-scoped edits only**
   Agents may edit only files allowed by role scope and explicit user instruction.

8. **Spec first, then code**
   If user changes intent, update spec context first, then code.

9. **No autonomous git operations**
   Never run `git add`, `git commit`, `git push`, `git rebase`, `git reset`, or branch-switch operations unless user explicitly requests it.

10. **Status-first resumption**
    Resumed chats must consult `00-current-status.md` before deciding the next action.

11. **Initialization requires a fresh live branch check**
    When the user asks to initialize, always perform a fresh live check of the current git branch at that moment. Do not rely on a previous branch check, previous status output, or remembered chat context from earlier in the same chat.

12. **Deterministic routing**
    Natural-language command routing must follow `04-command-routing.md`.

13. **Runtime memory isolation**
    Treat `.united-we-stand/` as installed framework content. Runtime branch memory writes must target `.spec-driven/` only.

14. **Detached HEAD safety**
    Never attach branch memory to `head`. If branch detection is detached/ambiguous, require an explicit branch name before writing branch memory.

15. **Branch-folder collision safety**
    When creating new branch memory, if target folder already exists and is not already linked to the same branch, require explicit user confirmation or a different folder name.

16. **Branch exception routing**
    If a branch uses a non-default memory folder, persist that exception in `.spec-driven/.branch-routing.json` and use it for subsequent branch-folder resolution.

17. **No implicit advancement from edit requests**
    Requests to add, modify, remove, clarify, or fix content inside a stage are amendment requests for that stage unless the user explicitly asks to advance, skip, or bypass.

18. **No downstream stage creation from in-stage amendments**
    Editing one stage must not create, complete, or populate a higher-numbered stage unless the user explicitly requests that higher stage or explicitly advances the workflow.

19. **Branch-scoped work stays in spec by default**
    If a request is branch-scoped and requires persistent work, operate through `.spec-driven/<branch>/` by default. Read and update the relevant spec files first unless the user explicitly says not to, or the request is unrelated, informational only, or does not require repository/spec changes.

20. **Never auto-advance stages**
    Never advance from one stage to the next automatically. A stage may become complete, but it must remain anchored until the user explicitly advances or explicitly confirms a bypass to one specific stage.

21. **Only one framework stage may run at a time**
    Never execute, advance, skip across, or initialize multiple framework stages in the same pass. If a request could reasonably be interpreted as involving two or more stages, explain the one-stage-at-a-time rule and ask the user to confirm one single stage, suggesting the next recommended numbered stage first.

22. **No backward stage regression**
    `Current stage` is a monotonic workflow progress tracker. Earlier-stage work may be amended later, but `Current stage`, `Completed steps`, and `Incompleted stages` must not move backward to an earlier numbered stage.

23. **Backward work must be recorded, not re-anchored**
    If the user requests planning, design, or implementation work after the workflow has already advanced past that stage, perform the requested work, update the relevant earlier stage files in place, and preserve the later `Current stage`. Record the impact in status metadata so downstream stale work is visible.

24. **Stage metadata must match created stage files**
    Workflow metadata is not independent from the branch folder contents. `Current stage` must always match the highest existing numbered stage file among `01-init.md` through `06-finalization.md`, and status checks must validate that alignment.

25. **No implicit framework entry when branch memory is missing**
    If branch memory does not exist yet and the user requests concrete code changes or other persistent work without explicitly asking to initialize the framework, do not silently enter a numbered framework stage and do not interrupt the user to announce missing framework setup. Continue helping with the request normally unless the user explicitly asks to initialize or explicitly brings up the framework.

26. **Framework guidance should be user-invoked when branch memory is missing**
    If branch memory does not exist yet, do not keep re-raising initialization or framework setup on ordinary work. Only surface initialization/framework guidance when the user explicitly asks to initialize, mentions the framework, or references installed framework files or commands.

27. **Finalizer requires explicit closure confirmation**
    `6-finalizer` never treats itself as definitively done on its own. It must surface final observations, ask the user to confirm that the final state is acceptable, and only then close the workflow.

28. **Closed workflow uses `Current stage = none`**
    After explicit user closure confirmation, the branch workflow becomes closed rather than anchored to an active numbered stage. In that closed state, `Current stage = none`, `Next recommended step = none`, and `6-finalizer` is recorded as completed.

29. **Post-closure work reopens finalizer**
    If the workflow was explicitly closed and the user later requests more branch changes, reopen `6-finalizer` as the current stage, clear closed/finalized state, and require finalization approval again after the new work is incorporated.

30. **Default-branch initialization requires confirmation**
    If the current branch is detected as the repository default branch and branch memory does not yet exist, explicit initialization requests must warn about default-branch risks and ask for confirmation before creating `.spec-driven/...` files. Explicit `--force` semantics are the only bypass for that confirmation.

## Stage Mandatory Set

Mandatory framework stages:

- `1-initializer`
- `4-implementer`

Optional framework stages:

- `0-status-checker`
- `2-planner`
- `3-designer`
- `5-code-reviewer`
- `6-finalizer`

## Branch Name Sanitization

Use deterministic branch folder names:

1. lowercase the branch name
2. replace `/` and `\` with `-`
3. replace unsupported characters with `-`
4. collapse repeated `-`
5. trim leading/trailing `-`

Example: `feature/New Checkout UI` -> `feature-new-checkout-ui`

## File Modification Rules

- Framework stages can update their own numbered file and `00-current-status.md` by default.
- Lower-numbered stage files may be updated when needed to reflect confirmed intent or reconcile drift.
- Higher-numbered stage files should not be edited by lower-numbered stages unless user explicitly requests bypass behavior.
- Review-focused stages should report discrepancies before rewriting earlier stage files.
- Finalizer may update wrap-up documentation (for example top-level `README.md`) when explicitly relevant to branch closure.
- Standalone role agents do not update stage files unless explicitly asked.
- A request such as `add this in planning`, `modify init`, or `update design` updates the targeted stage file in place and does not by itself change `Current stage`.
- A direct earlier-stage request issued from a later workflow stage, such as `implement this` during review, performs the requested work without regressing workflow metadata.

## Stage File Update Method

- Prefer updating existing structured sections in place.
- Add amendment/history sections only when preserving decision history is useful.
- Do not duplicate full stage content in the same file unless user explicitly requests log-style duplication.

## Missing Files and Folder Behavior

- If branch folder does not exist yet, do not create it during passive inspection.
- Branch folder under `.spec-driven/` is normally created by `1-initializer`, explicit branch-init action, or an explicit natural-language initialization request from the user.
- If folder exists and stage file is missing, corresponding stage may create it when run.
- If `00-current-status.md` is missing in an existing branch folder, reconstruct conservatively from available stage files and report reconstruction.
- If files are malformed or contradictory, preserve content and repair conservatively.

## Standalone Role Agent Rules

Standalone specialists can run at any time but do not automatically become framework stages.

- They should read `AGENTS.md`, relevant role docs, and branch context when needed.
- By default they do not mutate branch stage files.
- If asked to persist output, they should write only explicitly requested files.

## Build and Test Rule

- If no source or script code changed, do not run build/test unless user asks.
- For code changes, validate proportionately to risk and changed surface.
