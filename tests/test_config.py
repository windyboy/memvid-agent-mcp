"""Tests for server configuration."""

import os
from pathlib import Path

import pytest

from memvid_agent_mcp.config import ServerConfig


def test_default_config():
    """Test default configuration values."""
    config = ServerConfig()
    assert config.log_level == "INFO"
    assert config.default_memory_dir == Path.home() / ".memvid"
    assert config.max_search_results == 10
    assert config.embedding_model is None


def test_config_from_env(monkeypatch, tmp_path):
    """Test configuration from environment variables."""
    monkeypatch.setenv("MEMVID_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MEMVID_MEMORY_DIR", str(tmp_path))
    monkeypatch.setenv("MEMVID_MAX_SEARCH_RESULTS", "20")
    monkeypatch.setenv("MEMVID_EMBEDDING_MODEL", "custom-model")

    config = ServerConfig.from_env()
    assert config.log_level == "DEBUG"
    assert config.default_memory_dir == tmp_path
    assert config.max_search_results == 20
    assert config.embedding_model == "custom-model"


def test_config_from_env_defaults(monkeypatch):
    """Test configuration with default values when env vars not set."""
    # Clear relevant env vars
    for key in ["MEMVID_LOG_LEVEL", "MEMVID_MEMORY_DIR", "MEMVID_MAX_SEARCH_RESULTS", "MEMVID_EMBEDDING_MODEL"]:
        monkeypatch.delenv(key, raising=False)

    config = ServerConfig.from_env()
    assert config.log_level == "INFO"
    assert config.default_memory_dir == Path.home() / ".memvid"
    assert config.max_search_results == 10
    assert config.embedding_model is None


def test_setup_logging(test_config):
    """Test logging setup."""
    test_config.setup_logging()
    # If this doesn't raise, logging is configured correctly
    import logging
    logger = logging.getLogger("test")
    logger.info("Test message")
