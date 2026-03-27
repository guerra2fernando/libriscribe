## united-we-stand workflow

Use `AGENTS.md` at the repository root as the canonical instruction entrypoint.

Before acting:
1. Read `AGENTS.md`.
2. Follow the linked files under `.united-we-stand/` for framework, steering, agents, and playbooks.
3. Read and update branch state under `.spec-driven/<sanitized-current-branch>/`.
4. If present, read `.spec-driven/.branch-routing.json` to resolve branch-folder exceptions.

If branch memory does not exist yet and the user asks for concrete code changes or other persistent repo work without explicitly asking to initialize the framework, continue helping with the request normally and do not interrupt to explain framework setup. Do not create `.spec-driven/...` files unless the user explicitly asks to initialize or explicitly brings up the framework.

When initialization is requested, always perform a fresh live check of the current git branch before creating branch memory. Do not rely on a previous branch check, previous status output, or remembered branch context from earlier in the same chat.

If branch memory does not exist yet and the current branch is detected as the repository default branch, explicit init requests must warn about default-branch risks and ask for confirmation before creating `.spec-driven/...` files unless the user explicitly uses `--force`.

For the most reliable natural-language initialization when branch memory does not exist yet, reference any installed united-we-stand file together with the init request, for example `AGENTS.md initialize this`.
