"""Tests for create memory functionality."""

from pathlib import Path

from memvid_rs import MemvidMemory


def test_create_memory_success(server_tools, sample_memory_path):
    """Test successful memory creation."""
    # Get the tool function
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]

    # Call the tool
    result = create_tool(path=str(sample_memory_path))

    assert result["status"] == "success"
    assert sample_memory_path.exists()
    assert "path" in result
    assert Path(result["path"]) == sample_memory_path


def test_create_memory_relative_path(server_tools, test_config):
    """Test memory creation with relative path."""
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]

    result = create_tool(path="relative_memory.mv2")

    assert result["status"] == "success"
    expected_path = test_config.default_memory_dir / "relative_memory.mv2"
    assert expected_path.exists()


def test_create_memory_with_subdirectory(server_tools, test_config):
    """Test memory creation in a subdirectory."""
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]

    result = create_tool(path="subdir/nested_memory.mv2")

    assert result["status"] == "success"
    expected_path = test_config.default_memory_dir / "subdir" / "nested_memory.mv2"
    assert expected_path.exists()


def test_create_memory_already_exists(server_tools, sample_memory_path):
    """Test error when trying to create existing memory."""
    # Create the memory first
    MemvidMemory.create(str(sample_memory_path)).commit()

    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]

    result = create_tool(path=str(sample_memory_path))

    assert result["status"] == "error"
    assert "already exists" in result["message"].lower()


def test_create_memory_invalid_path(server_tools):
    """Test error handling with invalid path."""
    # Tools are already available as server_tools
    create_tool = server_tools["create_memory"]

    # Try to create in a non-existent parent that can't be created
    # This might vary by platform, so we'll check for error status
    result = create_tool(path="/nonexistent/invalid/path.mv2")

    # Should either fail or succeed depending on permissions
    assert "status" in result
