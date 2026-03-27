# Chat-First Workflow Guide

This document describes how to run **book-producer** within Claude, Copilot, Cursor, Antigravity, or similar chat-based agent tools.

## One-Time Setup

```bash
npm install -g book-producer
# or install from GitHub Packages if you publish a scoped mirror there
```

In your repository:

```bash
book-producer install
```

This creates `.book-framework/` with the framework assets and tool adapter docs.

## Initialization

Open your preferred chat tool and begin:

```text
Start a new book project. The book idea is "A detective solves cosmic mysteries".
```

The active tool does:

1. Scans `.spec/` in your repo folder.
2. Checks if a similar book idea exists.
3. Creates `.spec/cosmic-detective/` with:
   - `state.json`
   - `00-current-status.md`
   - `01-init.md`
   - `assets/`
4. Creates `cosmic-detective/chapters/` at repo root.
5. Registers the book on the current git branch in `.spec/.branch-mapping.json`.

Initialization is the only time more than one framework file is created up front (`00-current-status.md` and `01-init.md`).

After that:

- Each later numbered stage file is created lazily when the user approves entering that stage.
- Outside initialization, create at most two numbered stage files in one pass: the missing predecessor for recovery and the current stage file being started.

## Tool Modes

- Claude may use `book-producer orchestrate chapters ... --tool claude` or `book-producer orchestrate research ... --tool claude` to create parallel packets for independent work.
- Copilot, Cursor, Antigravity, and similar tools must use the matching `--tool` option and stay sequential.

## Directory Structure

```text
.book-framework/               <- Installed package assets (do not edit by hand)
  agents/
  framework/
  templates/
  tooling/
  AGENTS.md
  CHAT-WORKFLOW.md
.spec/
  .branch-mapping.json
  cosmic-detective/
    state.json
    00-current-status.md
    01-init.md
    assets/
      chapter-memory.json
cosmic-detective/
  chapters/
  manuscript-cosmic-detective-final.md
```

`.book-framework/` is the installed framework package inside the user's repository. `.spec/<slug>/` stores the book specs and workflow memory. `<slug>/` at repo root stores the actual book output.

## Key Points

- Chat is the primary workflow; CLI commands remain available for install, maintenance, and orchestration packets.
- Files persist on disk, so context survives chat sessions.
- Approval is explicit. The user controls each gate.
- Stage files are created lazily as the workflow advances.
