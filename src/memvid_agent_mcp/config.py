"""
Configuration management for Memvid MCP server.

Handles environment variables and server configuration.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Configuration for the Memvid MCP server."""

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    default_memory_dir: Path = Field(
        default_factory=lambda: Path.home() / ".memvid",
        description="Default directory for storing .mv2 memory files",
    )
    max_search_results: int = Field(
        default=10,
        description="Maximum number of search results to return",
    )
    embedding_model: Optional[str] = Field(
        default=None,
        description="Optional embedding model override",
    )

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        log_level = os.getenv("MEMVID_LOG_LEVEL", "INFO").upper()
        
        memory_dir_str = os.getenv("MEMVID_MEMORY_DIR")
        memory_dir = Path(memory_dir_str) if memory_dir_str else Path.home() / ".memvid"
        
        max_results = int(os.getenv("MEMVID_MAX_SEARCH_RESULTS", "10"))
        embedding_model = os.getenv("MEMVID_EMBEDDING_MODEL")

        return cls(
            log_level=log_level,
            default_memory_dir=memory_dir,
            max_search_results=max_results,
            embedding_model=embedding_model,
        )

    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
