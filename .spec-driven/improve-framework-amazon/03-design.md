# 03-design

## Architecture / Approach

The `book-framework` npm package installs a Claude-first, multi-agent book creation framework into any repository. It is **book-idea-scoped** and **chat-first**: workflow memory is organized around a named book project (the book idea), not the active git branch, and execution happens conversationally within Claude or similar agent-enabled tools.

**Execution model:**
- `book-framework install` → sets up `.book-framework/` assets (terminal action, one-time)
- `book-framework init [name]` → creates spec memory + book content directories (CLI optional; can also be done in chat)
- **All subsequent work** (stages 1–6) → happens in chat; agent reads/writes spec and book files directly; no additional CLI commands needed

The package mirrors the architecture of https://github.com/mrudinal/united-we-stand-framework (installed template assets + machine-readable state + durable file structure) while adding full chat-native workflow execution.

**Root directory layout:**
```
my-repo/
  .book-framework/          ← installed assets (agent must NOT edit these)
  .spec/                    ← spec workflow memory ONLY
    .branch-mapping.json    ← branch-to-book-idea registry
    <book-slug>/            ← spec memory for this book
      state.json
      00-current-status.md
      01-init.md … 06-finalization.md
      assets/
        chapter-memory.json
  <book-slug>/              ← actual book content (at repo root, not inside .spec)
    chapters/               ← one .md file per chapter
    manuscript-<slug>-final.md
```

The split between `.spec/<slug>/` (workflow memory) and `<slug>/` (book content) is intentional:
- Spec files are framework-managed and drive stage progression.
- Book content files are author-owned and never overwritten by the framework.

---

## Key Components

### 1. CLI Binary (`book-framework`) — Optional after Install

Entry point: `bin/book-framework.js` → `src/cli.ts`

**Required (terminal only):**

| Command | Description |
|---|---|
| `book-framework install` | Copy framework assets into the target repo (passive, one-time) |

**Optional (can be done in CLI or chat):**

| Command | Description |
|---|---|
| `book-framework init [name]` | Create or resume a named book idea (can also be done inline in chat) |
| `book-framework status [slug]` | Show current stage, progress, and active branches for a book idea |
| `book-framework list` | List all book ideas detected under `.spec/` |
| `book-framework use <name>` | Switch active book idea context (not needed; chat maintains full context) |
| `book-framework doctor` | Validate installed assets vs package version (optional maintenance) |
| `book-framework refresh` | Re-apply managed templates to installed assets (optional maintenance) |

**Primary workflow: after install, all work happens in chat.** The agent reads `.spec/<book-idea>/` files directly and writes stage outputs. CLI commands are provided as convenience shortcuts for terminal-first users.

`--force` flag availability (CLI only; not applicable in chat workflow):

| Command | `--force` behavior |
|---|---|
| `install --force` | Reset all installed assets to package defaults (overwrites user edits) |
| `init --force` | Reset bootstrap files for the selected book idea (preserves chapter artifacts) |
| `refresh --force` | Re-apply managed templates even when existing content is newer |

Force never bypasses mandatory approval gates. Every destructive force action must print a warning and require explicit acknowledgment (interactive prompt or `--yes` flag for CI paths).

**Chat workflow note:** Finalization approval happens conversationally; no CLI flags needed.

---

### 2. Framework Assets (installed files)

Laid down by `book-framework install` under `.book-framework/` in the target repo.

```
.book-framework/
  AGENTS.md                  # Entry point (mirrors united-we-stand AGENTS.md pattern)
  framework/
    01-core-rules.md
    02-state-model.md
    03-stage-lifecycle.md
    04-command-routing.md
    05-conflict-resolution.md
    06-spec-writing-standard.md
    07-definition-of-done.md
    08-skip-force-policy.md
    09-orchestration-policy.md
  agents/
    1-book-init.md
    2-book-planner.md
    3-book-designer.md
    4-chapter-writer.md
    5-book-reviewer.md
    6-publish-assembler.md
    standalone/
      book-project-manager.md
      concept-architect.md
      book-outliner.md
      developmental-editor.md
      line-editor.md
      character-world-designer.md
      research-fact-integrity.md
  templates/
    state.json.template
    00-current-status.md.template
    01-init.md.template
    02-plan.md.template
    03-design.md.template
    04-implementation.md.template
    05-review.md.template
    06-finalization.md.template
    chapter.md.template
```

**Managed vs user-editable files:**
- Templates and `framework/` docs: managed (refresh will overwrite unless `--force` is withheld)
- `agents/` docs and `AGENTS.md`: partially managed (fingerprinted; refresh warns before overwriting)
- Chapter artifacts under `.spec/<book-idea>/book/chapters/`: always user-owned; never overwritten

---

### 3. Directory Structure

#### 3a. Spec Memory (`.spec/<book-slug>/`)

Workflow state, stage files, and continuity assets. **Framework-managed. Agent writes to these; user may read them but should not hand-edit.**

```
.spec/
  .branch-mapping.json          # branch-to-book registry (see section 3c)
  <book-slug>/
    state.json                  # machine-readable runtime state
    00-current-status.md        # human-readable stage status
    01-init.md                  # book concept + acceptance criteria
    02-plan.md                  # execution plan, milestones, chapter list
    03-design.md                # full book design (plot, chapters, diagrams)
    04-implementation.md        # chapter writing log + revision tracker
    05-review.md                # review pass, issue list, resolved items
    06-finalization.md          # publish-assembly report + cleanup log
    assets/
      chapter-memory.json       # rolling chapter summaries + key facts
      character-profiles.md     # optional
      world-notes.md            # optional
      research-pack.md          # optional
```

#### 3b. Book Content (`<book-slug>/` at repo root)

Actual authored content. **Author-owned. Framework creates skeleton; agent writes chapters; framework NEVER overwrites.**

```
<book-slug>/
  chapters/
    01-<chapter-slug>.md        # one file per chapter
    02-<chapter-slug>.md
    ...
  manuscript-<slug>-final.md    # assembled by stage 6 (concat, no rewrite)
```

#### 3c. Branch Mapping (`.spec/.branch-mapping.json`)

Tracks which books are associated with which branches. Enables multi-book repos and cross-branch work.

```json
{
  "version": 1,
  "branches": {
    "main": ["my-book"],
    "feature/edit-chapter-5": ["my-book"],
    "feature/book-two": ["my-book", "another-book"]
  },
  "books": {
    "my-book": {
      "displayName": "My Book Title",
      "branches": ["main", "feature/edit-chapter-5", "feature/book-two"],
      "createdAt": "2026-03-26T00:00:00Z"
    },
    "another-book": {
      "displayName": "Another Book",
      "branches": ["feature/book-two"],
      "createdAt": "2026-03-26T00:00:00Z"
    }
  }
}
```

**Branch Resolution Policy (in chat):**

| Branch books count | User specifies book? | Action |
|---|---|---|
| 1 book | No | Use that book automatically |
| 1 book | Yes | Use specified book (may be on another branch) |
| Multiple books | No | Ask user which book they mean |
| Multiple books | Yes (name in message) | Use that book directly; no confirmation needed |
| 0 books | No | List all books in `.spec/` and ask |

Instructions for agents:
- **Always check `.spec/.branch-mapping.json` before asking the user which book.**
- **If the user mentions a book name or slug in their message, use that directly — do not ask for confirmation.**
- **When starting a new chat, read `.spec/.branch-mapping.json` + current branch to resolve active book context quickly.**
- Multiple books can be worked on in a single branch (e.g., `main`).
- One book can be worked on across multiple branches (common for edits, fixes).
- When a book is initialized on a branch, add the entry to `.branch-mapping.json` and update on every branch switch.

#### Book-Idea Naming and Matching Policy

- Book-idea names are normalized to lowercase slug: spaces → hyphens, special chars stripped.
- On `init <name>` (CLI or chat):
  1. Normalize input to slug.
  2. Exact match check against existing `.spec/` subdirectories.
  3. If exact match → offer to continue or create new (user choice required).
  4. If no exact match → fuzzy similarity check (Levenshtein distance ≤ 2 or substring containment).
  5. If close match found → display suggestion and ask user to confirm or proceed with new name.
  6. If no match → create new book-idea folder and bootstrap from templates.
- Collision handling: if two attempts produce the same slug, append a short timestamp suffix (e.g., `-2026`).

**In chat:** Agent scans `.spec/` directly, proposes matches, and user confirms which idea to continue or create new.

#### `state.json` Schema

```json
{
  "bookIdeaName": "my-book-title",
  "sanitizedBookIdeaName": "my-book-title",
  "bookIdeaMemoryFolder": ".spec/my-book-title",
  "currentStage": "3-designer",
  "completedSteps": ["1-book-init", "2-book-planner"],
  "incompletedStages": [],
  "nextRecommendedStep": "4-chapter-writer",
  "lastUpdatedBy": "book-framework-cli",
  "lastUpdatedAt": "2026-03-25T00:00:00Z",
  "initialized": true,
  "finalized": false,
  "orchestrationMode": "parallel",
  "chapterCount": 0,
  "manuscriptFile": null
}
```

`orchestrationMode` is set at init time based on detected tool. In chat mode (Claude), default is `parallel`; in other contexts, default is `sequential`. May be overridden via user preference in chat or `init --mode sequential` in CLI.

---

### 4. Agent Contracts

#### Stage Agents

| Stage | Agent | Inputs | Outputs | May write code |
|---|---|---|---|---|
| 1 | `1-book-init` | User idea, audience, category, publishing intent | `01-init.md`, `state.json` | No |
| 2 | `2-book-planner` | `01-init.md` | `02-plan.md`, updated `state.json` | No |
| 3 | `3-book-designer` | `01-init.md`, `02-plan.md` | `03-design.md` including full plot summary, per-chapter summaries, Mermaid story diagrams, and stage-4 implementation contract | No |
| 4 | `4-chapter-writer` | `03-design.md`, `02-plan.md`, `chapter-memory.json` (all summaries), full text of previous 4–5 chapter files (sliding window), chapter-N entry constraints from `continuity-checker` | Chapter `.md` files under `book/chapters/`, updated `chapter-memory.json`, `04-implementation.md` implementation summary | Yes (prose) |
| 5 | `5-book-reviewer` | All chapter files, `04-implementation.md` | `05-review.md` with spell-check, grammar, quality findings, and improvement suggestions | No |
| 6 | `6-publish-assembler` | Chapter files under `book/chapters/`, `05-review.md` | Final manuscript file via direct concat (no content rewrite), `06-finalization.md` | Cleanup only |

#### Stage 3 Content Design Deliverables (mandatory handoff)

`03-design.md` must include:

- Full plot summary (complete arc)
- Chapter-by-chapter summary table (one row per chapter)
- Mermaid diagrams for story flow and dependencies
- Canonical facts/constraints that stage 4 must not violate
- Stage-4 implementation contract: create `book/`, create `book/chapters/`, create one file per chapter defined in design

#### Standalone Role Agents (may run anytime; do not advance stage)

| Agent | Source | Role |
|---|---|---|
| `book-project-manager` | LibriScribe `project_manager` | Workflow orchestration, gate control, cross-agent coordination |
| `concept-architect` | LibriScribe `concept_generator` | Idea shaping, premise refinement, hook clarity |
| `book-outliner` | LibriScribe `outliner` + `scene_outliner` | Chapter plan elaboration, dependency sequencing |
| `developmental-editor` | LibriScribe `editor` / `editor_enhanced` | Structure, coherence, and argument flow revision |
| `line-editor` | LibriScribe `style_editor` | Style, clarity, voice, and sentence-level refinement |
| `character-world-designer` | LibriScribe `character_generator` + `worldbuilding` | Character profiles, world-building notes, setting consistency |
| `research-fact-integrity` | LibriScribe `researcher` + `fact_checker` | Research packs, fact cross-checking, citation notes |
| `chapter-arc-architect` | Research (Story Grid / Save the Cat methodology) | Plans the narrative or argumentative arc for each individual chapter before writing begins |
| `continuity-checker` | Research (manuscript QA practice) | Cross-chapter consistency tracking: character details, timeline, terminology, plot threads |
| `book-blurb-writer` | Research (Amazon KDP copywriting best practices) | Writes back-cover copy and Amazon listing description optimized for reader hook and discoverability |
| `sensitivity-reader` | Research (publishing industry standard) | Reviews for cultural accuracy, representation blind spots, and unintentional bias before finalization |

#### Agent Source Material Policy

- All agents derived from the original LibriScribe repo use the corresponding Python agent logic (`src/libriscribe/agents/`) and prompt YAML (`prompts/templates/`) as the **content baseline** for their markdown instruction files.
- Research-sourced agents are authored from scratch using established book-writing and publishing methodology (Story Grid, Save the Cat, Amazon KDP best practices, professional editing standards).
- Original source files (`src/`, `prompts/`) are deleted from the repo during the implementation stage after all content has been extracted and rewritten as framework agent docs (see Implementation Cleanup below).
- No Python runtime code is carried forward; only the instructional content and prompt logic is adapted.

---

### 5. Stage Lifecycle and Approval Gates

```mermaid
stateDiagram-v2
    [*] --> dormant : install
  dormant --> 1-book-init : init
    1-book-init --> awaiting_approval_1 : stage complete
    awaiting_approval_1 --> 2-book-planner : approved
    2-book-planner --> awaiting_approval_2 : stage complete
    awaiting_approval_2 --> 3-book-designer : approved
    3-book-designer --> awaiting_approval_3 : stage complete
    awaiting_approval_3 --> 4-chapter-writer : approved
    4-chapter-writer --> awaiting_approval_4 : stage complete
    awaiting_approval_4 --> 5-book-reviewer : approved
    5-book-reviewer --> awaiting_approval_5 : stage complete
    awaiting_approval_5 --> 6-publish-assembler : approved
    6-publish-assembler --> awaiting_final_confirm : assembly complete
    awaiting_final_confirm --> [*] : user confirms close
```

Rules:
- Only one stage active at a time. Auto-advancement is prohibited.
- Approval is always an explicit user instruction (no implicit approval from AI output alone).
- A stage may reach "complete" status but remains `Current stage` until user advances.
- `6-publish-assembler` requires a final explicit confirmation before cleanup actions run.

---

### 6. Orchestration Policy

```
Tool detection at init time:
  if CLAUDE_* env vars present, or .claude/ detected → mode = parallel
  else → mode = sequential

Override: book-framework init --mode [parallel|sequential]
```

**Parallel-allowed tasks (Claude mode):**
- Independent chapter drafts (different chapter numbers, no content dependencies)
- Per-chapter review passes
- Research pack generation for non-overlapping topics

**Always sequential (both modes):**
- concept → outline → chapter plan (hard dependency chain)
- Any step requiring prior approval output as input
- Finalization assembly (single writer, single output file)

**Parallel write-ownership rule:**
- Chapter files are owned exclusively one at a time per agent invocation.
- No two agent calls may write to the same chapter file simultaneously.
- `book-project-manager` is the serialization authority for parallel chapter writes.

---

### 6.1 Chat-First Execution Model

**After `book-framework install`, the agent (Claude) runs all stages conversationally:**

```
User (Chat) ──────┐
                  │
     Agent ◄──────┘  (1) User brings book-idea name
        │
        ├─ Agent scans .spec/<book-idea>/ (or creates it)
        │
        ├─ Stage 1: Agent reads 01-init.md, works with user, writes updates
        │
        ├─ User approves stage 1
        │
        ├─ Stage 2: Agent reads 01-init.md + 02-plan.md template, plans, writes 02-plan.md
        │
        ├─ User approves stage 2
        │
        ├─ Stage 3: Agent designs final book structure, writes 03-design.md
        │
        ├─ User approves stage 3
        │
        ├─ Stage 4: Agent materializes chapters:
        │    - reads 03-design.md from .spec/<book-idea>/
        │    - creates <book-idea>/chapters/ at REPO ROOT
        │    - writes 01-<slug>.md, 02-<slug>.md, ... to <book-idea>/chapters/
        │    - updates .spec/<book-idea>/assets/chapter-memory.json after each approval
        │    - writes .spec/<book-idea>/04-implementation.md
        │
        ├─ User approves stage 4
        │
        ├─ Stage 5: Agent reviews all chapters, writes .spec/<book-idea>/05-review.md
        │
        ├─ User approves stage 5
        │
        ├─ Stage 6: Agent assembles final manuscript:
        │    - reads all files from <book-idea>/chapters/ (REPO ROOT)
        │    - concatenates in order (no rewriting)
        │    - writes <book-idea>/manuscript-<book-idea>-final.md
        │    - writes .spec/<book-idea>/06-finalization.md
        │
        └─ User confirms finalization (with optional cleanup)
```

**Key behaviors in chat:**
- Agent maintains full context across messages; no `list` or `use` commands needed
- Agent reads spec files from `.spec/<book-idea>/` and book content from `<book-idea>/chapters/`
- Approval is explicit user confirmation within the chat
- State persists across chat sessions because files are on disk
- No intermediate CLI invocations needed after install
- Agent resolves active book context from `.spec/.branch-mapping.json` + current branch
- If user mentions a book name anywhere in message, use it directly without asking

---

### 7. Chapter Schema

Each chapter file lives at `<book-slug>/chapters/NN-<slug>.md` (repo root, **not** inside `.spec/`). Structure:

```markdown
---
chapter: 1
title: "Chapter Title"
status: draft | revised | approved
word_count_target: 3000
word_count_actual: 0
assigned_agent: chapter-writer
reviewer_notes: ""
---

# Chapter Title

<!-- chapter body -->
```

Frontmatter is machine-readable by the publish-assembler for:
- ordering by `chapter` field
- filtering by `status: approved` for final assembly
- word count reporting in finalization summary

---

### 7.1 Chapter Context Memory

#### Problem
Reading all prior chapters before writing each new one is impractical — full chapter history grows beyond a useful context window quickly. But writing without any prior-chapter awareness produces disconnected content.

#### Solution: Sliding Window + Rolling Summary JSON

Two context sources are composed for every chapter write:

| Context source | What it provides | When it's used |
|---|---|---|
| Full text of chapters N-4 → N-1 (last 4) | Immediate narrative flow, voice, scene continuity | Always fed directly to `chapter-writer` |
| `chapter-memory.json` summaries for chapters 1 → N-5 | Long-range facts, character states, plot threads, established rules | Fed as compressed structured context; no full text needed |

For chapters 1–4 no summary lookup is needed; the sliding window covers everything.

#### `chapter-memory.json` Schema

```json
{
  "version": 1,
  "chapters": [
    {
      "chapter": 1,
      "title": "Chapter Title",
      "status": "approved",
      "summary": "2–4 sentence plot/argument summary.",
      "key_facts": [
        "Character X learns Y.",
        "Location Z is established as dangerous.",
        "Term 'Syndicate' first defined here."
      ],
      "open_threads": [
        "What happened to character A after the meeting?"
      ],
      "word_count": 3240
    }
  ]
}
```

- `summary`: written by `continuity-checker` immediately after a chapter reaches `status: approved`.
- `key_facts`: bullet list of facts later chapters must not contradict.
- `open_threads`: unresolved plot/argument points that must be addressed in future chapters.
- File is append-only during normal operation; entries are never deleted, only updated to reflect revised status.

#### Per-Chapter Write Loop (inside stage 4)

```
For each chapter N in the approved outline:
  1. continuity-checker reads:
       - chapter-memory.json (all summaries + open threads)
       - full text of chapters max(1, N-4) → N-1
     outputs: "chapter-N-entry-constraints.md" (1 page max)
       - facts that must hold
       - open threads that must be addressed or explicitly deferred
       - tone/voice notes from recent chapters

  2. chapter-arc-architect reads:
       - 02-plan.md (chapter's intended arc)
       - chapter-N-entry-constraints.md
     outputs: chapter N beat sheet (appended to 04-implementation.md)

  3. chapter-writer reads:
       - chapter-N-entry-constraints.md
       - chapter N beat sheet
       - full text of chapters max(1, N-4) → N-1
       - chapter-memory.json summaries for chapters 1 → N-5
    writes: book/chapters/NN-<slug>.md (status: draft)

  4. After user approves chapter N:
       - continuity-checker updates chapter-memory.json:
           appends entry for chapter N
           resolves any open_threads closed by this chapter
           flags any new open_threads introduced
       - chapter frontmatter updated to status: approved
```

#### Entry Constraints File

`chapter-N-entry-constraints.md` is a temporary working file, written to `assets/` and overwritten each chapter. It is NOT committed as a permanent artifact — its content is captured in `chapter-memory.json` after approval.

#### Stage 4 Materialization Rule

Before drafting content, stage 4 must:

1. Create `<book-slug>/` at **repo root** (not inside `.spec/`)
2. Create `<book-slug>/chapters/` at repo root
3. Create one chapter file per chapter defined in `.spec/<book-slug>/03-design.md`
4. Record implementation alignment in `.spec/<book-slug>/04-implementation.md`

---

### 8. Implementation Cleanup

At the end of the `4-implementer` stage, after all framework assets are created and all agent instruction content has been extracted and rewritten from the original LibriScribe sources, the following original repo files are deleted:

| Path | Reason |
|---|---|
| `src/` | Python LibriScribe source — content extracted into framework agent docs |
| `prompts/` | Original prompt YAMLs — content rewritten as markdown agent instructions |
| `requirements.txt` | Python dependencies — no longer relevant |
| `setup.py` | Python package setup — replaced by `package.json` |
| `__init__.py` (root) | Python root init — not applicable to npm package |
| `CONTRIBUTING.md` | Old repo contributing guide — to be replaced if needed |
| `docs/` | Old Docusaurus documentation site — replaced by framework docs under `book-framework/docs/` |

Not deleted at this stage (separate cleanup gates):
- Any user-specified temporary/reference directory → deleted at **finalization** (stage 6) after explicit user confirmation

Safety controls:
- Implementation cleanup only runs after the full framework scaffold is verified to exist.
- Implementer must confirm each path exists before deleting.
- Deleted paths logged in `04-implementation.md` cleanup section.
- No force flag needed — this deletion is part of the approved implementation scope, but implementer must still list paths and verify before executing.

---

### 9. Finalization Assembly

`6-publish-assembler` flow:

```
1. Read all chapter files under `<book-slug>/chapters/` (repo root, not inside .spec)
2. Sort by chapter number (frontmatter field)
3. Concatenate chapter files exactly as written (copy/paste behavior)
6. Write final manuscript to: `<book-slug>/manuscript-<book-slug>-final.md` (repo root)
7. Write finalization summary to `.spec/<book-slug>/06-finalization.md`
8. Log chapter list and word counts
9. AWAIT explicit user confirmation before cleanup
10. On confirmation: delete any user-confirmed temporary/reference directories
11. Log deleted paths in 06-finalization.md cleanup section
```

Final manuscript filename: `<book-slug>/manuscript-<book-slug>-final.md` (at repo root, not inside .spec)
Format: plain Markdown, Amazon KDP-copy-paste friendly (no custom shortcodes, no embedded HTML)

Cleanup safety controls:
- Cleanup only runs inside stage 6 after finalization record is written.
- Explicit acknowledgment prompt (or `--yes` with `--force` for CI).
- Deleted paths are logged; if directories do not exist, log as skipped (no error).

---

### 9. Package Structure

```
book-framework/
  package.json
  tsconfig.json
  bin/
    book-framework.js           # shebang entry, delegates to src/cli.ts compiled output
  src/
    cli.ts                      # command router
    commands/
      install.ts
      init.ts
      status.ts                 # status command — stage progress + branch info
      list.ts
      use.ts
      doctor.ts
      refresh.ts
    lib/
      book-idea-manager.ts      # slug, match, create, state CRUD
      branch-mapper.ts          # .spec/.branch-mapping.json read/write
      state-manager.ts          # read/write state.json
      template-engine.ts        # file copy + stamp from templates
      force-policy.ts           # shared destructive-action guard
      orchestration.ts          # tool detection, mode selection
      chapter-assembler.ts      # chapter sorting, filter, concatenation
      chat-helper.ts            # chat-first workflow file I/O helpers
    assets/
      (same tree as .book-framework/ installed layout)
  tests/
    objective-init.test.ts
    objective-matching.test.ts
    stage-transitions.test.ts
    orchestration.test.ts
    chapter-assembler.test.ts
    force-policy.test.ts
    branch-mapper.test.ts
    status.test.ts
```

`package.json` key fields:
```json
{
  "name": "@book-framework/cli",
  "version": "0.1.0",
  "bin": { "book-framework": "bin/book-framework.js" },
  "files": ["bin", "src", "assets", "docs"],
  "engines": { "node": ">=18" }
}
```

---

### 10. Interfaces / Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as book-framework CLI
  participant BIM as book-idea-manager
    participant SM as state-manager
    participant TE as template-engine
  participant FS as .spec/<book-idea>/

  User->>CLI: book-framework init "My Book Title"
  CLI->>BIM: normalize("My Book Title") → "my-book-title"
  BIM->>FS: scan .spec/ for existing book ideas
  FS-->>BIM: no exact match found
  BIM->>CLI: no match; proceed with new book idea
    CLI->>TE: stamp templates → .spec/my-book-title/
    TE->>FS: write 00-current-status.md, 01-init.md, state.json
    SM->>FS: write state.json (initialized=true, currentStage=1-book-init)
  CLI->>User: Book idea "my-book-title" initialized. Run 1-book-init to begin.
```

---

## Constraints

- No code generation in stages 1–3 and 5–6 (prose only).
- Chapter files are the only user-owned artifacts; framework never overwrites them.
- Force flags never bypass approval gates.
- Cleanup is irreversible; the confirmation prompt is mandatory and cannot be silently skipped.
- Final manuscript must be plain Markdown with no tool-specific shortcodes.
- Package must remain Node 18+ compatible throughout.
- Book-idea memory (`.spec/<slug>/`) must function independently of active git branch.
- Chapter content (`<slug>/chapters/`) must not be inside `.spec/`.
- `.book-framework/` assets must NEVER be edited by the agent or the user during workflow.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| `.spec/<slug>/` for workflow memory, `<slug>/` at root for book content | Clear separation: framework controls spec; author owns content |
| `manuscript-<name>-final.md` at repo root inside book folder | Author can find and use manuscript without navigating `.spec/` internals |
| `.spec/.branch-mapping.json` for branch-to-book registry | Enables multi-book repos and cross-branch work without forcing one-branch-one-book |
| Tool detection at `init` time (not runtime) | Avoids repeated detection overhead; user can override explicitly |
| Levenshtein ≤ 2 for close-match suggestions | Conservative enough to avoid false positives on unrelated titles |
| Direct concat assembly from `book/chapters` | Finalizer performs copy/paste assembly without rewriting chapter content |
| Separate `force-policy.ts` module | Centralizes destructive-action guard logic for consistency across all commands |
| `book-project-manager` as standalone (not a stage) | Orchestration control should be available at any point; it is a persistent coordinator, not a lifecycle stage |

---

## Out of Scope for This Stage

- Actual npm package code implementation (deferred to `4-implementer`)
- Amazon metadata artifacts (deferred to v2 per init.md open questions)
- Compatibility aliases with existing `united-we-stand` command patterns (open question, not resolved in design)
- Final public package name/scope (open question from init.md; placeholder `@book-framework/cli` used above)

---

## Files Expected to Change in Implementation Stage

**Created:**

| File/Directory | Change |
|---|---|
| `book-framework/src/` | Full package source (CLI + commands + lib) |
| `book-framework/bin/` | CLI entry point |
| `book-framework/package.json` | Package manifest |
| `book-framework/assets/` | Installed template and framework doc assets |
| `book-framework/tests/` | Unit and integration test suite |

**Deleted during implementation** (after content extracted into framework assets):

| File/Directory | Reason |
|---|---|
| `src/` | Python source — superseded by framework agent docs |
| `prompts/` | Prompt YAMLs — rewritten as markdown agent instructions |
| `requirements.txt` | Python deps — no longer needed |
| `setup.py` | Python packaging — replaced by `package.json` |
| `__init__.py` (root) | Python root init — not applicable |
| `CONTRIBUTING.md` | Old contributing guide |
| `docs/` | Old Docusaurus docs site |

**Deleted at finalization** (stage 6, after explicit user confirmation):

| File/Directory | Reason |
|---|---|
| `<optional-temp-or-reference-dir>/` | Temporary/reference directory — no longer needed after framework ship |

**Created at runtime** (not committed source):

| File/Directory | Change |
|---|---|
| `.book-framework/` | Created by `book-framework install` in target repo |
| `.spec/<book-idea>/` | Spec memory created by `book-framework init` or agent init in chat |
| `<book-idea>/` (root) | Book content created by stage 4 (chapters + final manuscript) |

---

## Status

- Design complete.
- Ready for `4-implementer` after explicit user advancement.
