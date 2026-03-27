# Tooling

`book-producer` installs framework assets and tool entrypoints together.

## Installed framework package

The canonical source inside a target repository is:

```text
.book-framework/
```

That folder contains:

- framework rules
- stage agents
- templates
- tooling adapter docs

## Managed tool entrypoints

`book-producer install` also creates or refreshes these files so supported tools point back to the framework:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/book-producer.mdc`
- `.agents/workflows/book-producer.md`

Each managed file contains a `book-producer` section that points back to `.book-framework/`.

## Tool behavior

- Claude: parallel chapter and research packets allowed
- Copilot: sequential
- Cursor: sequential
- Antigravity: sequential

Use:

```bash
book-producer orchestrate chapters <slug> --tool <tool> --chapters 1,2
book-producer orchestrate research <slug> --tool <tool> --topics "topic one,topic two"
```

to generate the latest work packets for the chosen tool.

The generated packet follows the requested tool adapter even when `state.json` still reflects an earlier init-time mode. The stored mode remains visible in the packet output for traceability.
