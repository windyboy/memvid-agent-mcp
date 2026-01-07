"""Tests for list frames functionality."""

import pytest
from memvid_rs import MemvidMemory

from memvid_agent_mcp.server import create_server


@pytest.fixture
def memory_with_frames(sample_memory_path):
    """Create a memory with multiple frames."""
    memory = MemvidMemory.create(str(sample_memory_path))
    
    # Add 15 frames for pagination testing
    for i in range(15):
        memory.append(f"Frame number {i}")
    
    memory.commit()
    return sample_memory_path


def test_list_frames_default(mcp_server, memory_with_frames):
    """Test listing frames with default parameters."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(path=str(memory_with_frames))
    
    assert result["status"] == "success"
    assert "frames" in result
    assert result["total"] == 15
    assert result["offset"] == 0
    assert result["limit"] == 10
    assert len(result["frames"]) == 10


def test_list_frames_with_offset(mcp_server, memory_with_frames):
    """Test listing frames with offset."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(
        path=str(memory_with_frames),
        offset=5,
        limit=5,
    )
    
    assert result["status"] == "success"
    assert len(result["frames"]) == 5
    assert result["offset"] == 5
    # First frame should have index 5
    if result["frames"]:
        assert result["frames"][0]["index"] == 5


def test_list_frames_pagination(mcp_server, memory_with_frames):
    """Test paginating through all frames."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    all_frames = []
    offset = 0
    limit = 5
    
    while offset < 15:
        result = list_tool.fn(
            path=str(memory_with_frames),
            offset=offset,
            limit=limit,
        )
        assert result["status"] == "success"
        all_frames.extend(result["frames"])
        offset += limit
    
    assert len(all_frames) == 15


def test_list_frames_beyond_end(mcp_server, memory_with_frames):
    """Test listing with offset beyond total frames."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(
        path=str(memory_with_frames),
        offset=20,
        limit=10,
    )
    
    assert result["status"] == "success"
    assert len(result["frames"]) == 0


def test_list_frames_format(mcp_server, memory_with_frames):
    """Test that frames have correct format."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(path=str(memory_with_frames), limit=1)
    
    assert result["status"] == "success"
    if result["frames"]:
        frame = result["frames"][0]
        assert "index" in frame
        assert "text" in frame
        assert isinstance(frame["index"], int)
        assert isinstance(frame["text"], str)


def test_list_frames_empty_memory(mcp_server, sample_memory_path):
    """Test listing frames from empty memory."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.commit()
    
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "success"
    assert result["total"] == 0
    assert len(result["frames"]) == 0


def test_list_frames_nonexistent_memory(mcp_server, sample_memory_path):
    """Test listing from non-existent memory."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    list_tool = tools["list_frames"]
    
    result = list_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()
