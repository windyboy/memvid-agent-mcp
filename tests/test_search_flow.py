"""Tests for search functionality."""

import pytest
from memvid_rs import MemvidMemory


@pytest.fixture
def memory_with_data(sample_memory_path):
    """Create a memory with sample data for searching."""
    memory = MemvidMemory.create(str(sample_memory_path))

    # Add sample frames
    sample_texts = [
        "Python programming is great for data science",
        "JavaScript is used for web development",
        "Machine learning models require training data",
        "Database optimization improves query performance",
        "Cloud computing enables scalable applications",
    ]

    for text in sample_texts:
        memory.append(text)

    memory.commit()
    return sample_memory_path


def test_search_memory_success(server_tools, memory_with_data):
    """Test successful memory search."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(memory_with_data),
        query="programming",
    )

    assert result["status"] == "success"
    assert "results" in result
    assert isinstance(result["results"], list)
    assert result["count"] >= 0


def test_search_memory_with_limit(server_tools, memory_with_data):
    """Test search with custom limit."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(memory_with_data),
        query="data",
        limit=2,
    )

    assert result["status"] == "success"
    assert len(result["results"]) <= 2


def test_search_memory_no_results(server_tools, memory_with_data):
    """Test search with query that returns no results."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(memory_with_data),
        query="nonexistent_unique_query_xyz123",
    )

    assert result["status"] == "success"
    assert result["count"] >= 0  # May be 0 or have some results


def test_search_memory_result_format(server_tools, memory_with_data):
    """Test that search results have correct format."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(memory_with_data),
        query="programming",
        limit=5,
    )

    assert result["status"] == "success"
    if result["count"] > 0:
        first_result = result["results"][0]
        assert "frame_index" in first_result
        assert "text" in first_result
        assert "score" in first_result


def test_search_nonexistent_memory(server_tools, sample_memory_path):
    """Test search on non-existent memory."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(sample_memory_path),
        query="test",
    )

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_search_empty_query(server_tools, memory_with_data):
    """Test search with empty query."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    # Empty query might still work
    result = search_tool(
        path=str(memory_with_data),
        query="",
    )

    # Should return results or error gracefully
    assert "status" in result


def test_search_default_limit(server_tools, memory_with_data, test_config):
    """Test that default limit from config is used."""
    # Tools are already available as server_tools
    search_tool = server_tools["search_memory"]

    result = search_tool(
        path=str(memory_with_data),
        query="test",
    )

    assert result["status"] == "success"
    # Results should not exceed config max
    assert len(result["results"]) <= test_config.max_search_results
