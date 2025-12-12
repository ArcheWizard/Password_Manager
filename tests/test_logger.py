"""Tests for logger module."""

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import logger
from secure_password_manager.utils.logger import (
    clear_logs,
    get_log_entries,
    log_debug,
    log_error,
    log_info,
    log_warning,
)


@pytest.fixture
def temp_log_file(tmp_path, monkeypatch):
    """Create a temporary log file for testing."""

    log_dir = tmp_path

    # Reset logger initialization state
    monkeypatch.setattr(logger, "_initialized", False)
    monkeypatch.setattr(logger, "LOG_FILE", None)
    monkeypatch.setattr(logger, "LOG_DIR", None)

    # Mock get_log_dir to return test directory
    monkeypatch.setattr("secure_password_manager.utils.logger.get_log_dir", lambda: log_dir)

    # Clear existing handlers
    logger.logger.handlers.clear()

    # Force re-initialization with test paths
    logger._ensure_logger_initialized()

    # Return the actual log file path that will be created
    return tmp_path / "password_manager.log"


def test_log_info(temp_log_file):
    """Test info logging."""
    log_info("Test info message")

    # Check log file exists
    assert temp_log_file.exists()

    # Check message was logged
    content = temp_log_file.read_text()
    assert "Test info message" in content
    assert "INFO" in content


def test_log_error(temp_log_file):
    """Test error logging."""
    log_error("Test error message")

    content = temp_log_file.read_text()
    assert "Test error message" in content
    assert "ERROR" in content


def test_log_warning(temp_log_file):
    """Test warning logging."""
    log_warning("Test warning message")

    content = temp_log_file.read_text()
    assert "Test warning message" in content
    assert "WARNING" in content


def test_log_debug(temp_log_file):
    """Test debug logging."""
    log_debug("Test debug message")

    # Debug messages may not appear depending on log level
    # Just verify function executes without error


def test_get_log_entries_empty(temp_log_file):
    """Test get_log_entries with empty log."""
    entries = get_log_entries()
    assert entries == []


def test_get_log_entries_with_content(temp_log_file):
    """Test get_log_entries with log content."""
    # Write some log messages
    log_info("Message 1")
    log_info("Message 2")
    log_info("Message 3")

    entries = get_log_entries(count=10)

    assert len(entries) >= 3
    assert any("Message 1" in entry for entry in entries)
    assert any("Message 2" in entry for entry in entries)
    assert any("Message 3" in entry for entry in entries)


def test_get_log_entries_count_limit(temp_log_file):
    """Test get_log_entries respects count limit."""
    # Write many messages
    for i in range(100):
        log_info(f"Message {i}")

    entries = get_log_entries(count=10)
    assert len(entries) == 10


def test_get_log_entries_nonexistent_file(tmp_path, monkeypatch):
    """Test get_log_entries with non-existent log file."""
    nonexistent = tmp_path / "nonexistent.log"

    # Reset logger state
    monkeypatch.setattr(logger, "_initialized", False)
    monkeypatch.setattr(logger, "LOG_FILE", None)
    monkeypatch.setattr(logger, "LOG_DIR", None)

    # Mock get_log_dir to return tmp_path (where nonexistent.log would be)
    monkeypatch.setattr("secure_password_manager.utils.logger.get_log_dir", lambda: tmp_path)

    # Clear handlers to force reinitialization
    logger.logger.handlers.clear()

    # Now when get_log_entries() is called, it will initialize with our mocked path
    # and look for password_manager.log in tmp_path (which doesn't exist)
    entries = get_log_entries()
    assert entries == []


def test_clear_logs_with_backup(temp_log_file):
    """Test clearing logs with backup."""
    # Write some content
    log_info("Test message")
    assert temp_log_file.exists()

    result = clear_logs(backup=True)

    assert result is True
    # Original file should be renamed
    assert not temp_log_file.exists()
    # Backup file should exist
    backup_files = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*"))
    assert len(backup_files) > 0


def test_clear_logs_without_backup(temp_log_file):
    """Test clearing logs without backup."""
    log_info("Test message")
    assert temp_log_file.exists()

    result = clear_logs(backup=False)

    assert result is True
    assert not temp_log_file.exists()


def test_clear_logs_nonexistent_file(tmp_path, monkeypatch):
    """Test clearing non-existent log file."""
    nonexistent = tmp_path / "nonexistent.log"
    monkeypatch.setattr(logger, "LOG_FILE", str(nonexistent))

    result = clear_logs()
    assert result is True


@patch("os.rename")
def test_clear_logs_handles_error(mock_rename, temp_log_file):
    """Test clear_logs handles errors gracefully."""
    log_info("Test message")

    # Make rename fail
    mock_rename.side_effect = OSError("Permission denied")

    result = clear_logs(backup=True)
    assert result is False


def test_multiple_log_calls(temp_log_file):
    """Test multiple logging calls."""
    log_info("Info 1")
    log_error("Error 1")
    log_warning("Warning 1")
    log_info("Info 2")

    content = temp_log_file.read_text()
    assert "Info 1" in content
    assert "Error 1" in content
    assert "Warning 1" in content
    assert "Info 2" in content


def test_log_entries_preserve_order(temp_log_file):
    """Test that log entries maintain order."""
    messages = [f"Message {i}" for i in range(10)]
    for msg in messages:
        log_info(msg)

    entries = get_log_entries(count=20)
    entry_text = "".join(entries)

    # Verify messages appear in order
    for i in range(9):
        msg_current = f"Message {i}"
        msg_next = f"Message {i+1}"
        assert entry_text.find(msg_current) < entry_text.find(msg_next)


def test_log_file_created_in_correct_directory(tmp_path, monkeypatch):
    """Test that log file is created in log directory."""
    # Patch get_log_dir before resetting logger
    monkeypatch.setattr("secure_password_manager.utils.logger.get_log_dir", lambda: tmp_path)

    # Reset logger to force reinitialization with patched path
    logger.reset_logger()

    log_info("Test message")

    # Check log file exists in temp directory
    log_file = tmp_path / "password_manager.log"
    assert log_file.exists()
