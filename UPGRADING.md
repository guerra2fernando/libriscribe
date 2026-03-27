# Upgrading book-producer

## How to upgrade

Upgrading `book-producer` is two commands:

```bash
npm update -g book-producer
book-producer install --force
```

`install --force` overwrites all managed `.book-framework/` files with the latest package defaults.

## What is safe across upgrades

The following are **never touched** by `install --force`:

- `.spec/<book-slug>/` — your workflow memory (stage files, state.json)
- `<book-slug>/chapters/` — your chapter files
- `<book-slug>/manuscript-*-final.md` — your assembled manuscript

Only the installed framework assets under `.book-framework/` and the managed tool-entry sections are refreshed.

## When to upgrade

Run `install --force` when:

- A new version of the package has been published
- A stage agent or framework rule file has been updated
- The `CHAT-WORKFLOW.md` instructions need refreshing
- Tool adapter sections need refreshing

There is no per-version migration needed. The framework stores all book state in `.spec/` and all book content in `<book-slug>/`, both of which are version-independent. Later stage files remain lazily created as the workflow advances.

## Version history

See [VERSIONS.md](./VERSIONS.md) for detailed per-version notes and [CHANGELOG.md](./CHANGELOG.md) for a summary of changes.

3. **Check compatibility**:
   ```bash
   book-producer status <book-slug>
   book-producer doctor
   ```

4. **Report issues**:
   If you encounter problems, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).
