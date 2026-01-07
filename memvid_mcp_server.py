#!/usr/bin/env python3
"""
Memvid MCP Server

A Model Context Protocol (MCP) server that exposes Memvid memory management
capabilities to AI clients like Claude Desktop and Claude Code.

This server provides tools for:
- Creating and managing memory files (.mv2)
- Adding text and file content to memory
- Searching memory with semantic queries
- Managing memory timeline and history
"""

import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr to avoid interfering with JSON-RPC
_LOG_LEVEL = os.getenv("MEMVID_LOG_LEVEL", "WARNING").upper()
_LOG_LEVEL_VALUE = getattr(logging, _LOG_LEVEL, logging.WARNING)
logging.basicConfig(
    level=_LOG_LEVEL_VALUE,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("memvid")


# ============================================================================
# Helper Functions
# ============================================================================


def _normalize_file_path(file_path: str) -> str:
    """Expand user paths and normalize to an absolute path."""
    return os.path.abspath(os.path.expanduser(file_path))


def _tags_dict_to_list(tags: dict[str, str] | None) -> list[str] | None:
    """Convert tag dict to list of `key:value` strings."""
    if not tags:
        return None
    return [f"{key}:{value}" for key, value in tags.items()]


def _safe_commit(mem: Any) -> bool:
    """Attempt to commit changes; return False if commit is unsupported."""
    commit = getattr(mem, "commit", None)
    if commit is None:
        return False
    try:
        commit()
    except AttributeError:
        return False
    return True


def _require_memvid_sdk() -> Any:
    """Import and return memvid_sdk."""
    try:
        import memvid_sdk
    except ImportError as exc:
        raise ImportError(
            "memvid-sdk is not installed. Please install it with: pip install memvid-sdk"
        ) from exc
    return memvid_sdk


def _get_memvid_instance(file_path: str, create_if_missing: bool = False) -> Any:
    """
    Load or create a Memvid instance.

    Args:
        file_path: Path to the .mv2 memory file

    Returns:
        Memvid instance

    Raises:
        ImportError: If memvid-sdk is not installed
        Exception: If file operations fail
    """
    normalized_path = _normalize_file_path(file_path)
    parent_dir = os.path.dirname(normalized_path)
    if create_if_missing and parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    memvid_sdk = _require_memvid_sdk()

    if not os.path.exists(normalized_path):
        if not create_if_missing:
            raise FileNotFoundError(f"Memory file not found: {normalized_path}")
        mem = memvid_sdk.create(normalized_path)
        logger.info(f"Created new memory file: {normalized_path}")
        return mem

    try:
        if os.path.getsize(normalized_path) == 0:
            if create_if_missing:
                mem = memvid_sdk.create(normalized_path)
                logger.info(f"Created new memory file: {normalized_path}")
                return mem
            raise RuntimeError(
                "Memory file is empty or invalid at: "
                f"{normalized_path}. Delete and recreate it."
            )
    except OSError:
        # If we can't stat the file, fall through and let memvid-sdk report.
        pass

    try:
        mem = memvid_sdk.use("basic", normalized_path)
        logger.info(f"Opened existing memory file: {normalized_path}")
        return mem
    except FileNotFoundError:
        if not create_if_missing:
            raise
        mem = memvid_sdk.create(normalized_path)
        logger.info(f"Created new memory file: {normalized_path}")
        return mem
    except Exception as e:
        if "failed to fill whole buffer" in str(e):
            raise RuntimeError(
                "Memory file appears incomplete or corrupted at: "
                f"{normalized_path}. Delete and recreate it, or restore from backup."
            ) from e
        raise


# ============================================================================
# Core Memory Management Tools
# ============================================================================


@mcp.tool()
def memvid_create(file_path: str, description: str = "") -> str:
    """Create a new Memvid memory file.

    Creates a new .mv2 memory file at the specified path. This file will store
    all memory data, embeddings, and indices in a single portable file.

    Args:
        file_path: Path where the memory file will be created (e.g., 'memory.mv2')
        description: Optional description of the memory's purpose

    Returns:
        Success message with file path
    """
    try:
        normalized_path = _normalize_file_path(file_path)
        parent_dir = os.path.dirname(normalized_path)

        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        if os.path.exists(normalized_path):
            return f"Memory file already exists at: {normalized_path}"

        memvid_sdk = _require_memvid_sdk()
        memvid_sdk.create(normalized_path)
        logger.info(f"Created memory file: {normalized_path}")
        return f"Successfully created memory file at: {normalized_path}"
    except ImportError:
        return "ERROR: memvid-sdk is not installed"
    except Exception as e:
        logger.error(f"Failed to create memory file: {e}")
        return f"ERROR: Failed to create memory file: {str(e)}"


@mcp.tool()
def memvid_add_text(
    file_path: str,
    content: str,
    title: str = "",
    uri: str = "",
    tags: dict[str, str] | None = None,
) -> str:
    """Add text content to memory.

    Adds a text document or snippet to the memory file. The content is indexed
    for semantic search and can be tagged for organization.

    Args:
        file_path: Path to the memory file
        content: Text content to add
        title: Optional title for the content
        uri: Optional URI identifier (e.g., 'mv2://documents/note-001')
        tags: Optional dictionary of tags for categorization

    Returns:
        Success message with content ID or error message
    """
    try:
        mem = _get_memvid_instance(file_path, create_if_missing=True)

        metadata = tags or None
        tag_list = _tags_dict_to_list(tags)
        mem.put(
            title=title or None,
            metadata=metadata,
            text=content,
            uri=uri or None,
            tags=tag_list,
        )
        _safe_commit(mem)

        logger.info(f"Added text to memory: {file_path} (title: {title})")
        return f"Successfully added text to memory. Title: {title or 'Untitled'}"
    except ImportError:
        return "ERROR: memvid-sdk is not installed"
    except Exception as e:
        logger.error(f"Failed to add text to memory: {e}")
        return f"ERROR: Failed to add text: {str(e)}"


@mcp.tool()
def memvid_add_file(
    file_path: str,
    source_file: str,
    title: str = "",
    tags: dict[str, str] | None = None,
) -> str:
    """Add file content to memory.

    Reads a file from disk and adds its content to the memory. Supports
    text files and will extract text from PDFs if the feature is enabled.

    Args:
        file_path: Path to the memory file
        source_file: Path to the source file to add
        title: Optional title for the content
        tags: Optional dictionary of tags

    Returns:
        Success message or error message
    """
    try:
        from pathlib import Path

        normalized_source = _normalize_file_path(source_file)

        # Check if source file exists
        if not os.path.exists(normalized_source):
            return f"ERROR: Source file not found: {normalized_source}"

        if not title:
            title = os.path.basename(normalized_source)

        mem = _get_memvid_instance(file_path, create_if_missing=True)
        metadata = tags or None
        tag_list = _tags_dict_to_list(tags)
        uri = Path(normalized_source).resolve().as_uri()
        mem.put(
            title=title or None,
            metadata=metadata,
            file=normalized_source,
            uri=uri,
            tags=tag_list,
        )
        _safe_commit(mem)

        logger.info(f"Added file to memory: {normalized_source} (title: {title})")
        return f"Successfully added file to memory. Title: {title or 'Untitled'}"
    except Exception as e:
        logger.error(f"Failed to add file to memory: {e}")
        return f"ERROR: Failed to add file: {str(e)}"


@mcp.tool()
def memvid_commit(file_path: str) -> str:
    """Commit changes to memory file.

    Saves all pending changes to the memory file. This should be called after
    adding content to ensure changes are persisted.

    Args:
        file_path: Path to the memory file

    Returns:
        Success message or error message
    """
    try:
        normalized_path = _normalize_file_path(file_path)
        mem = _get_memvid_instance(file_path)
        committed = _safe_commit(mem)
        if committed:
            logger.info(f"Committed changes to memory: {normalized_path}")
            return f"Successfully committed changes to memory file: {normalized_path}"

        logger.info(f"Commit not supported by memvid-sdk: {normalized_path}")
        return "Commit not supported by memvid-sdk; changes are already persisted."
    except ImportError:
        return "ERROR: memvid-sdk is not installed"
    except Exception as e:
        logger.error(f"Failed to commit memory: {e}")
        return f"ERROR: Failed to commit: {str(e)}"


# ============================================================================
# Search and Query Tools
# ============================================================================


@mcp.tool()
def memvid_search(
    file_path: str,
    query: str,
    top_k: int = 5,
    snippet_chars: int = 200,
) -> str:
    """Search memory with semantic query.

    Performs a semantic search on the memory file to find relevant content.
    Uses vector similarity search to find the most relevant matches.

    Args:
        file_path: Path to the memory file
        query: Search query (natural language)
        top_k: Number of top results to return (default: 5)
        snippet_chars: Maximum characters to return in snippets (default: 200)

    Returns:
        Formatted search results or error message
    """
    try:
        normalized_path = _normalize_file_path(file_path)
        mem = _get_memvid_instance(file_path)

        # Perform search
        response = mem.find(query, k=top_k, snippet_chars=snippet_chars)

        # Format results
        hits = response.get("hits", [])
        if not hits:
            return f"No results found for query: {query}"

        results = [f"Search Results for: '{query}'\n" + "=" * 50]
        for i, hit in enumerate(hits, 1):
            title = hit.get("title") or "Untitled"
            score = hit.get("score", "N/A")
            snippet = hit.get("snippet", "")
            text = snippet[:snippet_chars] + "..." if len(snippet) > snippet_chars else snippet

            results.append(f"\n[{i}] {title}")
            results.append(f"Score: {score}")
            results.append(f"Text: {text}")

        logger.info(
            f"Searched memory: {normalized_path} (query: {query}, results: {len(hits)})"
        )
        return "\n".join(results)
    except ImportError:
        return "ERROR: memvid-sdk is not installed"
    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return f"ERROR: Failed to search: {str(e)}"


@mcp.tool()
def memvid_search_by_tag(
    file_path: str,
    tag_key: str,
    tag_value: str = "",
) -> str:
    """Search memory by tags.

    Finds content in memory that has been tagged with specific key-value pairs.

    Args:
        file_path: Path to the memory file
        tag_key: Tag key to search for
        tag_value: Optional tag value to match

    Returns:
        Formatted results or error message
    """
    try:
        normalized_path = _normalize_file_path(file_path)
        mem = _get_memvid_instance(file_path)
        entries = mem.timeline(limit=500)

        match_token = f"{tag_key}:{tag_value}" if tag_value else None
        results = [
            f"Tag Search Results for: '{tag_key}={tag_value}'\n" + "=" * 50
        ]
        matched = 0

        for entry in entries:
            uri = entry.get("uri")
            if not uri:
                continue
            frame = mem.frame(uri)
            frame_tags = frame.get("tags", [])
            if match_token:
                matched_tag = match_token in frame_tags
            else:
                matched_tag = any(
                    tag == tag_key or tag.startswith(f"{tag_key}:") for tag in frame_tags
                )
            if not matched_tag:
                continue

            matched += 1
            title = frame.get("title") or "Untitled"
            preview = entry.get("preview", "")
            results.append(f"\n[{matched}] {title}")
            results.append(f"Tags: {', '.join(frame_tags) if frame_tags else 'None'}")
            if preview:
                results.append(f"Preview: {preview}")

        if matched == 0:
            return f"No results found for tag: {tag_key}={tag_value}"

        logger.info(
            f"Searched memory by tag: {normalized_path} (tag: {tag_key}={tag_value}, results: {matched})"
        )
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Failed to search by tag: {e}")
        return f"ERROR: Failed to search by tag: {str(e)}"


# ============================================================================
# Memory Management Tools
# ============================================================================


@mcp.tool()
def memvid_info(file_path: str) -> str:
    """Get information about memory file.

    Returns metadata about the memory file including size, number of entries,
    creation time, and last modification time.

    Args:
        file_path: Path to the memory file

    Returns:
        Formatted information or error message
    """
    try:
        import os

        normalized_path = _normalize_file_path(file_path)

        if not os.path.exists(normalized_path):
            return f"ERROR: Memory file not found: {normalized_path}"

        # Get file stats
        stat = os.stat(normalized_path)
        size_mb = stat.st_size / (1024 * 1024)

        # Try to get memvid-specific info
        try:
            info_lines = [
                f"Memory File: {normalized_path}",
                f"Size: {size_mb:.2f} MB",
                f"Created: {stat.st_ctime}",
                f"Modified: {stat.st_mtime}",
            ]
        except Exception:
            info_lines = [
                f"Memory File: {normalized_path}",
                f"Size: {size_mb:.2f} MB",
                f"Created: {stat.st_ctime}",
                f"Modified: {stat.st_mtime}",
            ]

        logger.info(f"Retrieved info for memory: {normalized_path}")
        return "\n".join(info_lines)
    except Exception as e:
        logger.error(f"Failed to get memory info: {e}")
        return f"ERROR: Failed to get info: {str(e)}"


@mcp.tool()
def memvid_list_contents(file_path: str, limit: int = 20) -> str:
    """List contents of memory file.

    Lists all or recent entries in the memory file.

    Args:
        file_path: Path to the memory file
        limit: Maximum number of entries to return (default: 20)

    Returns:
        Formatted list of contents or error message
    """
    try:
        normalized_path = _normalize_file_path(file_path)
        mem = _get_memvid_instance(file_path)

        entries = mem.timeline(limit=limit)
        if not entries:
            return f"No entries found in memory: {normalized_path}"

        results = [f"Memory Contents (limit: {limit})\n" + "=" * 50]
        for i, entry in enumerate(entries, 1):
            uri = entry.get("uri")
            title = "Untitled"
            if uri:
                try:
                    frame = mem.frame(uri)
                    title = frame.get("title") or title
                except Exception:
                    pass
            preview = entry.get("preview", "")
            timestamp = entry.get("timestamp")

            results.append(f"\n[{i}] {title}")
            if timestamp is not None:
                results.append(f"Timestamp: {timestamp}")
            if preview:
                results.append(f"Preview: {preview}")

        logger.info(f"Listed contents of memory: {normalized_path}")
        return "\n".join(results)
    except ImportError:
        return "ERROR: memvid-sdk is not installed"
    except Exception as e:
        logger.error(f"Failed to list memory contents: {e}")
        return f"ERROR: Failed to list contents: {str(e)}"


# ============================================================================
# Utility Tools
# ============================================================================


@mcp.tool()
def memvid_get_status() -> str:
    """Get Memvid MCP server status.

    Returns information about the server including version, installed features,
    and availability of dependencies.

    Returns:
        Status information
    """
    try:
        import memvid_sdk
        memvid_version = getattr(memvid_sdk, "__version__", None)
        if memvid_version is None:
            from importlib import metadata

            try:
                memvid_version = metadata.version("memvid-sdk")
            except metadata.PackageNotFoundError:
                memvid_version = "unknown"
    except ImportError:
        memvid_version = "not installed"

    status_lines = [
        "Memvid MCP Server Status",
        "=" * 50,
        f"Server Version: 0.1.0",
        f"Memvid SDK Version: {memvid_version}",
        f"MCP SDK: Available",
        "",
        "Available Features:",
        "✓ Memory creation and management",
        "✓ Text content addition",
        "✓ File content import",
        "✓ Semantic search",
        "✓ Memory info and listing",
        "",
        "Status: Ready",
    ]

    logger.info("Server status requested")
    return "\n".join(status_lines)


@mcp.tool()
def memvid_export_search_results(
    file_path: str,
    query: str,
    format: str = "text",
    top_k: int = 10,
) -> str:
    """Export search results in specified format.

    Performs a search and exports results in the specified format
    (text, json, or markdown).

    Args:
        file_path: Path to the memory file
        query: Search query
        format: Output format ('text', 'json', or 'markdown')
        top_k: Number of results to include

    Returns:
        Formatted search results or error message
    """
    try:
        # Get search results
        results = memvid_search(file_path, query, top_k)

        if format.lower() == "json":
            # Convert to JSON format
            import json
            return json.dumps({"query": query, "results": results}, indent=2)
        elif format.lower() == "markdown":
            # Convert to Markdown format
            return f"# Search Results: {query}\n\n{results}"
        else:
            # Default to text
            return results
    except Exception as e:
        logger.error(f"Failed to export search results: {e}")
        return f"ERROR: Failed to export results: {str(e)}"


# ============================================================================
# Server Initialization
# ============================================================================


def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting Memvid MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
