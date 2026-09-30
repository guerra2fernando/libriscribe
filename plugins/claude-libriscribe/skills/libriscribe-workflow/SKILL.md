---
name: libriscribe-workflow
description: Work with local LibriScribe book projects through its MCP tools.
---

For a read workflow, list projects, select the user's intended project, inspect its status, then read or search the relevant chapter and run a narrative check when useful. Retrieval search only works when a local index already exists.

For a write workflow, inspect the project and relevant source artifacts first. Ask the user to explicitly confirm overwrite intent if the target already exists. Then run one generation or formatting action and inspect the resulting artifact and project status. Generation runs synchronously and may take time.

Never invent a project identifier, pass a filesystem path as the project, or claim success unless the tool confirms a nonempty artifact.
