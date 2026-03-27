<!-- united-we-stand:start -->
## united-we-stand Operating Contract

This repository uses **united-we-stand**, a spec-driven AI workflow framework that persists branch-aware context as markdown files.

### Entry and Read Order

1. Detect current git branch and sanitize branch name.
2. Read `AGENTS.md` first.
3. Read `.united-we-stand/framework/00-index.md` and follow framework reading order.
4. Read `.united-we-stand/framework/profiles/00-profile-selection.md` and apply relevant profiles.
5. Read `.united-we-stand/steering/00-index.md` and relevant steering docs.
6. Read relevant role contracts in `.united-we-stand/agents/` and scenario guides in `.united-we-stand/playbooks/`.
7. Read branch state under `.spec-driven/<sanitized-current-branch>/` if present.
8. If `.spec-driven/.branch-routing.json` exists, use it to resolve branch-to-folder exceptions.
9. Read `.spec-driven/<sanitized-current-branch>/state.json` when present as machine-readable runtime state.

### Core Workflow Rules

- Stages and steps are interchangeable terms.
- Follow staged workflow; do not jump straight to coding.
- `4-implementer` is the first framework stage allowed to change code.
- Keep specs and decisions updated when acting as framework stages.
- Update `00-current-status.md` whenever workflow state changes.
- Keep `Current stage` anchored until user explicitly advances or bypasses.
- Never auto-advance to the next phase. A stage may become complete, but it still stays anchored until the user explicitly advances or explicitly confirms a bypass.
- `6-finalizer` never closes the workflow on its own; it must ask for explicit user confirmation before the branch is considered done.
- Treat requests to add, modify, remove, clarify, or fix content inside a stage as in-place amendments, not as automatic advancement.
- Never move `Current stage` backward to an earlier numbered stage. If earlier-stage work is requested later, do the work, update the earlier stage files, and record the stale downstream impact in status metadata instead of regressing stage state.
- While workflow is active, `Current stage` must match the highest created numbered stage file present in `.spec-driven/<branch>/` among `01-init.md` through `06-finalization.md`; after explicit finalizer approval, closed workflow state may use `Current stage = none`.
- Avoid deadlocks: when user intent is clear (`continue`, `implement`, `fix`, `review`), take the nearest safe action and keep status traceability updated.
- Do not create, populate, or complete a higher-numbered stage just because the user amended the current stage.
- If a request could reasonably mean advancing through two or more phases at once, do not infer permission and do not execute multiple stages. Explain that united-we-stand only runs one stage at a time, suggest the next recommended numbered stage first, and ask the user to confirm one single stage to run now.
- Do not assume missing stage files are completed.
- Do not create branch state folders preemptively; `branch-init` or an explicit user initialization request should create them.
- If branch memory does not exist yet, natural start-of-work requests such as `let's start this`, `help me with this idea`, or `i want to build...` should default to `1-initializer`.
- If branch memory does not exist yet, explicit init requests such as `init the following`, `initialize this`, `let's init this`, `help me with the following idea, i want...`, `let's start building this`, `i want to build...`, `i want to create...`, or `let's work on...` should be treated as permission to create the branch spec and start `1-initializer`.
- When initialization is requested, always perform a fresh live check of the current git branch before creating branch memory.
- Never reuse an earlier branch check, earlier status output, or remembered branch context from the same chat as the initialization target.
- If branch memory does not exist yet and the user asks for concrete code changes or other persistent repo work without explicitly asking to initialize, do not interrupt to explain missing framework setup. Help with the request normally instead of inferring a numbered stage.
- Do not create `.spec-driven/...` files from that request alone. Only surface initialization/framework guidance when the user explicitly asks to initialize or explicitly brings up the framework.
- If branch memory does not exist yet and the current branch is detected as the repository default branch, explicit init requests must warn about default-branch risks and ask for confirmation before creating `.spec-driven/...` files unless the user explicitly uses `--force`.
- The most reliable direct NLP bootstrap is to reference any installed united-we-stand file together with the init request, for example `AGENTS.md initialize this` or `.united-we-stand/README.md init the following`.
- Runtime branch memory is writable under `.spec-driven/` only.
- Treat `.united-we-stand/` as installed framework content (do not use it for runtime branch memory updates).
- When the request is branch-scoped and requires planning, design, implementation, review, or other persistent work, operate inside `.spec-driven/<branch>/` by default.
- For branch-scoped work, read and update the relevant spec files first unless the user explicitly says not to, or the request is unrelated, informational only, or does not require repository/spec changes.
- If branch folder naming uses an exception, persist and read `.spec-driven/.branch-routing.json`.
- Keep `.spec-driven/<branch>/state.json` aligned with `00-current-status.md`.
- After explicit finalizer approval, closed workflow state should use `Current stage = none` and `Next recommended step = none`.
- If a closed branch later receives more work, reopen `6-finalizer` as the current stage and require final approval again after the new work.
- Use the exact `state.json` keys defined by the framework (`branchName`, `sanitizedBranchName`, `branchMemoryFolder`, `currentStage`, `completedSteps`, `incompletedStages`, `nextRecommendedStep`, `lastUpdatedBy`, `lastUpdatedAt`, `initialized`, `finalized`).
- Use persistent files over chat memory when they conflict.

Canonical source of these rules:

- `framework/01-core-rules.md`
- `framework/02-state-model.md`
- `framework/03-stage-lifecycle.md`
- `framework/04-command-routing.md`

### Required Status Fields (`00-current-status.md`)

- `Current branch`
- `Current stage`
- `Completed steps`
- `Incompleted stages`
- `Next recommended step`
- `Status note`
- `Blockers / warnings`
- `Last updated by`
- `Last updated at`

### Framework Stage Agents

- `0-status-checker`
- `1-initializer` (mandatory)
- `2-planner`
- `3-designer`
- `4-implementer` (mandatory)
- `5-code-reviewer`
- `6-finalizer`

### Standalone Role Agents

- `debugger`
- `documentation-writer`
- `project-manager`
- `refactorer`
- `test-strategist`
- `optimizer`
- `performance-reviewer`
- `accessibility-reviewer`
- `api-contract-writer`
- `data-modeler`
- `sql-database-designer`
- `migration-planner`
- `observability-reviewer`
- `release-coordinator`
- `web-designer`

Standalone roles may run anytime but do not automatically become framework stages. They should not update stage files unless explicitly asked.

### Routing Defaults

- Status/progress questions -> `0-status-checker`
- Planning/design requests -> `2-planner` / `3-designer`
- Implementation requests -> `4-implementer`
- Review requests -> `5-code-reviewer`
- Wrap-up requests -> `6-finalizer`
- Specialist requests -> matching standalone role

Canonical routing and ambiguity handling are defined in `.united-we-stand/framework/04-command-routing.md`.

### Conflict and Bypass

- For code/spec conflicts, follow `.united-we-stand/framework/05-conflict-resolution.md`.
- For skip/force behavior, follow `.united-we-stand/framework/08-skip-force-policy.md`.
- For completion/advancement semantics, follow `.united-we-stand/framework/02-state-model.md` and `.united-we-stand/framework/03-stage-lifecycle.md`.

### Modification Safety

- Spec first, then code when user intent changes.
- Preserve user-authored code unless explicit user instruction says otherwise.
- Respect role permissions and stage ownership rules.
- Never run destructive git actions unless explicitly instructed.

### Instruction Placement Map

To keep this entrypoint stable and reusable, detailed rules are intentionally moved to canonical files:

- State categories and next-step logic -> `framework/02-state-model.md`
- Routing modes (`continue`, `next step`, status deep review) -> `framework/04-command-routing.md`
- Spec-vs-code conflict resolution -> `framework/05-conflict-resolution.md`
- Stage file schemas and required sections -> `framework/06-spec-writing-standard.md`
- Completion criteria -> `framework/07-definition-of-done.md`
- Skip/force semantics -> `framework/08-skip-force-policy.md`
- Review depth and dimensions -> `framework/10-review-model.md`
- Language/project coding standards -> `framework/profiles/*.md`

### Directory Map

```text
.united-we-stand/
  framework/   # canonical reusable framework rules
  steering/    # repo-specific product/engineering steering
  agents/      # numbered framework stages + standalone specialists
  playbooks/   # scenario-specific workflow guides
.spec-driven/
  .branch-routing.json  # optional branch-folder exception map
  <sanitized-current-branch>/
    state.json
    00-current-status.md
    01-init.md ... 06-finalization.md
    07-decisions.md ... 13-retrospective.md
    modules/ api/ data/ ux/
```
<!-- united-we-stand:end -->
