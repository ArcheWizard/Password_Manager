"""GUI version of the Password Manager."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

from utils.crypto import encrypt_password, decrypt_password
from utils.database import init_db, add_password, get_passwords, delete_password
from utils.auth import authenticate
from utils.password_strength import evaluate_password_strength, generate_secure_password
from utils.backup import export_passwords, import_passwords

class PasswordManagerApp(tk.Tk):
    """Main GUI application for the Password Manager."""
    
    def __init__(self):
        super().__init__()
        self.title("Password Manager")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Initialize database
        init_db()
        
        # Master password check
        self.authenticate()
        
        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create widgets
        self.create_widgets()
        
    def authenticate(self):
        """Prompt for master password and verify."""
        for attempt in range(3):
            password = simpledialog.askstring("Login", 
                                             "Enter master password:", 
                                             show='*')
            if password is None:  # User cancelled
                self.quit()
                return
                
            if authenticate(password):
                return
                
            if attempt < 2:
                messagebox.showerror("Login Failed", 
                                     f"Incorrect password. {2-attempt} attempts remaining.")
            
        messagebox.showerror("Login Failed", "Too many failed attempts. Exiting.")
        self.quit()
        
    def create_widgets(self):
        """Create all the widgets for the application."""
        # Buttons frame
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Add Password", 
                  command=self.add_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Password", 
                  command=self.delete_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export", 
                  command=self.export_passwords).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Import", 
                  command=self.import_passwords).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", 
                  command=self.refresh_passwords).pack(side=tk.LEFT, padx=5)
        
        # Passwords table
        self.tree = ttk.Treeview(self.main_frame, columns=('ID', 'Website', 'Username', 'Password'))
        self.tree.heading('ID', text='ID')
        self.tree.heading('Website', text='Website')
        self.tree.heading('Username', text='Username')
        self.tree.heading('Password', text='Password')
        
        # Column widths
        self.tree.column('ID', width=40, stretch=tk.NO)
        self.tree.column('Website', width=150)
        self.tree.column('Username', width=150)
        self.tree.column('Password', width=200)
        
        # Hide the first column (which shows a default empty heading)
        self.tree['show'] = 'headings'
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        ttk.Label(self.main_frame, textvariable=self.status_var, 
                 relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, side=tk.BOTTOM)
        
        # Initial load
        self.refresh_passwords()
        
    def refresh_passwords(self):
        """Load passwords into the treeview."""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get passwords
        passwords = get_passwords()
        
        # Insert into tree
        for entry in passwords:
            entry_id, website, username, encrypted = entry
            decrypted = decrypt_password(encrypted)
            self.tree.insert('', 'end', values=(entry_id, website, username, decrypted))
            
        # Update status
        self.status_var.set(f"{len(passwords)} passwords stored")
        
    def add_password(self):
        """Add a new password."""
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add Password")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Website
        ttk.Label(dialog, text="Website:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        website_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=website_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # Username
        ttk.Label(dialog, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        username_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=username_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # Password
        ttk.Label(dialog, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show='*', width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # Strength indicator
        strength_var = tk.StringVar()
        ttk.Label(dialog, textvariable=strength_var).grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Generate button
        def generate():
            password = generate_secure_password()
            password_var.set(password)
            strength_var.set("Strength: Very Strong")
            
        ttk.Button(dialog, text="Generate Password", command=generate).grid(row=2, column=2, padx=10, pady=10)
        
        # Check password strength when modified
        def check_strength(*args):
            password = password_var.get()
            if password:
                score, description = evaluate_password_strength(password)
                strength_var.set(f"Strength: {description}")
            else:
                strength_var.set("")
                
        password_var.trace_add("write", check_strength)
        
        # Save button
        def save():
            website = website_var.get()
            username = username_var.get()
            password = password_var.get()
            
            if not (website and username and password):
                messagebox.showerror("Error", "All fields are required")
                return
                
            # Check strength
            if password and password_var.get() == password:  # Not auto-generated
                score, _ = evaluate_password_strength(password)
                if score < 3:
                    confirm = messagebox.askyesno("Weak Password", 
                                               "This password is weak. Use it anyway?")
                    if not confirm:
                        return
            
            encrypted = encrypt_password(password)
            add_password(website, username, encrypted)
            dialog.destroy()
            self.refresh_passwords()
            messagebox.showinfo("Success", "Password added successfully")
            
        ttk.Button(dialog, text="Save", command=save).grid(row=4, column=1, pady=20)
        
    def delete_password(self):
        """Delete the selected password."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "No password selected")
            return
            
        # Get ID from the selected item
        entry_id = self.tree.item(selected[0])['values'][0]
        
        confirm = messagebox.askyesno("Confirm", 
                                    "Are you sure you want to delete this password?")
        if confirm:
            delete_password(entry_id)
            self.refresh_passwords()
            messagebox.showinfo("Success", "Password deleted successfully")
            
    def export_passwords(self):
        """Export passwords to file."""
        filename = simpledialog.askstring("Export", 
                                        "Enter filename to export to:",
                                        initialvalue="backup.dat")
        if not filename:
            return
            
        password = simpledialog.askstring("Export", 
                                        "Enter master password to encrypt backup:",
                                        show='*')
        if not password:
            return
            
        if export_passwords(filename, password):
            messagebox.showinfo("Success", f"Passwords exported to {filename}")
        else:
            messagebox.showerror("Error", "No passwords to export")
            
    def import_passwords(self):
        """Import passwords from file."""
        filename = simpledialog.askstring("Import", 
                                        "Enter filename to import from:")
        if not filename or not os.path.exists(filename):
            messagebox.showerror("Error", f"File {filename} not found")
            return
            
        password = simpledialog.askstring("Import", 
                                        "Enter master password to decrypt backup:",
                                        show='*')
        if not password:
            return
            
        count = import_passwords(filename, password)
        if count > 0:
            self.refresh_passwords()
            messagebox.showinfo("Success", f"Imported {count} passwords successfully")
        else:
            messagebox.showerror("Error", "Failed to import passwords")

if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()