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
from utils.database import init_db, add_password, get_passwords, delete_password, get_categories, update_password
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
            
        # Get the entry_id from the first column of the selected row
        row = selected[0].row()
        entry_id = int(self.table.item(row, 0).text())
        website = self.table.item(row, 1).text()
        
        # Get current password data to determine current favorite status
        passwords = get_passwords()
        target_entry = None
        
        for entry in passwords:
            if entry[0] == entry_id:
                target_entry = entry
                break
        
        if not target_entry:
            QMessageBox.warning(self, "Error", f"No password found with ID {entry_id}")
            return
        
        # Extract current favorite status
        _, _, _, _, _, _, _, _, _, favorite = target_entry
        
        # Toggle favorite status
        new_favorite_status = not favorite
        
        # Update the password entry
        update_password(entry_id, favorite=new_favorite_status)
        
        # Refresh the table
        self.refresh_passwords()
        
        # Show status message
        if new_favorite_status:
            self.statusBar().showMessage(f"Added {website} to favorites", 3000)
        else:
            self.statusBar().showMessage(f"Removed {website} from favorites", 3000)
        
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
            
        # Get the entry_id from the first column of the selected row
        row = selected[0].row()
        entry_id = int(self.table.item(row, 0).text())
        
        # Get current password data
        passwords = get_passwords()
        target_entry = None
        
        for entry in passwords:
            if entry[0] == entry_id:
                target_entry = entry
                break
        
        if not target_entry:
            QMessageBox.error(self, "Error", f"No password found with ID {entry_id}")
            return
        
        # Extract current values
        _, website, username, encrypted, category, notes, _, _, expiry, favorite = target_entry
        password = decrypt_password(encrypted)
        
        # Create edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Password")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Website field
        website_edit = QLineEdit(website)
        layout.addRow("Website:", website_edit)
        
        # Username field
        username_edit = QLineEdit(username)
        layout.addRow("Username:", username_edit)
        
        # Password field with toggle to change
        password_group = QGroupBox("Password")
        password_layout = QVBoxLayout(password_group)
        
        current_pwd_label = QLabel(f"Current: {'•' * 8}")
        password_layout.addWidget(current_pwd_label)
        
        change_pwd_check = QCheckBox("Change password")
        password_layout.addWidget(change_pwd_check)
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setEnabled(False)
        password_layout.addWidget(password_edit)
        
        strength_label = QLabel("")
        password_layout.addWidget(strength_label)
        
        gen_btn = QPushButton("Generate Password")
        gen_btn.setEnabled(False)
        password_layout.addWidget(gen_btn)
        
        layout.addRow(password_group)
        
        # Category selection
        category_combo = QComboBox()
        categories = get_categories()
        category_index = 0
        
        for i, (name, _) in enumerate(categories):
            category_combo.addItem(name)
            if name == category:
                category_index = i
                
        category_combo.setCurrentIndex(category_index)
        layout.addRow("Category:", category_combo)
        
        # Notes field
        notes_edit = QLineEdit(notes)
        layout.addRow("Notes:", notes_edit)
        
        # Expiry field
        expiry_days = ""
        if expiry:
            days_left = int((expiry - time.time()) / 86400) if expiry > time.time() else 0
            expiry_days = str(days_left)
            
        expiry_edit = QLineEdit(expiry_days)
        expiry_edit.setPlaceholderText("Days until expiry (empty for never)")
        layout.addRow("Expires in:", expiry_edit)
        
        # Favorite checkbox
        favorite_check = QCheckBox("Mark as favorite")
        favorite_check.setChecked(favorite)
        layout.addRow("", favorite_check)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        layout.addRow(buttons)
        
        # Connect signals
        def toggle_password_change():
            enabled = change_pwd_check.isChecked()
            password_edit.setEnabled(enabled)
            gen_btn.setEnabled(enabled)
            if enabled:
                password_edit.setFocus()
            else:
                # Clear the field when disabled
                password_edit.setText("")
                strength_label.setText("")
        
        change_pwd_check.toggled.connect(toggle_password_change)
        
        def generate():
            password = generate_secure_password()
            password_edit.setText(password)
            password_edit.setEchoMode(QLineEdit.Normal)  # Show generated password
            strength_label.setText("<span style='color:green'>Very Strong</span>")
            
        gen_btn.clicked.connect(generate)
        
        def check_strength():
            if not change_pwd_check.isChecked():
                return
                
            pwd = password_edit.text()
            if pwd:
                score, description = evaluate_password_strength(pwd)
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
            new_website = website_edit.text()
            new_username = username_edit.text()
            new_category = category_combo.currentText()
            new_notes = notes_edit.text()
            new_favorite = favorite_check.isChecked()
            
            # Validate required fields
            if not (new_website and new_username):
                QMessageBox.warning(dialog, "Error", "Website and username are required")
                return
                
            # Get new password if changed
            new_password = None
            encrypted_password = None
            if change_pwd_check.isChecked():
                new_password = password_edit.text()
                if not new_password:
                    QMessageBox.warning(dialog, "Error", "Password cannot be empty")
                    return
                    
                # Check password strength if changed
                score, _ = evaluate_password_strength(new_password)
                if score < 3:
                    confirm = QMessageBox.question(dialog, "Weak Password", 
                                              "This password is weak. Use it anyway?",
                                              QMessageBox.Yes | QMessageBox.No)
                    if confirm == QMessageBox.No:
                        return
                
                # Encrypt the new password
                encrypted_password = encrypt_password(new_password)
            
            # Parse expiry days
            expiry_days = None
            if expiry_edit.text():
                if expiry_edit.text().isdigit():
                    expiry_days = int(expiry_edit.text())
                else:
                    QMessageBox.warning(dialog, "Error", "Expiry days must be a number")
                    return
            
            # Update the password entry
            update_password(
                entry_id, 
                website=new_website if new_website != website else None,
                username=new_username if new_username != username else None,
                encrypted_password=encrypted_password,
                category=new_category if new_category != category else None,
                notes=new_notes if new_notes != notes else None,
                expiry_days=expiry_days,
                favorite=new_favorite if new_favorite != favorite else None
            )
            
            dialog.accept()
            self.refresh_passwords()
            self.statusBar().showMessage("Password updated successfully", 3000)
                
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        
        # Show dialog
        if auto_close:
            auto_close.close()
            
        dialog.exec_()
        
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
        # Get backup directory
        backup_dir = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if not backup_dir:
            return
            
        # Get master password
        password, ok = QInputDialog.getText(self, "Backup", 
                                           "Enter master password to encrypt backup:", 
                                           QLineEdit.Password)
        if not ok or not password:
            return
            
        # Show waiting cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar().showMessage("Creating backup...")
        
        try:
            # Import from backup.py
            from utils.backup import create_full_backup
            
            # Create backup
            backup_path = create_full_backup(backup_dir, password)
            
            QApplication.restoreOverrideCursor()
            
            if backup_path:
                QMessageBox.information(self, "Success", f"Full backup created at:\n{backup_path}")
                self.statusBar().showMessage("Backup created successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to create backup")
                self.statusBar().showMessage("Backup failed")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.statusBar().showMessage("Backup failed")

    def restore_from_backup(self):
        """Restore data from a full backup"""
        # Warning message
        confirm = QMessageBox.warning(self, "Warning", 
                                  "Restoring will replace your current data. Make sure you have a backup!\n\nDo you want to continue?",
                                  QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
            
        # Get backup file
        filename, _ = QFileDialog.getOpenFileName(self, "Select Backup File", 
                                               "", "Zip Files (*.zip)")
        if not filename:
            return
            
        # Get master password
        password, ok = QInputDialog.getText(self, "Restore", 
                                          "Enter master password to decrypt backup:", 
                                          QLineEdit.Password)
        if not ok or not password:
            return
            
        # Show waiting cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar().showMessage("Restoring from backup...")
        
        try:
            # Import from backup.py
            from utils.backup import restore_from_backup
            
            # Restore from backup
            success = restore_from_backup(filename, password)
            
            QApplication.restoreOverrideCursor()
            
            if success:
                msg = QMessageBox.information(self, "Success", 
                                          "Backup restored successfully. The application will now close. Please restart it.")
                QApplication.quit()
            else:
                QMessageBox.warning(self, "Error", "Failed to restore from backup")
                self.statusBar().showMessage("Restore failed")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.statusBar().showMessage("Restore failed")

    def run_security_audit(self):
        """Run a security audit and display the results"""
        # Show waiting message and cursor
        self.statusBar().showMessage("Running security audit...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            # Run the audit
            from utils.security_audit import run_security_audit
            audit_results = run_security_audit()
            
            # Restore cursor
            QApplication.restoreOverrideCursor()
            
            # Update the UI with results
            score = audit_results["score"]
            issues = audit_results["issues"]
            
            # Set score with color
            if score >= 80:
                color = "green"
            elif score >= 60:
                color = "orange"
            else:
                color = "red"
            
            self.score_label.setText(f"Your security score: <span style='color:{color};font-weight:bold;'>{score}/100</span>")
            
            # Set issue counts
            weak_count = len(issues["weak_passwords"])
            reused_count = len(issues["reused_passwords"])
            expired_count = len(issues["expired_passwords"])
            breached_count = len(issues["breached_passwords"])
            
            self.weak_label.setText(f"Weak passwords: <span style='color:{'red' if weak_count else 'green'};'>{weak_count}</span>")
            self.reused_label.setText(f"Reused passwords: <span style='color:{'red' if reused_count else 'green'};'>{reused_count}</span>")
            self.expired_label.setText(f"Expired passwords: <span style='color:{'red' if expired_count else 'green'};'>{expired_count}</span>")
            self.breached_label.setText(f"Breached passwords: <span style='color:{'red' if breached_count else 'green'};'>{breached_count}</span>")
            
            # Show detailed results if there are issues
            total_issues = weak_count + reused_count + expired_count + breached_count
            if total_issues > 0:
                msg = QMessageBox(self)
                msg.setWindowTitle("Security Audit Results")
                msg.setIcon(QMessageBox.Warning)
                
                # Create detailed message
                details = f"Security Score: {score}/100\n\n"
                details += f"Issues found:\n\n"
                
                if weak_count:
                    details += f"WEAK PASSWORDS ({weak_count}):\n"
                    for issue in issues["weak_passwords"][:5]:  # Limit to 5 for readability
                        details += f"  • {issue['website']} ({issue['username']}) - Score: {issue['score']}\n"
                    if weak_count > 5:
                        details += f"  • ... and {weak_count - 5} more\n"
                    details += "\n"
                
                if reused_count:
                    details += f"REUSED PASSWORDS ({reused_count}):\n"
                    for issue in issues["reused_passwords"][:5]:  # Limit to 5
                        sites = ", ".join([site["website"] for site in issue["reused_with"]])
                        details += f"  • {issue['website']} ({issue['username']}) - Also used on: {sites}\n"
                    if reused_count > 5:
                        details += f"  • ... and {reused_count - 5} more\n"
                    details += "\n"
                
                if expired_count:
                    details += f"EXPIRED PASSWORDS ({expired_count}):\n"
                    for issue in issues["expired_passwords"][:5]:  # Limit to 5
                        details += f"  • {issue['website']} ({issue['username']}) - Expired {issue['expired_days']} days ago\n"
                    if expired_count > 5:
                        details += f"  • ... and {expired_count - 5} more\n"
                    details += "\n"
                
                if breached_count:
                    details += f"BREACHED PASSWORDS ({breached_count}):\n"
                    for issue in issues["breached_passwords"][:5]:  # Limit to 5
                        details += f"  • {issue['website']} ({issue['username']}) - Found in {issue['breach_count']} breaches\n"
                    if breached_count > 5:
                        details += f"  • ... and {breached_count - 5} more\n"
                    
                # Set text and detailed text
                msg.setText(f"Found {total_issues} security issues with your passwords.")
                msg.setDetailedText(details)
                
                # Add recommendations
                recommendations = (
                    "Recommendations:\n\n"
                    "• Generate strong, unique passwords for each account\n"
                    "• Replace weak passwords with stronger ones\n"
                    "• Update passwords that appear in data breaches immediately\n"
                    "• Consider using two-factor authentication where available"
                )
                msg.setInformativeText(recommendations)
                
                msg.exec_()
            else:
                QMessageBox.information(self, "Security Audit", "No security issues found! Your passwords are in good shape.")
            
            self.statusBar().showMessage("Security audit complete")
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"An error occurred during the security audit: {str(e)}")
            self.statusBar().showMessage("Security audit failed")

def main():
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)
    
    window = PasswordManagerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()