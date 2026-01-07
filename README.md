# memvid-agent-mcp

A **Model Context Protocol (MCP) server** that exposes [Memvid](https://github.com/memvid/memvid)
memory management to TUI clients like Codex CLI.

## Built on Memvid

This server is built on the [Memvid](https://github.com/memvid/memvid) core. Memvid stores AI
memory in a single, portable `.mv2` file with append-only frames, enabling fast local retrieval,
time-ordered history, and offline use without external databases.

## Features

- Create and manage `.mv2` memory files
- Add text/files and run semantic or tag search
- List contents, get memory info, and export search results

## Quickstart

```bash
git clone https://github.com/yourusername/memvid-agent-mcp.git
cd memvid-agent-mcp
python3 -m pip install -e ".[dev]" --user
python3 memvid_mcp_server.py
```

## Installation

### Prerequisites
- Python 3.10+
- Git

### Setup (pip, global user install)

```bash
python3 -m pip install -e ".[dev]" --user
python3 memvid_mcp_server.py
```

## Configuration (TUI)

Add the server to `~/.codex/config.toml`:

```toml
[mcp_servers.memvid]
command = "python3"
args = [
  "/path/to/memvid-agent-mcp/memvid_mcp_server.py"
]
env = {
  PYTHONUNBUFFERED = "1",
  MEMVID_LOG_LEVEL = "INFO"
}
```

Add global instructions (example):

```toml
[instructions]
text = """
# Global agent instructions

## Memvid MCP memory rules

- Use the `memvid` MCP server only for durable preferences, decisions, and long-lived project context.
- At the start of each task, query memory before acting.
  - Use `memvid_search` (or `memvid_search_by_tag` when tags are available).
- After each task, write back any new durable preferences/decisions/constraints.
  - Use `memvid_add_text` or `memvid_add_file`, then `memvid_commit`.
- Never store secrets, tokens, credentials, or transient errors/logs.
- Use consistent tags like `project`, `decision`, `preference`, `constraint`.
- Default memory file path: `~/.codex/memory/memvid.mv2` (override only if user specifies).
"""
```

If you prefer a virtual environment, replace the install step with a venv workflow and keep the same
`python3 /path/to/memvid_mcp_server.py` config entry.

## Usage

Common tools: `memvid_create`, `memvid_add_text`, `memvid_add_file`, `memvid_search`,
`memvid_search_by_tag`, `memvid_list_contents`, `memvid_info`, `memvid_get_status`,
`memvid_export_search_results`, `memvid_commit`.

## License

MIT License - see LICENSE file for details.
