"""
Memvid Agent MCP Server

Production-ready Model Context Protocol server for Memvid,
providing durable local AI memory storage.
"""

__version__ = "0.1.0"

from memvid_agent_mcp.server import create_server

__all__ = ["create_server", "__version__"]
