"""UI utilities for the Password Manager application."""

from typing import Any, List

from colorama import Fore, init

# Initialize colorama
init(autoreset=True)


def print_header(title: str) -> None:
    """Print a formatted header with the given title."""
    width = 50
    print(Fore.CYAN + "=" * width)
    print(Fore.CYAN + f"{title.center(width)}")
    print(Fore.CYAN + "=" * width)


def print_success(message: str) -> None:
    """Print a success message."""
    print(Fore.GREEN + f"✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(Fore.RED + f"✗ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(Fore.YELLOW + f"! {message}")


def print_menu_option(key: str, description: str, color: str = Fore.YELLOW) -> None:
    """Print a formatted menu option."""
    print(f"{color}[{key}] {Fore.WHITE}{description}")


def print_table(headers: List[str], rows: List[List[Any]]) -> None:
    """Print data in a formatted table with headers."""
    # Calculate column widths
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print headers
    header_row = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(Fore.CYAN + header_row)
    print(Fore.CYAN + "-" * len(header_row))

    # Print rows
    for row in rows:
        formatted_row = " | ".join(
            str(cell).ljust(widths[i]) for i, cell in enumerate(row)
        )
        print(Fore.WHITE + formatted_row)
