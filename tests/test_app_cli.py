"""Tests for CLI application (app.py).

Tests individual command functions from the main CLI application.
Focus on business logic rather than interactive menu flows.
"""

import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.apps import app
from secure_password_manager.utils.crypto import encrypt_password
from secure_password_manager.utils.database import add_password, get_passwords, init_db


@pytest.fixture
def setup_test_passwords(isolated_environment):
    """Set up test database with sample passwords."""
    import sqlite3
    from secure_password_manager.utils.paths import get_database_path

    init_db()

    # Directly create password_history table in the test database
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_id INTEGER NOT NULL,
            old_password BLOB NOT NULL,
            changed_at INTEGER NOT NULL,
            rotation_reason TEXT DEFAULT 'manual',
            changed_by TEXT DEFAULT 'user',
            FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

    encrypted_pw1 = encrypt_password("Password123!")
    encrypted_pw2 = encrypt_password("SecurePass456!")
    encrypted_pw3 = encrypt_password("MyPassword789!")

    add_password("example.com", "user@example.com", encrypted_pw1, "Work", "Test note 1")
    add_password("github.com", "developer@github.com", encrypted_pw2, "Development", "Test note 2")
    add_password("google.com", "personal@gmail.com", encrypted_pw3, "Personal", "Test note 3")

    return isolated_environment


# Test helper functions


def test_get_browser_bridge_settings(isolated_environment):
    """Test retrieving browser bridge settings."""
    from secure_password_manager.apps.app import _get_browser_bridge_settings
    from secure_password_manager.utils import config

    # Save test settings
    config.update_settings({"browser_bridge": {"enabled": True, "port": 43110}})

    settings = _get_browser_bridge_settings()

    assert settings is not None
    assert "enabled" in settings
    assert settings["enabled"] is True


def test_sync_browser_bridge_with_settings_enabled(isolated_environment):
    """Test syncing browser bridge when enabled in settings."""
    from secure_password_manager.apps.app import sync_browser_bridge_with_settings
    from secure_password_manager.utils import config

    config.update_settings({"browser_bridge": {"enabled": True}})

    with patch("secure_password_manager.apps.app.get_browser_bridge_service") as mock_service:
        mock_bridge = MagicMock()
        mock_bridge.is_running = False
        mock_service.return_value = mock_bridge

        sync_browser_bridge_with_settings()

        mock_bridge.start.assert_called_once()


def test_sync_browser_bridge_with_settings_disabled(isolated_environment):
    """Test syncing browser bridge when disabled in settings."""
    from secure_password_manager.apps.app import sync_browser_bridge_with_settings
    from secure_password_manager.utils import config

    config.update_settings({"browser_bridge": {"enabled": False}})

    with patch("secure_password_manager.apps.app.get_browser_bridge_service") as mock_service:
        mock_bridge = MagicMock()
        mock_bridge.is_running = True
        mock_service.return_value = mock_bridge

        sync_browser_bridge_with_settings()

        mock_bridge.stop.assert_called_once()


def test_shutdown_browser_bridge(isolated_environment):
    """Test shutting down browser bridge service."""
    from secure_password_manager.apps.app import shutdown_browser_bridge

    with patch("secure_password_manager.apps.app.get_browser_bridge_service") as mock_service:
        mock_bridge = MagicMock()
        mock_service.return_value = mock_bridge

        shutdown_browser_bridge()

        mock_bridge.stop.assert_called_once()


# Test password management functions


@patch("builtins.input")
@patch("getpass.getpass")
def test_add_new_password_basic(mock_getpass, mock_input, setup_test_passwords):
    """Test adding a new password with basic inputs."""
    from secure_password_manager.apps.app import add_new_password

    # Mock user inputs - password comes from input, not getpass!
    mock_input.side_effect = [
        "newsite.com",              # website
        "user@newsite.com",          # username
        "n",                        # don't generate password
        "X9z!Qw@3pL#7mK$5nV",     # password (very strong - 18 chars, all types)
        "General",                  # category
        "Test note",                # notes
        "",                          # no expiry days
    ]

    add_new_password()

    # Verify password was added
    passwords = get_passwords()
    assert len(passwords) == 4  # 3 from fixture + 1 new
    assert any(p[1] == "newsite.com" for p in passwords)


@patch("builtins.input")
@patch("getpass.getpass")
def test_add_new_password_with_generated(mock_getpass, mock_input, setup_test_passwords):
    """Test adding a password with generated password."""
    from secure_password_manager.apps.app import add_new_password

    mock_input.side_effect = [
        "testgen.com",      # website
        "user@test.com",    # username
        "y",                # generate password
        "",                 # use default length
        "",                 # include special chars (default: y)
        "n",                # don't copy to clipboard
        "General",          # category
        "",                 # no notes
        "",                 # no expiry days
    ]

    add_new_password()

    passwords = get_passwords()
    assert len(passwords) == 4
    assert any(p[1] == "testgen.com" for p in passwords)


@patch("builtins.input")
def test_search_passwords_found(mock_input, setup_test_passwords, capsys):
    """Test searching for passwords with results."""
    from secure_password_manager.apps.app import search_passwords

    mock_input.return_value = "github"

    search_passwords()

    captured = capsys.readouterr()
    assert "github.com" in captured.out
    assert "developer@github.com" in captured.out


@patch("builtins.input")
def test_search_passwords_not_found(mock_input, setup_test_passwords, capsys):
    """Test searching for passwords with no results."""
    from secure_password_manager.apps.app import search_passwords

    mock_input.return_value = "nonexistent"

    search_passwords()

    captured = capsys.readouterr()
    assert "No passwords found" in captured.out or "0" in captured.out


@patch("builtins.input")
def test_view_passwords_all(mock_input, setup_test_passwords, capsys):
    """Test viewing all passwords."""
    from secure_password_manager.apps.app import view_passwords

    mock_input.return_value = ""  # View all

    view_passwords()

    captured = capsys.readouterr()
    assert "example.com" in captured.out
    assert "github.com" in captured.out
    assert "google.com" in captured.out


@patch("builtins.input")
def test_view_passwords_by_category(mock_input, setup_test_passwords, capsys):
    """Test viewing passwords filtered by category."""
    from secure_password_manager.apps.app import view_passwords

    mock_input.return_value = "Work"

    view_passwords(category="Work")

    captured = capsys.readouterr()
    assert "example.com" in captured.out


@patch("builtins.input")
def test_delete_password_entry_success(mock_input, setup_test_passwords, capsys):
    """Test deleting a password entry."""
    from secure_password_manager.apps.app import delete_password_entry

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.side_effect = [str(password_id), "y"]  # ID and confirmation

    delete_password_entry()

    # Verify deletion
    passwords_after = get_passwords()
    assert len(passwords_after) == 2  # 3 - 1 = 2


@patch("builtins.input")
def test_delete_password_entry_cancel(mock_input, setup_test_passwords):
    """Test canceling password deletion."""
    from secure_password_manager.apps.app import delete_password_entry

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.side_effect = [str(password_id), "n"]  # ID and cancel

    delete_password_entry()

    # Verify no deletion
    passwords_after = get_passwords()
    assert len(passwords_after) == 3


@patch("builtins.input")
def test_delete_password_entry_invalid_id(mock_input, setup_test_passwords, capsys):
    """Test deleting with invalid password ID."""
    from secure_password_manager.apps.app import delete_password_entry

    mock_input.return_value = "99999"  # Non-existent ID

    delete_password_entry()

    captured = capsys.readouterr()
    assert "no password found" in captured.out.lower() or "invalid" in captured.out.lower()


@patch("builtins.input")
@patch("getpass.getpass")
def test_edit_password_change_website(mock_getpass, mock_input, setup_test_passwords):
    """Test editing password - changing website."""
    from secure_password_manager.apps.app import edit_password

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.side_effect = [
        str(password_id),    # password ID
        "newdomain.com",     # new website
        "",                  # keep username
        "n",                 # don't change password
        "",                  # keep category
        "",                  # keep notes
        "",                  # keep expiry
        "",                  # keep favorite
    ]

    edit_password()

    # Verify update
    passwords = get_passwords()
    updated = [p for p in passwords if p[0] == password_id][0]
    assert updated[1] == "newdomain.com"


@patch("builtins.input")
@patch("getpass.getpass")
def test_edit_password_change_username(mock_getpass, mock_input, setup_test_passwords):
    """Test editing password - changing username."""
    from secure_password_manager.apps.app import edit_password

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.side_effect = [
        str(password_id),        # password ID
        "",                      # keep website
        "newemail@example.com",  # new username
        "n",                     # don't change password
        "",                      # keep category
        "",                      # keep notes
        "",                      # keep expiry
        "",                      # keep favorite
    ]

    edit_password()

    passwords = get_passwords()
    updated = [p for p in passwords if p[0] == password_id][0]
    assert updated[2] == "newemail@example.com"


@patch("builtins.input")
@patch("getpass.getpass")
def test_edit_password_change_password(mock_getpass, mock_input, setup_test_passwords):
    """Test editing password - changing password itself."""
    from secure_password_manager.apps.app import edit_password
    from secure_password_manager.utils.crypto import decrypt_password

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.side_effect = [
        str(password_id),              # password ID
        "",                            # keep website
        "",                            # keep username
        "y",                           # change password
        "n",                           # don't generate
        "R7x!Tm@9vP#2nB$6qW",        # new password (very strong)
        "",                            # keep category
        "",                            # keep notes
        "",                            # keep expiry
        "",                            # keep favorite
        "",                            # rotation reason (default: manual)
    ]

    edit_password()

    passwords = get_passwords()
    updated = [p for p in passwords if p[0] == password_id][0]
    decrypted = decrypt_password(updated[3])
    assert decrypted == "R7x!Tm@9vP#2nB$6qW"


# Test password generator


@patch("builtins.input")
def test_generate_password_tool_default(mock_input, isolated_environment, capsys):
    """Test password generator with default settings."""
    from secure_password_manager.apps.app import generate_password_tool

    mock_input.side_effect = [
        "",    # default length
        "",    # include special chars (default: y)
        "n"    # don't save
    ]

    generate_password_tool()

    captured = capsys.readouterr()
    assert "generated password:" in captured.out.lower() or "password:" in captured.out.lower()


@patch("builtins.input")
def test_generate_password_tool_custom_length(mock_input, isolated_environment, capsys):
    """Test password generator with custom length."""
    from secure_password_manager.apps.app import generate_password_tool

    mock_input.side_effect = [
        "24",  # custom length
        "",    # include special chars (default: y)
        "n"    # don't save
    ]

    generate_password_tool()

    captured = capsys.readouterr()
    # Should generate a password
    assert "Password:" in captured.out or "Generated" in captured.out


# Test password expiry


@patch("builtins.input")
def test_check_expiring_passwords_none(mock_input, setup_test_passwords, capsys):
    """Test checking expiring passwords when none are expiring."""
    from secure_password_manager.apps.app import check_expiring_passwords

    mock_input.return_value = ""  # Mock any input prompts

    check_expiring_passwords()

    captured = capsys.readouterr()
    # Should show no expiring passwords
    assert "password" in captured.out.lower()


# Test backup functions


@patch("builtins.input")
def test_export_passwords_menu_success(mock_input, setup_test_passwords, tmp_path, capsys):
    """Test exporting passwords."""
    from secure_password_manager.apps.app import export_passwords_menu

    export_file = tmp_path / "export.dat"
    mock_input.side_effect = [
        str(export_file),      # filename
        "MyExportPassword",   # master password
        "",                    # include notes (default: y)
    ]

    export_passwords_menu()

    captured = capsys.readouterr()
    assert "Success" in captured.out or "exported" in captured.out.lower()
    assert export_file.exists()


@patch("builtins.input")
def test_import_passwords_menu_success(mock_input, setup_test_passwords, tmp_path, capsys):
    """Test importing passwords."""
    from secure_password_manager.apps.app import export_passwords_menu, import_passwords_menu

    # First export
    export_file = tmp_path / "export.dat"
    mock_input.side_effect = [
        str(export_file),    # filename
        "MyPassword",        # master password
        "",                  # include notes (default: y)
    ]
    export_passwords_menu()

    # Clear database
    from secure_password_manager.utils.database import delete_password
    for pwd in get_passwords():
        delete_password(pwd[0])

    # Then import
    mock_input.side_effect = [
        str(export_file),   # filename
        "MyPassword",       # master password
    ]
    import_passwords_menu()

    captured = capsys.readouterr()
    assert "Success" in captured.out or "imported" in captured.out.lower()


@patch("builtins.input")
def test_full_backup_menu(mock_input, setup_test_passwords, tmp_path, capsys):
    """Test creating full backup."""
    from secure_password_manager.apps.app import full_backup_menu

    backup_file = tmp_path / "backup.enc"
    mock_input.side_effect = [str(backup_file), "BackupPassword123"]

    full_backup_menu()

    captured = capsys.readouterr()
    assert "Success" in captured.out or "backup" in captured.out.lower()


# Test security audit


@patch("builtins.input")
def test_security_audit_menu_run_audit(mock_input, setup_test_passwords, capsys):
    """Test running security audit."""
    from secure_password_manager.apps.app import security_audit_menu

    mock_input.side_effect = [
        "1",   # Run audit
        "n",   # Don't view details
        "",    # Press Enter to continue
        "0"    # Exit
    ]

    with patch("secure_password_manager.apps.app.run_security_audit") as mock_audit:
        mock_audit.return_value = {
            "issues": {
                "weak_passwords": [],
                "reused_passwords": [],
                "breached_passwords": [],
                "duplicate_passwords": [],
                "expired_passwords": []
            },
            "score": 85,
            "total_passwords": 3
        }
        security_audit_menu()

        mock_audit.assert_called()


# Test logging


@patch("builtins.input")
def test_view_logs(mock_input, isolated_environment, capsys):
    """Test viewing application logs."""
    from secure_password_manager.apps.app import view_logs
    from secure_password_manager.utils.logger import log_info

    # Create some log entries
    log_info("Test log entry 1")
    log_info("Test log entry 2")

    mock_input.return_value = ""  # Mock any input prompts

    view_logs()

    captured = capsys.readouterr()
    assert "log" in captured.out.lower() or "Test log entry" in captured.out


# Test categories


@patch("builtins.input")
def test_categories_menu_add_category(mock_input, isolated_environment, capsys):
    """Test adding a new category."""
    from secure_password_manager.apps.app import categories_menu

    mock_input.side_effect = [
        "2",              # Add new category (option 2)
        "New Category",   # name
        "",               # color (default: blue)
    ]

    categories_menu()

    from secure_password_manager.utils.database import get_categories
    categories = get_categories()
    assert any(c[0] == "New Category" for c in categories)


@patch("builtins.input")
def test_categories_menu_view_categories(mock_input, isolated_environment, capsys):
    """Test viewing categories."""
    from secure_password_manager.apps.app import categories_menu
    from secure_password_manager.utils.database import add_category

    # Add test categories
    add_category("Test Category 1")
    add_category("Test Category 2")

    # Just display the categories menu
    mock_input.side_effect = ["0"]  # Exit immediately after viewing

    categories_menu()

    captured = capsys.readouterr()
    # Should show the categories in the menu display
    assert "Test Category 1" in captured.out or "Test Category 2" in captured.out or "category" in captured.out.lower()


# Test password history


@patch("builtins.input")
def test_view_password_history_entry(mock_input, setup_test_passwords, capsys):
    """Test viewing password history for an entry."""
    from secure_password_manager.apps.app import view_password_history_entry

    passwords = get_passwords()
    password_id = passwords[0][0]

    mock_input.return_value = str(password_id)

    view_password_history_entry()

    captured = capsys.readouterr()
    # Should show history or no history message
    assert "history" in captured.out.lower() or "no" in captured.out.lower() or str(password_id) in captured.out


# Test main menu functions


def test_main_menu_structure(isolated_environment, capsys):
    """Test that main menu displays correctly."""
    from secure_password_manager.apps.app import main_menu

    with patch("builtins.input", return_value="0"):  # Exit immediately
        main_menu()

    captured = capsys.readouterr()
    assert "Password" in captured.out or "Menu" in captured.out


def test_passwords_menu_structure(isolated_environment, capsys):
    """Test that passwords menu displays correctly."""
    from secure_password_manager.apps.app import passwords_menu

    with patch("builtins.input", return_value="0"):  # Exit immediately
        passwords_menu()

    captured = capsys.readouterr()
    assert "Password" in captured.out or "Menu" in captured.out


def test_backup_menu_structure(isolated_environment, capsys):
    """Test that backup menu displays correctly."""
    from secure_password_manager.apps.app import backup_menu

    with patch("builtins.input", return_value="0"):  # Exit immediately
        backup_menu()

    captured = capsys.readouterr()
    assert "Backup" in captured.out or "Menu" in captured.out


# Integration tests


@patch("builtins.input")
@patch("getpass.getpass")
def test_add_search_delete_workflow(mock_getpass, mock_input, isolated_environment):
    """Test complete workflow: add, search, delete password."""
    from secure_password_manager.apps.app import (
        add_new_password,
        delete_password_entry,
        search_passwords,
    )

    init_db()

    # Add password
    mock_input.side_effect = [
        "workflow.com",
        "user@workflow.com",
        "n",                       # don't generate
        "K5m!Zx@8rT#1pQ$9wN",     # password (very strong)
        "General",
        "",                         # no notes
        "",                         # no expiry
    ]
    add_new_password()

    # Search for it (search_passwords calls view_passwords which asks for show_expired)
    mock_input.side_effect = [
        "workflow",                 # search term
        "",                         # show expired (default: y)
        "q",                        # quit from view options
    ]
    search_passwords()

    # Verify it exists
    passwords = get_passwords()
    assert any(p[1] == "workflow.com" for p in passwords)
    password_id = [p[0] for p in passwords if p[1] == "workflow.com"][0]

    # Delete it
    mock_input.side_effect = [str(password_id), "y"]
    delete_password_entry()

    # Verify deletion
    passwords = get_passwords()
    assert not any(p[1] == "workflow.com" for p in passwords)


@patch("builtins.input")
@patch("getpass.getpass")
def test_add_edit_workflow(mock_getpass, mock_input, isolated_environment):
    """Test workflow: add password, then edit it."""
    from secure_password_manager.apps.app import add_new_password, edit_password

    init_db()

    # Add password
    mock_input.side_effect = [
        "editme.com",
        "original@user.com",
        "n",                       # don't generate
        "F3v!Hx@7wS#4mL$2bC",     # password (very strong)
        "General",
        "",                         # no notes
        "",                         # no expiry
    ]
    add_new_password()

    passwords = get_passwords()
    assert len(passwords) > 0, "No passwords found after adding"
    password_id = passwords[0][0]

    # Edit username
    mock_input.side_effect = [
        str(password_id),
        "",                      # keep website
        "updated@user.com",     # new username
        "n",                     # don't change password
        "",                      # keep category
        "",                      # keep notes
        "",                      # keep expiry
        "",                      # keep favorite
    ]
    edit_password()

    # Verify edit
    passwords = get_passwords()
    assert len(passwords) > 0, "No passwords found after editing"
    updated = passwords[0]
    assert updated[2] == "updated@user.com"
