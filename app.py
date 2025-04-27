"""Main application module for the Password Manager."""
from utils.crypto import encrypt_password, decrypt_password
from utils.database import init_db, add_password, get_passwords, delete_password
from utils.ui import (
    print_header, print_success, print_error, print_warning,
    print_menu_option, print_table
)
from utils.auth import authenticate
from utils.password_strength import evaluate_password_strength, generate_secure_password
from utils.backup import export_passwords, import_passwords
from colorama import Fore, Style, init
import os

# Initialize Colorama
init(autoreset=True)

def main_menu() -> None:
    """Display the main menu options to the user."""
    print_header("Password Manager")
    print_menu_option("1", "Add a new password")
    print_menu_option("2", "View saved passwords")
    print_menu_option("3", "Delete a password")
    print_menu_option("5", "Export passwords")
    print_menu_option("6", "Import passwords")
    print_menu_option("4", "Exit", Fore.RED)

def add_new_password() -> None:
    """Prompt user for new password details and save to database with encryption."""
    print_header("Add New Password")
    website = input("Website: ")
    username = input("Username: ")
    
    # Add option for generated password
    use_generated = input("Generate secure password? (y/n): ").lower() == 'y'
    
    if use_generated:
        password = generate_secure_password()
        print_success(f"Generated password: {password}")
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
        
        if score < 3:
            confirm = input("This password is weak. Use it anyway? (y/n): ")
            if confirm.lower() != 'y':
                print_warning("Password entry canceled")
                return
    
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

def login() -> bool:
    """Prompt for master password and authenticate."""
    print_header("Password Manager Login")
    password = input("Enter master password: ")
    if authenticate(password):
        print_success("Authentication successful")
        return True
    else:
        print_error("Incorrect password")
        return False

def export_passwords_menu() -> None:
    """Menu option to export passwords."""
    print_header("Export Passwords")
    filename = input("Enter filename to export to (default: backup.dat): ")
    if not filename:
        filename = "backup.dat"
    
    master_pass = input("Enter master password to encrypt backup: ")
    
    if export_passwords(filename, master_pass):
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

if __name__ == "__main__":
    init_db()
    
    # Try authentication up to 3 times
    authenticated = False
    for attempt in range(3):
        if login():
            authenticated = True
            break
        print_warning(f"Login failed. {2-attempt} attempts remaining.")
    
    if not authenticated:
        print_error("Too many failed attempts. Exiting.")
        exit(1)
    
    while True:
        main_menu()
        choice = input(f"{Fore.YELLOW}Select an option: ")

        if choice == '1':
            add_new_password()
        elif choice == '2':
            view_passwords()
        elif choice == '3':
            delete_password_entry()
        elif choice == '5':
            export_passwords_menu()
        elif choice == '6':
            import_passwords_menu()
        elif choice == '4':
            print(Fore.MAGENTA + "Goodbye!")
            break
        else:
            print_error("Invalid option, please try again.")
