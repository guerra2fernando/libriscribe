# Claude Adapter

Claude is the only supported adapter that may execute parallel chapter or research packets.

## Read order

1. `.book-framework/tooling/shared.md`
2. `.book-framework/framework/09-orchestration-policy.md`
3. `.spec/<book-slug>/state.json`
4. Current stage file and stage agent

## Working rules

- Use `book-producer orchestrate chapters <slug> --tool claude --chapters ...` for independent chapter packets.
- Use `book-producer orchestrate research <slug> --tool claude --topics ...` for independent research packets.
- Never assign two parallel packets to the same chapter file.
- Respect explicit approval gates before starting the next stage.
