# 01-init

## Raw idea / problem statement
Perform a full reset of initialization direction and redefine the framework as a Claude-first, multi-agent **book creation framework** that can be installed as an **npm package** in any repository.

Reference sources to follow:
- https://github.com/guerra2fernando/libriscribe for collaborative multi-agent writing baseline.
- https://github.com/mrudinal/united-we-stand-framework for packaging, install/init behavior, staged workflow memory patterns, and command ergonomics.

Required workflow stages (book context):
1. initialize
2. plan
3. design
4. implement
5. review
6. finalize (renamed semantics: **publish-assembly finalization**)

Critical operating constraints:
- User approval is mandatory after each stage before proceeding.
- Execution mode must be tool-aware:
	- Claude: default parallel-capable orchestration.
	- VS Code, Cursor, Codex, and others: default sequential orchestration.
	- Any tool may fall back to sequential when dependency/approval ordering requires it.
- `implement` is where full chapter drafting is executed.
- Finalization assembles all approved chapters into one editable, final manuscript file.
- Framework must stay inactive after install until the user explicitly initializes a book idea.
- Scope model is **book-idea-scoped**, not branch-scoped.

## Inputs
- Existing LibriScribe repository analysis (book-agent domain baseline).
- LibriScribe reference analysis (approval-gated collaborative orchestration model).
- United We Stand reference analysis (CLI/package/template architecture and init lifecycle).

## Constraints
- Keep the current stage anchored to `1-initializer` until explicit user advancement.
- Do not create later stage files (`02`–`06`) during initialization.
- Initialization defines direction and acceptance criteria only; no implementation changes in this step.
- Runtime target is Claude-first workflow operations, not Python CLI runtime.
- Book-idea execution must be independent from active git branch.

## Scope (in)
- Rewrite initializer definition for the new product direction.
- Lock stage semantics for book production lifecycle.
- Define mandatory approval gates between all stages.
- Define parallel-vs-sequential orchestration rule.
- Define npm package direction and required CLI command surface.
- Define minimal required agent set for MVP.
- Define book-idea discovery/reuse behavior for `.spec/<book-idea-name>/` memory.

## Scope (out)
- Writing stage-2 planning backlog in this step.
- Implementing npm package code in this step.
- Migrating all repo files in this step.
- Final stage naming migration in runtime code (captured as future planning work).

## Analysis findings used by this initialization
### From LibriScribe reference (https://github.com/guerra2fernando/libriscribe)
- Strong user approval protocol between major actions.
- Explicit role coordination model where parallel sub-work is integrated back into a controlled approval flow.
- Durable session/state artifacts suitable for long-running multi-step collaboration.

### From United We Stand reference (https://github.com/mrudinal/united-we-stand-framework)
- npm-distributed CLI model (`install`, `branch-init`, `doctor`, `refresh`) with reusable installed templates.
- Durable runtime memory model with machine-readable state companion file.
- One-stage-at-a-time enforcement and deterministic stage transitions.

### Book-idea-scope adaptation decision
- Replace branch-scoped memory with book-idea-scoped memory:
	- `.spec/<book-idea-name>/00-current-status.md`
	- `.spec/<book-idea-name>/01-init.md` ... `06-finalization.md`
	- `.spec/<book-idea-name>/state.json`
- Active branch becomes contextual only; it does not decide workflow identity.
- Installed framework remains dormant until explicit book-idea initialization.

### From current LibriScribe repo
- Mature domain decomposition for book writing (concept, outline, chapter writing, editing, formatting).
- Prompt assets already available and reusable for agent instructions.
- Python runtime is not the target delivery vehicle for this branch direction.

## Target stage definitions (book context)
1. **1-initializer (book-init)**
	- Capture idea, audience, category, constraints, desired output quality, publishing intent.
	- Confirm success criteria and non-goals.
	- Approval required to advance.

2. **2-planner (book-plan)**
	- Build execution plan: milestones, chapter lifecycle, dependencies, risks, and checkpoints.
	- Define where parallel work is allowed.
	- Approval required to advance.

3. **3-designer (book-design)**
	- Define system/workflow design: agent contracts, handoff artifacts, approval interfaces, chapter schema.
	- Specify finalization artifact structure.
	- Approval required to advance.

4. **4-implementer (book-implementation)**
	- Execute actual chapter writing workflow according to approved plan/design.
	- Produce full chapter drafts and tracked revisions.
	- Approval required to advance.

5. **5-code-reviewer (book-review)**
	- Perform structural, quality, consistency, and integrity review of full manuscript flow.
	- Output fixes/priorities before finalization.
	- Approval required to advance.

6. **6-finalizer (publish-assembly finalization)**
	- New semantic label: **publish-assembly finalization**.
	- Assemble all approved chapters into one final manuscript file.
	- Keep output editable by user and ready for Amazon copy/paste workflow.
	- Explicit user closure confirmation required.

## Parallel/sequence orchestration rule
- **Claude default mode**: parallel-capable orchestration for independent tasks.
- **Other tools default mode**: sequential orchestration.
- **Parallel mode**: allowed only for independent chapter drafting, research packs, or per-chapter review tasks.
- **Sequential mode**: required whenever outputs depend on prior approvals (e.g., concept -> outline -> writing).
- Orchestrator agent decides execution mode per step but cannot bypass approval gates.

## Explicit initialization and book-idea matching
- After `install`, framework behavior is passive (no automatic stage execution).
- Workflow starts only when user explicitly initializes a book idea.
- Initialization flow:
	1. Parse/normalize idea into a book-idea name (sanitized slug).
	2. Search existing book-idea specs under `.spec/` for exact or close match.
	3. If a matching book idea exists, ask user:
		 - continue existing book idea, or
		 - create new book-idea spec.
	4. If no match exists, create new book-idea spec folder.
- This matching step is mandatory before writing initialization artifacts.

## Proposed minimal MVP agent set
1. `book-project-manager` (workflow orchestrator + gate controller)
2. `concept-architect` (idea shaping)
3. `book-outliner` (chapter planning)
4. `chapter-writer` (full chapter drafting)
5. `developmental-editor` (structure/coherence revision)
6. `line-editor` (style/clarity refinement)
7. `publish-assembler` (single final manuscript assembly)

Optional specialists:
- `character-world-designer`
- `research-fact-integrity`

## npm package direction (initializer target)
- Build a distributable package (same delivery style as the United We Stand reference framework) installable in any repo.
- Target command surface for MVP:
  - `book-framework install`
	- `book-framework init`
	- `book-framework list`
	- `book-framework use`
  - `book-framework doctor`
  - `book-framework refresh`
- Install should lay down framework docs/agents and book-idea-memory-ready templates.

## Assumptions
- The package will be Node 18+ compatible and CLI-driven.
- Existing prompt assets can be transformed into stage/agent instructions.
- First supported final output is one Markdown manuscript file.
- Book-idea names can be deterministically normalized and reused across branches.

## Open questions
- Final public package name/scope.
- Whether to keep compatibility aliases with existing `united-we-stand` command patterns.
- Whether finalization should rename only stage semantics or also file/command labels.
- Whether Amazon metadata artifacts are in MVP or v2.
- Matching policy for "close match" book-idea detection (exact-only vs similarity threshold).

## Success criteria
- Initialization rewritten to the new product direction and approved by user.
- Stage semantics and approval policy are unambiguous.
- npm-package direction and CLI target are explicitly captured.
- Implementation-stage and finalization-stage expectations are explicitly captured.
- Book-idea-scoped memory model and explicit-init behavior are explicitly captured.
- Tool-specific default orchestration behavior is explicitly captured.

## Status
- `1-initializer` updated with the full new direction.
- Waiting for explicit user instruction to advance to `2-planner`.
