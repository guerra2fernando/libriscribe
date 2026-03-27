# .book-framework

This folder is the installed runtime framework for `book-producer`.

It is intended for people using the package inside their repositories to create books with AI assistance.

## Install The Package

The primary public package on npm is:

- `book-producer`

Install it globally from npm:

```bash
npm install -g book-producer
```

Requirements:

- Node.js 18+
- git

### Alternative: install from GitHub Packages

If you are installing from GitHub Packages instead, authenticate npm first.

Treat `@mrudinal` below as the current example GitHub Packages scope for this repository. If you install from your own fork or organization, replace it with your own GitHub owner scope.

#### 1. Create a GitHub personal access token (classic)

Create a token with at least:

- `read:packages`

If the package is tied to a private repository, also include the repository permissions required by your GitHub account setup.

#### 2. Authenticate npm to GitHub Packages

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

#### 3. Install from GitHub Packages

```bash
npm install -g @mrudinal/book-producer --registry=https://npm.pkg.github.com
```

#### 4. Verify the CLI is available

```bash
book-producer --version
```

## Use It In A Repository

Go to the target repository where you want to write a book:

```bash
cd /path/to/your-repository
```

Install the framework files:

```bash
book-producer install
```

Create a new book idea:

```bash
book-producer init "My Book Title"
```

For resetting the framework back to the defaults and overwriting everything under `.book-framework/`:

```bash
book-producer install --force
```

Use `install --force` when you want to discard local edits to the installed framework and restore the default files shipped by the package. Treat `.book-framework/` as resettable package content, not as the place for book-specific working memory. Book-specific state, stage notes, and chapter drafts should live under `.spec/<book-slug>/` and `<book-slug>/chapters/` respectively.

## What Gets Installed

`book-producer install` writes:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/book-producer.mdc`
- `.agents/workflows/book-producer.md`
- the installed framework docs and agent files under `.book-framework/`

`book-producer install --force` resets the installed framework back to the package defaults and overwrites the shipped files under `.book-framework/`.

`book-producer init "Book Title"` writes:

- `.spec/<book-slug>/state.json`
- `.spec/<book-slug>/00-current-status.md`
- `.spec/<book-slug>/01-init.md`
- `.spec/<book-slug>/assets/chapter-memory.json`
- `.spec/.branch-mapping.json` (created or updated)
- `<book-slug>/chapters/` at repo root (empty directory for chapter files)

Later stage files are created lazily as the workflow advances with explicit user approval.

`book-producer init "Book Title" --force` resets `.spec/<book-slug>/` for that book only. It does not delete chapter files already written under `<book-slug>/chapters/`.

## Use It In Chat First

After `book-producer install` and `book-producer init`, the intended primary interface is the AI chat, not a long CLI workflow.

Typical chat start examples:

- `initialize this book idea`
- `capture the concept for me`
- `let's start this book`
- `i want to write a book about...`
- `plan this book`
- `design the structure`
- `write the chapters`
- `review this book`
- `finalize this`
- `what's my status`

How chat usage works:

- if book spec memory does not exist yet, explicit initialization prompts should start `1-book-init`
- broad start-of-work prompts such as `let's start this`, `i want to write a book about...`, or `let's work on this book` should default to `1-book-init` when no spec exists
- if book spec memory does not exist yet and you ask for direct writing help without mentioning the framework, the AI should help you normally and should not interrupt to explain framework setup
- framework initialization guidance should appear only when you explicitly ask to initialize or explicitly bring up the framework
- when initialization is requested, the AI should read `state.json` and `00-current-status.md` to confirm the book has been created with `book-producer init` before proceeding
- if no book spec exists yet and the user asks to initialize without having run `book-producer init`, the AI should prompt them to run `book-producer init "Book Title"` first

For the most reliable initialization bootstrap, explicitly reference an installed framework file in the prompt, for example `AGENTS.md initialize this book idea` or `.book-framework/CHAT-WORKFLOW.md let's start capturing the concept`. Also indicate that only the initialization step should run now.

In normal chat usage, the AI should read `state.json` and `00-current-status.md` before acting, follow the numbered workflow stages, and use standalone agents only when the task calls for specialized help.

## Stage Workflow

The numbered framework stages drive the book from idea to published manuscript:

| Stage | Agent | Stage file | What happens |
|-------|-------|------------|--------------|
| 1 | `1-book-init` | `01-init.md` | Capture concept, audience, genre, publishing intent, success criteria |
| 2 | `2-book-planner` | `02-plan.md` | Build execution plan: chapter list, milestones, dependencies |
| 3 | `3-book-designer` | `03-design.md` | Final content design: plot summary, chapter summaries, Mermaid diagrams |
| 4 | `4-chapter-writer` | `04-implementation.md` | Create chapter files under `<book-slug>/chapters/` |
| 5 | `5-book-reviewer` | `05-review.md` | Editorial, grammar, continuity, and quality review pass *(optional)* |
| 6 | `6-publish-assembler` | `06-finalization.md` | Assemble approved chapters into the final manuscript |

`00-current-status.md` is created at initialization and updated throughout the workflow to reflect the current stage, completed steps, blockers, and the next recommended action.

**User approval is mandatory after every stage. No auto-advancement.**

### Mandatory vs Optional

Mandatory stages:

- `1-book-init`
- `2-book-planner`
- `3-book-designer`
- `4-chapter-writer`
- `6-publish-assembler`

Optional stages:

- `5-book-reviewer` — the user may advance directly from stage 4 to stage 6; if skipped, it is noted in `00-current-status.md` and recorded in `incompletedStages`

### Proper Order

Normal workflow order:

1. `1-book-init`
2. `2-book-planner`
3. `3-book-designer`
4. `4-chapter-writer`
5. `5-book-reviewer` *(optional)*
6. `6-publish-assembler`

### Important Workflow Rules

- a fresh book idea starts in active `1-book-init` mode
- the current stage stays anchored until the user explicitly advances
- never auto-advance to the next stage
- adding or modifying content inside a stage does not advance that stage by itself
- never move the workflow backward to an earlier numbered stage once a later stage has been reached
- `Current stage` should match the highest created numbered stage file in `.spec/<book-slug>/` among `01-init.md` through `06-finalization.md`; after explicit finalization approval, the workflow closes
- if you ask to modify planning, init, design, or review content, the AI should update that stage in place without creating the next stage file
- if you ask for earlier-stage work after the workflow has already moved forward, the AI should do that work without regressing `Current stage`, `Completed steps`, or `Incompleted stages`; it should record the stale downstream impact in status metadata instead
- if a request could be interpreted as advancing through two or more stages at once, the AI should explain that book-producer runs one stage at a time, suggest the next recommended stage first, and ask the user to confirm one single stage to run now
- stage files are created lazily; outside initialization, at most two numbered stage files may be created in one pass — a missing predecessor for recovery and the current stage being started now
- only `4-chapter-writer` may produce chapter prose files under `<book-slug>/chapters/`
- only `6-publish-assembler` may assemble the final manuscript and run cleanup
- `6-publish-assembler` requires explicit user confirmation before any cleanup; cleanup is irreversible

## Standalone Specialists

Standalone agents can be used at any appropriate point in the workflow. They do not advance the numbered framework stages.

### Available at any time (before or after init)

- `concept-architect`: shape a raw idea into a compelling concept — logline, core premise, unique angle, suggested titles, genre, and open questions; takes free text as input, no spec required
- `book-outliner`: produce a detailed chapter-by-chapter outline with scene breakdowns, dependency annotations, and parallel-safe chapter flags; useful before or during stage 2
- `book-blurb-writer`: write back-cover and Amazon listing copy — hook, setup, stakes, call to action, keyword list, and category recommendations

### Available after init (stage 1 and later)

- `line-editor`: sentence-level style refinement — sentence variety, word choice, tone consistency, clarity, descriptive language, and paragraph flow; preserves all plot points and authorial voice
- `sensitivity-reader`: review content for cultural accuracy, representation blind spots, stereotyping, harmful language, and exploitative framing; outputs a flagged review report with severity levels and suggestions
- `research-fact-integrity`: conduct topic research or verify historical, technical, geographic, and cultural accuracy in existing chapters; outputs reports only, does not edit prose

### Available after chapters exist (stage 4 and later)

- `developmental-editor`: structural and coherence revision — argument flow, narrative logic, chapter purpose clarity, character arc consistency, and scene effectiveness; compares content against `02-plan.md` and `03-design.md`
- `continuity-checker`: maintain cross-chapter consistency — produces entry constraints before each chapter write and updates `chapter-memory.json` after chapter approval; never edits chapter prose directly
- `chapter-arc-architect`: plan the narrative or argumentative arc for a specific chapter before writing — beat sheet covering opening, inciting event, complications, crisis, climax, and resolution

### Available during active workflow (after init)

- `character-world-designer`: create and maintain character profiles (`assets/character-profiles.md`) and world-building notes (`assets/world-notes.md`) to keep the book universe consistent across chapters
- `book-project-manager`: workflow orchestration — monitor state across book ideas, coordinate parallel chapter writes (Claude only), surface gate-pending states, escalate spec conflicts, and maintain the chapter assignment log in `04-implementation.md`

## CLI Commands vs Chat Commands

There are only a small number of CLI commands:

```bash
book-producer install                                                            # install framework into repo
book-producer install --force                                                    # reset framework files to package defaults
book-producer init "Book Title"                                                  # create a new book idea
book-producer init "Book Title" --force                                          # reset existing book spec
book-producer status [slug]                                                      # show current stage and progress
book-producer list                                                               # list all book ideas in this repo
book-producer use <slug>                                                         # set active book context
book-producer doctor                                                             # validate framework health
book-producer refresh                                                            # re-apply managed framework files
book-producer orchestrate chapters [slug] --tool <tool> --chapters 1,2          # chapter work packets
book-producer orchestrate research [slug] --tool <tool> --topics "topic"        # research packets
```

The numbered framework stages are called from the AI chat, not from the CLI. There are no CLI subcommands for stages such as `book-producer planner` or `book-producer reviewer`.

## Using Natural Language In Chat

You can talk to the AI very naturally. You do not need rigid command syntax as long as the intent is clear.

Examples:

- `initialize this book idea`
- `let's start this book`
- `i want to write a book about cosmic detectives`
- `capture the concept`
- `plan this book`
- `design the chapters`
- `start writing`
- `write the next chapter`
- `review this book`
- `finalize this`
- `assemble the manuscript`
- `what's my status`
- `where are we`
- `next step`
- `continue`

The framework routes short natural prompts such as `continue`, `next step`, `review this`, and `what's my status` to the nearest safe workflow action based on the current stage in `state.json`.

- If you ask to modify a specific stage — for example `update the plan` or `add this to the design` — that is treated as an in-place stage amendment, not permission to advance to the next stage
- If you ask for earlier-stage work while already in a later stage, the AI should perform that work without moving the workflow backward; instead it should mark downstream state as needing refresh in the status metadata
- If no spec exists and you ask for writing help without mentioning the framework, the AI should continue helping normally and should not announce missing setup

## Framework Stage Chat Routes

| Natural language | Routes to |
|---|---|
| `initialize this book idea` | `1-book-init` |
| `let's start this book` | `1-book-init` when no spec exists |
| `capture the concept` | `1-book-init` |
| `i want to write a book about...` | `1-book-init` when no spec exists |
| `plan this book` | `2-book-planner` |
| `build the execution plan` | `2-book-planner` |
| `design this book` | `3-book-designer` |
| `design the chapters` | `3-book-designer` |
| `write the chapters` | `4-chapter-writer` |
| `start writing` | `4-chapter-writer` |
| `write chapter N` | `4-chapter-writer` |
| `review this book` | `5-book-reviewer` |
| `do an editorial review` | `5-book-reviewer` |
| `finalize this` | `6-publish-assembler` |
| `assemble the manuscript` | `6-publish-assembler` |
| `wrap this up` | `6-publish-assembler` |

These route labels select the acting stage behavior. If the workflow is already in a later stage, they must not regress `Current stage`, `Completed steps`, or `Incompleted stages`.

## Status Chat Routes

| Natural language | Action |
|---|---|
| `what's my status` | Read `state.json` and `00-current-status.md`, report current stage and next recommended step |
| `where are we` | Same |
| `show me the current status` | Same |
| `what stage are we on` | Same |
| `check for gaps` | Read status files and identify missing or incomplete stage content |
| `next step` | Report the recommended next step from `00-current-status.md` |

Status answers should always state both the current stage and the recommended next step.

## Standalone Agent Chat Routes

| Natural language | Routes to |
|---|---|
| `develop a concept for...` | `concept-architect` |
| `help me shape this idea` | `concept-architect` |
| `outline this book` | `book-outliner` |
| `create a chapter outline` | `book-outliner` |
| `write a blurb` | `book-blurb-writer` |
| `write the back cover copy` | `book-blurb-writer` |
| `edit this chapter for style` | `line-editor` |
| `clean up the prose` | `line-editor` |
| `edit this for structure` | `developmental-editor` |
| `check narrative structure` | `developmental-editor` |
| `check continuity` | `continuity-checker` |
| `check for contradictions` | `continuity-checker` |
| `research [topic]` | `research-fact-integrity` |
| `check the facts in this chapter` | `research-fact-integrity` |
| `review for sensitivity` | `sensitivity-reader` |
| `check representation` | `sensitivity-reader` |
| `design the characters` | `character-world-designer` |
| `build the world` | `character-world-designer` |
| `plan the arc for chapter N` | `chapter-arc-architect` |
| `manage this project` | `book-project-manager` |

## Runtime Spec Memory

Runtime book memory is stored outside this folder at:

- `.spec/<book-slug>/`
- `.spec/.branch-mapping.json`
- `.spec/<book-slug>/state.json`

`state.json` is the machine-readable book record and includes:

- book idea name and sanitized slug
- resolved book memory folder and content directory
- current workflow stage
- completed and incompleted stages
- next recommended step
- orchestration mode (`parallel` or `sequential`)
- chapter count and finalization status
- update metadata

Fresh `book-producer init` creates the book folder, writes `00-current-status.md`, `01-init.md`, and `state.json`, and leaves the book in active `1-book-init` mode until stage 1 content is completed. It does not pre-create later numbered stage files from initialization alone.

Keep book-specific and chapter-specific working context in `.spec/<book-slug>/`. The installed `.book-framework/` directory should be treated as the default framework layer that can be refreshed or reset to package defaults at any time.

## What To Read First

Normal read order after installation and init:

1. Repository `AGENTS.md`
2. `.book-framework/framework/01-core-rules.md`
3. `.book-framework/framework/09-orchestration-policy.md` and the matching file under `.book-framework/tooling/` for the active tool
4. `.spec/<book-slug>/state.json` and `00-current-status.md`
5. The current stage agent file under `.book-framework/agents/`
6. For specialist work, the relevant standalone agent under `.book-framework/agents/standalone/`

## Layers

- `framework/`: canonical reusable workflow rules, state model, stage lifecycle, command routing, and orchestration policy
- `agents/`: numbered framework stage agents plus standalone specialists
- `templates/`: stamped spec files used during `book-producer init` and stage advancement
- `tooling/`: tool-specific adapter guidance for Claude, Copilot, Cursor, and Antigravity

## Typical First-Time Flow

```bash
git checkout -b my-new-book      # optional: work on a dedicated branch
book-producer install
book-producer init "My Book Title"
book-producer doctor
```

Then open your AI tool and start in chat:

```text
AGENTS.md initialize this book idea. Only do the initialization step.
```

Continue through the stages in chat:

```text
plan this book
design the chapters
write the chapters
review this book
finalize this
```

At any point, ask for status:

```text
what's my status
```
