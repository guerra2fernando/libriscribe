# Local MCP integrations

LibriScribe includes a local stdio MCP server and local plugin packages for Claude Code and Codex. Both launch the installed `libriscribe.mcp_server` package and expose the same eleven tools. The MCP server runs on the user's machine and accesses only the configured local projects directory. Remote MCP hosting and public ChatGPT plugin submission are outside the project's roadmap. Generation and PDF formatting tools may call the LLM provider configured by the user.

## Install and configure

From the repository root, install LibriScribe into the Python environment that your MCP client can run:

```powershell
python -m pip install -e .
$env:PROJECTS_DIR = 'C:\Users\you\Books\libriscribe-projects'
```

On macOS or Linux:

```bash
python -m pip install -e .
export PROJECTS_DIR="$HOME/Books/libriscribe-projects"
```

`PROJECTS_DIR` is the only project root the tools access. Set it in the environment inherited by Claude Code or Codex. Without it, LibriScribe uses its package-relative `projects` directory, independent of the launch directory; with an editable install, that is this repository's `projects/` folder. Project calls use a direct child project identifier and never accept caller-provided paths.

## Launch and inspect the MCP server

Run directly over stdio:

```bash
python -m libriscribe.mcp_server
```

The installed console command is also available:

```bash
libriscribe-mcp
```

The process waits for MCP protocol input on stdin; diagnostics are written to stderr. Generation is synchronous and the client waits for it to finish. There are no background jobs or cancellation IDs.

## Load the local plugins

### Claude Code

With Claude Code installed, load the plugin for a session from the repository root:

```bash
claude --plugin-dir ./plugins/claude-libriscribe
```

Claude Code discovers the plugin manifest, root `.mcp.json`, and skill directory. The command is the portable installed-package invocation `python -m libriscribe.mcp_server`, so the cached plugin does not depend on a checkout-relative script path.

### Codex

Codex supports local plugin marketplaces. From the repository root, add this repository as a local marketplace:

```bash
codex plugin marketplace add .
```

Then install it from the CLI:

```bash
codex plugin add libriscribe@libriscribe-local
```

The repository catalog at `.agents/plugins/marketplace.json` points to `plugins/codex-libriscribe`. The compatibility manifest references `./.mcp.json` and `./skills/` from the plugin root. The plugin also appears in the Codex desktop Plugins Directory after restart.

## Example workflows

Create: call `create_project` with a project identifier, title, and any desired metadata. It creates an empty project with `project_data.json` and initial status, refuses duplicate identifiers, and makes no LLM call. Then inspect it with `list_projects` and `get_project_status`.

Manual edit: call `get_chapter` and retain its `revision_token`, then call `replace_chapter_text` with the complete replacement text and that token. It edits an existing original or revised file atomically, rejects stale tokens, and makes no LLM call. Read the chapter again to inspect the saved text and new token.

Generated write: inspect status and source files first. Then run one of `generate_outline`, `write_chapter`, `edit_chapter`, or `format_book`, and inspect its artifact plus `get_project_status`. Writes default to refusing overwrite. New generated files are staged inside the project and promoted only after validation. PDF formatting may call the configured provider and incur cost; Markdown formatting is local. Outline generation, chapter writing, and AI chapter editing may also call the configured provider and incur cost. On failure or a possibly interrupted run, read the operation and recovery guidance, inspect the artifact, and choose whether to retry one operation explicitly.

Read: call `list_projects`, choose a returned `project` identifier, call `get_project_status`, then call `get_chapter` (page with `start_char` and `max_chars`) or `search_project`. Retrieval search reports disabled or missing indexes explicitly and does not build one. `check_narrative` reads the existing graph and makes no LLM call.

Tool errors have `{ "ok": false, "error": { "code", "message" } }`; successes have `{ "ok": true, "result": ... }`. Chapter text is paginated with explicit character offsets and a `has_more` flag, and includes a SHA-256 `revision_token`. Project status includes the latest service operation state (`complete`, `failed`, or `in_progress`, which may indicate interruption) and recovery guidance. Status files are backward-compatible with existing projects.

## Testing

Run `pytest -q` for the service and MCP contract tests. The stdio test starts a real child process and performs initialize, list-tools, and call-tool requests using the Python MCP SDK. Plugin JSON is checked by tests; host-specific loading should also be smoke-tested with the Claude Code or Codex CLI available on the machine.
