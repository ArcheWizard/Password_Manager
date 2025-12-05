"""Clipboard management with auto-clear functionality.

This module provides secure clipboard operations with automatic clearing after a
configurable timeout to prevent sensitive data from remaining in the clipboard.
"""

from __future__ import annotations

import threading
from typing import Optional

import pyperclip

from secure_password_manager.utils import config
from secure_password_manager.utils.logger import log_info


class ClipboardManager:
    """Manages clipboard operations with automatic clearing."""

    def __init__(self) -> None:
        self._clear_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def copy(self, text: str, auto_clear: bool = True) -> None:
        """
        Copy text to clipboard with optional auto-clear.

        Args:
            text: The text to copy to clipboard.
            auto_clear: Whether to automatically clear the clipboard after timeout.
        """
        # Cancel any existing timer
        self._cancel_timer()

        # Copy to clipboard
        pyperclip.copy(text)
        log_info("Content copied to clipboard")

        # Schedule auto-clear if enabled
        if auto_clear:
            clear_seconds = config.get_setting("clipboard.auto_clear_seconds", 25)
            if clear_seconds > 0:
                self._schedule_clear(clear_seconds)

    def _schedule_clear(self, seconds: int) -> None:
        """Schedule clipboard clearing after specified seconds."""
        with self._lock:
            self._clear_timer = threading.Timer(seconds, self._clear_clipboard)
            self._clear_timer.daemon = True
            self._clear_timer.start()
            log_info(f"Clipboard will auto-clear in {seconds} seconds")

    def _clear_clipboard(self) -> None:
        """Clear the clipboard contents."""
        try:
            pyperclip.copy("")
            log_info("Clipboard cleared automatically")
        except Exception as e:
            log_info(f"Failed to clear clipboard: {e}")

    def _cancel_timer(self) -> None:
        """Cancel any pending clear timer."""
        with self._lock:
            if self._clear_timer and self._clear_timer.is_alive():
                self._clear_timer.cancel()
                self._clear_timer = None

    def clear_now(self) -> None:
        """Immediately clear the clipboard and cancel any pending timers."""
        self._cancel_timer()
        self._clear_clipboard()

    def __del__(self) -> None:
        """Cleanup: cancel timer on deletion."""
        self._cancel_timer()


# Global clipboard manager instance
_clipboard_manager: Optional[ClipboardManager] = None


def get_clipboard_manager() -> ClipboardManager:
    """Get or create the global clipboard manager instance."""
    global _clipboard_manager
    if _clipboard_manager is None:
        _clipboard_manager = ClipboardManager()
    return _clipboard_manager


def copy_to_clipboard(text: str, auto_clear: bool = True) -> None:
    """
    Convenience function to copy text to clipboard with auto-clear.

    Args:
        text: The text to copy.
        auto_clear: Whether to automatically clear after timeout (default: True).
    """
    manager = get_clipboard_manager()
    manager.copy(text, auto_clear=auto_clear)


def clear_clipboard() -> None:
    """Convenience function to immediately clear the clipboard."""
    manager = get_clipboard_manager()
    manager.clear_now()
