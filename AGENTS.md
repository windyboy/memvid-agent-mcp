# Repository Guidelines

## Project Structure & Module Organization
- `memvid_mcp_server.py` is the main MCP server implementation.
- `test_memvid_mcp.py` contains the test suite.
- `pyproject.toml` defines dependencies and tooling configuration.
- `venv/` is a local virtual environment (do not commit changes inside it).

## Build, Test, and Development Commands
- `uv sync --all-extras` installs runtime and dev dependencies into the local environment.
- `uv run python memvid_mcp_server.py` runs the MCP server locally.
- `uv run pytest` runs the test suite.
- `uv run ruff check memvid_mcp_server.py` runs lint checks.
- `uv run black memvid_mcp_server.py` formats the main module.

## Coding Style & Naming Conventions
- Python 3.10+ codebase; keep code compatible with `requires-python` in `pyproject.toml`.
- Formatting: Black with `line-length = 100`.
- Linting: Ruff with `line-length = 100`.
- Typing: Mypy is configured; keep type hints consistent where present.
- Naming: follow PEP 8 (snake_case for functions/vars, CapWords for classes).

## Testing Guidelines
- Framework: Pytest with `pytest-asyncio` for async tests.
- Run tests with `uv run pytest`.
- Prefer descriptive test names that mirror behavior (e.g., `test_create_memory_file`).

## Commit & Pull Request Guidelines
- No commit conventions are documented in this repo; use clear, imperative messages (e.g., "Add MCP config example").
- PRs should include: summary of changes, testing performed, and any relevant configuration notes.

## Agent-Specific Instructions
- If using Codex CLI, document agent instructions here so contributors can follow the same MCP usage patterns.
- For MCP memory usage, specify when to read from and write to the `memvid` server to ensure consistent behavior.

### MCP Memory Policy
- Use the `memvid` MCP server only for durable preferences, decisions, and long-lived project context.
- At the start of each task, query memory before acting.
  - Use `memvid_search` (or `memvid_search_by_tag` when tags are available).
- After each task, write back any new durable preferences/decisions/constraints.
  - Use `memvid_add_text` or `memvid_add_file`, then `memvid_commit`.
- Never store secrets, tokens, credentials, or transient errors/logs.
- Use consistent tags like `project`, `decision`, `preference`, `constraint`.
- Default memory file path: `~/.codex/memory/memvid.mv2` (override only if user specifies).
