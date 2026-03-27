# .united-we-stand

This folder is the installed runtime framework for `united-we-stand`.

It is meant for people using the package inside their repositories.

## Install The Package

The primary public package in npm is:

- `@rudinmax87/united-we-stand`

This is the current public npm example for this repository. If you are using a fork or republished variant, replace that scope and package name with your own.

Install it globally from npm:

```bash
npm install -g @rudinmax87/united-we-stand
```

Requirements:

- Node.js 18+
- git

### Alternative: install from GitHub Packages

If you are intentionally installing from GitHub Packages instead, authenticate npm first.

Treat `@mrudinal` below as the current example GitHub Packages scope for this repository. If you install from your own fork or organization, replace it with your own GitHub owner scope.

### 1. Create a GitHub personal access token (classic)

Create a token with at least:

- `read:packages`

If the package is tied to a private repository and your account needs repository access through the token, also include the repository permissions required by your GitHub account setup.

### 2. Authenticate npm to GitHub Packages

Option A: add your token to `~/.npmrc`

```ini
@YOUR_GITHUB_SCOPE:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_PAT_CLASSIC
```

Example for this repository:

```ini
@mrudinal:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_PAT_CLASSIC
```

Option B: log in with npm

```bash
npm login --scope=@YOUR_GITHUB_SCOPE --auth-type=legacy --registry=https://npm.pkg.github.com
```

Example for this repository:

```bash
npm login --scope=@mrudinal --auth-type=legacy --registry=https://npm.pkg.github.com
```

When prompted, use:

- Username: your GitHub username
- Password: your GitHub personal access token (classic)
- Email: your GitHub account email

### 3. Install the package globally from GitHub Packages

```bash
npm install -g @YOUR_GITHUB_SCOPE/united-we-stand
```

Installing this specific package:

```bash
npm install -g @mrudinal/united-we-stand
```

If your scope mapping is not already in `~/.npmrc`, you can also install with the registry flag explicitly:

```bash
npm install -g @YOUR_GITHUB_SCOPE/united-we-stand --registry=https://npm.pkg.github.com
```

Installing this specific package from github:

```bash
npm install -g @mrudinal/united-we-stand --registry=https://npm.pkg.github.com
```

### 4. Verify the CLI is available

```bash
united-we-stand --version
```

## Use It In A Repository

Go to the target repository:

```bash
cd /path/to/your-repository
```

Install the framework files:

```bash
united-we-stand install
```

For resetting the framework back to the defaults and overwrite everything under `.united-we-stand/`:

```bash
united-we-stand install --force
```

Use `install --force` when you want to discard local edits to the installed framework and restore the default framework files shipped by the package. Treat `.united-we-stand/` as resettable package content, not as the place for branch-specific working memory. Branch-specific and request-specific custom rules, decisions, notes, and execution state should live under `.spec-driven/<branch-folder>/` in the files created by `branch-init`.

## What Gets Installed

`united-we-stand install` writes:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.agents/workflows/united-we-stand.md`
- `.cursor/rules/united-we-stand.mdc`
- the installed framework docs and agent files under `.united-we-stand/`

`united-we-stand install --force` resets the installed framework back to the package defaults and overwrites the shipped files under:

- the installed framework docs and agent files under `.united-we-stand/`

Use that when `.united-we-stand/` was edited locally and you want the default framework back.

Branch templates remain package-internal assets used during initialization and normal chat-driven framework usage. They are not meant to be treated as user-edited installed docs.

`united-we-stand branch-init` writes:

- `.spec-driven/<branch-folder>/00-current-status.md`
- `.spec-driven/<branch-folder>/01-init.md`
- `.spec-driven/<branch-folder>/state.json`
- `.spec-driven/.branch-routing.json` when a branch uses a non-default folder mapping

### Use It In Chat First

After `united-we-stand install`, the intended primary interface is the AI chat, not a long CLI workflow.

Typical chat bootstrap examples:

- `initialize this`
- `init the following`
- `let's start this`
- `help me with the following idea, i want...`
- `plan this`
- `design this`
- `implement this`
- `do a code review`
- `wrap this up`
- `what's my status`

How chat usage works:

- if branch memory does not exist yet, explicit initialization prompts should start `1-initializer`
- broad start-of-work prompts should also default to `1-initializer` unless you explicitly ask for a later stage
- if branch memory does not exist yet and you ask for direct code changes without explicitly asking to initialize, the AI should continue helping normally and should not interrupt to explain framework setup
- framework initialization guidance should appear only when you explicitly ask to initialize or explicitly bring up the framework
- when initialization is requested, the AI should always do a fresh live check of the current git branch before creating branch memory
- it should not reuse an earlier branch check, earlier status output, or remembered branch context from the same chat as the initialization target
- if the current branch is the detected default branch, initialization should warn and ask for confirmation before creating branch memory unless you explicitly use `--force`

The workflow is mainly used in chat after installation:

1. `1-initializer`: `AGENTS.md initialize this branch for adding OAuth login`
2. `2-planner`: `plan this feature`
3. `3-designer`: `design the architecture for this change`
4. `4-implementer`: `implement this now`
5. `5-code-reviewer`: `do a code review`
6. `6-finalizer`: `wrap this up`

`0-status-checker` is a routing and validation stage, not a delivery stage. Example: `what's my status`

For the most reliable initialization bootstrap, explicitly reference an installed framework file in the prompt, for example `.united-we-stand/README.md initialize this` or `AGENTS.md init the following`.
In normal chat usage, the AI should create branch memory during initialization, follow the numbered workflow stages, and use standalone agents only when the task calls for specialized help.

After the workflow is initialized, each stage writes or updates its branch file as follows:

| Stage | File name | General description |
|-------|-----------|---------------------|
| `0-status-checker` | `00-current-status.md` | Current branch status, blockers, recommended next step, and routing state |
| `1-initializer` | `01-init.md` | Raw idea, scope, assumptions, open questions, and success criteria |
| `2-planner` | `02-plan.md` | Ordered plan, dependencies, risks, and suggested execution order |
| `3-designer` | `03-design.md` | Architecture, interfaces, boundaries, data flow, and design decisions |
| `4-implementer` | `04-implementation.md` | What changed in code, validation performed, and remaining gaps |
| `5-code-reviewer` | `05-code-review.md` | Quality, maintainability, security, optimization, and review findings |
| `6-finalizer` | `06-finalization.md` | Final summary, uncaptured changes, doc updates, and closure confirmation |

## Runtime Branch Memory

Runtime branch memory is intentionally stored outside this folder at:

- `.spec-driven/<sanitized-branch>/`
- `.spec-driven/.branch-routing.json`
- `.spec-driven/<sanitized-branch>/state.json`

`state.json` is the machine-readable branch record and includes:

- original branch name
- sanitized branch name
- resolved branch memory folder
- current workflow stage
- completed and incompleted stages
- next recommended step
- update metadata

Fresh `branch-init` creates the branch folder, captures the raw idea in `01-init.md`, writes `00-current-status.md` and `state.json`, and leaves the branch in active `1-initializer` mode until initializer content is completed.
It should not pre-create later numbered stage files just from initialization alone.

Keep branch-specific and request-specific working context in `.spec-driven/<branch-folder>/`. The installed `.united-we-stand/` directory should be treated as the default framework layer that can be refreshed or reset back to package defaults.
For branch-scoped work, the AI should operate inside `.spec-driven/<branch-folder>/` by default and update the relevant spec files first unless you explicitly say not to, or the request is unrelated, informational only, or does not require repository/spec changes.

## What To Read First

Normal read order after installation:

1. repository `AGENTS.md`
2. `.united-we-stand/framework/00-index.md`
3. relevant profile docs under `.united-we-stand/framework/profiles/`
4. relevant steering docs under `.united-we-stand/steering/`
5. branch runtime files under `.spec-driven/<branch-folder>/`

## Framework Stage Order

The numbered framework stages are:

0. `0-status-checker`: inspect workflow state, detect gaps, validate consistency, and route the next correct action
1. `1-initializer`: capture the branch intent, scope, assumptions, open questions, and success criteria
2. `2-planner`: turn initialized intent into an ordered execution plan with dependencies and risks
3. `3-designer`: define architecture, interfaces, boundaries, and implementation approach before coding
4. `4-implementer`: make the code changes and record what changed plus how it was validated
5. `5-code-reviewer`: review implementation quality, security, test sufficiency, and remaining issues
6. `6-finalizer`: summarize delivered scope, identify spec/code mismatches or uncaptured changes, ask for explicit user approval, and only then close the workflow with `Current stage = none`

### Proper Order

Normal workflow order:

1. `1-initializer`
2. `2-planner`
3. `3-designer`
4. `4-implementer`
5. `5-code-reviewer`
6. `6-finalizer`

`0-status-checker` is a routing and validation stage, not a delivery stage.

### Mandatory vs Optional

Mandatory framework stages:

- `1-initializer`
- `4-implementer`

Optional framework stages:

- `0-status-checker`
- `2-planner`
- `3-designer`
- `5-code-reviewer`
- `6-finalizer`

### Important Workflow Rules

- a fresh branch starts in active `1-initializer` mode
- the current stage stays anchored until the user explicitly advances or bypasses it
- never auto-advance to the next phase
- adding or modifying content inside a stage does not advance that stage by itself
- never move the workflow backward to an earlier numbered stage once a later stage has been reached
- while workflow is active, `Current stage` should match the highest created numbered stage file in `.spec-driven/<branch-folder>/` among `01-init.md` through `06-finalization.md`; after explicit finalizer approval, closed workflow may use `Current stage = none`
- if you ask to change planning, init, design, review, or finalization content, the AI should update that stage in place without creating the next stage
- if you ask for earlier-stage work after the workflow has already moved forward, the AI should do that work without regressing `Current stage`, `Completed steps`, or `Incompleted stages`; it should record the stale downstream impact in status metadata instead
- if a request could be interpreted as advancing through two or more phases at once, the AI should explain that united-we-stand only runs one stage at a time, suggest the next recommended numbered stage first, and ask the user to confirm one single stage
- for branch-scoped work, the AI should stay inside `.spec-driven/<branch-folder>/` by default and update specs first unless you explicitly say otherwise
- later stage files should be created when those stages are actually started or explicitly amended
- `4-implementer` is the first framework stage allowed to change code
- `6-finalizer` should check for meaningful code/doc changes that were not captured in the specs, ask the user to confirm the final state, and only then close the workflow with `Current stage = none`
- if a closed branch receives new work later, the workflow should reopen `6-finalizer` and require final approval again
- standalone specialist agents are separate from the numbered framework stages

## CLI Commands vs Chat Commands

There are only four CLI commands:

- `united-we-stand install`
- `united-we-stand branch-init "Describe the change"`
- `united-we-stand refresh`
- `united-we-stand doctor`

There are no CLI subcommands for the numbered framework stages such as `united-we-stand planner` or `united-we-stand finalizer`.

The numbered stages are meant to be called from the AI chat, not from the CLI.

## Using Natural Language In Chat

You can talk to the AI very naturally. You do not need rigid command syntax as long as the intent is clear.

Examples:

- `initialize this branch for adding OAuth login`
- `let's start this`
- `help me with the following idea, i want a community tab`
- `i want to build a community section`
- `i want to create an admin login flow`
- `let's work on the admin login flow`
- `plan this feature`
- `design the architecture for this change`
- `implement this now`
- `do a code review`
- `wrap this up`
- `what's my status`
- `continue`
- `next step`

The framework is designed to route short natural requests such as `continue`, `fix it`, `implement this`, `review this`, and `check for gaps` to the nearest safe workflow action.

- If you ask to modify a specific stage, for example `add this in planning` or `update init`, that should be treated as an in-place stage amendment and not as permission to auto-advance to the next stage.
- If you ask for earlier-stage work while the branch is already in a later stage, the AI should perform that work without moving the workflow backward; instead it should mark downstream state as needing refresh in the status metadata.
- The most reliable direct NLP bootstrap for initialization is to reference any installed united-we-stand file together with the init request, for example `AGENTS.md initialize this` or `.united-we-stand/README.md init the following`.
- If branch memory does not exist yet, an explicit request such as `init the following` or `initialize this` should be treated as permission to create the branch spec and start `1-initializer`.
- If branch memory does not exist yet and the current branch is detected as the repository default branch, explicit init requests should still warn and ask for confirmation before creating `.spec-driven/...` unless you explicitly use `--force`.
- If branch memory does not exist yet, broader natural phrases such as `let's start this`, `help me with the following idea, i want...`, `i want to build...`, `i want to create...`, or `let's work on...` should also default to `1-initializer` unless you explicitly ask for a later stage.
- If branch memory does not exist yet and you ask for concrete code changes or other persistent repo work without explicitly asking to initialize the framework, the AI should continue helping with that request normally and should not interrupt to explain framework setup.
- In that situation it should not create `.spec-driven/...` files unless you explicitly ask to initialize or explicitly bring up the framework.

## Framework Stage Chat Routes

Examples for each numbered stage:

- `initialize this` -> `1-initializer`
- `init the following` -> `1-initializer`
- `plan this` -> `2-planner`
- `design this` -> `3-designer`
- `implement this` -> `4-implementer`
- `review this` or `do a code review` -> `5-code-reviewer`
- `finalize this` or `wrap this up` -> `6-finalizer`

These route labels describe which framework behavior handles the request. They do not mean the workflow metadata should move backward if the branch is already in a later stage.

More example prompts:

- `initialize this branch for adding OAuth login`
- `let's start this`
- `help me with the following idea, i want a community tab`
- `i want to build a community section`
- `i want to create an admin login flow`
- `let's work on the admin login flow`
- `plan this feature`
- `design the architecture for this change`
- `implement this now`
- `do a code review`
- `wrap this up`

Related status and progression prompts:

- `what's my status`
- `show my status`
- `check for gaps`
- `continue`
- `next step`
- `do the next step`

Status answers should always state both:

- the current stage
- the recommended next stage

## Direct Chat Routes

Framework-stage routes:

- `what's my status` -> `0-status-checker`
- `show my status` -> `0-status-checker`
- `check for gaps` -> `0-status-checker`
- `initialize this` -> `1-initializer`
- `init the following` -> `1-initializer`
- `let's start this` -> `1-initializer` when branch memory does not exist yet
- `help me with the following idea, i want...` -> `1-initializer` when branch memory does not exist yet
- `i want to build...` -> `1-initializer` when branch memory does not exist yet
- `i want to create...` -> `1-initializer` when branch memory does not exist yet
- `let's work on...` -> `1-initializer` when branch memory does not exist yet
- `plan this` -> `2-planner`
- `design this` -> `3-designer`
- `implement this` -> `4-implementer`
- `review this` -> `5-code-reviewer`
- `do a code review` -> `5-code-reviewer`
- `review quality` -> `5-code-reviewer` with quality scope
- `review security` -> `5-code-reviewer` with security scope
- `security compliance check` -> `5-code-reviewer` with security scope
- `finalize this` -> `6-finalizer`
- `wrap this up` -> `6-finalizer`

These direct route labels select the acting stage behavior. If the workflow is already in a later stage, they must not regress `Current stage`, `Completed steps`, or `Incompleted stages`.

If branch memory does not exist yet and a direct request such as `implement this`, `fix these vulnerabilities`, `upgrade this dependency`, or `refactor this module` would otherwise cause repo changes, the AI should not silently enter that framework stage. It should continue helping with the request normally without announcing missing framework setup unless you explicitly ask to initialize or explicitly bring up the framework.

Standalone specialist routes:

- `debug this` -> `debugger`
- `document this` -> `documentation-writer`
- `manage this project` -> `project-manager`
- `refactor this` -> `refactorer`
- `plan tests for this` -> `test-strategist`
- `check optimization` / `review website optimization` -> `optimizer`
- `check performance` -> `performance-reviewer`
- `check accessibility` -> `accessibility-reviewer`
- `write api contracts` -> `api-contract-writer`
- `model the data` -> `data-modeler`
- `design sql schema` / `create database diagrams` / `modelo entidad relacion` -> `sql-database-designer`
- `plan migration` -> `migration-planner`
- `review observability` -> `observability-reviewer`
- `prepare release` -> `release-coordinator`
- `design the website layout` / `improve the palette` / `make the UI more formal` -> `web-designer`

Standalone route examples:

- `debug this failing branch-init flow`
- `document this install process`
- `refactor this CLI without changing behavior`
- `plan tests for this doctor command`
- `check optimization for this landing page`
- `write api contracts for the new endpoint`
- `design sql schema for the booking tables`
- `create database diagrams for this workflow`
- `make this website more formal`
- `make the landing page more llamativa`
- `prepare release for this package`

## Standalone Agents

Standalone agents can be used at any time when the task needs specialized help. They do not automatically become framework stages.

- `debugger`: investigate failures, isolate likely causes, and propose or implement minimal fixes when asked
- `documentation-writer`: write or improve documentation without automatically changing framework stage files
- `project-manager`: summarize scope, blockers, milestones, dependencies, and coordination needs
- `refactorer`: plan or execute structural improvements while preserving behavior
- `test-strategist`: design proportionate test strategy and identify critical test coverage gaps
- `optimizer`: review website optimization, Lighthouse/PageSpeed risks, startup cost, media delivery, caching, and real-user performance bottlenecks
- `performance-reviewer`: review latency, throughput, memory, and performance hotspots
- `accessibility-reviewer`: review accessibility concerns for UI work, including semantics and navigation
- `api-contract-writer`: define API request/response boundaries, contracts, and field exposure rules
- `data-modeler`: design or review schemas, migrations, and data boundaries
- `sql-database-designer`: design SQL schemas, migration layout, and required database flowcharts, sequence diagrams, entity-relationship models, and relational models
- `migration-planner`: plan safe technical or data migrations, including rollback and compatibility concerns
- `observability-reviewer`: review logging, metrics, tracing, and operational diagnosability
- `release-coordinator`: prepare release-readiness summaries, rollout notes, and follow-up actions
- `web-designer`: define or refine layout direction, palette, contrast, and audience-appropriate visual design for website changes

## Layers

- `framework/`: canonical reusable workflow rules
- `steering/`: repository-specific steering
- `agents/`: numbered framework agents plus standalone specialists
- `playbooks/`: scenario-specific routing guides

## Using The CLI

Initialize branch memory for the branch you are working on:

```bash
united-we-stand branch-init "Describe the change you want to make"
```

If you are on the repository default branch, `branch-init` should warn and ask for confirmation before creating branch memory there. This is meant to reduce long-lived workflow state on `main`/`master`-style branches when a feature branch would be safer.

If you are in detached HEAD, provide the branch name explicitly:

```bash
united-we-stand branch-init --branch feature/my-change "Describe the change you want to make"
```

If branch memory already exists and you intentionally want to reset only that branch memory back to initializer bootstrap files, use:

```bash
united-we-stand branch-init --force "Describe the change you want to make"
```

`branch-init --force` resets `.spec-driven/<branch-folder>/` for that branch only. It does not revert or roll back code changes in your repository.

Check the repository health:

```bash
united-we-stand doctor
```

Check a specific branch explicitly:

```bash
united-we-stand doctor --branch feature/my-change
```

Refresh missing framework files and managed blocks:

```bash
united-we-stand refresh
```

## Typical First-Time Flow

```bash
git checkout -b feature/my-change
united-we-stand install
united-we-stand branch-init "Describe the change you want to make"
united-we-stand doctor
```

Chat-first alternative:

```text
git checkout -b feature/my-change
united-we-stand install
then ask the AI: "initialize this" or "let's start this"
```
