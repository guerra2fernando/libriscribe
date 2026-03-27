# FAQ

## What gets installed in a user's repository?

`.book-framework/` is installed in the target repository. That is the installed framework package.

Managed tool entrypoints are also created or refreshed so the supported tools point back to `.book-framework/`.

## Where are the book specs stored?

In:

```text
.spec/<book-slug>/
```

That folder stores workflow memory and stage specs.

## Where are the actual chapters and manuscript stored?

At:

```text
<book-slug>/
```

in the repository root.

## Are stage files created all at once?

No.

- Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`.
- Later numbered stage files are created lazily as the user approves each stage.
- Outside initialization, no more than two numbered stage files should be created in one pass.

## Which tools are supported?

The framework is designed to work with Claude, Copilot, Cursor, and Antigravity.

- Claude may use parallel packets.
- The others stay sequential.

## Does the package require Git?

Git gives the best experience because branch mapping uses the current branch name. Fresh repos are supported, including unborn branches before the first content commit.

## Do upgrades overwrite my book content?

No. `book-producer install --force` refreshes `.book-framework/` and the managed tool-entry sections only. It does not overwrite `.spec/<book-slug>/` or `<book-slug>/chapters/`.
