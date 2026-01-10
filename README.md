# Memvid MCP Server

A TypeScript/Node.js implementation of the Model Context Protocol (MCP) server that integrates [Memvid](https://github.com/memvid/memvid) with AI agents like Claude Desktop and Codex CLI.

This server allows you to use Memvid's memory management directly from your AI workflows. Memvid stores agent memory in a single `.mv2` file—no database needed, fully offline-first, with built-in semantic search and tagging.

## What You Can Do

- **Create memory files** to store agent context and decisions
- **Add content** (text or files) with optional tags and metadata
- **Search semantically** using natural language queries
- **Organize by tags** for structured memory management
- **Export results** in multiple formats (text, JSON, markdown)
- **Persist changes** with a simple commit operation

## Quick Start

### Prerequisites

- Node.js 18 or higher
- npm, yarn, or pnpm

### Installation

```bash
git clone https://github.com/windyboy/memvid-agent-mcp.git
cd memvid-agent-mcp
npm install
npm run build
```

### Configure Claude Desktop

Find your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "memvid": {
      "command": "node",
      "args": ["/path/to/memvid-agent-mcp/dist/index.js"],
      "env": {
        "MEMVID_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Restart Claude Desktop, and you're done!

### For Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.memvid]
command = "node"
args = ["/path/to/memvid-agent-mcp/dist/index.js"]
env = { MEMVID_LOG_LEVEL = "INFO" }
```

## Available Tools

### Memory Management
- `memvid_create` — Create a new memory file
- `memvid_add_text` — Add text content with optional title and tags
- `memvid_add_file` — Add file content to memory
- `memvid_commit` — Save changes to disk

### Search & Query
- `memvid_search` — Semantic search across memory
- `memvid_search_by_tag` — Find content by tags
- `memvid_list_contents` — Browse all stored content

### Utilities
- `memvid_info` — Get memory file statistics
- `memvid_get_status` — Check server health
- `memvid_export_search_results` — Export search results

## Example Usage

In Claude or your AI agent:

```
Create a memory file at ~/.codex/memory/memvid.mv2
Add this text to it:
  Title: "Database Architecture Decision"
  Content: "We decided to use PostgreSQL for the main database..."
  Tags: {"project": "backend", "type": "decision"}

Later, search for: "What database did we choose?"
```

## Development

Run in development mode (TypeScript directly, no build needed):

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Code quality checks:

```bash
npm run type-check  # TypeScript type checking
npm run lint        # ESLint
npm run format      # Prettier
npm run test        # Vitest
```

## How It Works

```
Your AI Agent (Claude, Codex, etc.)
            ↓
    JSON-RPC 2.0 over STDIO
            ↓
  Memvid MCP Server (Node.js)
            ↓
    @memvid/sdk (Node.js binding)
            ↓
  Memvid Core (Rust, high-performance)
            ↓
    .mv2 Memory Files (local disk)
```

## Configuration

Set the log level via environment variable:

```bash
export MEMVID_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Tips & Best Practices

- **Use consistent tags** across your memory for easier organization
- **Commit regularly** to ensure changes are saved
- **Keep memory files local** for best performance
- **Search semantically** — natural language queries work best
- **One file per agent** is a good starting point

## Troubleshooting

**"@memvid/sdk is not installed"**
```bash
npm install @memvid/sdk
```

**Memory file not found**
- Make sure the path is absolute
- Check file permissions
- Create the file first with `memvid_create`

**Search returns no results**
- Verify content was added with `memvid_add_text`
- Run `memvid_commit` after adding content
- Try simpler search queries
- Check the memory file is valid

**Server won't start**
- Ensure Node.js 18+ is installed
- Run `npm install` to get all dependencies
- Check Claude Desktop logs for errors

## Contributing

Found a bug or have an idea? Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit (`git commit -m 'Add your feature'`)
5. Push (`git push origin feature/your-feature`)
6. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Related

- [Memvid](https://github.com/memvid/memvid) — The core memory technology
- [Model Context Protocol](https://modelcontextprotocol.io/) — MCP specification
- [Claude Desktop](https://claude.ai/download) — AI client with MCP support
