"""Tests for interactive CLI components."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.interactive import (
    confirm_action,
    hidden_input,
    menu_selection,
)


@patch("getpass.getpass")
def test_hidden_input(mock_getpass):
    """Test hidden_input function."""
    mock_getpass.return_value = "secret_password"

    result = hidden_input("Enter password: ")

    assert result == "secret_password"
    mock_getpass.assert_called_once_with("Enter password: ")


@patch("builtins.input")
def test_menu_selection_valid_choice(mock_input):
    """Test menu_selection with valid choice."""
    mock_input.return_value = "1"

    options = [("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3")]
    result = menu_selection(options)

    assert result == "1"


@patch("builtins.input")
def test_menu_selection_custom_prompt(mock_input):
    """Test menu_selection with custom prompt."""
    mock_input.return_value = "a"

    options = [("a", "First"), ("b", "Second")]
    result = menu_selection(options, prompt="Choose: ")

    assert result == "a"


@patch("builtins.input")
@patch("builtins.print")
def test_menu_selection_invalid_then_valid(mock_print, mock_input):
    """Test menu_selection with invalid then valid choice."""
    mock_input.side_effect = ["invalid", "2"]

    options = [("1", "Option 1"), ("2", "Option 2")]
    result = menu_selection(options)

    assert result == "2"
    # Check that error message was printed
    assert any("Invalid option" in str(call) for call in mock_print.call_args_list)


@patch("builtins.input")
def test_menu_selection_displays_options(mock_input, capsys):
    """Test that menu_selection displays all options."""
    mock_input.return_value = "1"

    options = [("1", "First option"), ("2", "Second option"), ("3", "Third option")]
    menu_selection(options)

    captured = capsys.readouterr()
    assert "[1] First option" in captured.out
    assert "[2] Second option" in captured.out
    assert "[3] Third option" in captured.out


@patch("builtins.input")
def test_confirm_action_yes(mock_input):
    """Test confirm_action with 'yes' response."""
    mock_input.return_value = "y"

    result = confirm_action("Proceed?")

    assert result is True


@patch("builtins.input")
def test_confirm_action_yes_full(mock_input):
    """Test confirm_action with 'yes' spelled out."""
    mock_input.return_value = "yes"

    result = confirm_action()

    assert result is True


@patch("builtins.input")
def test_confirm_action_no(mock_input):
    """Test confirm_action with 'no' response."""
    mock_input.return_value = "n"

    result = confirm_action("Continue?")

    assert result is False


@patch("builtins.input")
def test_confirm_action_no_full(mock_input):
    """Test confirm_action with 'no' spelled out."""
    mock_input.return_value = "no"

    result = confirm_action()

    assert result is False


@patch("builtins.input")
@patch("builtins.print")
def test_confirm_action_invalid_then_valid(mock_print, mock_input):
    """Test confirm_action with invalid then valid response."""
    mock_input.side_effect = ["maybe", "invalid", "y"]

    result = confirm_action()

    assert result is True
    # Check that error messages were printed
    assert mock_print.call_count >= 2


@patch("builtins.input")
def test_confirm_action_case_insensitive(mock_input):
    """Test that confirm_action handles uppercase."""
    mock_input.return_value = "Y"

    result = confirm_action()

    assert result is True


@patch("builtins.input")
def test_menu_selection_single_option(mock_input):
    """Test menu_selection with single option."""
    mock_input.return_value = "only"

    options = [("only", "Only option")]
    result = menu_selection(options)

    assert result == "only"


@patch("builtins.input")
def test_menu_selection_numeric_keys(mock_input):
    """Test menu_selection with numeric keys."""
    mock_input.return_value = "123"

    options = [("123", "Option 123"), ("456", "Option 456")]
    result = menu_selection(options)

    assert result == "123"


@patch("builtins.input")
def test_menu_selection_special_chars_keys(mock_input):
    """Test menu_selection with special character keys."""
    mock_input.return_value = "q"

    options = [("q", "Quit"), ("?", "Help"), ("!", "Alert")]
    result = menu_selection(options)

    assert result == "q"


@patch("builtins.input")
def test_confirm_action_default_prompt(mock_input):
    """Test confirm_action uses default prompt."""
    mock_input.return_value = "y"

    confirm_action()

    # Check that input was called with the default prompt
    mock_input.assert_called_with("Are you sure? (y/n): ")
