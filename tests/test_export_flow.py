"""Tests for export functionality."""

import json

import pytest
from memvid_rs import MemvidMemory

from memvid_agent_mcp.server import create_server


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


def test_export_memory_json(mcp_server, memory_for_export):
    """Test exporting memory as JSON."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(
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


def test_export_memory_text(mcp_server, memory_for_export):
    """Test exporting memory as plain text."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(
        path=str(memory_for_export),
        output_format="text",
    )
    
    assert result["status"] == "success"
    assert result["format"] == "text"
    assert result["count"] == 3
    assert isinstance(result["data"], str)
    assert "[Frame 0]" in result["data"]


def test_export_memory_csv(mcp_server, memory_for_export):
    """Test exporting memory as CSV."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(
        path=str(memory_for_export),
        output_format="csv",
    )
    
    assert result["status"] == "success"
    assert result["format"] == "csv"
    assert result["count"] == 3
    assert isinstance(result["data"], str)
    assert "index,text" in result["data"]


def test_export_memory_default_format(mcp_server, memory_for_export):
    """Test export with default format (JSON)."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(path=str(memory_for_export))
    
    assert result["status"] == "success"
    assert result["format"] == "json"


def test_export_memory_invalid_format(mcp_server, memory_for_export):
    """Test export with invalid format."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(
        path=str(memory_for_export),
        output_format="invalid_format",
    )
    
    assert result["status"] == "error"
    assert "unsupported" in result["message"].lower()


def test_export_empty_memory(mcp_server, sample_memory_path):
    """Test exporting empty memory."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.commit()
    
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["data"] == []


def test_export_nonexistent_memory(mcp_server, sample_memory_path):
    """Test exporting non-existent memory."""
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(path=str(sample_memory_path))
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_export_csv_escaping(mcp_server, sample_memory_path):
    """Test CSV export with special characters."""
    memory = MemvidMemory.create(str(sample_memory_path))
    memory.append('Text with "quotes" in it')
    memory.commit()
    
    tools = {tool.name: tool for tool in mcp_server.list_tools()}
    export_tool = tools["export_memory"]
    
    result = export_tool.fn(
        path=str(sample_memory_path),
        output_format="csv",
    )
    
    assert result["status"] == "success"
    # Quotes should be escaped
    assert '""' in result["data"]
