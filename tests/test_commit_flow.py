"""Tests for commit functionality."""

import pytest
from memvid_rs import MemvidMemory

from memvid_agent_mcp.server import create_server


def test_commit_memory_success(mcp_server, sample_memory_path):
    """Test successful memory commit."""
    # Create memory and add data
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.append("Test frame")
    memory.commit()
    
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    commit_tool = tools["commit_memory"]
    
    result = commit_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "success"
    assert "path" in result


def test_commit_nonexistent_memory(mcp_server, sample_memory_path):
    """Test commit on non-existent memory."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    commit_tool = tools["commit_memory"]
    
    result = commit_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_commit_after_add(mcp_server, sample_memory_path):
    """Test commit after adding frames."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    add_tool = tools["add_frame"]
    commit_tool = tools["commit_memory"]
    
    # Create, add, commit
    create_tool.fn(path=str(sample_memory_path))
    add_tool.fn(path=str(sample_memory_path), text="Frame 1")
    add_tool.fn(path=str(sample_memory_path), text="Frame 2")
    
    result = commit_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "success"
    
    # Verify data persisted
    memory = MemvidMemory.open(str(sample_memory_path))
    assert memory.len() == 2


def test_commit_relative_path(mcp_server, test_config):
    """Test commit with relative path."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    commit_tool = tools["commit_memory"]
    
    create_tool.fn(path="relative_commit.mv2")
    result = commit_tool.fn(path="relative_commit.mv2")
    
    assert result["status"] == "success"
