"""Interactive CLI components."""

import getpass
from typing import List, Tuple


def hidden_input(prompt: str) -> str:
    """Get password input without showing characters."""
    return getpass.getpass(prompt)


def menu_selection(
    options: List[Tuple[str, str]], prompt: str = "Select an option: "
) -> str:
    """Display an interactive menu and return the selected option key."""
    for key, desc in options:
        print(f"[{key}] {desc}")

    while True:
        choice = input(prompt)
        valid_keys = [key for key, _ in options]
        if choice in valid_keys:
            return choice
        print(f"Invalid option. Please choose from {', '.join(valid_keys)}")


def confirm_action(prompt: str = "Are you sure?") -> bool:
    """Ask for confirmation with yes/no prompt."""
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        print("Please enter 'y' or 'n'")
