# book-producer

This repository is the documentation, source, build, test, and publish workspace for the `book-producer` package.

The runtime framework README that gets installed into target repositories is:

- [`.book-framework/README.md`](./assets/README.md)

`book-producer` is a stage-based book creation framework for AI-assisted writing. It gives AI assistants a structured way to handle book projects — from concept to published manuscript — with persistent book-aware context instead of relying only on chat history.

The framework combines detailed staged instructions, reusable templates, and specialist agents that are invoked based on the task at hand. It is designed to work with Claude, GitHub Copilot, Cursor, Antigravity, and similar AI coding and writing environments.

## What it does

`book-producer` supports a two-step install model:

1. A user installs the package globally on their machine from npm or from a GitHub Packages mirror.
2. The user runs `book-producer install` inside any repository where they want to write a book.

Inside that target repository:

- `.book-framework/` stores the installed framework package assets
- `.spec/<book-slug>/` stores book workflow memory and stage specs
- `<book-slug>/` at repo root stores chapter drafts and the final manuscript

Once installed and initialized, the framework helps an AI assistant understand:

- the current book idea and its slug
- the current workflow stage
- what has already been decided and written
- what file should be updated next
- how to continue work consistently across supported tools and chat sessions

## Why it exists

Most AI writing workflows lose context between chats, tools, and sessions. `book-producer` exists to give AI assistants a predictable, durable workflow model inside the repository itself.

Instead of depending only on temporary chat history, the framework stores book progress and stage outputs in markdown files that travel with the repository. This makes it easier to:

- resume writing later without re-explaining context
- switch between supported AI tools
- keep planning and implementation grounded in written state
- reduce repeated prompting
- keep multi-stage book work organized from concept through manuscript assembly

## The package

The package installs a global CLI named:

- `book-producer`

The built package ships:

- compiled CLI output (`dist/`)
- framework assets (`assets/`)
- `README.md`
- `CHANGELOG.md`
- `VERSIONS.md`
- `TROUBLESHOOTING.md`
- `UPGRADING.md`
- `LICENSE`

## How to install it

Install the public npm package with:

```bash
npm install -g book-producer
```

Then, inside a target repository:

```bash
book-producer install
```

For resetting the framework back to the defaults and overwriting everything under `.book-framework/`:

```bash
book-producer install --force
```

## What files it creates

Running `book-producer install` installs:

- `.book-framework/README.md` — the runtime user guide installed into the repository
- the framework docs and agent files under `.book-framework/`
- editor and agent pointer files:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.github/copilot-instructions.md`
  - `.cursor/rules/book-producer.mdc`
  - `.agents/workflows/book-producer.md`

It also installs the framework agents, including:

- numbered framework agents:
  - `1-book-init`
  - `2-book-planner`
  - `3-book-designer`
  - `4-chapter-writer`
  - `5-book-reviewer`
  - `6-publish-assembler`
- standalone specialist agents:
  - `concept-architect`
  - `book-outliner`
  - `book-blurb-writer`
  - `line-editor`
  - `developmental-editor`
  - `character-world-designer`
  - `chapter-arc-architect`
  - `continuity-checker`
  - `research-fact-integrity`
  - `sensitivity-reader`
  - `book-project-manager`

Running `book-producer init "Book Title"` creates:

- `.spec/<book-slug>/state.json`
- `.spec/<book-slug>/00-current-status.md`
- `.spec/<book-slug>/01-init.md`
- `.spec/<book-slug>/assets/chapter-memory.json`
- `.spec/.branch-mapping.json`
- `<book-slug>/chapters/` at repo root

## Book workflow layout

After `book-producer install` and `book-producer init "My Book"`:

```text
.book-framework/
.spec/
  .branch-mapping.json
  my-book/
    state.json
    00-current-status.md
    01-init.md
    assets/
      chapter-memory.json
my-book/
  chapters/
```

Important:

- `.book-framework/` is the installed framework package inside the user's repository.
- `.spec/<book-slug>/` is where the book specs and workflow memory live.
- `<book-slug>/` at repo root is the actual book output (chapters and final manuscript).

## Stage model

Six numbered stages drive the workflow:

| Stage | Agent | Stage file | What happens |
|-------|-------|------------|--------------|
| 1 | `1-book-init` | `01-init.md` | Capture concept, audience, genre, publishing intent, success criteria |
| 2 | `2-book-planner` | `02-plan.md` | Build execution plan: chapter list, milestones, dependencies |
| 3 | `3-book-designer` | `03-design.md` | Final content design: plot summary, chapter summaries, Mermaid diagrams |
| 4 | `4-chapter-writer` | `04-implementation.md` | Create chapter files under `<book-slug>/chapters/` |
| 5 | `5-book-reviewer` | `05-review.md` | Editorial, grammar, continuity, and quality review *(optional)* |
| 6 | `6-publish-assembler` | `06-finalization.md` | Assemble approved chapters into the final manuscript |

Stage files are created lazily:

- Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`.
- Later numbered stage files are created only when that stage starts after explicit user approval.
- Outside initialization, create at most two numbered stage files in one pass: a missing predecessor for recovery and the current stage file being started.

The workflow is used in chat after installation. The stages are as follows:

1. `1-book-init`: `AGENTS.md initialize this book idea`
2. `2-book-planner`: `plan this book`
3. `3-book-designer`: `design the chapters`
4. `4-chapter-writer`: `write the chapters`
5. `5-book-reviewer`: `review this book`
6. `6-publish-assembler`: `finalize this`

All of those steps are called in the AI chat and do not need to be referenced explicitly after initialization. Simple prompts such as `lets move to the next step`, `next step`, or `do the next step` should move the framework to the next numbered stage.

If a request sounds like it is asking for multiple stages at once, book-producer should explain that it only runs one stage at a time, suggest the next recommended numbered stage first, and ask the user to confirm one single stage to run now.

## What safety and destructive behavior exists

The framework is designed to install into the target repository and update its own managed framework files.

Important behavior to know:

- `book-producer install` writes or updates framework-related files in the repository

- `book-producer install --force` resets the installed framework files under `.book-framework/` back to the package defaults

- `book-producer init --force` is intended to reset the current book spec files under `.spec/<book-slug>/` for that book only; it does not delete chapter files under `<book-slug>/chapters/`

- the install command may update pointer files such as `AGENTS.md` and `.github/copilot-instructions.md` so supported tools are redirected to the installed framework

- `6-publish-assembler` requires explicit user confirmation before any cleanup step; cleanup is irreversible

As with any repository-writing tool, review changes before committing them, especially when using `--force`.

## One simple example flow

A typical workflow looks like this:

1. Install the package globally:

```bash
npm install -g book-producer
```

2. Install the framework inside your repository:

```bash
book-producer install
```

3. Create a new book idea:

```bash
book-producer init "The Last Signal"
```

4. In a new chat in your supported AI tool, initialize the book:

```text
AGENTS.md initialize this book idea. Only do the initialization step.
```

5. Continue through the numbered workflow stages in chat:

```text
plan this book
design the chapters
write the chapters
review this book
finalize this
```

6. At any point, ask for status:

```text
what's my status
```

## Tool compatibility

The framework is designed to work with:

- Claude
- GitHub Copilot
- Cursor
- Antigravity

Tool behavior is intentionally different:

- Claude may use parallel chapter or research packets created with `book-producer orchestrate ... --tool claude`.
- Copilot, Cursor, Antigravity, and other tools must stay sequential.

Orchestration mode is auto-detected at `book-producer init` time: parallel if `ANTHROPIC_API_KEY`, `CLAUDE_*` env vars, or a `.claude/` directory is present; sequential otherwise. It can be overridden with `--mode parallel|sequential`.

## CLI commands

```bash
book-producer install
book-producer init "My Book"
book-producer status [slug]
book-producer list
book-producer use <slug>
book-producer doctor
book-producer refresh
book-producer orchestrate chapters [slug] --tool <tool> --chapters 1,2
book-producer orchestrate research [slug] --tool <tool> --topics "topic one,topic two"
```

## Creating Your Own Package

If you want to generate and publish your own package variant of this framework, follow [PACKAGE-PUBLISHING.md](./PACKAGE-PUBLISHING.md).

## Contents in this repository

### What This Repository Contains

- `src/`
  - CLI entrypoint, commands, and library code
- `assets/`
  - framework markdown assets that are installed into target repositories
- `tests/`
  - unit, integration, and built-CLI smoke coverage
- `scripts/`
  - maintainer scripts, including registry publish artifact preparation
- `docs/`
  - API reference, architecture notes, FAQ, and tooling documentation
- `VERSIONS.md`
  - manual package version history and release notes

Two directories at the root of this source repository are used for managing its own development workflow and are **not** part of the published package:

- `.united-we-stand/` — multi-agent coordination framework used for feature development, reviews, and releases of this repo
- `.spec-driven/` — spec-driven workflow state for the currently active development branch

These directories are excluded from the npm package `files` field and will never appear in a user's project.

## Repository Layout

```text
repo-root/
|-- assets/
|-- bin/
|-- docs/
|-- scripts/
|-- src/
|   |-- cli.ts
|   |-- commands/
|   `-- lib/
|-- tests/
|-- CHANGELOG.md
|-- LICENSE
|-- package.json
|-- README.md
|-- VERSIONS.md
`-- tsconfig.json
```

## Validation

This repository is validated with:

- `npm run build`
- `npm test`
- `npm run lint`
- `npm audit --omit=dev`
- `npm pack --dry-run`
- fresh global install and target-repo smoke tests

## Documentation

- [PACKAGE-PUBLISHING.md](./PACKAGE-PUBLISHING.md)
- [docs/API.md](./docs/API.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/FAQ.md](./docs/FAQ.md)
- [docs/TOOLING.md](./docs/TOOLING.md)

# License

This project is licensed under the **MIT License**.

That means you may use it, copy it, modify it, merge it, publish it, distribute it, sublicense it, and/or sell copies of it, subject only to the conditions of the MIT License itself.

Those MIT conditions are:

1. The copyright notice must be included in copies or substantial portions of the software.
2. The software is provided **as is**, without warranty of any kind.

There are **no additional legal restrictions beyond MIT**.

See the [LICENSE](./LICENSE) file for the full legal text.

### Permissions

| Permission | Allowed |
|---|---|
| Personal use | ✔ |
| Commercial use | ✔ |
| Modification | ✔ |
| Distribution | ✔ |
| Private use | ✔ |
| Sublicensing | ✔ |
| Warranty or liability from the maintainer | ✖ |

**Commercial use is explicitly permitted.** You may use this package and its installed framework files in commercial products, client projects, internal enterprise tools, or any paid service without restriction and without requiring a separate commercial license.

### Community Terms

The following are **community requests and project norms**, not additional legal license conditions.

#### Public Use and Participation

This framework is public and free for anyone to use, evaluate, and deploy. You are actively invited to try it, give feedback, and adapt it to your own workflows.

- **Forks are welcome.** Fork this repository freely for personal use, team use, or to build something new on top of it.
- **Pull requests are welcome.** If you find a bug or want to improve the framework, open a PR. PRs that fix broken behavior are reviewed with priority.
- **Bug fixes take priority over new features.** The stability and correctness of the framework model comes before expanding its scope. A broken workflow rule or incorrect CLI behavior will be addressed before a new agent or stage is added.
- **Feature requests are accepted as issues.** If you have a feature idea, open an issue. There is no guarantee of implementation, but well-reasoned requests are considered.

#### Derived Works and Attribution (requested, not required)

If you publish a framework, package, tool, or product that is substantially based on or inspired by `book-producer`, attribution is appreciated.

Suggested credit information:

| Field | Suggested value |
|---|---|
| Author / maintainer username | `mrudinal` |
| Package name and version | `book-producer@<version you based your work on>` |
| Source repository URL | `https://github.com/mrudinal/book-producer` |

Suggested credit format:

```text
Based on book-producer@<version> by mrudinal
https://github.com/mrudinal/book-producer
```

# Versioning

This project follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`):

- `PATCH` — backwards-compatible bug fixes
- `MINOR` — backwards-compatible new features or agents
- `MAJOR` — breaking changes to the CLI interface, framework file layout, or workflow model

You can safely pin a minor version (e.g., `^0.1.0`) and expect patch updates to be non-breaking within that range.

# No Warranty

This software is provided as-is. The MIT License explicitly disclaims all warranties. Use it in production at your own discretion. Bugs will be addressed but there is no SLA or guaranteed response time.
