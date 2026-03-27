# Antigravity Adapter

Antigravity integrations must run `book-producer` work sequentially.

## Read order

1. `.book-framework/tooling/shared.md`
2. `.book-framework/framework/09-orchestration-policy.md`
3. `.spec/<book-slug>/state.json`
4. Current stage file and stage agent

## Working rules

- Use `book-producer orchestrate ... --tool antigravity` to produce serialized work packets.
- Do not parallelize chapter or research writes.
- Keep one active writer per file and stage at a time.
