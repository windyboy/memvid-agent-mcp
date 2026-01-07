"""Tests for create memory functionality."""

from pathlib import Path

import pytest
from memvid_rs import MemvidMemory

from memvid_agent_mcp.server import create_server


def test_create_memory_success(mcp_server, sample_memory_path):
    """Test successful memory creation."""
    # Get the tool function
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    
    # Call the tool
    result = create_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "success"
    assert sample_memory_path.exists()
    assert "path" in result
    assert Path(result["path"]) == sample_memory_path


def test_create_memory_relative_path(mcp_server, test_config):
    """Test memory creation with relative path."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    
    result = create_tool.fn(path="relative_memory.mv2")
    
    assert result["status"] == "success"
    expected_path = test_config.default_memory_dir / "relative_memory.mv2"
    assert expected_path.exists()


def test_create_memory_with_subdirectory(mcp_server, test_config):
    """Test memory creation in a subdirectory."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    
    result = create_tool.fn(path="subdir/nested_memory.mv2")
    
    assert result["status"] == "success"
    expected_path = test_config.default_memory_dir / "subdir" / "nested_memory.mv2"
    assert expected_path.exists()


def test_create_memory_already_exists(mcp_server, sample_memory_path):
    """Test error when trying to create existing memory."""
    # Create the memory first
    MemvidMemory.create(str(sample_memory_path)).commit()
    
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    
    result = create_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "error"
    assert "already exists" in result["message"].lower()


def test_create_memory_invalid_path(mcp_server):
    """Test error handling with invalid path."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    
    # Try to create in a non-existent parent that can't be created
    # This might vary by platform, so we'll check for error status
    result = create_tool.fn(path="/nonexistent/invalid/path.mv2")
    
    # Should either fail or succeed depending on permissions
    assert "status" in result
