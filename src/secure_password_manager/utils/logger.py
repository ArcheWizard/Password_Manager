"""Logging utilities for password manager."""

import logging
import os
import time
from typing import Optional

from secure_password_manager.utils.paths import get_log_dir

# Lazy initialization variables
LOG_DIR: Optional[str] = None
LOG_FILE: Optional[str] = None
_initialized = False

logger = logging.getLogger("password_manager")


def _ensure_logger_initialized() -> None:
    """Ensure logger is initialized with proper paths."""
    global LOG_DIR, LOG_FILE, _initialized

    if _initialized:
        return

    LOG_DIR = str(get_log_dir())
    LOG_FILE = os.path.join(LOG_DIR, "password_manager.log")

    # Configure logger only once
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

    _initialized = True


def log_info(message: str) -> None:
    """Log an informational message."""
    _ensure_logger_initialized()
    logger.info(message)


def log_error(message: str) -> None:
    """Log an error message."""
    _ensure_logger_initialized()
    logger.error(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    _ensure_logger_initialized()
    logger.warning(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    _ensure_logger_initialized()
    logger.debug(message)


def get_log_entries(count: int = 50) -> list:
    """Get the most recent log entries."""
    _ensure_logger_initialized()
    entries = []
    assert LOG_FILE is not None

    if not os.path.exists(LOG_FILE):
        return entries

    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()

        # Get the last 'count' lines
        return lines[-count:]
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return entries


def clear_logs(backup: bool = True) -> bool:
    """Clear logs with optional backup."""
    _ensure_logger_initialized()
    assert LOG_FILE is not None
    if not os.path.exists(LOG_FILE):
        return True

    try:
        if backup:
            timestamp = int(time.time())
            backup_file = f"{LOG_FILE}.{timestamp}"
            os.rename(LOG_FILE, backup_file)
        else:
            os.remove(LOG_FILE)

        return True
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return False


def reset_logger() -> None:
    """Reset logger state for testing purposes."""
    global LOG_DIR, LOG_FILE, _initialized

    LOG_DIR = None
    LOG_FILE = None
    _initialized = False

    # Remove all handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
