# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TypeScript/Node.js MCP (Model Context Protocol) server that exposes Memvid memory management capabilities to AI clients like Claude Desktop and Codex CLI. The server provides tools for creating memory files (.mv2), adding content, and performing semantic searches.

**Key Dependencies:**
- `@memvid/sdk` - Rust-backed Node.js SDK for memory operations
- `@modelcontextprotocol/sdk` - MCP protocol implementation
- Communication: JSON-RPC 2.0 over STDIO

## Development Commands

```bash
# Development (TypeScript directly, no build)
npm run dev

# Build for production
npm run build

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

**Single-File Architecture:**
- All code is in `src/index.ts` (~1014 lines)
- No separate modules or files - everything is self-contained

**Code Structure (top to bottom):**
1. **Imports & Setup** (lines 1-52): Dependencies, logging configuration
2. **Type Definitions** (lines 54-130): Tool argument interfaces, MemvidInstance interface
3. **Helper Functions** (lines 132-196): Path normalization, tag conversion, validation helpers, Memvid instance management
4. **Tool Implementations** (lines 198-580): 10 tool functions (memvidCreate, memvidAddText, etc.)
5. **MCP Server Setup** (lines 582-1014): Tool definitions with JSON schemas, request handlers, server initialization

**Key Architectural Patterns:**
- **Path Handling**: All file paths support tilde (~) expansion via `normalizeFilePath()`
- **Tag Format**: Tags are stored as objects `{key: value}` but converted to `"key:value"` strings for Memvid SDK
- **Error Handling**: All tool functions return strings (success or "ERROR: ..." messages)
- **Lazy Creation**: Memory files are auto-created if missing when `createIfMissing=true` is passed to `getMemvidInstance()`
- **Logging**: All logs go to stderr (not stdout) to avoid interfering with JSON-RPC communication

**Critical Implementation Details:**
- `getMemvidInstance()` handles three cases: file doesn't exist, file is empty, file exists
- Uses `create()` for new files, `use("basic", path, {mode: "open"})` for existing files
- `memvid_commit` calls `mem.seal()` if available (SDK version dependent)
- Search results are formatted as human-readable text, not JSON
- All file operations use async `fsPromises` API (no blocking synchronous operations)

## Input Validation & Security

**Validation Helpers:**
- `validateRequiredString(value, fieldName)`: Validates non-empty strings, throws error if invalid
- `validateOptionalNumber(value, fieldName, min?, max?)`: Validates numbers with optional range checks

**Validation Applied To:**
- `memvidAddText`: file_path, content (required strings)
- `memvidAddFile`: file_path, source_file (required strings)
- `memvidSearch`: file_path, query (required strings); top_k (1-100); snippet_chars (1-10000)
- `memvidSearchByTag`: file_path, tag_key (required strings); limit (1-100000)

**Security Features:**
- Optional path validation via `MEMVID_ALLOWED_DIRS` environment variable
- Set to colon-separated list of allowed directories (e.g., `/home/user/memories:/tmp/memvid`)
- When set, all file operations are restricted to these directories
- Prevents path traversal attacks and unauthorized file access

**Type Safety:**
- `MemvidInstance` interface defines all Memvid SDK methods used
- Tool argument interfaces for all 10 tools (MemvidCreateArgs, MemvidAddTextArgs, etc.)
- No use of `any` types - all casts go through `unknown` first

## TypeScript Configuration

- **Target**: ES2020 with ES modules (`"type": "module"` in package.json)
- **Strict Mode**: All strict checks enabled (noImplicitAny, strictNullChecks, etc.)
- **Output**: Compiled to `dist/` directory
- **Entry Point**: `dist/index.js` (has shebang for CLI execution)

## Memvid Memory Usage Rules (from .cursorrules)

When working with this codebase, follow these memory management patterns:

- Use Memvid for durable user preferences, decisions, and project context
- At task start: Query memory for relevant context (`memvid_search` or `memvid_search_by_tag`)
- After task: Write back new durable preferences/decisions (`memvid_add_text` + `memvid_commit`)
- Never store: secrets, tokens, credentials, transient errors
- Use consistent tags: `project`, `decision`, `preference`, `constraint`
- Default memory file path: `memory.mv2`

## Testing the Server

To test locally with Claude Desktop:

1. Build: `npm run build`
2. Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "memvid": {
         "command": "node",
         "args": ["/absolute/path/to/memvid-agent-mcp/dist/index.js"],
         "env": {
           "MEMVID_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```
3. Restart Claude Desktop
4. Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`

## Common Modification Patterns

**Adding a new tool:**
1. Add tool implementation function (lines 119-483 section)
2. Add tool definition to `tools` array (lines 489-705)
3. Add case to switch statement in request handler (lines 740-801)

**Modifying tool behavior:**
- Tool functions are async and return `Promise<string>`
- Always use `normalizeFilePath()` for file path parameters
- Use `getMemvidInstance(filePath, createIfMissing)` to get Memvid instance
- Log with `log(level, message)` - goes to stderr

**Tag handling:**
- Input: `{key: value}` object from MCP client
- Conversion: `tagsObjectToList()` converts to `["key:value"]` array
- Storage: Both formats stored (array in `tags`, object in `metadata`)
