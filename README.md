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

#### `memvid_create`
Create a new Memvid memory file (.mv2 format). This file stores all memory data, embeddings, and indices in a single portable file. Supports tilde (~) expansion for home directory paths.

**Parameters:**
- `file_path` (required): Path where the memory file will be created. Supports absolute paths, relative paths, and tilde (~) expansion (e.g., `memory.mv2`, `~/.codex/memory/memvid.mv2`). The parent directory will be created if it doesn't exist.
- `description` (optional): Optional description of the memory's purpose.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "description": "AI agent persistent memory storage"
}
```

#### `memvid_add_text`
Add text content to memory with optional metadata. The content is automatically indexed for semantic search and can be organized using tags. Use this for storing decisions, preferences, constraints, and other persistent information.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion. The file will be created if it doesn't exist.
- `content` (required): Text content to add to memory. Use clear, descriptive text for better search results.
- `title` (optional): Optional title for the content. Helps identify entries when browsing or searching.
- `uri` (optional): Optional URI identifier (e.g., `mv2://documents/note-001`). Useful for creating structured references.
- `tags` (optional): Dictionary of tags for categorization (e.g., `{"type": "decision", "project": "backend"}`). Tags are converted to `"key:value"` format internally. Recommended keys: `type`, `category`, `project`, `status`.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "title": "Database Architecture Decision",
  "content": "We decided to use PostgreSQL for the main database because of its strong transaction support and JSON capabilities.",
  "tags": {
    "type": "decision",
    "category": "architecture",
    "project": "backend"
  }
}
```

#### `memvid_add_file`
Read a file from disk and add its content to memory. The file content is indexed for semantic search. Use this to import documents, configuration files, or other text-based files into memory.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion. The file will be created if it doesn't exist.
- `source_file` (required): Path to the source file to add. Must be an absolute or relative path to an existing file.
- `title` (optional): Optional title for the content. If omitted, the basename of the source file will be used.
- `tags` (optional): Dictionary of tags for categorization (e.g., `{"type": "file", "category": "config"}`).

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "source_file": "/path/to/requirements.txt",
  "title": "Project Dependencies",
  "tags": {
    "type": "file",
    "category": "dependencies"
  }
}
```

#### `memvid_commit`
Commit and persist all pending changes to the memory file. Ensures that all previously added content is safely written to disk. Recommended after batch operations or when data integrity is critical.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2"
}
```

### Search & Query

#### `memvid_search`
Perform semantic search across memory content using natural language queries. Returns the most relevant results based on semantic similarity, ordered by relevance score. Use natural language questions or descriptive phrases for best results.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion.
- `query` (required): Search query in natural language. Use descriptive questions or phrases rather than keywords (e.g., `"What database did we choose?"` instead of `"database"`).
- `top_k` (optional): Number of top results to return (default: `5`). Typically 5-10 results are sufficient.
- `snippet_chars` (optional): Maximum characters to return in result snippets (default: `200`). Longer snippets provide more context.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "query": "What database did we choose?",
  "top_k": 5,
  "snippet_chars": 300
}
```

#### `memvid_search_by_tag`
Search memory by tag key-value pairs. Returns all entries that match the specified tag criteria. This is typically faster than semantic search when you know the exact tags.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion.
- `tag_key` (required): Tag key to search for (e.g., `"type"`, `"project"`, `"category"`). If `tag_value` is not provided, matches any entry with this tag key.
- `tag_value` (optional): Tag value to match. If provided, only entries with exact `"key:value"` tag match. If omitted, returns all entries with the tag key (any value).

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "tag_key": "type",
  "tag_value": "decision"
}
```

#### `memvid_list_contents`
List entries in the memory file in chronological order (timeline). Returns entries with their titles, timestamps, and previews. Useful for browsing all stored content or reviewing recent additions.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion.
- `limit` (optional): Maximum number of entries to return (default: `20`). Use higher values to see more entries.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "limit": 50
}
```

### Utilities

#### `memvid_info`
Get metadata and statistics about a memory file. Returns file size (in MB), creation time, and last modification time. Useful for monitoring memory file growth.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion. The file must exist.

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2"
}
```

#### `memvid_get_status`
Get the status and version information of the Memvid MCP server. Returns server version, Memvid SDK version, available features, and server health status. Useful for debugging and verifying server configuration.

**Parameters:** None

**Example:**
```json
{}
```

#### `memvid_export_search_results`
Perform a semantic search and export the results in a specified format. Combines `memvid_search` with format conversion. Useful for generating reports, documentation, or structured data from search queries.

**Parameters:**
- `file_path` (required): Path to the memory file. Supports tilde (~) expansion.
- `query` (required): Search query in natural language (same as `memvid_search`).
- `format` (optional): Output format: `"text"` (human-readable, default), `"json"` (structured JSON), or `"markdown"` (formatted Markdown).
- `top_k` (optional): Number of results to include in the export (default: `10`).

**Example:**
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "query": "architecture decisions",
  "format": "markdown",
  "top_k": 10
}
```

## Example Usage

### Basic Example

In Claude or your AI agent:

```
Create a memory file at ~/.codex/memory/memvid.mv2
Add this text to it:
  Title: "Database Architecture Decision"
  Content: "We decided to use PostgreSQL for the main database..."
  Tags: {"project": "backend", "type": "decision"}

Later, search for: "What database did we choose?"
```

### Complete Workflow Example

#### 1. Create Memory File
```json
{
  "tool": "memvid_create",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "description": "AI agent persistent memory storage"
  }
}
```

#### 2. Store Architecture Decision
```json
{
  "tool": "memvid_add_text",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "title": "Database Selection Decision",
    "content": "We decided to use PostgreSQL for the main database. Key reasons: 1) Strong ACID compliance 2) Excellent JSON support 3) Active community and ecosystem 4) Proven reliability at scale.",
    "tags": {
      "type": "decision",
      "category": "architecture",
      "project": "backend",
      "status": "active"
    }
  }
}
```

#### 3. Store Code Style Preferences
```json
{
  "tool": "memvid_add_text",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "title": "TypeScript Code Style",
    "content": "Project uses 2-space indentation. Prefer const over let. Functions use function keyword over arrow functions for top-level functions. Use explicit return type annotations. Prefer interfaces over type aliases for object shapes.",
    "tags": {
      "type": "preference",
      "category": "style",
      "language": "typescript"
    }
  }
}
```

#### 4. Commit Changes
```json
{
  "tool": "memvid_commit",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2"
  }
}
```

#### 5. Query Memory (Semantic Search)
```json
{
  "tool": "memvid_search",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "query": "What database did we choose?",
    "top_k": 5,
    "snippet_chars": 300
  }
}
```

#### 6. Query Memory (By Tag)
```json
{
  "tool": "memvid_search_by_tag",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "tag_key": "type",
    "tag_value": "decision"
  }
}
```

#### 7. List All Contents
```json
{
  "tool": "memvid_list_contents",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "limit": 20
  }
}
```

#### 8. Export Search Results
```json
{
  "tool": "memvid_export_search_results",
  "arguments": {
    "file_path": "~/.codex/memory/memvid.mv2",
    "query": "architecture decisions",
    "format": "markdown",
    "top_k": 10
  }
}
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

### Use Cases

Memvid MCP server is designed for storing **durable, long-lived** information:

**✅ Suitable for storing:**
- **User preferences and settings**: Code style, tool choices, workflow preferences
- **Project decisions**: Architecture choices, technology stack decisions, design pattern preferences
- **Project context**: Project goals, constraints, important conventions
- **Long-term knowledge**: Project-specific rules, team standards, historical decisions

**❌ Not suitable for storing:**
- **Sensitive information**: API keys, passwords, tokens, credentials
- **Temporary data**: Session state, temporary variables, runtime logs
- **Error information**: Transient errors, debug logs
- **One-time query results**: Query results that don't need persistence

### Standard Workflow

#### 1. Before Task - Query Memory
Use `memvid_search` or `memvid_search_by_tag` to query relevant context before starting a task.

```
→ Understand project history, decisions, and preferences
→ Ensure consistency with previous choices
→ Avoid repeating work
```

#### 2. During Task - Use Memory
Make decisions and perform operations based on the queried context.

```
→ Follow stored preferences and conventions
→ Reference historical decisions to avoid duplication
→ Maintain consistency with project standards
```

#### 3. After Task - Write New Memory
Use `memvid_add_text` or `memvid_add_file` to add new persistent information, then `memvid_commit` to ensure data persistence.

```
→ Record new decisions and preferences
→ Document important context for future tasks
→ Commit changes to ensure data safety
```

### Tag Usage Guidelines

Use a consistent tag system to improve maintainability:

**Tag Naming Conventions:**
- Use lowercase letters with hyphens or underscores
- Keep tag key names short and semantically clear
- Use hierarchical tag structures when appropriate

**Recommended Tag Keys:**

| Tag Key | Purpose | Example Values |
|---------|---------|----------------|
| `type` | Content type | `decision`, `preference`, `constraint`, `note` |
| `category` | Classification | `architecture`, `style`, `workflow`, `tooling` |
| `project` | Project identifier | `backend`, `frontend`, `infra` |
| `status` | Status | `active`, `deprecated`, `experimental` |
| `priority` | Priority level | `high`, `medium`, `low` |

**Tag Usage Example:**
```json
{
  "type": "decision",
  "category": "architecture",
  "project": "backend",
  "status": "active"
}
```

### Performance Recommendations

1. **File location**: Keep memory files on local disk for best performance
2. **Batch operations**: Call `memvid_commit` after multiple additions rather than after each one
3. **Search optimization**: Use appropriate `top_k` values (typically 5-10 is sufficient)
4. **Tag queries**: Use `memvid_search_by_tag` when you know the exact tags, as it's faster than semantic search

### Common Patterns

#### Pattern 1: Store Architecture Decisions
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "title": "Database Selection Decision",
  "content": "Project uses PostgreSQL as the primary database. Reasons: 1) Strong transaction support 2) JSON support 3) Active community",
  "tags": {
    "type": "decision",
    "category": "database",
    "status": "active"
  }
}
```

#### Pattern 2: Store Code Style Preferences
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "title": "TypeScript Code Style",
  "content": "Project uses 2-space indentation, prefers const, functions prefer function keyword, uses explicit type annotations.",
  "tags": {
    "type": "preference",
    "category": "style",
    "language": "typescript"
  }
}
```

#### Pattern 3: Query Decision History
```json
{
  "file_path": "~/.codex/memory/memvid.mv2",
  "tag_key": "type",
  "tag_value": "decision"
}
```

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
