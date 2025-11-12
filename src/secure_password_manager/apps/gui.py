"""PyQt5 version of the Password Manager."""

import sys
import time

import pyperclip
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt as QtCoreQt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from secure_password_manager.utils.auth import authenticate, set_master_password
from secure_password_manager.utils.backup import export_passwords, import_passwords
from secure_password_manager.utils.crypto import (
    decrypt_password,
    encrypt_password,
    is_key_protected,
    protect_key_with_master_password,
    set_master_password_context,
)
from secure_password_manager.utils.database import (
    add_category,
    add_password,
    delete_password,
    get_categories,
    get_passwords,
    init_db,
    update_password,
)
from secure_password_manager.utils.logger import get_log_entries
from secure_password_manager.utils.password_analysis import (
    evaluate_password_strength,
    generate_secure_password,
)
from secure_password_manager.utils.paths import get_auth_json_path
from secure_password_manager.utils.two_factor import (
    disable_2fa,
    is_2fa_enabled,
    setup_totp,
)


class PasswordManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Password Manager")
        self.setGeometry(100, 100, 1000, 600)

        # Initialize database
        init_db()

        # Authenticate and set master password context
        password = self.get_master_password()
        if password is None:
            sys.exit(0)

        # Import crypto functions
        from secure_password_manager.utils.crypto import (
            is_key_protected,
            load_key,
            set_master_password_context,
        )

        # Store password for later use (e.g., change password, protect key)
        self._master_password = password

        # Set master password context and verify key access
        if is_key_protected():
            # Key is protected, set context and verify we can decrypt it
            try:
                set_master_password_context(password)
                load_key()  # Verify we can load the protected key
            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Key Decryption Failed",
                    f"Failed to decrypt the encryption key with the provided master password.\n\n"
                    f"Error: {str(e)}\n\n"
                    "This could mean:\n"
                    "1. The master password is incorrect\n"
                    "2. The encryption key file is corrupted\n"
                    "3. The key was protected with a different password\n\n"
                    "The application will now exit.",
                )
                sys.exit(1)
        else:
            # Key is not protected, but we should still set context for potential protection later
            set_master_password_context(password)

        # Create UI
        self.init_ui()

    def get_master_password(self):
        """Prompt for master password and return it if authentication succeeds, else None."""
        import os

        # Check if this is first-time setup
        auth_file = str(get_auth_json_path())

        if not os.path.exists(auth_file):
            # First-time setup
            return self.first_time_setup()

        # Existing user - authenticate
        for attempt in range(3):
            password, ok = QInputDialog.getText(
                self, "Login", "Enter master password:", QLineEdit.Password
            )
            if not ok:  # User cancelled
                return None

            if authenticate(password):
                return password

            if attempt < 2:
                QMessageBox.warning(
                    self,
                    "Login Failed",
                    f"Incorrect password. {2 - attempt} attempts remaining.",
                )

        QMessageBox.critical(self, "Login Failed", "Too many failed attempts.")
        return None

    def first_time_setup(self):
        """Handle first-time setup by creating a master password."""
        # Show welcome message
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Welcome to Secure Password Manager")
        msg.setText("First-time Setup")
        msg.setInformativeText(
            "Welcome! It looks like this is your first time using the Password Manager.\n\n"
            "You'll need to create a master password that will protect all your stored passwords.\n\n"
            "⚠️ Important:\n"
            "• Make sure it's secure and memorable\n"
            "• You'll need it every time you open this app\n"
            "• If you forget it, your passwords cannot be recovered!"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if msg.exec_() != QMessageBox.Ok:
            return None

        # Create master password dialog
        while True:
            password, ok = QInputDialog.getText(
                self,
                "Create Master Password",
                "Create your master password (at least 8 characters):",
                QLineEdit.Password,
            )

            if not ok:  # User cancelled
                return None

            # Validate password length
            if len(password) < 8:
                QMessageBox.warning(
                    self,
                    "Password Too Short",
                    "Your master password must be at least 8 characters long.\n\nPlease try again.",
                )
                continue

            # Confirm password
            confirm, ok = QInputDialog.getText(
                self,
                "Confirm Master Password",
                "Confirm your master password:",
                QLineEdit.Password,
            )

            if not ok:  # User cancelled
                return None

            # Check if passwords match
            if password != confirm:
                QMessageBox.warning(
                    self,
                    "Passwords Don't Match",
                    "The passwords you entered don't match.\n\nPlease try again.",
                )
                continue

            # Check password strength
            score, feedback = evaluate_password_strength(password)

            if score < 3:
                # Warn about weak password
                reply = QMessageBox.question(
                    self,
                    "Weak Password Warning",
                    f"Your master password is weak (strength: {score}/4).\n\n"
                    f"Suggestions:\n{feedback}\n\n"
                    "Do you want to use this password anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply != QMessageBox.Yes:
                    continue

            # Create the master password
            try:
                set_master_password(password)
                QMessageBox.information(
                    self,
                    "Setup Complete",
                    "✓ Master password created successfully!\n\n"
                    "You can now start managing your passwords.",
                )
                return password
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Setup Failed",
                    f"Failed to create master password: {str(e)}\n\nPlease try again.",
                )
                continue

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

        # Create the categories tab
        self.categories_tab = QWidget()
        self.central_widget.addTab(self.categories_tab, "Categories")

        # Create the settings tab
        self.settings_tab = QWidget()
        self.central_widget.addTab(self.settings_tab, "Settings")

        # Create the logs tab
        self.logs_tab = QWidget()
        self.central_widget.addTab(self.logs_tab, "Logs")

        # Set up the password manager tab
        self.setup_passwords_tab()

        # Set up the security tab
        self.setup_security_tab()

        # Set up the backup tab
        self.setup_backup_tab()

        # Set up the categories tab
        self.setup_categories_tab()

        # Set up the settings tab
        self.setup_settings_tab()

        # Set up the logs tab
        self.setup_logs_tab()

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

        # Show expiring soon checkbox
        self.show_expiring_only = QCheckBox("Expiring Soon (30 days)")
        self.show_expiring_only.setChecked(False)
        self.show_expiring_only.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.show_expiring_only)

        # Favorites only checkbox
        self.favorites_only = QCheckBox("Favorites Only")
        self.favorites_only.setChecked(False)
        self.favorites_only.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.favorites_only)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Website", "Username", "Password", "Category", "Created", "Expires"]
        )

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
        self.table.horizontalHeader().setStretchLastSection(
            True
        )  # Stretch last section
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Stretch website column
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )  # Stretch username column
        self.table.setSortingEnabled(True)  # Enable sorting

        # Context menu for table
        self.table.setContextMenuPolicy(QtCoreQt.ContextMenuPolicy.CustomContextMenu)
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

        export_desc = QLabel(
            "Export your passwords to an encrypted file that can be used to restore them later."
        )
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

        backup_desc = QLabel(
            "Create a complete backup including your database, encryption keys, and settings."
        )
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

    # authenticate() is now replaced by get_master_password()

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
        expiring_only = self.show_expiring_only.isChecked()
        favorites_only_filter = self.favorites_only.isChecked()

        # Get passwords with filters
        passwords = get_passwords(category, search_term, show_expired)

        # Additional filtering for expiring soon
        if expiring_only:
            current_time = int(time.time())
            thirty_days = 30 * 86400
            passwords = [
                p
                for p in passwords
                if p[8] and p[8] <= current_time + thirty_days and p[8] > current_time
            ]

        # Filter favorites only
        if favorites_only_filter:
            passwords = [p for p in passwords if p[9]]  # p[9] is favorite column

        # Fill table
        self.table.setRowCount(len(passwords))

        for row, entry in enumerate(passwords):
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

            # Format expiry
            days_left = None
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
            id_item.setTextAlignment(
                QtCoreQt.AlignmentFlag.AlignCenter
            )  # Center the ID value
            self.table.setItem(row, 0, id_item)

            website_item = QTableWidgetItem(website)
            if favorite:
                website_item.setForeground(QColor("#ffd700"))  # Gold for favorites
            self.table.setItem(row, 1, website_item)

            username_item = QTableWidgetItem(username)
            self.table.setItem(row, 2, username_item)

            password_item = QTableWidgetItem("••••••••")  # Mask password
            password_item.setData(
                QtCoreQt.ItemDataRole.UserRole, decrypted
            )  # Store real password as data
            password_item.setTextAlignment(
                QtCoreQt.AlignmentFlag.AlignCenter
            )  # Center the dots
            self.table.setItem(row, 3, password_item)

            category_item = QTableWidgetItem(category)
            self.table.setItem(row, 4, category_item)

            created_item = QTableWidgetItem(created_str)
            created_item.setTextAlignment(
                QtCoreQt.AlignmentFlag.AlignCenter
            )  # Center the date
            self.table.setItem(row, 5, created_item)

            expiry_item = QTableWidgetItem(expiry_str)
            expiry_item.setTextAlignment(
                QtCoreQt.AlignmentFlag.AlignCenter
            )  # Center the expiry info
            if expiry and days_left is not None and days_left < 0:
                expiry_item.setForeground(QColor("red"))
            elif expiry and days_left is not None and days_left < 7:
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
        password = password_item.data(
            QtCoreQt.ItemDataRole.UserRole
        )  # Get the stored password

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
        password = password_item.data(QtCoreQt.ItemDataRole.UserRole)

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
            QtCoreQt.Orientation.Horizontal,
            dialog,
        )
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

                strength_label.setText(
                    f"<span style='color:{color}'>{description}</span>"
                )
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
                QMessageBox.warning(
                    dialog, "Error", "Website, username and password are required"
                )
                return

            # Check strength
            if password:
                score, _ = evaluate_password_strength(password)
                if score < 3:
                    confirm = QMessageBox.question(
                        dialog,
                        "Weak Password",
                        "This password is weak. Use it anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
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
        _, website, username, encrypted, category, notes, _, _, expiry, favorite = (
            target_entry
        )
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
            days_left = (
                int((expiry - time.time()) / 86400) if expiry > time.time() else 0
            )
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
            QtCoreQt.Orientation.Horizontal,
            dialog,
        )
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

                strength_label.setText(
                    f"<span style='color:{color}'>{description}</span>"
                )
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
                QMessageBox.warning(
                    dialog, "Error", "Website and username are required"
                )
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
                    confirm = QMessageBox.question(
                        dialog,
                        "Weak Password",
                        "This password is weak. Use it anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
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
                favorite=new_favorite if new_favorite != favorite else None,
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

        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete the password for {website}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            delete_password(entry_id)
            self.refresh_passwords()
            self.statusBar().showMessage("Password deleted successfully")

        if auto_close:
            auto_close.close()

    def export_passwords(self):
        """Export passwords to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Passwords", "", "Data Files (*.dat)"
        )
        if not filename:
            return

        password, ok = QInputDialog.getText(
            self,
            "Export",
            "Enter master password to encrypt backup:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return

        if export_passwords(filename, password):
            QMessageBox.information(
                self, "Success", f"Passwords exported to {filename}"
            )
        else:
            QMessageBox.warning(self, "Error", "No passwords to export")

    def import_passwords(self):
        """Import passwords from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Passwords", "", "Data Files (*.dat)"
        )
        if not filename:
            return

        password, ok = QInputDialog.getText(
            self,
            "Import",
            "Enter master password to decrypt backup:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return

        count = import_passwords(filename, password)
        if count > 0:
            self.refresh_passwords()
            QMessageBox.information(
                self, "Success", f"Imported {count} passwords successfully"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to import passwords")

    def create_full_backup(self):
        """Create a full backup of all data"""
        # Get backup directory
        backup_dir = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if not backup_dir:
            return

        # Get master password
        password, ok = QInputDialog.getText(
            self,
            "Backup",
            "Enter master password to encrypt backup:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return

        # Show waiting cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar().showMessage("Creating backup...")

        try:
            # Import from backup.py
            from secure_password_manager.utils.backup import create_full_backup

            # Create backup
            backup_path = create_full_backup(backup_dir, password)

            QApplication.restoreOverrideCursor()

            if backup_path:
                QMessageBox.information(
                    self, "Success", f"Full backup created at:\n{backup_path}"
                )
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
        confirm = QMessageBox.warning(
            self,
            "Warning",
            "Restoring will replace your current data. Make sure you have a backup!\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        # Get backup file
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "Zip Files (*.zip)"
        )
        if not filename:
            return

        # Get master password
        password, ok = QInputDialog.getText(
            self,
            "Restore",
            "Enter master password to decrypt backup:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return

        # Show waiting cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar().showMessage("Restoring from backup...")

        try:
            # Import from backup.py
            from secure_password_manager.utils.backup import restore_from_backup

            # Restore from backup
            success = restore_from_backup(filename, password)

            QApplication.restoreOverrideCursor()

            if success:
                msg = QMessageBox.information(
                    self,
                    "Success",
                    "Backup restored successfully. The application will now close. Please restart it.",
                )
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
            from secure_password_manager.utils.security_audit import run_security_audit

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

            self.score_label.setText(
                f"Your security score: <span style='color:{color};font-weight:bold;'>{score}/100</span>"
            )

            # Set issue counts
            weak_count = len(issues["weak_passwords"])
            reused_count = len(issues["reused_passwords"])
            expired_count = len(issues["expired_passwords"])
            breached_count = len(issues["breached_passwords"])

            self.weak_label.setText(
                f"Weak passwords: <span style='color:{'red' if weak_count else 'green'};'>{weak_count}</span>"
            )
            self.reused_label.setText(
                f"Reused passwords: <span style='color:{'red' if reused_count else 'green'};'>{reused_count}</span>"
            )
            self.expired_label.setText(
                f"Expired passwords: <span style='color:{'red' if expired_count else 'green'};'>{expired_count}</span>"
            )
            self.breached_label.setText(
                f"Breached passwords: <span style='color:{'red' if breached_count else 'green'};'>{breached_count}</span>"
            )

            # Show detailed results if there are issues
            total_issues = weak_count + reused_count + expired_count + breached_count
            if total_issues > 0:
                msg = QMessageBox(self)
                msg.setWindowTitle("Security Audit Results")
                msg.setIcon(QMessageBox.Warning)

                # Create detailed message
                details = f"Security Score: {score}/100\n\n"
                details += "Issues found:\n\n"

                if weak_count:
                    details += f"WEAK PASSWORDS ({weak_count}):\n"
                    for issue in issues["weak_passwords"][
                        :5
                    ]:  # Limit to 5 for readability
                        details += f"  • {issue['website']} ({issue['username']}) - Score: {issue['score']}\n"
                    if weak_count > 5:
                        details += f"  • ... and {weak_count - 5} more\n"
                    details += "\n"

                if reused_count:
                    details += f"REUSED PASSWORDS ({reused_count}):\n"
                    for issue in issues["reused_passwords"][:5]:  # Limit to 5
                        sites = ", ".join(
                            [site["website"] for site in issue["reused_with"]]
                        )
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
                msg.setText(
                    f"Found {total_issues} security issues with your passwords."
                )
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
                QMessageBox.information(
                    self,
                    "Security Audit",
                    "No security issues found! Your passwords are in good shape.",
                )

            self.statusBar().showMessage("Security audit complete")

        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                self, "Error", f"An error occurred during the security audit: {str(e)}"
            )
            self.statusBar().showMessage("Security audit failed")

    def setup_categories_tab(self):
        """Set up the categories management tab"""
        layout = QVBoxLayout()
        self.categories_tab.setLayout(layout)

        # Title
        title = QLabel("<h2>Category Management</h2>")
        layout.addWidget(title)

        # Categories list
        list_group = QGroupBox("Existing Categories")
        list_layout = QVBoxLayout()

        self.categories_list = QTableWidget()
        self.categories_list.setColumnCount(3)
        self.categories_list.setHorizontalHeaderLabels(
            ["Name", "Color", "Password Count"]
        )
        self.categories_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.categories_list.setEditTriggers(QTableWidget.NoEditTriggers)
        list_layout.addWidget(self.categories_list)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Add new category section
        add_group = QGroupBox("Add New Category")
        add_layout = QFormLayout()

        self.new_category_name = QLineEdit()
        self.new_category_name.setPlaceholderText("Enter category name...")
        add_layout.addRow("Name:", self.new_category_name)

        self.new_category_color = QComboBox()
        colors = [
            "blue",
            "red",
            "green",
            "purple",
            "orange",
            "yellow",
            "cyan",
            "magenta",
            "brown",
            "pink",
        ]
        for color in colors:
            self.new_category_color.addItem(color.capitalize(), color)
        add_layout.addRow("Color:", self.new_category_color)

        add_category_btn = QPushButton("Add Category")
        add_category_btn.clicked.connect(self.add_new_category)
        add_layout.addRow("", add_category_btn)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Categories")
        refresh_btn.clicked.connect(self.refresh_categories)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        # Load categories
        self.refresh_categories()

    def refresh_categories(self):
        """Refresh the categories list"""
        try:
            categories = get_categories()
            passwords = get_passwords()

            # Count passwords per category
            category_counts = {}
            for p in passwords:
                cat = p[4]  # category column
                category_counts[cat] = category_counts.get(cat, 0) + 1

            self.categories_list.setRowCount(len(categories))

            for row, (name, color) in enumerate(categories):
                name_item = QTableWidgetItem(name)
                self.categories_list.setItem(row, 0, name_item)

                color_item = QTableWidgetItem(color)
                color_item.setForeground(QColor(color))
                self.categories_list.setItem(row, 1, color_item)

                count = category_counts.get(name, 0)
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
                self.categories_list.setItem(row, 2, count_item)

            self.statusBar().showMessage(f"{len(categories)} categories loaded")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load categories: {str(e)}")

    def add_new_category(self):
        """Add a new category"""
        name = self.new_category_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a category name.")
            return

        color = self.new_category_color.currentData()

        try:
            add_category(name, color)
            QMessageBox.information(
                self, "Success", f"Category '{name}' added successfully!"
            )

            # Refresh both the categories list and the passwords tab combo
            self.refresh_categories()

            # Update the category combo in passwords tab
            self.category_combo.clear()
            self.category_combo.addItem("All Categories")
            categories = get_categories()
            for cat_name, _ in categories:
                self.category_combo.addItem(cat_name)

            # Clear input
            self.new_category_name.clear()

            self.statusBar().showMessage(f"Category '{name}' added")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add category: {str(e)}")

    def setup_settings_tab(self):
        """Set up the settings tab with master password, 2FA, and key protection options"""
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)

        # Title
        title = QLabel("<h2>Settings</h2>")
        layout.addWidget(title)

        # Master Password Section
        mp_group = QGroupBox("Master Password")
        mp_layout = QVBoxLayout()

        change_pw_btn = QPushButton("Change Master Password")
        change_pw_btn.clicked.connect(self.change_master_password)
        mp_layout.addWidget(change_pw_btn)

        mp_group.setLayout(mp_layout)
        layout.addWidget(mp_group)

        # Two-Factor Authentication Section
        twofa_group = QGroupBox("Two-Factor Authentication (TOTP)")
        twofa_layout = QVBoxLayout()

        self.twofa_status_label = QLabel()
        twofa_layout.addWidget(self.twofa_status_label)

        self.setup_2fa_btn = QPushButton("Setup 2FA")
        self.setup_2fa_btn.clicked.connect(self.setup_2fa)
        twofa_layout.addWidget(self.setup_2fa_btn)

        self.disable_2fa_btn = QPushButton("Disable 2FA")
        self.disable_2fa_btn.clicked.connect(self.disable_2fa)
        twofa_layout.addWidget(self.disable_2fa_btn)

        twofa_group.setLayout(twofa_layout)
        layout.addWidget(twofa_group)

        # Key Protection Section
        key_group = QGroupBox("Encryption Key Protection")
        key_layout = QVBoxLayout()

        key_info = QLabel(
            "Key protection encrypts your vault key with your master password,\n"
            "providing additional security if the key file is stolen."
        )
        key_info.setWordWrap(True)
        key_layout.addWidget(key_info)

        self.key_status_label = QLabel()
        key_layout.addWidget(self.key_status_label)

        self.protect_key_btn = QPushButton("Enable Key Protection")
        self.protect_key_btn.clicked.connect(self.toggle_key_protection)
        key_layout.addWidget(self.protect_key_btn)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # System Information Section
        sys_group = QGroupBox("System Information")
        sys_layout = QVBoxLayout()

        self.system_info_label = QLabel()
        sys_layout.addWidget(self.system_info_label)

        refresh_info_btn = QPushButton("Refresh Info")
        refresh_info_btn.clicked.connect(self.update_system_info)
        sys_layout.addWidget(refresh_info_btn)

        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)

        layout.addStretch()

        # NOW update all status labels and buttons (after widgets are created)
        self.update_2fa_status()
        self.update_2fa_buttons()
        self.update_key_protection_status()
        self.update_system_info()

    def setup_logs_tab(self):
        """Set up the activity logs tab"""
        layout = QVBoxLayout()
        self.logs_tab.setLayout(layout)

        # Title
        title = QLabel("<h2>Activity Logs</h2>")
        layout.addWidget(title)

        # Controls
        controls_layout = QHBoxLayout()

        refresh_logs_btn = QPushButton("Refresh Logs")
        refresh_logs_btn.clicked.connect(self.refresh_logs)
        controls_layout.addWidget(refresh_logs_btn)

        clear_display_btn = QPushButton("Clear Display")
        clear_display_btn.clicked.connect(lambda: self.logs_text.clear())
        controls_layout.addWidget(clear_display_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Logs display (read-only text area)
        from PyQt5.QtWidgets import QTextEdit

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFontFamily("Courier")
        layout.addWidget(self.logs_text)

        # Load logs
        self.refresh_logs()

    def update_2fa_status(self):
        """Update the 2FA status label"""
        if is_2fa_enabled():
            self.twofa_status_label.setText("Status: ✓ Enabled")
            self.twofa_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.twofa_status_label.setText("Status: ✗ Disabled")
            self.twofa_status_label.setStyleSheet("color: red; font-weight: bold;")

    def update_2fa_buttons(self):
        """Update 2FA button states based on whether 2FA is enabled"""
        enabled = is_2fa_enabled()
        self.setup_2fa_btn.setEnabled(not enabled)
        self.disable_2fa_btn.setEnabled(enabled)

    def update_key_protection_status(self):
        """Update the key protection status label"""
        if is_key_protected():
            self.key_status_label.setText("Status: ✓ Key is protected")
            self.key_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.protect_key_btn.setText("Disable Key Protection")
        else:
            self.key_status_label.setText("Status: ✗ Key is not protected")
            self.key_status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.protect_key_btn.setText("Enable Key Protection")

    def update_system_info(self):
        """Update system information display"""
        import os

        passwords = get_passwords()
        categories = get_categories()

        info_text = f"Password Count: {len(passwords)}\n"
        info_text += f"Category Count: {len(categories)}\n"
        info_text += f"2FA Status: {'Enabled' if is_2fa_enabled() else 'Disabled'}\n"
        info_text += (
            f"Key Protection: {'Enabled' if is_key_protected() else 'Disabled'}\n"
        )

        # File sizes
        if os.path.exists("passwords.db"):
            size = os.path.getsize("passwords.db") / 1024
            info_text += f"Database Size: {size:.2f} KB\n"

        self.system_info_label.setText(info_text)

    def refresh_logs(self):
        """Refresh the activity logs display"""
        try:
            logs = get_log_entries(count=100)
            if logs:
                self.logs_text.setPlainText("\n".join(logs))
                self.statusBar().showMessage(f"Loaded {len(logs)} log entries")
            else:
                self.logs_text.setPlainText("No log entries found.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load logs: {str(e)}")

    def change_master_password(self):
        """Dialog to change the master password"""
        import json

        from secure_password_manager.utils.auth import verify_password

        dialog = QDialog(self)
        dialog.setWindowTitle("Change Master Password")
        dialog.setModal(True)

        layout = QFormLayout()

        # Current password
        current_pw_input = QLineEdit()
        current_pw_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Current Password:", current_pw_input)

        # New password
        new_pw_input = QLineEdit()
        new_pw_input.setEchoMode(QLineEdit.Password)
        layout.addRow("New Password:", new_pw_input)

        # Confirm new password
        confirm_pw_input = QLineEdit()
        confirm_pw_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Confirm Password:", confirm_pw_input)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            QtCoreQt.Orientation.Horizontal,
            dialog,
        )
        layout.addRow(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            current_pass = current_pw_input.text()
            new_pass = new_pw_input.text()
            confirm_pass = confirm_pw_input.text()

            # Validate current password
            try:
                with open("auth.json") as f:
                    auth_data = json.load(f)
                    auth_hash = auth_data["master_hash"]

                if not verify_password(auth_hash, current_pass):
                    QMessageBox.warning(self, "Error", "Current password is incorrect.")
                    return
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not verify password: {str(e)}"
                )
                return

            # Validate new password
            if len(new_pass) < 8:
                QMessageBox.warning(
                    self, "Error", "New password must be at least 8 characters long."
                )
                return

            if new_pass != confirm_pass:
                QMessageBox.warning(self, "Error", "New passwords do not match.")
                return

            # Check password strength
            strength = evaluate_password_strength(new_pass)
            score = strength.get("score", 0) if isinstance(strength, dict) else 0
            feedback = (
                strength.get("feedback", "") if isinstance(strength, dict) else ""
            )

            if score < 3:
                reply = QMessageBox.question(
                    self,
                    "Weak Password",
                    f"Password strength: {score}/5 - {feedback}\n\n"
                    "This password is considered weak. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            # Update password
            try:
                set_master_password(new_pass)
                set_master_password_context(new_pass)

                # If key is protected, suggest re-protecting with new password
                if is_key_protected():
                    reply = QMessageBox.question(
                        self,
                        "Re-protect Key",
                        "Your encryption key is currently protected with the old master password.\n\n"
                        "Would you like to re-protect it with the new master password?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.Yes:
                        try:
                            from secure_password_manager.utils.crypto import (
                                unprotect_key,
                            )

                            unprotect_key(current_pass)
                            protect_key_with_master_password(new_pass)
                            QMessageBox.information(
                                self,
                                "Success",
                                "Master password changed and key re-protected successfully!",
                            )
                        except Exception as e:
                            QMessageBox.warning(
                                self,
                                "Warning",
                                f"Password changed but key re-protection failed: {str(e)}",
                            )
                else:
                    QMessageBox.information(
                        self, "Success", "Master password changed successfully!"
                    )

                self.statusBar().showMessage("Master password updated")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to change password: {str(e)}"
                )

    def setup_2fa(self):
        """Setup TOTP two-factor authentication"""
        if is_2fa_enabled():
            QMessageBox.information(
                self, "2FA", "Two-factor authentication is already enabled."
            )
            return

        reply = QMessageBox.question(
            self,
            "Setup 2FA",
            "This will generate a new TOTP secret and QR code.\n\n"
            "You'll need to scan the QR code with your authenticator app.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                secret = setup_totp()

                msg = QMessageBox(self)
                msg.setWindowTitle("2FA Setup Complete")
                msg.setText(
                    "Two-factor authentication has been set up!\n\n"
                    f"Secret: {secret}\n\n"
                    "A QR code has been saved to 'totp_qr.png'.\n"
                    "Scan it with your authenticator app (Google Authenticator, Authy, etc.).\n\n"
                    "You will need to enter a code from your app on next login."
                )
                msg.setIcon(QMessageBox.Information)

                # Try to show QR code if file exists
                import os

                if os.path.exists("totp_qr.png"):
                    from PyQt5.QtGui import QPixmap

                    pixmap = QPixmap("totp_qr.png")
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(
                            300, 300, QtCoreQt.AspectRatioMode.KeepAspectRatio
                        )
                        msg.setIconPixmap(pixmap)

                msg.exec_()

                self.update_2fa_status()
                self.update_2fa_buttons()
                self.update_system_info()

                self.statusBar().showMessage("2FA enabled successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to setup 2FA: {str(e)}")

    def disable_2fa(self):
        """Disable two-factor authentication"""
        if not is_2fa_enabled():
            QMessageBox.information(
                self, "2FA", "Two-factor authentication is already disabled."
            )
            return

        reply = QMessageBox.question(
            self,
            "Disable 2FA",
            "Are you sure you want to disable two-factor authentication?\n\n"
            "This will reduce the security of your account.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                disable_2fa()
                QMessageBox.information(
                    self, "Success", "Two-factor authentication has been disabled."
                )

                self.update_2fa_status()
                self.update_2fa_buttons()
                self.update_system_info()

                self.statusBar().showMessage("2FA disabled")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to disable 2FA: {str(e)}")

    def toggle_key_protection(self):
        """Toggle encryption key protection on/off"""
        try:
            if is_key_protected():
                # Disable protection
                reply = QMessageBox.question(
                    self,
                    "Disable Key Protection",
                    "This will decrypt your vault key and store it in plaintext.\n\n"
                    "Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    from secure_password_manager.utils.crypto import unprotect_key

                    unprotect_key(self._master_password)
                    # Clear the context since we're back to plaintext
                    set_master_password_context(None)
                    QMessageBox.information(
                        self,
                        "Success",
                        "Key protection disabled. Your key is now stored in plaintext.",
                    )
                    self.update_key_protection_status()
                    self.update_system_info()
                    self.statusBar().showMessage("Key protection disabled")
            else:
                # Enable protection
                reply = QMessageBox.question(
                    self,
                    "Enable Key Protection",
                    "This will encrypt your vault key with your master password.\n\n"
                    "You'll need to enter your master password at login to decrypt it.\n\n"
                    "Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    # Pass the stored master password explicitly
                    protect_key_with_master_password(self._master_password)
                    # Set the context so the key can be loaded
                    set_master_password_context(self._master_password)
                    QMessageBox.information(
                        self,
                        "Success",
                        "Key protection enabled. Your vault key is now encrypted with your master password.",
                    )
                    self.update_key_protection_status()
                    self.update_system_info()
                    self.statusBar().showMessage("Key protection enabled")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to toggle key protection: {str(e)}"
            )


def main():
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)

    window = PasswordManagerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
