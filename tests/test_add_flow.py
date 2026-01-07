"""Tests for add frame functionality."""

from pathlib import Path

import pytest
from memvid_rs import MemvidMemory

from memvid_agent_mcp.server import create_server


@pytest.fixture
def existing_memory(sample_memory_path):
    """Create an existing memory for testing."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.commit()
    return sample_memory_path


def test_add_frame_success(mcp_server, existing_memory):
    """Test successful frame addition."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    add_tool = tools["add_frame"]
    
    result = add_tool.fn(
        path=str(existing_memory),
        text="This is a test frame",
    )
    
    assert result["status"] == "success"
    assert "frame_index" in result
    assert result["frame_index"] >= 0


def test_add_frame_with_metadata(mcp_server, existing_memory):
    """Test frame addition with metadata."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    add_tool = tools["add_frame"]
    
    metadata = {"category": "test", "priority": "high"}
    result = add_tool.fn(
        path=str(existing_memory),
        text="Frame with metadata",
        metadata=metadata,
    )
    
    assert result["status"] == "success"
    assert "frame_index" in result


def test_add_multiple_frames(mcp_server, existing_memory):
    """Test adding multiple frames sequentially."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    add_tool = tools["add_frame"]
    
    texts = [
        "First frame",
        "Second frame",
        "Third frame",
    ]
    
    frame_indices = []
    for text in texts:
        result = add_tool.fn(path=str(existing_memory), text=text)
        assert result["status"] == "success"
        frame_indices.append(result["frame_index"])
    
    # Indices should be sequential
    assert len(frame_indices) == 3
    assert frame_indices == sorted(frame_indices)


def test_add_frame_to_nonexistent_memory(mcp_server, sample_memory_path):
    """Test error when adding to non-existent memory."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    add_tool = tools["add_frame"]
    
    result = add_tool.fn(
        path=str(sample_memory_path),
        text="This should fail",
    )
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_add_frame_empty_text(mcp_server, existing_memory):
    """Test adding frame with empty text."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    add_tool = tools["add_frame"]
    
    result = add_tool.fn(
        path=str(existing_memory),
        text="",
    )
    
    # Should still succeed with empty text
    assert result["status"] == "success"


def test_add_frame_relative_path(mcp_server, test_config):
    """Test adding frame with relative path."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    create_tool = tools["create_memory"]
    add_tool = tools["add_frame"]
    
    # Create with relative path
    create_tool.fn(path="relative.mv2")
    
    # Add with relative path
    result = add_tool.fn(
        path="relative.mv2",
        text="Frame in relative memory",
    )
    
    assert result["status"] == "success"
