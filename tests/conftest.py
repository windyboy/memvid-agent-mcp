"""Shared test fixtures and utilities."""

import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

from memvid_agent_mcp.config import ServerConfig
from memvid_agent_mcp.server import create_server


@pytest.fixture
def temp_memory_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test memory files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_memory_dir: Path) -> ServerConfig:
    """Create a test configuration."""
    return ServerConfig(
        log_level="DEBUG",
        default_memory_dir=temp_memory_dir,
        max_search_results=5,
    )


@pytest.fixture
def server_tools(test_config: ServerConfig) -> dict[str, Callable[..., dict[str, Any]]]:
    """Create server and return tool functions directly."""
    # Create the server which registers all tools
    server = create_server(test_config)

    # Extract the registered tool functions
    # FastMCP stores tools internally, we need to access them
    tools = {}
    for tool in server._tool_manager._tools.values():
        tools[tool.name] = tool.fn

    return tools


@pytest.fixture
def sample_memory_path(temp_memory_dir: Path) -> Path:
    """Return a path for a sample memory file."""
    return temp_memory_dir / "test_memory.mv2"
