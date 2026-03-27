# API Reference

`book-producer` is primarily a CLI package.

## Supported CLI surface

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

## Internal module groups

- `src/commands/` - CLI command handlers
- `src/lib/book-idea-manager.ts` - book creation and slug matching
- `src/lib/branch-mapper.ts` - branch-to-book registry
- `src/lib/state-manager.ts` - state reads and writes
- `src/lib/template-engine.ts` - framework asset installation
- `src/lib/tool-adapters.ts` - managed tool entrypoint sections
- `src/lib/orchestration.ts` - init-time mode detection
- `src/lib/work-orchestrator.ts` - tool-specific chapter and research work packets

## Runtime layout

- `.book-framework/` - installed framework package inside a target repo
- `.spec/<book-slug>/` - book workflow memory and specs
- `<book-slug>/` - chapter files and manuscript output

## Stability note

The CLI and on-disk layout are the supported interfaces for `0.1.x`.
