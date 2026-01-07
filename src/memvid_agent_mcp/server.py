"""
Main MCP server implementation for Memvid.

Provides tools for creating, managing, and searching .mv2 memory files.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from memvid_rs import MemvidMemory
from pydantic import BaseModel, Field

from memvid_agent_mcp.config import ServerConfig

logger = logging.getLogger(__name__)


class CreateMemoryInput(BaseModel):
    """Input schema for creating a new memory file."""

    path: str = Field(
        description="Path to the .mv2 memory file to create",
    )


class AddFrameInput(BaseModel):
    """Input schema for adding a frame to memory."""

    path: str = Field(
        description="Path to the .mv2 memory file",
    )
    text: str = Field(
        description="Text content to add as a new frame",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata to attach to the frame",
    )


class SearchInput(BaseModel):
    """Input schema for searching memory."""

    path: str = Field(
        description="Path to the .mv2 memory file",
    )
    query: str = Field(
        description="Search query text",
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of results to return (uses server default if not specified)",
    )


class ListFramesInput(BaseModel):
    """Input schema for listing frames."""

    path: str = Field(
        description="Path to the .mv2 memory file",
    )
    offset: Optional[int] = Field(
        default=0,
        description="Starting index for pagination",
    )
    limit: Optional[int] = Field(
        default=10,
        description="Number of frames to return",
    )


class ExportInput(BaseModel):
    """Input schema for exporting memory."""

    path: str = Field(
        description="Path to the .mv2 memory file",
    )
    output_format: str = Field(
        default="json",
        description="Export format (json, text, csv)",
    )


class CommitInput(BaseModel):
    """Input schema for committing memory changes."""

    path: str = Field(
        description="Path to the .mv2 memory file to commit",
    )


def create_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """
    Create and configure the Memvid MCP server.

    Args:
        config: Optional server configuration. If None, loads from environment.

    Returns:
        Configured FastMCP server instance.
    """
    if config is None:
        config = ServerConfig.from_env()

    config.setup_logging()
    logger.info("Initializing Memvid MCP server")

    # Ensure default memory directory exists
    config.default_memory_dir.mkdir(parents=True, exist_ok=True)

    mcp = FastMCP("memvid-agent", dependencies=[config])

    @mcp.tool()
    def create_memory(path: str) -> Dict[str, Any]:
        """
        Create a new Memvid .mv2 memory file.

        Args:
            path: Path where the new memory file should be created.
                  Can be relative or absolute. If relative, created in default memory dir.

        Returns:
            Dictionary containing the absolute path of the created memory file.

        Example:
            create_memory("my_agent_memory.mv2")
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            # Ensure parent directory exists
            memory_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file already exists
            if memory_path.exists():
                raise ValueError(f"Memory file already exists: {memory_path}")

            # Create the memory
            logger.info(f"Creating new memory at: {memory_path}")
            memory = MemvidMemory.create(str(memory_path))
            memory.commit()

            logger.info(f"Successfully created memory: {memory_path}")
            return {
                "status": "success",
                "message": f"Created memory file at {memory_path}",
                "path": str(memory_path),
            }

        except Exception as e:
            logger.error(f"Failed to create memory: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to create memory: {str(e)}",
            }

    @mcp.tool()
    def add_frame(path: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new frame (text entry) to an existing Memvid memory.

        Args:
            path: Path to the .mv2 memory file.
            text: Text content to add to the memory.
            metadata: Optional dictionary of metadata to attach to the frame.

        Returns:
            Dictionary containing the frame index and status.

        Example:
            add_frame("my_memory.mv2", "Important conversation about project X", {"category": "work"})
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            if not memory_path.exists():
                raise FileNotFoundError(f"Memory file not found: {memory_path}")

            logger.info(f"Adding frame to memory: {memory_path}")
            
            # Open existing memory and append
            memory = MemvidMemory.open(str(memory_path))
            frame_idx = memory.append(text)
            
            # Note: memvid-rs may need API updates to support metadata
            # For now, we'll just log it
            if metadata:
                logger.debug(f"Metadata attached to frame {frame_idx}: {metadata}")

            logger.info(f"Successfully added frame {frame_idx} to {memory_path}")
            return {
                "status": "success",
                "message": f"Added frame to memory",
                "frame_index": frame_idx,
                "path": str(memory_path),
            }

        except Exception as e:
            logger.error(f"Failed to add frame: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to add frame: {str(e)}",
            }

    @mcp.tool()
    def search_memory(path: str, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for frames in a Memvid memory using semantic and text search.

        Args:
            path: Path to the .mv2 memory file.
            query: Search query text.
            limit: Maximum number of results to return (default: server config max).

        Returns:
            Dictionary containing matching frames and their scores.

        Example:
            search_memory("my_memory.mv2", "project planning discussions", limit=5)
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            if not memory_path.exists():
                raise FileNotFoundError(f"Memory file not found: {memory_path}")

            if limit is None:
                limit = config.max_search_results

            logger.info(f"Searching memory {memory_path} for: {query}")
            
            memory = MemvidMemory.open(str(memory_path))
            results = memory.search(query, limit=limit)

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "frame_index": result.get("index", 0),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                })

            logger.info(f"Found {len(formatted_results)} results")
            return {
                "status": "success",
                "results": formatted_results,
                "count": len(formatted_results),
                "query": query,
            }

        except Exception as e:
            logger.error(f"Failed to search memory: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to search memory: {str(e)}",
            }

    @mcp.tool()
    def list_frames(path: str, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        List frames from a Memvid memory file with pagination.

        Args:
            path: Path to the .mv2 memory file.
            offset: Starting index for pagination (default: 0).
            limit: Number of frames to return (default: 10).

        Returns:
            Dictionary containing frames and pagination info.

        Example:
            list_frames("my_memory.mv2", offset=0, limit=20)
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            if not memory_path.exists():
                raise FileNotFoundError(f"Memory file not found: {memory_path}")

            logger.info(f"Listing frames from {memory_path} (offset={offset}, limit={limit})")
            
            memory = MemvidMemory.open(str(memory_path))
            
            # Get total count
            total_count = memory.len()
            
            # Get frames in range
            frames = []
            for i in range(offset, min(offset + limit, total_count)):
                try:
                    frame_text = memory.get_frame(i)
                    frames.append({
                        "index": i,
                        "text": frame_text,
                    })
                except Exception as e:
                    logger.warning(f"Failed to get frame {i}: {e}")
                    continue

            logger.info(f"Retrieved {len(frames)} frames")
            return {
                "status": "success",
                "frames": frames,
                "count": len(frames),
                "total": total_count,
                "offset": offset,
                "limit": limit,
            }

        except Exception as e:
            logger.error(f"Failed to list frames: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to list frames: {str(e)}",
            }

    @mcp.tool()
    def export_memory(path: str, output_format: str = "json") -> Dict[str, Any]:
        """
        Export all frames from a Memvid memory file.

        Args:
            path: Path to the .mv2 memory file.
            output_format: Format for export (json, text, csv). Default: json.

        Returns:
            Dictionary containing exported data in requested format.

        Example:
            export_memory("my_memory.mv2", "json")
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            if not memory_path.exists():
                raise FileNotFoundError(f"Memory file not found: {memory_path}")

            logger.info(f"Exporting memory from {memory_path} as {output_format}")
            
            memory = MemvidMemory.open(str(memory_path))
            total_count = memory.len()
            
            # Collect all frames
            frames = []
            for i in range(total_count):
                try:
                    frame_text = memory.get_frame(i)
                    frames.append({
                        "index": i,
                        "text": frame_text,
                    })
                except Exception as e:
                    logger.warning(f"Failed to get frame {i}: {e}")
                    continue

            # Format based on requested type
            if output_format.lower() == "json":
                export_data = frames
            elif output_format.lower() == "text":
                export_data = "\n\n".join(
                    f"[Frame {f['index']}]\n{f['text']}" for f in frames
                )
            elif output_format.lower() == "csv":
                csv_lines = ["index,text"]
                for f in frames:
                    # Simple CSV escaping
                    text = f['text'].replace('"', '""')
                    csv_lines.append(f"{f['index']},\"{text}\"")
                export_data = "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported format: {output_format}")

            logger.info(f"Exported {len(frames)} frames")
            return {
                "status": "success",
                "data": export_data,
                "format": output_format,
                "count": len(frames),
            }

        except Exception as e:
            logger.error(f"Failed to export memory: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to export memory: {str(e)}",
            }

    @mcp.tool()
    def commit_memory(path: str) -> Dict[str, Any]:
        """
        Commit pending changes to a Memvid memory file.

        This ensures all appended frames are persisted to disk.

        Args:
            path: Path to the .mv2 memory file.

        Returns:
            Dictionary containing commit status.

        Example:
            commit_memory("my_memory.mv2")
        """
        try:
            # Resolve path
            memory_path = Path(path)
            if not memory_path.is_absolute():
                memory_path = config.default_memory_dir / memory_path

            if not memory_path.exists():
                raise FileNotFoundError(f"Memory file not found: {memory_path}")

            logger.info(f"Committing changes to {memory_path}")
            
            memory = MemvidMemory.open(str(memory_path))
            memory.commit()

            logger.info(f"Successfully committed {memory_path}")
            return {
                "status": "success",
                "message": f"Committed changes to {memory_path}",
                "path": str(memory_path),
            }

        except Exception as e:
            logger.error(f"Failed to commit memory: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to commit memory: {str(e)}",
            }

    logger.info("Memvid MCP server initialized with all tools")
    return mcp
