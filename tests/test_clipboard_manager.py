"""Tests for clipboard_manager module."""

import time
from unittest.mock import MagicMock, patch

import pytest

from secure_password_manager.utils.clipboard_manager import (
    ClipboardManager,
    clear_clipboard,
    copy_to_clipboard,
    get_clipboard_manager,
)


def test_clipboard_manager_copy_without_auto_clear():
    """Test copying to clipboard without auto-clear."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        manager.copy("test_password", auto_clear=False)
        mock_copy.assert_called_once_with("test_password")

    # Ensure no timer was scheduled
    assert manager._clear_timer is None


def test_clipboard_manager_copy_with_auto_clear():
    """Test copying to clipboard with auto-clear enabled."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=1):
            manager.copy("test_password", auto_clear=True)
            mock_copy.assert_called_once_with("test_password")

            # Verify timer was scheduled
            assert manager._clear_timer is not None
            assert manager._clear_timer.is_alive()

            # Wait for auto-clear
            time.sleep(1.5)

            # Verify clipboard was cleared
            assert mock_copy.call_count == 2
            mock_copy.assert_called_with("")


def test_clipboard_manager_multiple_copies_cancel_previous_timer():
    """Test that multiple copies cancel previous timers."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=2):
            # First copy
            manager.copy("password1", auto_clear=True)
            first_timer = manager._clear_timer
            assert first_timer is not None

            # Second copy should cancel first timer
            time.sleep(0.5)
            manager.copy("password2", auto_clear=True)
            second_timer = manager._clear_timer

            assert first_timer is not second_timer
            assert not first_timer.is_alive()
            assert second_timer.is_alive()


def test_clipboard_manager_clear_now():
    """Test immediate clipboard clearing."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=10):
            # Copy with auto-clear
            manager.copy("test_password", auto_clear=True)
            assert manager._clear_timer is not None

            # Clear immediately
            manager.clear_now()

            # Verify timer was canceled
            assert manager._clear_timer is None or not manager._clear_timer.is_alive()

            # Verify clipboard was cleared
            assert mock_copy.call_count == 2
            mock_copy.assert_called_with("")


def test_clipboard_manager_zero_clear_seconds_disables_auto_clear():
    """Test that setting clear_seconds to 0 disables auto-clear."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=0):
            manager.copy("test_password", auto_clear=True)

            # Only one copy call should have been made (no auto-clear)
            mock_copy.assert_called_once_with("test_password")
            assert manager._clear_timer is None


def test_clipboard_manager_handles_clear_errors():
    """Test that clipboard manager handles clearing errors gracefully."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        # First call succeeds, second call (clear) raises exception
        mock_copy.side_effect = [None, Exception("Clipboard access denied")]

        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=0.5):
            manager.copy("test_password", auto_clear=True)

            # Wait for auto-clear attempt
            time.sleep(1)

            # Should not raise exception
            assert mock_copy.call_count == 2


def test_global_clipboard_manager_singleton():
    """Test that get_clipboard_manager returns the same instance."""
    manager1 = get_clipboard_manager()
    manager2 = get_clipboard_manager()

    assert manager1 is manager2


def test_copy_to_clipboard_convenience_function():
    """Test the convenience function copy_to_clipboard."""
    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=1):
            copy_to_clipboard("test_password")

            mock_copy.assert_called_once_with("test_password")


def test_clear_clipboard_convenience_function():
    """Test the convenience function clear_clipboard."""
    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy") as mock_copy:
        clear_clipboard()

        mock_copy.assert_called_once_with("")


def test_clipboard_manager_thread_safety():
    """Test that clipboard manager operations are thread-safe."""
    manager = ClipboardManager()

    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy"):
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=2):
            import threading

            def copy_operation():
                manager.copy(f"password_{threading.current_thread().name}", auto_clear=True)
                time.sleep(0.1)
                manager.clear_now()

            threads = [threading.Thread(target=copy_operation) for _ in range(5)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # If we get here without deadlock, thread safety works
            assert True


def test_clipboard_manager_cleanup_on_deletion():
    """Test that clipboard manager cleans up timer on deletion."""
    with patch("secure_password_manager.utils.clipboard_manager.pyperclip.copy"):
        with patch("secure_password_manager.utils.clipboard_manager.config.get_setting", return_value=10):
            manager = ClipboardManager()
            manager.copy("test_password", auto_clear=True)

            timer = manager._clear_timer
            assert timer is not None
            assert timer.is_alive()

            # Delete manager (calls __del__)
            manager._cancel_timer()
            del manager

            # Timer should be canceled
            time.sleep(0.2)
            assert not timer.is_alive()
