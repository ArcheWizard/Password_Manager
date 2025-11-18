"""Main application module for the Password Manager."""

import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional

import pyperclip
from colorama import Fore, Style, init

from secure_password_manager.services.browser_bridge import (
    BrowserBridgeService,
    get_browser_bridge_service,
)
from secure_password_manager.utils import config
from secure_password_manager.utils.config import KEY_MODE_FILE, KEY_MODE_PASSWORD
from secure_password_manager.utils.auth import authenticate, set_master_password
from secure_password_manager.utils.backup import (
    create_full_backup,
    export_passwords,
    import_passwords,
    restore_from_backup,
)
from secure_password_manager.utils.crypto import (
    decrypt_password,
    encrypt_password,
    is_key_protected,
    load_kdf_params,
    protect_key_with_master_password,
    set_master_password_context,
    unprotect_key,
)
from secure_password_manager.utils.key_management import (
    KeyManagementError,
    apply_kdf_parameters,
    benchmark_kdf,
    get_key_mode,
    switch_key_mode,
)
from secure_password_manager.utils.database import (
    add_category,
    add_password,
    delete_password,
    get_categories,
    get_expiring_passwords,
    get_passwords,
    init_db,
    update_password,
)
from secure_password_manager.utils.logger import get_log_entries, log_info
from secure_password_manager.utils.password_analysis import (
    evaluate_password_strength,
    generate_secure_password,
    get_password_improvement_suggestions,
)
from secure_password_manager.utils.security_audit import run_security_audit
from secure_password_manager.utils.two_factor import (
    disable_2fa,
    is_2fa_enabled,
    setup_totp,
    verify_totp,
)
from secure_password_manager.utils.ui import (
    print_error,
    print_header,
    print_menu_option,
    print_success,
    print_table,
    print_warning,
)
from secure_password_manager.utils.paths import (
    get_database_path,
    get_secret_key_enc_path,
    get_secret_key_path,
)

# Initialize Colorama
init(autoreset=True)


def _get_browser_bridge_settings() -> Dict[str, Any]:
    return config.load_settings().get("browser_bridge", {})


def sync_browser_bridge_with_settings() -> None:
    service = get_browser_bridge_service()
    settings = _get_browser_bridge_settings()
    if settings.get("enabled"):
        if not service.is_running:
            service.start()
            log_info("Browser bridge started (settings enabled)")
    elif service.is_running:
        service.stop()


def shutdown_browser_bridge() -> None:
    service = get_browser_bridge_service()
    if service.is_running:
        service.stop()


def main_menu() -> None:
    """Display the main menu options to the user."""
    print_header("Password Manager")
    print_menu_option("1", "Manage Passwords")
    print_menu_option("2", "Categories")
    print_menu_option("3", "Backup & Restore")
    print_menu_option("4", "Settings")
    print_menu_option("5", "View Activity Log")
    print_menu_option("6", "Security Audit")  # New option
    print_menu_option("0", "Exit", Fore.RED)


def passwords_menu() -> None:
    """Display the password management menu."""
    print_header("Password Management")
    print_menu_option("1", "Add New Password")
    print_menu_option("2", "View All Passwords")
    print_menu_option("3", "Search Passwords")
    print_menu_option("4", "Edit Password")
    print_menu_option("5", "Delete Password")
    print_menu_option("6", "Generate Secure Password")
    print_menu_option("7", "Check Expiring Passwords")
    print_menu_option("0", "Back to Main Menu")


def add_new_password() -> None:
    """Prompt user for new password details and save to database with encryption."""
    print_header("Add New Password")
    website = input("Website: ")
    username = input("Username: ")

    # Add option for generated password
    use_generated = input("Generate secure password? (y/n): ").lower() == "y"

    if use_generated:
        length = input("Password length (default: 16): ")
        length = int(length) if length.isdigit() else 16

        special_chars = (
            input("Include special characters? (y/n, default: y): ").lower() != "n"
        )

        password = generate_secure_password(length, special_chars)
        print_success(f"Generated password: {password}")

        # Copy to clipboard
        if input("Copy to clipboard? (y/n): ").lower() == "y":
            pyperclip.copy(password)
            print_success("Password copied to clipboard")
    else:
        password = input("Password: ")
        score, strength = evaluate_password_strength(password)

        # Color-code the strength feedback
        color = Fore.RED
        if score >= 4:
            color = Fore.GREEN
        elif score >= 3:
            color = Fore.YELLOW

        print(f"Password strength: {color}{strength}{Style.RESET_ALL}")

        # Show suggestions for weak passwords
        if score < 3:
            print_warning("Password is weak. Consider the following improvements:")
            suggestions = get_password_improvement_suggestions(password)
            for suggestion in suggestions:
                print(f"  - {suggestion}")

            confirm = input("Use this password anyway? (y/n): ")
            if confirm.lower() != "y":
                print_warning("Password entry canceled")
                return

    # Get category
    categories = get_categories()
    if categories:
        print("\nAvailable categories:")
        for i, (name, color) in enumerate(categories, 1):
            print(f"{Fore.YELLOW}[{i}]{Fore.RESET} {name}")

        cat_choice = input("\nSelect category (number or name, default: General): ")

        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            category = categories[int(cat_choice) - 1][0]
        elif cat_choice in [name for name, _ in categories]:
            category = cat_choice
        elif cat_choice:
            # New category
            if (
                input(
                    f"Category '{cat_choice}' doesn't exist. Create it? (y/n): "
                ).lower()
                == "y"
            ):
                add_category(cat_choice)
                category = cat_choice
            else:
                category = "General"
        else:
            category = "General"
    else:
        category = "General"

    # Optional notes
    notes = input("Notes (optional): ")

    # Optional expiry
    expiry_input = input("Set password to expire in days (leave empty for never): ")
    expiry_days = int(expiry_input) if expiry_input.isdigit() else None

    encrypted = encrypt_password(password)
    add_password(website, username, encrypted, category, notes, expiry_days)
    print_success("Password added successfully!")
    log_info(f"Added new password for {website} in category {category}")


def view_passwords(
    category: Optional[str] = None, search_term: Optional[str] = None
) -> None:
    """Retrieve and display all passwords in a readable format."""
    show_expired = input("Show expired passwords? (y/n, default: y): ").lower() != "n"

    print_header("Saved Passwords")
    passwords = get_passwords(category, search_term, show_expired)

    if not passwords:
        print_error("No passwords found.")
        return

    rows = []
    for entry in passwords:
        (
            entry_id,
            website,
            username,
            encrypted,
            category,
            notes,
            created,
            updated,
            expiry,
            favorite,
        ) = entry
        decrypted = decrypt_password(encrypted)

        # Format dates
        created_str = time.strftime("%Y-%m-%d", time.localtime(created))

        # Add expiry warning
        if expiry and expiry < time.time():
            expiry_str = f"{Fore.RED}EXPIRED{Style.RESET_ALL}"
        elif expiry:
            days_left = int((expiry - time.time()) / 86400)
            if days_left <= 7:
                expiry_str = f"{Fore.RED}{days_left} days{Style.RESET_ALL}"
            elif days_left <= 30:
                expiry_str = f"{Fore.YELLOW}{days_left} days{Style.RESET_ALL}"
            else:
                expiry_str = f"{days_left} days"
        else:
            expiry_str = "Never"

        # Mark favorites
        fav_mark = "★ " if favorite else ""

        rows.append(
            [
                entry_id,
                f"{fav_mark}{website}",
                username,
                decrypted,
                category,
                created_str,
                expiry_str,
            ]
        )

    headers = [
        "ID",
        "Website",
        "Username",
        "Password",
        "Category",
        "Created",
        "Expires In",
    ]
    print_table(headers, rows)

    # Post-view options
    print("\nOptions:")
    print("  [c] Copy password to clipboard")
    print("  [f] Mark/unmark as favorite")
    print("  [d] Delete password")
    print("  [e] Edit password")
    print("  [q] Back to menu")

    choice = input("\nSelect option: ").lower()

    if choice == "c":
        pass_id = input("Enter ID of password to copy: ")
        try:
            pass_id = int(pass_id)
            for entry in rows:
                if entry[0] == pass_id:
                    pyperclip.copy(entry[3])
                    print_success("Password copied to clipboard")
                    log_info(f"Copied password for ID {pass_id}")
                    break
            else:
                print_error("Invalid ID")
        except ValueError:
            print_error("Invalid ID. Please enter a number.")

    elif choice == "f":
        pass_id = input("Enter ID of password to toggle favorite: ")
        try:
            for entry in passwords:
                if entry[0] == int(pass_id):
                    # Toggle favorite
                    update_password(int(pass_id), favorite=not entry[9])
                    print_success(
                        f"{'Added to' if not entry[9] else 'Removed from'} favorites"
                    )
                    log_info(f"Updated favorite status for ID {pass_id}")
                    break
            else:
                print_error("Invalid ID")
        except ValueError:
            print_error("Invalid ID. Please enter a number.")

    elif choice == "d":
        delete_password_entry()

    elif choice == "e":
        edit_password()


def search_passwords() -> None:
    """Search passwords by website or username."""
    print_header("Search Passwords")
    search_term = input("Enter search term: ")

    if not search_term:
        print_warning("Search canceled")
        return

    view_passwords(search_term=search_term)


def delete_password_entry() -> None:
    """Delete a password entry by ID after user confirmation."""
    print_header("Delete Password")
    entry_id = input("Enter ID of the password to delete: ")

    try:
        entry_id = int(entry_id)

        # Get the entry to confirm
        for entry in get_passwords():
            if entry[0] == entry_id:
                website = entry[1]
                username = entry[2]
                break
        else:
            print_error(f"No password found with ID {entry_id}")
            return

        confirm = input(
            f"Are you sure you want to delete password for {website} ({username})? (y/n): "
        )
        if confirm.lower() != "y":
            print_warning("Deletion canceled")
            return

        delete_password(entry_id)
        print_success("Password deleted successfully!")
        log_info(f"Deleted password for {website} (ID: {entry_id})")
    except ValueError:
        print_error("Invalid ID. Please enter a number.")


def edit_password() -> None:
    """Edit an existing password entry."""
    print_header("Edit Password")
    entry_id = input("Enter ID of the password to edit: ")

    try:
        entry_id = int(entry_id)

        # Get the entry to edit
        entries = get_passwords()
        target_entry = None

        for entry in entries:
            if entry[0] == entry_id:
                target_entry = entry
                break

        if not target_entry:
            print_error(f"No password found with ID {entry_id}")
            return

        # Current values
        _, website, username, encrypted, category, notes, _, _, expiry, favorite = (
            target_entry
        )
        password = decrypt_password(encrypted)

        print(f"\nCurrent values for ID {entry_id}:")
        print(f"Website: {website}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Category: {category}")
        print(f"Notes: {notes}")
        print(f"Favorite: {'Yes' if favorite else 'No'}")

        # Get new values
        print("\nEnter new values (leave empty to keep current)")
        new_website = input(f"Website [{website}]: ") or website
        new_username = input(f"Username [{username}]: ") or username

        new_password_prompt = input("Change password? (y/n): ").lower()
        if new_password_prompt == "y":
            use_generated = input("Generate secure password? (y/n): ").lower() == "y"

            if use_generated:
                length = input("Password length (default: 16): ")
                length = int(length) if length.isdigit() else 16

                special_chars = (
                    input("Include special characters? (y/n, default: y): ").lower()
                    != "n"
                )

                new_password = generate_secure_password(length, special_chars)
                print_success(f"Generated password: {new_password}")

                # Copy to clipboard
                if input("Copy to clipboard? (y/n): ").lower() == "y":
                    pyperclip.copy(new_password)
                    print_success("Password copied to clipboard")
            else:
                new_password = input("New password: ")
                score, strength = evaluate_password_strength(new_password)

                # Color-code the strength feedback
                color = Fore.RED
                if score >= 4:
                    color = Fore.GREEN
                elif score >= 3:
                    color = Fore.YELLOW

                print(f"Password strength: {color}{strength}{Style.RESET_ALL}")

                # Show suggestions for weak passwords
                if score < 3:
                    print_warning(
                        "Password is weak. Consider the following improvements:"
                    )
                    suggestions = get_password_improvement_suggestions(new_password)
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")

                    confirm = input("Use this password anyway? (y/n): ")
                    if confirm.lower() != "y":
                        new_password = password  # Keep original
        else:
            new_password = password  # Keep original

        # Get categories
        categories = get_categories()
        print("\nAvailable categories:")
        for i, (cat_name, _) in enumerate(categories, 1):
            print(f"{Fore.YELLOW}[{i}]{Fore.RESET} {cat_name}")

        cat_choice = input(f"\nCategory [{category}]: ")

        if not cat_choice:
            new_category = category
        elif cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            new_category = categories[int(cat_choice) - 1][0]
        elif cat_choice in [name for name, _ in categories]:
            new_category = cat_choice
        else:
            # New category
            if (
                input(
                    f"Category '{cat_choice}' doesn't exist. Create it? (y/n): "
                ).lower()
                == "y"
            ):
                add_category(cat_choice)
                new_category = cat_choice
            else:
                new_category = category

        # Notes
        new_notes = input(f"Notes [{notes}]: ") or notes

        # Expiry
        if expiry:
            days_left = (
                int((expiry - time.time()) / 86400) if expiry > time.time() else 0
            )
            print(f"Current expiry: {days_left} days left")
        else:
            print("Current expiry: Never")

        expiry_input = input(
            "Set password to expire in days (leave empty to keep current): "
        )
        if expiry_input:
            if expiry_input.isdigit():
                new_expiry_days = int(expiry_input)
            else:
                new_expiry_days = None
        else:
            new_expiry_days = None  # Keep current

        # Favorite
        fav_input = input(
            f"Mark as favorite? (y/n, current: {'y' if favorite else 'n'}): "
        ).lower()
        if fav_input in ["y", "n"]:
            new_favorite = fav_input == "y"
        else:
            new_favorite = favorite

        # Update the entry
        if new_password != password:
            encrypted_password = encrypt_password(new_password)
        else:
            encrypted_password = None  # No change

        update_password(
            entry_id,
            website=new_website if new_website != website else None,
            username=new_username if new_username != username else None,
            encrypted_password=encrypted_password,
            category=new_category if new_category != category else None,
            notes=new_notes if new_notes != notes else None,
            expiry_days=new_expiry_days,
            favorite=new_favorite if new_favorite != favorite else None,
        )

        print_success("Password updated successfully!")
        log_info(f"Updated password for {new_website} (ID: {entry_id})")
    except ValueError:
        print_error("Invalid ID. Please enter a number.")


def generate_password_tool() -> None:
    """Tool for generating secure passwords."""
    print_header("Password Generator")

    length = input("Password length (default: 16): ")
    length = int(length) if length.isdigit() else 16

    special_chars = (
        input("Include special characters? (y/n, default: y): ").lower() != "n"
    )

    password = generate_secure_password(length, special_chars)
    print_success(f"Generated password: {password}")

    # Evaluate strength
    score, strength = evaluate_password_strength(password)
    color = Fore.RED
    if score >= 4:
        color = Fore.GREEN
    elif score >= 3:
        color = Fore.YELLOW

    print(f"Password strength: {color}{strength}{Style.RESET_ALL}")

    # Copy to clipboard
    if input("Copy to clipboard? (y/n): ").lower() == "y":
        pyperclip.copy(password)
        print_success("Password copied to clipboard")


def check_expiring_passwords() -> None:
    """Check for passwords that are about to expire."""
    print_header("Expiring Passwords")

    days = input("Check for passwords expiring within how many days? (default: 30): ")
    days = int(days) if days.isdigit() else 30

    expiring = get_expiring_passwords(days)

    if not expiring:
        print_success(f"No passwords expiring within {days} days.")
        return

    print_warning(f"Found {len(expiring)} passwords expiring within {days} days:")

    rows = []
    for entry in expiring:
        entry_id, website, username, encrypted, category, _, _, _, expiry, _ = entry

        # Calculate days left
        days_left = int((expiry - time.time()) / 86400)

        # Color code based on urgency
        if days_left <= 7:
            days_str = f"{Fore.RED}{days_left} days{Style.RESET_ALL}"
        else:
            days_str = f"{Fore.YELLOW}{days_left} days{Style.RESET_ALL}"

        rows.append([entry_id, website, username, category, days_str])

    print_table(["ID", "Website", "Username", "Category", "Expiring In"], rows)

    print("\nOptions:")
    print("  [r] Renew password")
    print("  [v] View full password details")
    print("  [q] Back to menu")

    choice = input("\nSelect option: ").lower()

    if choice == "r":
        entry_id = input("Enter ID of password to renew: ")
        try:
            entry_id = int(entry_id)

            # Get new expiry
            new_days = input("Renew for how many days? (default: 90): ")
            new_days = int(new_days) if new_days.isdigit() and int(new_days) > 0 else 90

            update_password(entry_id, expiry_days=new_days)
            print_success(f"Password renewed for {new_days} days")
            log_info(f"Renewed password ID {entry_id} for {new_days} days")
        except ValueError:
            print_error("Invalid ID. Please enter a number.")

    elif choice == "v":
        # Show the password view for these entries
        view_passwords()


def categories_menu() -> None:
    """Display and manage categories."""
    print_header("Categories")

    categories = get_categories()

    if not categories:
        print_warning("No categories found.")
    else:
        print("Available categories:")
        for i, (name, color) in enumerate(categories, 1):
            print(f"{Fore.YELLOW}[{i}]{Fore.RESET} {name}")

    print("\nOptions:")
    print("  [1] View passwords by category")
    print("  [2] Add new category")
    print_menu_option("0", "Back to main menu")

    choice = input("\nSelect option: ")

    if choice == "1":
        if not categories:
            print_error("No categories available.")
            return

        cat_choice = input("Select category (number or name): ")

        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            category = categories[int(cat_choice) - 1][0]
        elif cat_choice in [name for name, _ in categories]:
            category = cat_choice
        else:
            print_error("Invalid category.")
            return

        view_passwords(category=category)

    elif choice == "2":
        name = input("Enter new category name: ")

        if not name:
            print_warning("Category name cannot be empty.")
            return

        # Check if already exists
        if name in [cat[0] for cat in categories]:
            print_error(f"Category '{name}' already exists.")
            return

        color = input("Enter color (default: blue): ") or "blue"

        add_category(name, color)
        print_success(f"Added new category: {name}")
        log_info(f"Added new category: {name}")


def backup_menu() -> None:
    """Display backup and restore options."""
    print_header("Backup & Restore")

    print_menu_option("1", "Export passwords")
    print_menu_option("2", "Import passwords")
    print_menu_option("3", "Full backup")
    print_menu_option("4", "Restore from backup")
    print_menu_option("0", "Back to main menu")

    choice = input(f"{Fore.YELLOW}Select an option: ")

    if choice == "1":
        export_passwords_menu()
    elif choice == "2":
        import_passwords_menu()
    elif choice == "3":
        full_backup_menu()
    elif choice == "4":
        restore_backup_menu()


def export_passwords_menu() -> None:
    """Menu option to export passwords."""
    print_header("Export Passwords")

    filename = input("Enter filename to export to (default: backup.dat): ")
    if not filename:
        filename = "backup.dat"

    master_pass = input("Enter master password to encrypt backup: ")

    include_notes = input("Include notes in export? (y/n, default: y): ").lower() != "n"

    if export_passwords(filename, master_pass, include_notes):
        print_success(f"Passwords exported to {filename}")
    else:
        print_error("No passwords to export")


def import_passwords_menu() -> None:
    """Menu option to import passwords."""
    print_header("Import Passwords")

    filename = input("Enter filename to import from: ")

    if not os.path.exists(filename):
        print_error(f"File {filename} not found")
        return

    master_pass = input("Enter master password to decrypt backup: ")

    count = import_passwords(filename, master_pass)
    if count > 0:
        print_success(f"Imported {count} passwords successfully")
    else:
        print_error("Failed to import passwords")


def full_backup_menu() -> None:
    """Create a full backup of all data."""
    print_header("Full Backup")

    backup_dir = input("Enter backup directory (default: ./backups): ")
    if not backup_dir:
        backup_dir = "backups"

    master_pass = input("Enter master password to encrypt backup: ")

    backup_path = create_full_backup(backup_dir, master_pass)
    if backup_path:
        print_success(f"Full backup created at {backup_path}")
    else:
        print_error("Backup failed")


def restore_backup_menu() -> None:
    """Restore from a full backup."""
    print_header("Restore Backup")

    print_warning(
        "⚠️ Restoring will replace your current data. Make sure you have a backup!"
    )
    confirm = input("Do you want to continue? (y/n): ")

    if confirm.lower() != "y":
        print_warning("Restore canceled")
        return

    backup_path = input("Enter backup file path: ")

    if not os.path.exists(backup_path):
        print_error(f"Backup file {backup_path} not found")
        return

    master_pass = input("Enter master password to decrypt backup: ")

    if restore_from_backup(backup_path, master_pass):
        print_success("Backup restored successfully")
        print_warning("The application will now exit. Please restart.")
        exit(0)
    else:
        print_error("Restore failed")


def view_logs() -> None:
    """View recent log entries."""
    print_header("Activity Log")

    count = input("How many log entries to show? (default: 20): ")
    count = int(count) if count.isdigit() else 20

    logs = get_log_entries(count)

    if not logs:
        print_warning("No log entries found.")
        return

    for log in logs:
        # Replace common patterns with colored text
        if " - INFO - " in log:
            log = log.replace(" - INFO - ", f" - {Fore.GREEN}INFO{Fore.RESET} - ")
        elif " - ERROR - " in log:
            log = log.replace(" - ERROR - ", f" - {Fore.RED}ERROR{Fore.RESET} - ")
        elif " - WARNING - " in log:
            log = log.replace(
                " - WARNING - ", f" - {Fore.YELLOW}WARNING{Fore.RESET} - "
            )

        print(log.strip())

    input("\nPress Enter to continue...")


def security_audit_menu() -> None:
    """Display security audit options."""
    print_header("Security Audit")

    print_menu_option("1", "Run Full Security Audit")
    print_menu_option("2", "Check Weak Passwords")
    print_menu_option("3", "Check Reused Passwords")
    print_menu_option("4", "Check Breached Passwords")
    print_menu_option("0", "Back to Main Menu")

    choice = input(f"{Fore.YELLOW}Select an option: ")

    if choice == "1":
        print_header("Running Full Security Audit")
        print("This may take a moment...")

        audit_results = run_security_audit()
        score = audit_results["score"]

        # Display the security score with color
        if score >= 80:
            color = Fore.GREEN
        elif score >= 60:
            color = Fore.YELLOW
        else:
            color = Fore.RED

        print(f"\nYour security score: {color}{score}/100{Style.RESET_ALL}")

        # Show issue summaries
        issues = audit_results["issues"]

        weak_count = len(issues["weak_passwords"])
        reused_count = len(issues["reused_passwords"])
        duplicate_count = len(issues["duplicate_passwords"])
        expired_count = len(issues["expired_passwords"])
        breached_count = len(issues["breached_passwords"])

        print("\nIssues found:")
        print(
            f"{Fore.RED if weak_count else Fore.GREEN}• Weak passwords: {weak_count}{Style.RESET_ALL}"
        )
        print(
            f"{Fore.RED if reused_count else Fore.GREEN}• Reused passwords: {reused_count}{Style.RESET_ALL}"
        )
        print(
            f"{Fore.YELLOW if duplicate_count else Fore.GREEN}• Duplicate entries: {duplicate_count}{Style.RESET_ALL}"
        )
        print(
            f"{Fore.RED if expired_count else Fore.GREEN}• Expired passwords: {expired_count}{Style.RESET_ALL}"
        )
        print(
            f"{Fore.RED if breached_count else Fore.GREEN}• Breached passwords: {breached_count}{Style.RESET_ALL}"
        )

        # Offer to fix issues
        if (
            weak_count
            or reused_count
            or duplicate_count
            or expired_count
            or breached_count
        ):
            if (
                input(
                    "\nWould you like to see details about these issues? (y/n): "
                ).lower()
                == "y"
            ):
                if weak_count:
                    print(f"\n{Fore.RED}Weak Passwords:{Style.RESET_ALL}")
                    for issue in issues["weak_passwords"]:
                        print(
                            f"  • {issue['website']} ({issue['username']}) - Score: {issue['score']}"
                        )

                if reused_count:
                    print(f"\n{Fore.RED}Reused Passwords:{Style.RESET_ALL}")
                    for issue in issues["reused_passwords"]:
                        sites = ", ".join(
                            [f"{site['website']}" for site in issue["reused_with"]]
                        )
                        print(
                            f"  • {issue['website']} ({issue['username']}) - Also used on: {sites}"
                        )

                if duplicate_count:
                    print(f"\n{Fore.YELLOW}Duplicate Entries:{Style.RESET_ALL}")
                    for issue in issues["duplicate_passwords"]:
                        print(
                            f"  • {issue['website']} ({issue['username']}) - Duplicate of ID: {issue['duplicate_id']}"
                        )

                if expired_count:
                    print(f"\n{Fore.RED}Expired Passwords:{Style.RESET_ALL}")
                    for issue in issues["expired_passwords"]:
                        print(
                            f"  • {issue['website']} ({issue['username']}) - Expired {issue['expired_days']} days ago"
                        )

                if breached_count:
                    print(f"\n{Fore.RED}Breached Passwords:{Style.RESET_ALL}")
                    for issue in issues["breached_passwords"]:
                        print(
                            f"  • {issue['website']} ({issue['username']}) - Found in {issue['breach_count']} breaches"
                        )
        else:
            print_success(
                "\nNo security issues found! Your passwords are in good shape."
            )

        input("\nPress Enter to continue...")

    elif choice == "2":
        print_header("Checking Weak Passwords")
        audit_results = run_security_audit()
        weak_passwords = audit_results["issues"]["weak_passwords"]

        if not weak_passwords:
            print_success("No weak passwords found!")
        else:
            print_warning(f"Found {len(weak_passwords)} weak passwords:")

            rows = []
            for issue in weak_passwords:
                rows.append(
                    [
                        issue["id"],
                        issue["website"],
                        issue["username"],
                        issue["score"],
                        issue["category"],
                    ]
                )

            print_table(["ID", "Website", "Username", "Score", "Category"], rows)

            print("\nRecommendations:")
            print("  1. Generate a new strong password for each weak password")
            print("  2. Update the password on the website")
            print("  3. Update the password in the password manager")

        input("\nPress Enter to continue...")

    elif choice == "3":
        print_header("Checking Reused Passwords")
        audit_results = run_security_audit()
        reused_passwords = audit_results["issues"]["reused_passwords"]

        if not reused_passwords:
            print_success("No reused passwords found!")
        else:
            print_warning(f"Found {len(reused_passwords)} reused passwords:")

            for i, issue in enumerate(reused_passwords, 1):
                sites = ", ".join([site["website"] for site in issue["reused_with"]])
                print(
                    f"{Fore.YELLOW}{i}.{Style.RESET_ALL} {issue['website']} ({issue['username']})"
                )
                print(f"   Also used on: {sites}")

            print("\nRecommendations:")
            print("  1. Generate a unique password for each account")
            print("  2. Start with high-value accounts (banking, email, etc.)")
            print("  3. Use the password generator in this app")

        input("\nPress Enter to continue...")

    elif choice == "4":
        print_header("Checking Breached Passwords")
        print("This will check your passwords against known data breaches.")
        print("No passwords are sent over the internet - only partial hashes.")

        if input("Continue? (y/n): ").lower() != "y":
            return

        print("\nChecking for breached passwords...")
        audit_results = run_security_audit()
        breached_passwords = audit_results["issues"]["breached_passwords"]

        if not breached_passwords:
            print_success("No breached passwords found!")
        else:
            print_warning(f"Found {len(breached_passwords)} breached passwords:")

            rows = []
            for issue in breached_passwords:
                rows.append(
                    [
                        issue["id"],
                        issue["website"],
                        issue["username"],
                        issue["breach_count"],
                        issue["category"],
                    ]
                )

            print_table(["ID", "Website", "Username", "Breach Count", "Category"], rows)

            print("\nRecommendations:")
            print("  1. Change these passwords immediately")
            print("  2. Use a unique, strong password for each site")
            print("  3. Enable two-factor authentication where available")

        input("\nPress Enter to continue...")


def settings_menu() -> None:
    """Display settings menu."""
    print_header("Settings")

    print_menu_option("1", "Change master password")
    print_menu_option("2", "Key management mode")
    print_menu_option("3", "KDF tuning wizard")
    print_menu_option("4", "View system information")
    print_menu_option("5", "Clear logs")
    print_menu_option("6", "Two-Factor Authentication")
    print_menu_option("7", "Browser Bridge (Experimental)")
    print_menu_option("0", "Back to main menu")

    choice = input(f"{Fore.YELLOW}Select an option: ")

    if choice == "1":
        current_pass = input("Enter current master password: ")

        if not authenticate(current_pass):
            print_error("Incorrect password")
            return

        new_pass = input("Enter new master password: ")
        confirm_pass = input("Confirm new master password: ")

        if new_pass != confirm_pass:
            print_error("Passwords do not match")
            return

        if len(new_pass) < 8:
            print_error("Password must be at least 8 characters")
            return

        score, _ = evaluate_password_strength(new_pass)
        if score < 3:
            confirm = input("This master password is weak. Use it anyway? (y/n): ")
            if confirm.lower() != "y":
                print_warning("Password change canceled")
                return

        set_master_password(new_pass)
        set_master_password_context(new_pass)

        # Re-wrap encryption key if protection enabled
        if is_key_protected():
            try:
                unprotect_key(current_pass)
                protect_key_with_master_password(new_pass)
                print_success(
                    "Master password changed and encryption key re-protected"
                )
            except Exception as exc:
                print_warning(
                    "Password changed but key re-protection failed: " + str(exc)
                )
        else:
            print_success("Master password changed successfully")

        log_info("Master password changed")

    elif choice == "2":
        key_management_menu()

    elif choice == "3":
        kdf_tuning_wizard()

    elif choice == "4":
        print_header("System Information")

        # Database info
        conn = sqlite3.connect(str(get_database_path()))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM passwords")
        password_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM passwords WHERE expiry_date IS NOT NULL")
        expiring_count = cursor.fetchone()[0]

        conn.close()

        print(f"Total passwords: {password_count}")
        print(f"Total categories: {category_count}")
        print(f"Passwords with expiry: {expiring_count}")

        # File info
        db_path = get_database_path()
        db_size = db_path.stat().st_size if db_path.exists() else 0
        print(f"Database size: {db_size / 1024:.2f} KB")

        key_path = get_secret_key_path()
        enc_key_path = get_secret_key_enc_path()
        key_exists = key_path.exists() or enc_key_path.exists()
        print(f"Encryption key: {'Present' if key_exists else 'Missing'}")

        # Version info
        with open("VERSION.txt") as f:
            version = f.read().strip()

        print(f"Password Manager version: {version}")

        input("\nPress Enter to continue...")

    elif choice == "5":
        confirm = input("Are you sure you want to clear logs? (y/n): ")
        if confirm.lower() == "y":
            from utils.logger import clear_logs

            if clear_logs(backup=True):
                print_success("Logs cleared with backup")
            else:
                print_error("Failed to clear logs")

    elif choice == "6":
        twofa_menu()

    elif choice == "7":
        browser_bridge_menu()


def twofa_menu() -> None:
    """Configure two-factor authentication."""
    print_header("Two-Factor Authentication")

    if is_2fa_enabled():
        print_success("Two-factor authentication is currently enabled.")
        print("\nOptions:")
        print_menu_option("1", "Disable 2FA")
        print_menu_option("2", "Test 2FA")
        print_menu_option("0", "Back to settings")

        choice = input(f"{Fore.YELLOW}Select an option: ")

        if choice == "1":
            confirm = input(
                "Are you sure you want to disable 2FA? This will reduce security. (y/n): "
            )
            if confirm.lower() == "y":
                if disable_2fa():
                    print_success("Two-factor authentication disabled.")
                    log_info("Two-factor authentication disabled")
                else:
                    print_error("Failed to disable 2FA.")

        elif choice == "2":
            code = input("Enter the code from your authenticator app: ")
            if verify_totp(code):
                print_success("Code verified successfully.")
            else:
                print_error(
                    "Invalid code. Please make sure your authenticator app is synchronized."
                )

    else:
        print_warning("Two-factor authentication is currently disabled.")
        print("Enabling 2FA adds an extra layer of security to your password manager.")
        print(
            "You'll need an authenticator app like Google Authenticator, Authy, or Microsoft Authenticator."
        )

        if input("\nWould you like to enable 2FA now? (y/n): ").lower() == "y":
            # Generate a secret key and QR code
            secret, qr_path = setup_totp()

            print("\nSetup instructions:")
            print("1. Open your authenticator app")
            print("2. Add a new account by scanning this QR code:")
            print(f"   QR code saved to: {qr_path}")
            print("3. Or manually enter this secret key:")
            print(f"   {secret}")

            # Verify setup
            print("\nTo verify setup, enter the code from your authenticator app:")
            for attempt in range(3):
                code = input("Code: ")
                if verify_totp(code):
                    print_success("Two-factor authentication enabled successfully!")
                    log_info("Two-factor authentication enabled")
                    break
                else:
                    print_error(f"Invalid code. {2 - attempt} attempts remaining.")
            else:
                print_error("Failed to verify 2FA setup. 2FA has not been enabled.")
                disable_2fa()


def browser_bridge_menu() -> None:
    """Configure and inspect the browser bridge service."""
    service = get_browser_bridge_service()

    while True:
        settings = _get_browser_bridge_settings()
        endpoint = f"http://{settings.get('host', '127.0.0.1')}:{settings.get('port', 43110)}"

        print_header("Browser Bridge (Experimental)")
        print(f"Enabled: {'Yes' if settings.get('enabled') else 'No'}")
        print(f"Service running: {'Yes' if service.is_running else 'No'}")
        print(f"Endpoint: {endpoint}")
        print_menu_option("1", "Toggle enable/disable")
        print_menu_option("2", "Start/stop service")
        print_menu_option("3", "Generate pairing code")
        print_menu_option("4", "View active tokens")
        print_menu_option("5", "Revoke token")
        print_menu_option("0", "Back to settings")

        choice = input(f"{Fore.YELLOW}Select an option: ").strip()

        if choice == "1":
            enabled = not settings.get("enabled", False)
            config.update_settings({"browser_bridge": {"enabled": enabled}})
            if enabled:
                service.start()
                log_info("Browser bridge enabled via CLI settings")
                print_success("Browser bridge enabled and started")
            else:
                service.stop()
                log_info("Browser bridge disabled via CLI settings")
                print_warning("Browser bridge disabled and stopped")

        elif choice == "2":
            if service.is_running:
                service.stop()
                print_success("Browser bridge stopped")
            else:
                service.start()
                print_success("Browser bridge started")

        elif choice == "3":
            if not service.is_running:
                print_warning("Start the browser bridge before generating a pairing code.")
                continue
            record = service.generate_pairing_code()
            expires = time.strftime("%H:%M:%S", time.localtime(record["expires_at"]))
            print_success(
                f"Pairing code: {record['code']} (expires at {expires})"
            )

        elif choice == "4":
            tokens = service.list_tokens()
            if not tokens:
                print_warning("No active tokens.")
            else:
                print("\nActive tokens:")
                _print_tokens(tokens)
                input("\nPress Enter to continue...")

        elif choice == "5":
            tokens = service.list_tokens()
            if not tokens:
                print_warning("No tokens to revoke.")
                continue
            _print_tokens(tokens)
            selection = input("Enter token number to revoke: ")
            if not selection.isdigit():
                print_error("Invalid selection")
                continue
            index = int(selection) - 1
            if not 0 <= index < len(tokens):
                print_error("Invalid selection")
                continue
            token_value = tokens[index]["token"]
            if service.revoke_token(token_value):
                print_success("Token revoked")
            else:
                print_error("Failed to revoke token")

        elif choice == "0":
            break

        else:
            print_error("Invalid option, please try again.")


def _print_tokens(tokens: List[Dict[str, Any]]) -> None:
    for idx, token in enumerate(tokens, start=1):
        expires = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token["expires_at"]))
        fingerprint = token.get("fingerprint", "unknown")
        browser = token.get("browser", "unknown")
        preview = f"{token['token'][:6]}...{token['token'][-4:]}"
        print(
            f"[{idx}] {preview} | {browser} | fingerprint={fingerprint} | expires={expires}"
        )


def _format_key_mode_label(mode: str) -> str:
    return (
        "Master-password-derived (no secret.key)"
        if mode == KEY_MODE_PASSWORD
        else "File key (secret.key on disk)"
    )


def key_management_menu() -> None:
    """Allow users to switch between key management modes."""
    while True:
        mode = get_key_mode()
        print_header("Key Management Mode")
        print(f"Current mode: {_format_key_mode_label(mode)}")
        key_present = get_secret_key_path().exists() or get_secret_key_enc_path().exists()
        print(f"Secret key files present: {'Yes' if key_present else 'No'}")
        print_menu_option("1", "Switch to master-password-derived mode")
        print_menu_option("2", "Switch to file-key mode")
        print_menu_option("0", "Back to settings")

        choice = input(f"{Fore.YELLOW}Select an option: ").strip()
        if choice == "0":
            break
        if choice not in {"1", "2"}:
            print_error("Invalid option, please try again.")
            continue

        target = KEY_MODE_PASSWORD if choice == "1" else KEY_MODE_FILE
        if target == mode:
            print_warning("Already using that key mode.")
            continue

        master_password = input("Re-enter master password to confirm: ")
        if not authenticate(master_password):
            print_error("Master password verification failed.")
            continue

        print_warning("Re-encrypting vault. This may take a moment...")
        try:
            result = switch_key_mode(target, master_password)
            set_master_password_context(master_password)
            log_info(f"Switched key mode to {target}")
            print_success(
                f"Switched to {_format_key_mode_label(target)}"
                f" (re-encrypted {result['entries_reencrypted']} entries)"
            )
        except KeyManagementError as exc:
            print_error(f"Failed to switch key mode: {exc}")


def kdf_tuning_wizard() -> None:
    """Interactive wizard that benchmarks and updates PBKDF2 parameters."""
    settings = config.load_settings()
    current_iteration_setting = settings.get("key_management", {}).get(
        "kdf_iterations", 390_000
    )
    target_default = settings.get("key_management", {}).get("benchmark_target_ms", 350)
    salt, crypto_iterations, _ = load_kdf_params()

    print_header("KDF Tuning Wizard")
    print(f"Master password hash iterations: {current_iteration_setting:,}")
    print(f"Encryption/key-wrapping iterations: {crypto_iterations:,}")
    print(f"Salt size: {len(salt)} bytes")

    target_input = input(
        f"Target unlock time in milliseconds [{target_default}]: "
    ).strip()
    if target_input:
        try:
            target_ms = int(target_input)
        except ValueError:
            print_error("Invalid target value.")
            return
    else:
        target_ms = target_default

    if target_ms < 50:
        print_error("Target must be at least 50 ms.")
        return

    config.update_settings({"key_management": {"benchmark_target_ms": target_ms}})
    print_warning("Running PBKDF2 benchmark...")

    try:
        benchmark = benchmark_kdf(target_ms)
    except KeyManagementError as exc:
        print_error(f"Benchmark failed: {exc}")
        return

    samples = benchmark.get("samples", [])
    if samples:
        print("\nSamples:")
        for sample in samples:
            print(
                f"  - {sample['iterations']:,} iterations -> {sample['duration_ms']:.1f} ms"
            )

    recommended = benchmark["recommended_iterations"]
    est_ms = benchmark["estimated_duration_ms"]
    print_success(
        f"Recommended iterations: {recommended:,} (~{est_ms:.1f} ms on this machine)"
    )

    apply_choice = input("Apply these parameters now? (y/n): ").strip().lower()
    if apply_choice != "y":
        return

    salt_prompt = input(f"Salt size in bytes (default {len(salt)}): ").strip()
    salt_bytes = len(salt)
    if salt_prompt:
        try:
            salt_bytes = int(salt_prompt)
        except ValueError:
            print_error("Invalid salt size.")
            return

    master_password = input("Re-enter master password to confirm: ")
    print_warning("Applying new KDF parameters. This may take a moment...")

    try:
        summary = apply_kdf_parameters(master_password, recommended, salt_bytes)
        set_master_password_context(master_password)
        log_info(
            "KDF parameters updated via CLI wizard"
        )
    except KeyManagementError as exc:
        print_error(f"Failed to update KDF parameters: {exc}")
        return

    print_success(
        f"Updated KDF to {summary['iterations']:,} iterations with {summary['salt_bytes']} byte salt"
    )
    entries = summary.get("entries_reencrypted", 0)
    if entries:
        print(f"Re-encrypted {entries} stored passwords.")
    if summary.get("password_mode"):
        print("Master-password-derived vault re-wrapped with new parameters.")


def login() -> bool:
    """Prompt for master password and authenticate."""
    print_header("Password Manager Login")

    # Check if first run - use proper path
    from secure_password_manager.utils.paths import get_auth_json_path

    auth_file = str(get_auth_json_path())

    if not os.path.exists(auth_file):
        print_warning("First-time setup. You'll need to create a master password.")
        print("This password will protect all your stored passwords.")
        print("Make sure it's secure and you don't forget it!")

        while True:
            password = input("\nCreate master password: ")
            confirm = input("Confirm master password: ")

            if password != confirm:
                print_error("Passwords don't match. Try again.")
                continue

            if len(password) < 8:
                print_error("Password must be at least 8 characters")
                return False

            score, _ = evaluate_password_strength(password)
            if score < 3:
                confirm = input("This master password is weak. Use it anyway? (y/n): ")
                if confirm.lower() != "y":
                    print_warning("Setup canceled")
                    return False

            # Set the master password
            set_master_password(password)
            set_master_password_context(password)

            print_success("Master password created successfully")
            log_info("Master password created")
            return True

    # Existing user - authenticate
    for attempt in range(3):
        password = input("Enter master password: ")

        if authenticate(password):
            # Set master password context after successful authentication
            set_master_password_context(password)

            # Try to load the key to verify everything works
            try:
                from secure_password_manager.utils.crypto import load_key

                load_key()
            except ValueError as e:
                print_error(f"Failed to load encryption key: {e}")
                print_error("This could mean:")
                print_error("1. The encryption key file is corrupted")
                print_error("2. The key protection is misconfigured")
                print_error("\nPlease restore from backup or start fresh.")
                return False

            return True

        if attempt < 2:
            print_warning(f"Incorrect password. {2 - attempt} attempts remaining.")

    return False


def main() -> int:
    """Main entry point for command line application."""
    init_db()

    try:
        # Try authentication up to 3 times
        authenticated = False
        for attempt in range(3):
            if login():
                authenticated = True
                break
            print_warning(f"Login failed. {2 - attempt} attempts remaining.")

        if not authenticated:
            print_error("Too many failed attempts. Exiting.")
            return 1

        sync_browser_bridge_with_settings()

        while True:
            main_menu()
            choice = input(f"{Fore.YELLOW}Select an option: ")

            if choice == "1":
                passwords_menu()
                password_choice = input(f"{Fore.YELLOW}Select an option: ")
                if password_choice == "1":
                    add_new_password()
                elif password_choice == "2":
                    view_passwords()
                elif password_choice == "3":
                    search_passwords()
                elif password_choice == "4":
                    edit_password()
                elif password_choice == "5":
                    delete_password_entry()
                elif password_choice == "6":
                    generate_password_tool()
                elif password_choice == "7":
                    check_expiring_passwords()
                elif password_choice == "0":
                    continue
                else:
                    print_error("Invalid option, please try again.")

            elif choice == "2":
                categories_menu()

            elif choice == "3":
                backup_menu()

            elif choice == "4":
                settings_menu()

            elif choice == "5":
                view_logs()

            elif choice == "6":
                security_audit_menu()

            elif choice == "0":
                print(Fore.MAGENTA + "Goodbye!")
                break

            else:
                print_error("Invalid option, please try again.")

        return 0
    finally:
        shutdown_browser_bridge()


if __name__ == "__main__":
    sys.exit(main())
