"""Main application module for the Password Manager."""
from utils.crypto import encrypt_password, decrypt_password
from utils.database import init_db, add_password, get_passwords, delete_password
from utils.ui import (
    print_header, print_success, print_error, print_warning,
    print_menu_option, print_table
)
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

def main_menu() -> None:
    """Display the main menu options to the user."""
    print_header("Password Manager")
    print_menu_option("1", "Add a new password")
    print_menu_option("2", "View saved passwords")
    print_menu_option("3", "Delete a password")
    print_menu_option("4", "Exit", Fore.RED)

def add_new_password() -> None:
    """Prompt user for new password details and save to database with encryption."""
    print_header("Add New Password")
    website = input("Website: ")
    username = input("Username: ")
    password = input("Password: ")
    encrypted = encrypt_password(password)
    add_password(website, username, encrypted)
    print_success("Password added successfully!")

def view_passwords() -> None:
    """Retrieve and display all saved passwords in a readable format."""
    print_header("Saved Passwords")
    passwords = get_passwords()
    if not passwords:
        print_error("No passwords saved yet.")
        return

    rows = []
    for entry in passwords:
        entry_id, website, username, encrypted = entry
        decrypted = decrypt_password(encrypted)
        rows.append([entry_id, website, username, decrypted])
    
    print_table(["ID", "Website", "Username", "Password"], rows)

def delete_password_entry() -> None:
    """Delete a password entry by ID after user confirmation."""
    print_header("Delete Password")
    entry_id = input("Enter ID of the password to delete: ")
    try:
        delete_password(int(entry_id))
        print_success("Password deleted successfully!")
    except ValueError:
        print_error("Invalid ID. Please enter a number.")

if __name__ == "__main__":
    init_db()
    
    while True:
        main_menu()
        choice = input(f"{Fore.YELLOW}Select an option: ")

        if choice == '1':
            add_new_password()
        elif choice == '2':
            view_passwords()
        elif choice == '3':
            delete_password_entry()
        elif choice == '4':
            print(Fore.MAGENTA + "Goodbye!")
            break
        else:
            print_error("Invalid option, please try again.")
