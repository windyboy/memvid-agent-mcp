"""Tests for export functionality."""

import pytest
from memvid_rs import MemvidMemory


@pytest.fixture
def memory_for_export(sample_memory_path):
    """Create a memory with data for export testing."""
    memory = MemvidMemory.create(str(sample_memory_path))

    sample_frames = [
        "First frame content",
        "Second frame content",
        "Third frame content",
    ]

    for text in sample_frames:
        memory.append(text)

    memory.commit()
    return sample_memory_path


def test_export_memory_json(server_tools, memory_for_export):
    """Test exporting memory as JSON."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(
        path=str(memory_for_export),
        output_format="json",
    )

    assert result["status"] == "success"
    assert result["format"] == "json"
    assert result["count"] == 3
    assert isinstance(result["data"], list)

    # Validate JSON structure
    for item in result["data"]:
        assert "index" in item
        assert "text" in item


def test_export_memory_text(server_tools, memory_for_export):
    """Test exporting memory as plain text."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(
        path=str(memory_for_export),
        output_format="text",
    )

    assert result["status"] == "success"
    assert result["format"] == "text"
    assert result["count"] == 3
    assert isinstance(result["data"], str)
    assert "[Frame 0]" in result["data"]


def test_export_memory_csv(server_tools, memory_for_export):
    """Test exporting memory as CSV."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(
        path=str(memory_for_export),
        output_format="csv",
    )

    assert result["status"] == "success"
    assert result["format"] == "csv"
    assert result["count"] == 3
    assert isinstance(result["data"], str)
    assert "index,text" in result["data"]


def test_export_memory_default_format(server_tools, memory_for_export):
    """Test export with default format (JSON)."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(path=str(memory_for_export))

    assert result["status"] == "success"
    assert result["format"] == "json"


def test_export_memory_invalid_format(server_tools, memory_for_export):
    """Test export with invalid format."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(
        path=str(memory_for_export),
        output_format="invalid_format",
    )

    assert result["status"] == "error"
    assert "unsupported" in result["message"].lower()


def test_export_empty_memory(server_tools, sample_memory_path):
    """Test exporting empty memory."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.commit()

    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(path=str(sample_memory_path))

    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["data"] == []


def test_export_nonexistent_memory(server_tools, sample_memory_path):
    """Test exporting non-existent memory."""
    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(path=str(sample_memory_path))

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_export_csv_escaping(server_tools, sample_memory_path):
    """Test CSV export with special characters."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.append('Text with "quotes" in it')
    memory.commit()

    # Tools are already available as server_tools
    export_tool = server_tools["export_memory"]

    result = export_tool(
        path=str(sample_memory_path),
        output_format="csv",
    )

    assert result["status"] == "success"
    # Quotes should be escaped
    assert '""' in result["data"]
