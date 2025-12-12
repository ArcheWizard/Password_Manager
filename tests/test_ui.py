"""Tests for UI utilities module."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.ui import (
    print_error,
    print_header,
    print_menu_option,
    print_success,
    print_table,
    print_warning,
)


def test_print_header(capsys):
    """Test print_header output."""
    print_header("Test Title")

    captured = capsys.readouterr()
    assert "Test Title" in captured.out
    assert "=" in captured.out


def test_print_success(capsys):
    """Test print_success output."""
    print_success("Operation completed")

    captured = capsys.readouterr()
    assert "Operation completed" in captured.out
    assert "✓" in captured.out


def test_print_error(capsys):
    """Test print_error output."""
    print_error("Something went wrong")

    captured = capsys.readouterr()
    assert "Something went wrong" in captured.out
    assert "✗" in captured.out


def test_print_warning(capsys):
    """Test print_warning output."""
    print_warning("This is a warning")

    captured = capsys.readouterr()
    assert "This is a warning" in captured.out
    assert "!" in captured.out


def test_print_menu_option_default(capsys):
    """Test print_menu_option with default color."""
    print_menu_option("1", "First option")

    captured = capsys.readouterr()
    assert "[1]" in captured.out
    assert "First option" in captured.out


def test_print_menu_option_custom_color(capsys):
    """Test print_menu_option with custom color."""
    from colorama import Fore

    print_menu_option("2", "Second option", color=Fore.GREEN)

    captured = capsys.readouterr()
    assert "[2]" in captured.out
    assert "Second option" in captured.out


def test_print_table_simple(capsys):
    """Test print_table with simple data."""
    headers = ["Name", "Age", "City"]
    rows = [
        ["Alice", "30", "New York"],
        ["Bob", "25", "London"],
        ["Charlie", "35", "Paris"],
    ]

    print_table(headers, rows)

    captured = capsys.readouterr()
    assert "Name" in captured.out
    assert "Age" in captured.out
    assert "City" in captured.out
    assert "Alice" in captured.out
    assert "Bob" in captured.out
    assert "Charlie" in captured.out


def test_print_table_empty_rows(capsys):
    """Test print_table with empty rows."""
    headers = ["Col1", "Col2"]
    rows = []

    print_table(headers, rows)

    captured = capsys.readouterr()
    assert "Col1" in captured.out
    assert "Col2" in captured.out


def test_print_table_varying_widths(capsys):
    """Test print_table with varying column widths."""
    headers = ["Short", "Medium Column", "Very Long Header Name"]
    rows = [
        ["A", "B", "C"],
        ["Very long content", "X", "Y"],
    ]

    print_table(headers, rows)

    captured = capsys.readouterr()
    # Should handle varying widths
    assert "Short" in captured.out
    assert "Very long content" in captured.out


def test_print_header_centering(capsys):
    """Test that print_header centers the title."""
    print_header("X")

    captured = capsys.readouterr()
    lines = captured.out.split("\n")

    # Find the line with the title
    title_line = [line for line in lines if "X" in line and "=" not in line][0]

    # Should have spacing on both sides
    # Remove ANSI codes for checking
    import re

    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", title_line)
    # The width should be 50 (default width in ui.py)
    assert len(clean_line) == 50  # Full width including padding


def test_print_table_alignment(capsys):
    """Test print_table column alignment."""
    headers = ["Name", "Value"]
    rows = [["A", "1"], ["BB", "22"], ["CCC", "333"]]

    print_table(headers, rows)

    captured = capsys.readouterr()
    # Table should be properly formatted
    assert "|" in captured.out
    assert "-" in captured.out


def test_print_success_with_special_chars(capsys):
    """Test print_success with special characters."""
    print_success("Success! 🎉 Complete")

    captured = capsys.readouterr()
    assert "Success!" in captured.out
    assert "Complete" in captured.out


def test_print_error_with_newlines(capsys):
    """Test print_error with newlines in message."""
    print_error("Error line 1\nError line 2")

    captured = capsys.readouterr()
    assert "Error line 1" in captured.out
    assert "Error line 2" in captured.out


def test_print_warning_empty_message(capsys):
    """Test print_warning with empty message."""
    print_warning("")

    captured = capsys.readouterr()
    assert "!" in captured.out


def test_print_menu_option_numeric_key(capsys):
    """Test print_menu_option with numeric key."""
    print_menu_option("123", "Numeric option")

    captured = capsys.readouterr()
    assert "[123]" in captured.out
    assert "Numeric option" in captured.out


def test_print_table_with_numbers(capsys):
    """Test print_table with numeric data."""
    headers = ["ID", "Count", "Price"]
    rows = [[1, 100, 19.99], [2, 50, 29.99]]

    print_table(headers, rows)

    captured = capsys.readouterr()
    assert "100" in captured.out
    assert "19.99" in captured.out


def test_print_header_long_title(capsys):
    """Test print_header with very long title."""
    long_title = "A" * 100
    print_header(long_title)

    captured = capsys.readouterr()
    assert long_title in captured.out


def test_print_table_single_row(capsys):
    """Test print_table with single row."""
    headers = ["Column"]
    rows = [["Value"]]

    print_table(headers, rows)

    captured = capsys.readouterr()
    assert "Column" in captured.out
    assert "Value" in captured.out


def test_print_table_single_column(capsys):
    """Test print_table with single column."""
    headers = ["Data"]
    rows = [["A"], ["B"], ["C"]]

    print_table(headers, rows)

    captured = capsys.readouterr()
    assert "Data" in captured.out
    assert "A" in captured.out
    assert "B" in captured.out
    assert "C" in captured.out


def test_colorama_autoreset():
    """Test that colorama is initialized with autoreset."""
    # This is mainly to ensure the import works correctly
    from colorama import Fore

    # Should be able to use colors
    assert hasattr(Fore, "GREEN")
    assert hasattr(Fore, "RED")
    assert hasattr(Fore, "YELLOW")
    assert hasattr(Fore, "CYAN")
