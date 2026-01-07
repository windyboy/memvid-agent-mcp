"""
Command-line interface for Memvid MCP server.

Provides easy startup and configuration of the server.
"""

import argparse
import sys
from pathlib import Path

from memvid_agent_mcp import create_server
from memvid_agent_mcp.config import ServerConfig


def main() -> None:
    """Main CLI entry point for the Memvid MCP server."""
    parser = argparse.ArgumentParser(
        description="Memvid MCP Server - Model Context Protocol server for Memvid memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  MEMVID_LOG_LEVEL            Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  MEMVID_MEMORY_DIR           Default directory for .mv2 files (default: ~/.memvid)
  MEMVID_MAX_SEARCH_RESULTS   Maximum search results to return (default: 10)
  MEMVID_EMBEDDING_MODEL      Optional embedding model override

Examples:
  # Start server with default settings
  memvid-mcp

  # Start with custom memory directory
  MEMVID_MEMORY_DIR=/path/to/memories memvid-mcp

  # Start with debug logging
  MEMVID_LOG_LEVEL=DEBUG memvid-mcp

  # Start with custom transport
  memvid-mcp --transport stdio
        """,
    )

    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "streamable-http", "sse"],
        help="MCP transport protocol to use (default: stdio)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to for HTTP/SSE transports (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP/SSE transports (default: 8000)",
    )

    parser.add_argument(
        "--memory-dir",
        type=Path,
        help="Override default memory directory",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override logging level",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    # Load configuration
    config = ServerConfig.from_env()

    # Apply CLI overrides
    if args.memory_dir:
        config.default_memory_dir = args.memory_dir
    if args.log_level:
        config.log_level = args.log_level

    # Ensure memory directory exists
    config.default_memory_dir.mkdir(parents=True, exist_ok=True)

    # Create and run server
    try:
        mcp = create_server(config)
        
        print(f"Starting Memvid MCP server...", file=sys.stderr)
        print(f"Transport: {args.transport}", file=sys.stderr)
        print(f"Memory directory: {config.default_memory_dir}", file=sys.stderr)
        print(f"Log level: {config.log_level}", file=sys.stderr)
        
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport in ["streamable-http", "sse"]:
            print(f"Server: http://{args.host}:{args.port}", file=sys.stderr)
            mcp.run(transport=args.transport, host=args.host, port=args.port)
        else:
            print(f"Unsupported transport: {args.transport}", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
