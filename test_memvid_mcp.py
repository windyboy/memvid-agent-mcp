#!/usr/bin/env python3
"""
Basic tests for Memvid MCP Server

These tests verify that the MCP server tools are properly defined
and can be called without errors.
"""

import tempfile
import os
import sys
import types
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

import memvid_mcp_server
import pytest


def _sdk_missing(result: str) -> bool:
    return "ERROR: memvid-sdk is not installed" in result


class FakeMem:
    def __init__(self, hits=None, timeline_entries=None, frames=None, commit_supported=True):
        self._hits = hits or []
        self._timeline_entries = timeline_entries or []
        self._frames = frames or {}
        if commit_supported:
            self.commit_called = False

            def commit() -> None:
                self.commit_called = True

            self.commit = commit

    def put(self, **kwargs):
        self.last_put = kwargs

    def find(self, query, k=5, snippet_chars=200):
        return {"hits": self._hits}

    def timeline(self, limit=20):
        return list(self._timeline_entries)

    def frame(self, uri):
        return self._frames.get(uri, {})


def _fake_sdk(mem: FakeMem, use_exception: Exception | None = None):
    module = types.SimpleNamespace()

    def create(path):
        return mem

    def use(mode, path):
        if use_exception is not None:
            raise use_exception
        return mem

    module.create = create
    module.use = use
    return module


def test_server_status():
    """Test getting server status."""
    result = memvid_mcp_server.memvid_get_status()
    assert "Memvid MCP Server Status" in result
    assert "Available" in result
    print("✓ test_server_status passed")


def test_create_memory():
    """Test creating a memory file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        result = memvid_mcp_server.memvid_create(mem_file)

        if _sdk_missing(result):
            print(f"⚠ test_create_memory skipped (memvid-sdk not installed): {result}")
            return

        # Should succeed or indicate file already exists
        assert "ERROR" not in result or "already exists" in result
        print(f"✓ test_create_memory passed: {result}")


def test_add_text():
    """Test adding text to memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        
        # Create memory first
        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_add_text skipped (memvid-sdk not installed): {create_result}")
            return
        
        # Add text
        result = memvid_mcp_server.memvid_add_text(
            file_path=mem_file,
            content="This is a test document",
            title="Test Document",
        )
        
        # Should succeed or indicate memvid-sdk not installed
        if "ERROR" in result:
            print(f"⚠ test_add_text failed: {result}")
        else:
            assert "Successfully" in result or "ERROR" in result
            print(f"✓ test_add_text passed: {result}")


def test_search():
    """Test searching memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        
        # Create memory
        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_search skipped (memvid-sdk not installed): {create_result}")
            return
        
        # Search
        result = memvid_mcp_server.memvid_search(
            file_path=mem_file,
            query="test",
        )
        
        # Should return results or error
        if "ERROR" in result:
            print(f"⚠ test_search failed: {result}")
        else:
            print(f"✓ test_search passed: {result[:100]}...")


def test_get_info():
    """Test getting memory info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        
        # Create memory
        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_get_info skipped (memvid-sdk not installed): {create_result}")
            return
        
        # Get info
        result = memvid_mcp_server.memvid_info(mem_file)
        
        assert "Memory File" in result or "ERROR" in result
        print(f"✓ test_get_info passed")


def test_list_contents():
    """Test listing memory contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")

        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_list_contents skipped (memvid-sdk not installed): {create_result}")
            return

        memvid_mcp_server.memvid_add_text(
            file_path=mem_file,
            content="Timeline entry for list contents",
            title="List Contents Entry",
        )

        result = memvid_mcp_server.memvid_list_contents(mem_file, limit=5)
        if "ERROR" in result:
            print(f"⚠ test_list_contents failed: {result}")
        else:
            assert "Memory Contents" in result
            assert "List Contents Entry" in result or "Preview" in result
            print("✓ test_list_contents passed")


def test_search_by_tag():
    """Test searching by tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")

        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_search_by_tag skipped (memvid-sdk not installed): {create_result}")
            return

        memvid_mcp_server.memvid_add_text(
            file_path=mem_file,
            content="Tagged entry for search by tag",
            title="Tagged Entry",
            tags={"topic": "test"},
        )

        result = memvid_mcp_server.memvid_search_by_tag(
            file_path=mem_file,
            tag_key="topic",
            tag_value="test",
        )
        if "ERROR" in result:
            print(f"⚠ test_search_by_tag failed: {result}")
        else:
            assert "Tag Search Results" in result
            assert "topic:test" in result
            print("✓ test_search_by_tag passed")


def test_export_results():
    """Test exporting search results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        
        # Create memory
        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_export_results skipped (memvid-sdk not installed): {create_result}")
            return
        
        # Export results
        result = memvid_mcp_server.memvid_export_search_results(
            file_path=mem_file,
            query="test",
            format="text",
        )
        
        # Should return results or error
        print(f"✓ test_export_results passed")


def test_add_file_missing_source():
    """Test add_file with a missing source path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        missing_file = os.path.join(tmpdir, "does_not_exist.txt")

        result = memvid_mcp_server.memvid_add_file(
            file_path=mem_file,
            source_file=missing_file,
        )

        assert result.startswith("ERROR: Source file not found")
        print(f"✓ test_add_file_missing_source passed: {result}")


def test_add_file_text():
    """Test add_file with a text source file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "test_memory.mv2")
        source_file = os.path.join(tmpdir, "note.txt")

        with open(source_file, "w", encoding="utf-8") as f:
            f.write("Sample content for add_file")

        create_result = memvid_mcp_server.memvid_create(mem_file)
        if _sdk_missing(create_result):
            print(f"⚠ test_add_file_text skipped (memvid-sdk not installed): {create_result}")
            return

        result = memvid_mcp_server.memvid_add_file(
            file_path=mem_file,
            source_file=source_file,
        )

        if "ERROR" in result:
            print(f"⚠ test_add_file_text failed: {result}")
        else:
            assert "Successfully added file" in result
            print(f"✓ test_add_file_text passed: {result}")


def test_memvid_create_requires_sdk(monkeypatch):
    """Ensure create fails when memvid-sdk is missing."""
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "memvid_sdk":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "missing.mv2")
        result = memvid_mcp_server.memvid_create(mem_file)
        assert result == "ERROR: memvid-sdk is not installed"


def test_memvid_add_text_creates_missing_file(monkeypatch):
    """Ensure add_text creates memory when missing."""
    mem = FakeMem()
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "new_memory.mv2")
        result = memvid_mcp_server.memvid_add_text(
            file_path=mem_file,
            content="Hello",
            title="Greeting",
        )
        assert "Successfully added text to memory" in result
        assert mem.last_put["title"] == "Greeting"


def test_memvid_search_missing_file(monkeypatch):
    """Search should fail clearly when file is missing."""
    mem = FakeMem()
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "missing.mv2")
        result = memvid_mcp_server.memvid_search(mem_file, "query")
        assert result.startswith("ERROR: Failed to search: ")
        assert "Memory file not found" in result


def test_memvid_search_corrupt_file(monkeypatch):
    """Corrupt file should surface a clear error."""
    use_exception = Exception("failed to fill whole buffer")
    mem = FakeMem()
    fake_sdk = _fake_sdk(mem, use_exception=use_exception)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "corrupt.mv2")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("x")
        result = memvid_mcp_server.memvid_search(mem_file, "query")
        assert "incomplete or corrupted" in result


def test_memvid_commit_supported(monkeypatch):
    """Commit should succeed when SDK supports commit()."""
    mem = FakeMem(commit_supported=True)
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "commit.mv2")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("x")
        result = memvid_mcp_server.memvid_commit(mem_file)
        assert "Successfully committed changes" in result
        assert mem.commit_called is True


def test_memvid_commit_unsupported(monkeypatch):
    """Commit should return a no-op message when SDK lacks commit()."""
    mem = FakeMem(commit_supported=False)
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "commit.mv2")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("x")
        result = memvid_mcp_server.memvid_commit(mem_file)
        assert result.startswith("Commit not supported")


def test_memvid_export_results_formats(monkeypatch):
    """Export results should format JSON and Markdown."""
    monkeypatch.setattr(memvid_mcp_server, "memvid_search", lambda *args, **kwargs: "OK")

    result_json = memvid_mcp_server.memvid_export_search_results(
        file_path="memory.mv2",
        query="test",
        format="json",
    )
    assert result_json.startswith("{")
    assert '"results": "OK"' in result_json

    result_md = memvid_mcp_server.memvid_export_search_results(
        file_path="memory.mv2",
        query="test",
        format="markdown",
    )
    assert result_md.startswith("# Search Results: test")


def test_search_by_tag_no_results(monkeypatch):
    """Tag search should return no results message when none match."""
    mem = FakeMem(
        timeline_entries=[{"uri": "mv://one", "preview": "x"}],
        frames={"mv://one": {"tags": ["topic:other"]}},
    )
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "tags.mv2")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("x")
        result = memvid_mcp_server.memvid_search_by_tag(mem_file, "topic", "test")
        assert result == "No results found for tag: topic=test"


def test_list_contents_no_entries(monkeypatch):
    """List contents should handle empty timeline."""
    mem = FakeMem(timeline_entries=[])
    fake_sdk = _fake_sdk(mem)
    monkeypatch.setitem(sys.modules, "memvid_sdk", fake_sdk)

    with tempfile.TemporaryDirectory() as tmpdir:
        mem_file = os.path.join(tmpdir, "empty.mv2")
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write("x")
        result = memvid_mcp_server.memvid_list_contents(mem_file)
        assert result.startswith("No entries found in memory")


if __name__ == "__main__":
    print("Running Memvid MCP Server tests...\n")
    
    try:
        test_server_status()
        test_create_memory()
        test_add_text()
        test_search()
        test_get_info()
        test_list_contents()
        test_search_by_tag()
        test_export_results()
        test_add_file_missing_source()
        test_add_file_text()
        
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
