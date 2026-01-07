"""Tests for commit functionality."""

from memvid_rs import MemvidMemory


def test_commit_memory_success(server_tools, sample_memory_path):
    """Test successful memory commit."""
    # Create memory and add data
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.append("Test frame")
    memory.commit()

    # Tools are already available as server_tools
    commit_tool = server_tools["commit_memory"]

    result = commit_tool(path=str(sample_memory_path))

    assert result["status"] == "success"
    assert "path" in result


def test_commit_nonexistent_memory(server_tools, sample_memory_path):
    """Test commit on non-existent memory."""
    # Tools are already available as server_tools
    commit_tool = server_tools["commit_memory"]

    result = commit_tool(path=str(sample_memory_path))

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_commit_after_add(server_tools, sample_memory_path):
    """Test commit after adding frames."""
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]
    add_tool = server_tools["add_frame"]
    commit_tool = server_tools["commit_memory"]

    # Create, add, commit
    create_tool(path=str(sample_memory_path))
    add_tool(path=str(sample_memory_path), text="Frame 1")
    add_tool(path=str(sample_memory_path), text="Frame 2")

    result = commit_tool(path=str(sample_memory_path))

    assert result["status"] == "success"

    # Verify data persisted
    memory = MemvidMemory.open(str(sample_memory_path))
    assert memory.frame_count() == 2


def test_commit_relative_path(server_tools, test_config):
    """Test commit with relative path."""
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]
    commit_tool = server_tools["commit_memory"]

    create_tool(path="relative_commit.mv2")
    result = commit_tool(path="relative_commit.mv2")

    assert result["status"] == "success"
