---
name: libriscribe-workflow
description: Work with local LibriScribe book projects through its MCP tools.
---

For a writing workflow, call `list_projects` first. If the user wants a new project, call `create_project` with structured project fields; it creates an empty local project without an LLM call. Select the returned or user-selected project identifier, then inspect `get_project_status` before acting.

Generate or edit one artifact at a time. `generate_outline`, `write_chapter`, `edit_chapter`, and PDF `format_book` may call the configured provider and incur provider cost. Inspect the result and status after each operation. Before retrying a failed or possibly interrupted operation, review its recovery guidance and inspect the target artifact; retry only that one explicit operation.

For a user-authored edit, call `get_chapter`, retain its `revision_token`, then call `replace_chapter_text` with the complete revised text and token. This manual operation makes no LLM call, uses optimistic concurrency, and cannot create a missing chapter version. Call `get_chapter` again to inspect the saved text and new token. Markdown formatting and project creation do not call an LLM.

For read workflows, inspect status, then read the relevant chapter or search. Retrieval search only works when a local index already exists. `check_narrative` makes no LLM call.

Never invent a project identifier, pass a filesystem path as the project, or claim success unless the tool confirms a nonempty artifact. Generation defaults to refusing overwrite. If overwriting is explicitly requested, inspect the old artifact first.
