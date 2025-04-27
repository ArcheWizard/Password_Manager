"""PyQt5 version of the Password Manager."""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                            QLineEdit, QTableWidget, QTableWidgetItem,
                            QDialog, QFormLayout, QMessageBox, QInputDialog,
                            QDialogButtonBox, QFileDialog, QTabWidget,
                            QComboBox, QCheckBox, QGroupBox, QSplitter,
                            QHeaderView, QStatusBar, QToolBar, QAction)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

from utils.crypto import encrypt_password, decrypt_password
from utils.database import init_db, add_password, get_passwords, delete_password, get_categories
from utils.auth import authenticate
from utils.password_analysis import evaluate_password_strength, generate_secure_password
from utils.backup import export_passwords, import_passwords
from utils.security_audit import run_security_audit
from utils.security_analyzer import analyze_password_security
import pyperclip
import time

class PasswordManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Password Manager")
        self.setGeometry(100, 100, 1000, 600)
        
        # Initialize database
        init_db()
        
        # Authenticate
        if not self.authenticate():
            sys.exit(0)
        
        # Create UI
        self.init_ui()
        
    def init_ui(self):
        # Set up central widget with tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create the password manager tab
        self.passwords_tab = QWidget()
        self.central_widget.addTab(self.passwords_tab, "Passwords")
        
        # Create the security tab
        self.security_tab = QWidget()
        self.central_widget.addTab(self.security_tab, "Security")
        
        # Create the backup tab
        self.backup_tab = QWidget()
        self.central_widget.addTab(self.backup_tab, "Backup")
        
        # Set up the password manager tab
        self.setup_passwords_tab()
        
        # Set up the security tab
        self.setup_security_tab()
        
        # Set up the backup tab
        self.setup_backup_tab()
        
        # Create toolbar
        self.create_toolbar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Load passwords
        self.refresh_passwords()
        
    def create_toolbar(self):
        """Create a toolbar with common actions"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        
        # Add Password Action
        add_action = QAction("Add Password", self)
        add_action.triggered.connect(self.add_password)
        toolbar.addAction(add_action)
        
        # Copy Password Action
        copy_action = QAction("Copy Password", self)
        copy_action.triggered.connect(self.copy_password)
        toolbar.addAction(copy_action)
        
        # Refresh Action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_passwords)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Export Action
        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_passwords)
        toolbar.addAction(export_action)
        
        # Import Action
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.import_passwords)
        toolbar.addAction(import_action)
        
    def setup_passwords_tab(self):
        """Set up the passwords tab UI"""
        layout = QVBoxLayout(self.passwords_tab)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        categories = get_categories()
        for name, _ in categories:
            self.category_combo.addItem(name)
        self.category_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_combo)
        
        # Search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_edit)
        
        # Show expired checkbox
        self.show_expired = QCheckBox("Show Expired")
        self.show_expired.setChecked(True)
        self.show_expired.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.show_expired)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Website", "Username", "Password", "Category", "Created", "Expires"])
        
        # Set column widths
        self.table.setColumnWidth(0, 60)  # Slightly wider for ID
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 120)  # Narrower for password
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        
        # Improved styling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # Select entire rows
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make it read-only
        self.table.verticalHeader().setVisible(False)  # Hide vertical header
        self.table.horizontalHeader().setStretchLastSection(True)  # Stretch last section
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Stretch website column
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Stretch username column
        self.table.setSortingEnabled(True)  # Enable sorting
        
        # Context menu for table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Password")
        add_btn.clicked.connect(self.add_password)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit Password")
        edit_btn.clicked.connect(self.edit_password)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete Password")
        delete_btn.clicked.connect(self.delete_password)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        copy_btn = QPushButton("Copy Password")
        copy_btn.clicked.connect(self.copy_password)
        btn_layout.addWidget(copy_btn)
        
        layout.addLayout(btn_layout)
    
    def setup_security_tab(self):
        """Set up the security audit tab UI"""
        layout = QVBoxLayout(self.security_tab)
        
        # Security score section
        score_group = QGroupBox("Security Score")
        score_layout = QVBoxLayout(score_group)
        
        self.score_label = QLabel("Your security score: Not calculated")
        score_layout.addWidget(self.score_label)
        
        layout.addWidget(score_group)
        
        # Issues section
        issues_group = QGroupBox("Security Issues")
        issues_layout = QVBoxLayout(issues_group)
        
        self.weak_label = QLabel("Weak passwords: Not calculated")
        issues_layout.addWidget(self.weak_label)
        
        self.reused_label = QLabel("Reused passwords: Not calculated")
        issues_layout.addWidget(self.reused_label)
        
        self.expired_label = QLabel("Expired passwords: Not calculated")
        issues_layout.addWidget(self.expired_label)
        
        self.breached_label = QLabel("Breached passwords: Not calculated")
        issues_layout.addWidget(self.breached_label)
        
        layout.addWidget(issues_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        run_audit_btn = QPushButton("Run Security Audit")
        run_audit_btn.clicked.connect(self.run_security_audit)
        actions_layout.addWidget(run_audit_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
    
    def setup_backup_tab(self):
        """Set up the backup tab UI"""
        layout = QVBoxLayout(self.backup_tab)
        
        # Export section
        export_group = QGroupBox("Export Passwords")
        export_layout = QVBoxLayout(export_group)
        
        export_desc = QLabel("Export your passwords to an encrypted file that can be used to restore them later.")
        export_layout.addWidget(export_desc)
        
        export_btn = QPushButton("Export Passwords")
        export_btn.clicked.connect(self.export_passwords)
        export_layout.addWidget(export_btn)
        
        layout.addWidget(export_group)
        
        # Import section
        import_group = QGroupBox("Import Passwords")
        import_layout = QVBoxLayout(import_group)
        
        import_desc = QLabel("Import passwords from a previously exported file.")
        import_layout.addWidget(import_desc)
        
        import_btn = QPushButton("Import Passwords")
        import_btn.clicked.connect(self.import_passwords)
        import_layout.addWidget(import_btn)
        
        layout.addWidget(import_group)
        
        # Full backup section
        backup_group = QGroupBox("Full Backup")
        backup_layout = QVBoxLayout(backup_group)
        
        backup_desc = QLabel("Create a complete backup including your database, encryption keys, and settings.")
        backup_layout.addWidget(backup_desc)
        
        backup_btn = QPushButton("Create Full Backup")
        backup_btn.clicked.connect(self.create_full_backup)
        backup_layout.addWidget(backup_btn)
        
        layout.addWidget(backup_group)
        
        # Restore section
        restore_group = QGroupBox("Restore from Backup")
        restore_layout = QVBoxLayout(restore_group)
        
        restore_desc = QLabel("Restore your passwords and settings from a full backup.")
        restore_layout.addWidget(restore_desc)
        
        restore_btn = QPushButton("Restore from Backup")
        restore_btn.clicked.connect(self.restore_from_backup)
        restore_layout.addWidget(restore_btn)
        
        layout.addWidget(restore_group)
        
        layout.addStretch()
        
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
        """Refresh the password table with current filters"""
        self.apply_filters()
        
    def apply_filters(self):
        """Apply category and search filters to password list."""
        # Clear table
        self.table.setRowCount(0)
        
        # Get filter values
        category = None
        if self.category_combo.currentIndex() > 0:
            category = self.category_combo.currentText()
            
        search_term = self.search_edit.text() if self.search_edit.text() else None
        show_expired = self.show_expired.isChecked()
        
        # Get passwords with filters
        passwords = get_passwords(category, search_term, show_expired)
        
        # Fill table
        self.table.setRowCount(len(passwords))
        for row, entry in enumerate(passwords):
            entry_id, website, username, encrypted, category, notes, created, updated, expiry, favorite = entry
            decrypted = decrypt_password(encrypted)
            
            # Format dates
            created_str = time.strftime('%Y-%m-%d', time.localtime(created))
            
            # Format expiry
            if expiry:
                days_left = int((expiry - time.time()) / 86400)
                if days_left < 0:
                    expiry_str = "EXPIRED"
                else:
                    expiry_str = f"{days_left} days"
            else:
                expiry_str = "Never"
            
            # Set the items with appropriate colors - FIXED ID DISPLAY
            id_item = QTableWidgetItem(str(entry_id))
            id_item.setTextAlignment(Qt.AlignCenter)  # Center the ID value
            self.table.setItem(row, 0, id_item)
            
            website_item = QTableWidgetItem(website)
            if favorite:
                website_item.setForeground(QColor("#ffd700"))  # Gold for favorites
            self.table.setItem(row, 1, website_item)
            
            username_item = QTableWidgetItem(username)
            self.table.setItem(row, 2, username_item)
            
            password_item = QTableWidgetItem("••••••••")  # Mask password
            password_item.setData(Qt.UserRole, decrypted)  # Store real password as data
            password_item.setTextAlignment(Qt.AlignCenter)  # Center the dots
            self.table.setItem(row, 3, password_item)
            
            category_item = QTableWidgetItem(category)
            self.table.setItem(row, 4, category_item)
            
            created_item = QTableWidgetItem(created_str)
            created_item.setTextAlignment(Qt.AlignCenter)  # Center the date
            self.table.setItem(row, 5, created_item)
            
            expiry_item = QTableWidgetItem(expiry_str)
            expiry_item.setTextAlignment(Qt.AlignCenter)  # Center the expiry info
            if expiry and days_left < 0:
                expiry_item.setForeground(QColor("red"))
            elif expiry and days_left < 7:
                expiry_item.setForeground(QColor("orange"))
            self.table.setItem(row, 6, expiry_item)
            
        self.statusBar().showMessage(f"{len(passwords)} passwords found")
    
    def show_context_menu(self, position):
        """Show context menu for table items"""
        menu = QDialog(self)
        menu.setWindowTitle("Options")
        menu.setFixedWidth(200)
        
        layout = QVBoxLayout(menu)
        
        copy_btn = QPushButton("Copy Password")
        copy_btn.clicked.connect(lambda: self.copy_password(auto_close=menu))
        layout.addWidget(copy_btn)
        
        toggle_btn = QPushButton("Toggle Favorite")
        toggle_btn.clicked.connect(lambda: self.toggle_favorite(auto_close=menu))
        layout.addWidget(toggle_btn)
        
        edit_btn = QPushButton("Edit Password")
        edit_btn.clicked.connect(lambda: self.edit_password(auto_close=menu))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete Password")
        delete_btn.clicked.connect(lambda: self.delete_password(auto_close=menu))
        layout.addWidget(delete_btn)
        
        show_btn = QPushButton("Show Password")
        show_btn.clicked.connect(lambda: self.show_password(auto_close=menu))
        layout.addWidget(show_btn)
        
        menu.move(self.mapToGlobal(position))
        menu.exec_()
        
    def copy_password(self, auto_close=None):
        """Copy selected password to clipboard"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        # Get password from the third column (index 3) of the selected row
        row = selected[0].row()
        password_item = self.table.item(row, 3)
        password = password_item.data(Qt.UserRole)  # Get the stored password
        
        pyperclip.copy(password)
        self.statusBar().showMessage("Password copied to clipboard", 2000)
        
        if auto_close:
            auto_close.close()
    
    def show_password(self, auto_close=None):
        """Temporarily show the selected password"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        row = selected[0].row()
        password_item = self.table.item(row, 3)
        password = password_item.data(Qt.UserRole)
        
        password_item.setText(password)
        
        # Reset after 3 seconds
        QTimer.singleShot(3000, lambda: password_item.setText("••••••••"))
        
        if auto_close:
            auto_close.close()
    
    def toggle_favorite(self, auto_close=None):
        """Toggle favorite status for selected password"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        # TODO: Implement toggle favorite functionality
        QMessageBox.information(self, "Coming Soon", "Toggle favorite feature coming soon!")
        
        if auto_close:
            auto_close.close()
        
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
        category_combo = QComboBox()
        categories = get_categories()
        for name, _ in categories:
            category_combo.addItem(name)
        layout.addRow("Category:", category_combo)
        
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
            password_edit.setEchoMode(QLineEdit.Normal)  # Show generated password
            strength_label.setText("Very Strong")
            
        gen_btn.clicked.connect(generate)
        
        def check_strength():
            password = password_edit.text()
            if password:
                score, description = evaluate_password_strength(password)
                # Set color based on strength
                if score >= 4:
                    color = "green"
                elif score >= 3:
                    color = "orange"
                else:
                    color = "red"
                    
                strength_label.setText(f"<span style='color:{color}'>{description}</span>")
            else:
                strength_label.setText("")
                
        password_edit.textChanged.connect(check_strength)
        
        def accept():
            website = website_edit.text()
            username = username_edit.text()
            password = password_edit.text()
            category = category_combo.currentText()
            notes = notes_edit.text()
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
        
    def edit_password(self, auto_close=None):
        """Edit the selected password"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        # TODO: Implement edit password functionality
        QMessageBox.information(self, "Coming Soon", "Edit password feature coming soon!")
        
        if auto_close:
            auto_close.close()
        
    def delete_password(self, auto_close=None):
        """Delete the selected password"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "No password selected")
            return
            
        # Get ID from the first column of the selected row
        row = selected[0].row()
        entry_id = int(self.table.item(row, 0).text())
        website = self.table.item(row, 1).text()
        
        confirm = QMessageBox.question(self, "Confirm", 
                                    f"Are you sure you want to delete the password for {website}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_password(entry_id)
            self.refresh_passwords()
            self.statusBar().showMessage("Password deleted successfully")
        
        if auto_close:
            auto_close.close()
            
    def export_passwords(self):
        """Export passwords to file"""
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
        """Import passwords from file"""
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
    
    def create_full_backup(self):
        """Create a full backup of all data"""
        # TODO: Implement full backup
        QMessageBox.information(self, "Coming Soon", "Full backup feature coming soon!")
    
    def restore_from_backup(self):
        """Restore data from a full backup"""
        # TODO: Implement restore from backup
        QMessageBox.information(self, "Coming Soon", "Restore from backup feature coming soon!")
    
    def run_security_audit(self):
        """Run a security audit and display the results"""
        # Show waiting message
        self.statusBar().showMessage("Running security audit...")
        
        # TODO: Implement security audit
        QMessageBox.information(self, "Coming Soon", "Security audit feature coming soon!")
        
        self.statusBar().showMessage("Security audit complete")

def main():
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)
    
    window = PasswordManagerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()