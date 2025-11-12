"""Logging utilities for password manager."""

import logging
import os
import time

from secure_password_manager.utils.paths import get_log_dir

# Setup logging
LOG_DIR = str(get_log_dir())
LOG_FILE = os.path.join(LOG_DIR, "password_manager.log")

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

logger = logging.getLogger("password_manager")


def log_info(message: str) -> None:
    """Log an informational message."""
    logger.info(message)


def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)


def get_log_entries(count: int = 50) -> list:
    """Get the most recent log entries."""
    entries = []

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
