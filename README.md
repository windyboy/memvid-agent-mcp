# Memvid MCP Server (TypeScript)

A high-performance **Model Context Protocol (MCP) server** written in TypeScript/Node.js that exposes [Memvid](https://github.com/memvid/memvid) memory management capabilities to AI clients like Claude Desktop and Codex CLI.

Memvid is a portable, serverless memory layer for AI agents that packages data, embeddings, search structure, and metadata into a single `.mv2` file. This MCP server bridges Memvid with your AI workflows, enabling persistent memory management directly from Claude.

## Features

### Core Memory Operations
- **Create Memory Files**: Initialize new `.mv2` memory files
- **Add Content**: Add text and file content to memory with metadata
- **Semantic Search**: Query memory using natural language
- **Tag-based Search**: Organize and find content by tags
- **Commit Changes**: Persist memory updates

### Memory Management
- **File Information**: View memory file statistics
- **Content Listing**: Browse memory contents with timeline
- **Export Results**: Export search results in multiple formats (text, JSON, markdown)

### Performance & Type Safety
- **TypeScript**: Full type safety and IDE support
- **Rust Backend**: High-performance Memvid core via N-API
- **No Database**: Single-file memory, offline-first
- **Framework Integration**: Direct support for LangChain, LlamaIndex, etc.

## Installation

### Prerequisites
- **Node.js** 18+ or higher
- **npm**, **yarn**, or **pnpm** package manager
- **Git**

### Setup

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/windyboy/memvid-agent-mcp.git
   cd memvid-agent-mcp
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   pnpm install
   # or
   yarn install
   ```

3. **Build the project**
   ```bash
   npm run build
   ```

## Configuration

### Claude Desktop Setup

1. **Locate Claude Desktop configuration**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add Memvid MCP Server to configuration**
   ```json
   {
     "mcpServers": {
       "memvid": {
         "command": "node",
         "args": [
           "/path/to/memvid-agent-mcp/dist/index.js"
         ],
         "env": {
           "MEMVID_LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the server

### Codex CLI Setup

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.memvid]
command = "node"
args = [
  "/path/to/memvid-agent-mcp/dist/index.js"
]
env = {
  MEMVID_LOG_LEVEL = "INFO"
}
```

## Usage

### Basic Workflow

1. **Create a memory file**
   ```
   Tool: memvid_create
   Parameters: file_path = "~/.codex/memory/memvid.mv2"
   ```

2. **Add content to memory**
   ```
   Tool: memvid_add_text
   Parameters:
   - file_path = "~/.codex/memory/memvid.mv2"
   - content = "Your text content here"
   - title = "Content Title"
   - tags = {"project": "alpha", "type": "decision"}
   ```

3. **Search memory**
   ```
   Tool: memvid_search
   Parameters:
   - file_path = "~/.codex/memory/memvid.mv2"
   - query = "What did we decide about the database?"
   - top_k = 5
   ```

4. **Commit changes**
   ```
   Tool: memvid_commit
   Parameters: file_path = "~/.codex/memory/memvid.mv2"
   ```

### Available Tools

#### Memory Management
- `memvid_create` - Create a new memory file
- `memvid_add_text` - Add text content to memory
- `memvid_add_file` - Add file content to memory
- `memvid_commit` - Save changes to memory file

#### Search & Query
- `memvid_search` - Semantic search on memory
- `memvid_search_by_tag` - Search by tags
- `memvid_list_contents` - List memory contents

#### Information
- `memvid_info` - Get memory file information
- `memvid_get_status` - Get server status
- `memvid_export_search_results` - Export results in different formats

## Development

### Running in Development Mode

```bash
npm run dev
```

This uses `tsx` to run TypeScript directly without compilation.

### Building for Production

```bash
npm run build
```

Output is in the `dist/` directory.

### Code Quality

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Formatting
npm run format

# Testing
npm run test
```

## Architecture

```
Claude Desktop / Codex CLI
        ↓
   JSON-RPC 2.0 (STDIO)
        ↓
Memvid MCP Server (TypeScript/Node.js)
        ↓
   @modelcontextprotocol/sdk
        ↓
   @memvid/sdk (Node.js)
        ↓
   Memvid Core (Rust N-API)
        ↓
   .mv2 Memory Files
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `MEMVID_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | WARNING |

## Performance Considerations

- **Memory file size**: Single `.mv2` files can contain millions of documents
- **Search speed**: Semantic search is typically sub-100ms for local files
- **Indexing**: First search on new content may take longer as indices are built
- **Concurrent access**: Not recommended for concurrent writes to same file

## Security

- **File paths**: Validated to prevent directory traversal
- **Input validation**: All parameters are validated before use
- **Error messages**: Sanitized to avoid information leakage
- **Permissions**: Respects system file permissions

## Troubleshooting

### "@memvid/sdk is not installed"
```bash
npm install @memvid/sdk
```

### Memory file not found
- Ensure the file path is correct and absolute
- Check file permissions
- Verify the file exists or use `memvid_create` first

### Search returns no results
- Verify content was added with `memvid_add_text`
- Ensure `memvid_commit` was called
- Try simpler search queries
- Check that the memory file is valid

### Server won't start
- Check Node.js version (18+)
- Verify all dependencies are installed (`npm install`)
- Review Claude Desktop logs
- Ensure no other process is using the same port

## Comparison: TypeScript vs Python

| Feature | TypeScript | Python |
|---------|-----------|--------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Type Safety | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Framework Integration | Built-in | Manual |
| Startup Time | Fast | Slower |
| Bundle Size | Smaller | Larger |
| Development | Excellent | Good |

## Roadmap

- [ ] Advanced timeline and history features
- [ ] Batch operations (bulk add/delete)
- [ ] HTTP/WebSocket transport support
- [ ] Multi-file memory management
- [ ] Memory merging and splitting
- [ ] Advanced query syntax
- [ ] Integration with LLM analysis

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.
