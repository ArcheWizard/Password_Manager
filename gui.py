"""PyQt5 version of the Password Manager."""
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                            QLineEdit, QTableWidget, QTableWidgetItem,
                            QDialog, QFormLayout, QMessageBox, QInputDialog,
                            QDialogButtonBox, QFileDialog)
from PyQt5.QtCore import Qt

from utils.crypto import encrypt_password, decrypt_password
from utils.database import init_db, add_password, get_passwords, delete_password
from utils.auth import authenticate
from utils.password_analysis import evaluate_password_strength, generate_secure_password
from utils.backup import export_passwords, import_passwords

class PasswordManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize database
        init_db()
        
        # Authenticate
        if not self.authenticate():
            sys.exit(0)
        
        # Create UI
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Password")
        add_btn.clicked.connect(self.add_password)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Password")
        delete_btn.clicked.connect(self.delete_password)
        btn_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_passwords)
        btn_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_passwords)
        btn_layout.addWidget(import_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_passwords)
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Website", "Username", "Password"])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 250)
        layout.addWidget(self.table)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Load passwords
        self.refresh_passwords()
        
    def authenticate(self):
        for attempt in range(3):
            password, ok = QInputDialog.getText(self, "Login", 
                                              "Enter master password:", 
                                              QLineEdit.Password)
            if not ok:  # User cancelled
                return False
                
            if authenticate(password):
                return True
                
            if attempt < 2:
                QMessageBox.warning(self, "Login Failed", 
                                  f"Incorrect password. {2-attempt} attempts remaining.")
        
        QMessageBox.critical(self, "Login Failed", "Too many failed attempts.")
        return False
        
    def refresh_passwords(self):
        # Clear table
        self.table.setRowCount(0)
            
        # Get passwords
        passwords = get_passwords()
        
        # Fill table
        self.table.setRowCount(len(passwords))
        for row, entry in enumerate(passwords):
            entry_id, website, username, encrypted, category, notes, created, updated, expiry, favorite = entry
            decrypted = decrypt_password(encrypted)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(entry_id)))
            self.table.setItem(row, 1, QTableWidgetItem(website))
            self.table.setItem(row, 2, QTableWidgetItem(username))
            self.table.setItem(row, 3, QTableWidgetItem(decrypted))
            
        self.statusBar().showMessage(f"{len(passwords)} passwords stored")
        
    def add_password(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Password")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        website_edit = QLineEdit()
        layout.addRow("Website:", website_edit)
        
        username_edit = QLineEdit()
        layout.addRow("Username:", username_edit)
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", password_edit)
        
        strength_label = QLabel("")
        layout.addRow("Strength:", strength_label)
        
        # Add category selection
        category_edit = QLineEdit("General")
        layout.addRow("Category:", category_edit)
        
        # Add notes field
        notes_edit = QLineEdit()
        layout.addRow("Notes:", notes_edit)
        
        # Add expiry field
        expiry_edit = QLineEdit()
        expiry_edit.setPlaceholderText("Days until expiry (optional)")
        layout.addRow("Expires in:", expiry_edit)
        
        gen_btn = QPushButton("Generate Password")
        layout.addRow("", gen_btn)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        layout.addRow(buttons)
        
        # Connect signals
        def generate():
            password = generate_secure_password()
            password_edit.setText(password)
            strength_label.setText("Very Strong")
            
        gen_btn.clicked.connect(generate)
        
        def check_strength():
            password = password_edit.text()
            if password:
                score, description = evaluate_password_strength(password)
                strength_label.setText(description)
            else:
                strength_label.setText("")
                
        password_edit.textChanged.connect(check_strength)
        
        def accept():
            website = website_edit.text()
            username = username_edit.text()
            password = password_edit.text()
            category = category_edit.text() or "General"
            notes = notes_edit.text() or ""
            expiry_days = None
            
            if expiry_edit.text() and expiry_edit.text().isdigit():
                expiry_days = int(expiry_edit.text())
            
            if not (website and username and password):
                QMessageBox.warning(dialog, "Error", "Website, username and password are required")
                return
                
            # Check strength
            if password:
                score, _ = evaluate_password_strength(password)
                if score < 3:
                    confirm = QMessageBox.question(dialog, "Weak Password", 
                                               "This password is weak. Use it anyway?",
                                               QMessageBox.Yes | QMessageBox.No)
                    if confirm == QMessageBox.No:
                        return
            
            encrypted = encrypt_password(password)
            add_password(website, username, encrypted, category, notes, expiry_days)
            dialog.accept()
            self.refresh_passwords()
            QMessageBox.information(self, "Success", "Password added successfully")
            
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec_()
        
    def delete_password(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        # Get ID from the first column of the selected row
        row = selected[0].row()
        entry_id = int(self.table.item(row, 0).text())
        
        confirm = QMessageBox.question(self, "Confirm", 
                                    "Are you sure you want to delete this password?",
                                    QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_password(entry_id)
            self.refresh_passwords()
            QMessageBox.information(self, "Success", "Password deleted successfully")
            
    def export_passwords(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Passwords", 
                                               "", "Data Files (*.dat)")
        if not filename:
            return
            
        password, ok = QInputDialog.getText(self, "Export", 
                                          "Enter master password to encrypt backup:", 
                                          QLineEdit.Password)
        if not ok or not password:
            return
            
        if export_passwords(filename, password):
            QMessageBox.information(self, "Success", f"Passwords exported to {filename}")
        else:
            QMessageBox.warning(self, "Error", "No passwords to export")
            
    def import_passwords(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Passwords", 
                                               "", "Data Files (*.dat)")
        if not filename:
            return
            
        password, ok = QInputDialog.getText(self, "Import", 
                                          "Enter master password to decrypt backup:", 
                                          QLineEdit.Password)
        if not ok or not password:
            return
            
        count = import_passwords(filename, password)
        if count > 0:
            self.refresh_passwords()
            QMessageBox.information(self, "Success", f"Imported {count} passwords successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to import passwords")

def main():
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)
    window = PasswordManagerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()