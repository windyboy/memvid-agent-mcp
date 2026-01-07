# Memvid Agent MCP

Production-ready Model Context Protocol (MCP) server for [Memvid](https://memvid.com/) - providing durable, portable, local AI memory storage in a single file.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-red.svg)](https://github.com/astral-sh/ruff)

## Overview

This MCP server exposes Memvid's powerful `.mv2` memory files through a standardized Model Context Protocol interface, enabling AI agents and LLM applications to:

- 🗄️ Create and manage persistent memory stores
- ✍️ Add frames (text entries) with optional metadata
- 🔍 Perform semantic and full-text hybrid search
- 📋 List and paginate through memory contents
- 📤 Export memory in multiple formats (JSON, text, CSV)
- 💾 Commit changes with crash-safe guarantees

Perfect for building AI agents with long-term memory, chatbots with conversation history, knowledge bases, and any application requiring fast, portable memory storage.

## Features

- ✅ **Production-Ready**: Comprehensive error handling, logging, and type hints
- 🔧 **Easy Setup**: Simple CLI with environment variable configuration
- 🧪 **Well-Tested**: Full pytest coverage for all flows
- 📚 **Documented**: Clear API docs and examples for every tool
- 🎨 **Quality**: Formatted with Black, linted with Ruff
- 🐍 **Modern Python**: Compatible with Python 3.10+

## Installation

### Using pip

```bash
pip install memvid-agent-mcp
```

### From source

```bash
git clone https://github.com/windyboy/memvid-agent-mcp.git
cd memvid-agent-mcp
pip install -e ".[dev]"
```

## Quick Start

### Start the MCP Server

```bash
# Start with default settings (stdio transport)
memvid-mcp

# Start with debug logging
MEMVID_LOG_LEVEL=DEBUG memvid-mcp

# Start with custom memory directory
MEMVID_MEMORY_DIR=/path/to/memories memvid-mcp

# Start with HTTP transport
memvid-mcp --transport streamable-http --port 8000
```

### Configuration

Configure the server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMVID_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `MEMVID_MEMORY_DIR` | Default directory for .mv2 files | `~/.memvid` |
| `MEMVID_MAX_SEARCH_RESULTS` | Maximum search results to return | `10` |
| `MEMVID_EMBEDDING_MODEL` | Optional embedding model override | `None` |

## MCP Tools Reference

### 1. `create_memory`

Create a new Memvid .mv2 memory file.

**Parameters:**
- `path` (string): Path where the memory file should be created. Can be relative or absolute.

**Example:**
```json
{
  "path": "my_agent_memory.mv2"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Created memory file at /path/to/my_agent_memory.mv2",
  "path": "/path/to/my_agent_memory.mv2"
}
```

### 2. `add_frame`

Add a new frame (text entry) to an existing memory.

**Parameters:**
- `path` (string): Path to the .mv2 memory file
- `text` (string): Text content to add
- `metadata` (object, optional): Metadata to attach to the frame

**Example:**
```json
{
  "path": "my_memory.mv2",
  "text": "Important conversation about project X",
  "metadata": {
    "category": "work",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Added frame to memory",
  "frame_index": 42,
  "path": "/path/to/my_memory.mv2"
}
```

### 3. `search_memory`

Search for frames using semantic and text search.

**Parameters:**
- `path` (string): Path to the .mv2 memory file
- `query` (string): Search query text
- `limit` (integer, optional): Maximum results to return

**Example:**
```json
{
  "path": "my_memory.mv2",
  "query": "project planning discussions",
  "limit": 5
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "frame_index": 10,
      "text": "We discussed the project timeline...",
      "score": 0.92
    }
  ],
  "count": 1,
  "query": "project planning discussions"
}
```

### 4. `list_frames`

List frames from a memory with pagination.

**Parameters:**
- `path` (string): Path to the .mv2 memory file
- `offset` (integer, optional): Starting index for pagination (default: 0)
- `limit` (integer, optional): Number of frames to return (default: 10)

**Example:**
```json
{
  "path": "my_memory.mv2",
  "offset": 0,
  "limit": 20
}
```

**Response:**
```json
{
  "status": "success",
  "frames": [
    {
      "index": 0,
      "text": "First frame content"
    }
  ],
  "count": 20,
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

### 5. `export_memory`

Export all frames from a memory in various formats.

**Parameters:**
- `path` (string): Path to the .mv2 memory file
- `output_format` (string): Export format - `json`, `text`, or `csv` (default: json)

**Example:**
```json
{
  "path": "my_memory.mv2",
  "output_format": "json"
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "index": 0,
      "text": "Frame content"
    }
  ],
  "format": "json",
  "count": 100
}
```

### 6. `commit_memory`

Commit pending changes to ensure all data is persisted to disk.

**Parameters:**
- `path` (string): Path to the .mv2 memory file

**Example:**
```json
{
  "path": "my_memory.mv2"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Committed changes to /path/to/my_memory.mv2",
  "path": "/path/to/my_memory.mv2"
}
```

## Usage Examples

### Complete Workflow Example

```python
# This demonstrates a typical workflow using the MCP tools

# 1. Create a new memory
create_memory(path="assistant_memory.mv2")

# 2. Add conversation history
add_frame(
    path="assistant_memory.mv2",
    text="User asked about Python best practices",
    metadata={"type": "question", "topic": "python"}
)

add_frame(
    path="assistant_memory.mv2",
    text="Recommended PEP 8 style guide and type hints",
    metadata={"type": "response", "topic": "python"}
)

# 3. Commit the changes
commit_memory(path="assistant_memory.mv2")

# 4. Search for related conversations
search_memory(
    path="assistant_memory.mv2",
    query="python coding standards",
    limit=5
)

# 5. List recent frames
list_frames(
    path="assistant_memory.mv2",
    offset=0,
    limit=10
)

# 6. Export for analysis
export_memory(
    path="assistant_memory.mv2",
    output_format="json"
)
```

### Building a Knowledge Base

```python
# Create a knowledge base for a specific domain
create_memory(path="kb/engineering.mv2")

# Add domain knowledge
topics = [
    "Microservices architecture enables independent deployment",
    "Database indexing improves query performance",
    "CI/CD pipelines automate testing and deployment",
]

for topic in topics:
    add_frame(
        path="kb/engineering.mv2",
        text=topic,
        metadata={"category": "engineering"}
    )

commit_memory(path="kb/engineering.mv2")

# Search the knowledge base
search_memory(
    path="kb/engineering.mv2",
    query="how to improve performance",
    limit=3
)
```

### Chatbot with Memory

```python
# Initialize chatbot memory
create_memory(path="chatbot_sessions.mv2")

# Store each conversation turn
def remember_conversation(user_msg, bot_response):
    add_frame(
        path="chatbot_sessions.mv2",
        text=f"User: {user_msg}\nBot: {bot_response}",
        metadata={"timestamp": "2026-01-07T10:00:00Z"}
    )
    commit_memory(path="chatbot_sessions.mv2")

# Recall relevant context
def recall_context(query):
    return search_memory(
        path="chatbot_sessions.mv2",
        query=query,
        limit=5
    )
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/windyboy/memvid-agent-mcp.git
cd memvid-agent-mcp

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=memvid_agent_mcp --cov-report=html

# Run specific test file
pytest tests/test_create_flow.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking (optional)
mypy src/
```

### Project Structure

```
memvid-agent-mcp/
├── src/
│   └── memvid_agent_mcp/
│       ├── __init__.py      # Package initialization
│       ├── config.py        # Configuration management
│       ├── server.py        # MCP server implementation
│       └── cli.py           # CLI entry point
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_config.py       # Config tests
│   ├── test_create_flow.py  # Create memory tests
│   ├── test_add_flow.py     # Add frame tests
│   ├── test_search_flow.py  # Search tests
│   ├── test_list_flow.py    # List frames tests
│   ├── test_export_flow.py  # Export tests
│   └── test_commit_flow.py  # Commit tests
├── pyproject.toml           # Project metadata and deps
├── README.md                # This file
└── .gitignore              # Git ignore rules
```

## Error Handling

All tools return a consistent response format:

**Success:**
```json
{
  "status": "success",
  "message": "Operation completed",
  ...additional data...
}
```

**Error:**
```json
{
  "status": "error",
  "message": "Detailed error message"
}
```

Common error scenarios:
- File not found: Memory file doesn't exist
- Already exists: Attempting to create existing memory
- Invalid path: Path permissions or invalid format
- Invalid format: Unsupported export format

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Format with Black and lint with Ruff
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Links

- [Memvid Official Site](https://memvid.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Memvid Python SDK](https://pypi.org/project/memvid-rs/)
- [GitHub Repository](https://github.com/windyboy/memvid-agent-mcp)

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/windyboy/memvid-agent-mcp/issues)
- Check the [Memvid documentation](https://memvid.com/docs)
- Review the [MCP documentation](https://modelcontextprotocol.io/docs)
