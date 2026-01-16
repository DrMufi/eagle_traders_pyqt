import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QComboBox, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from database import Database

class UserManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('User Management')
        layout = QVBoxLayout(self)

        # Title
        title = QLabel('User Management')
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton('Add User')
        add_btn.clicked.connect(self.add_user)
        button_layout.addWidget(add_btn)

        change_pass_btn = QPushButton('Change Password')
        change_pass_btn.clicked.connect(self.change_password)
        button_layout.addWidget(change_pass_btn)

        delete_btn = QPushButton('Delete User')
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)

        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.load_users)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(['ID', 'Username', 'Role'])
        layout.addWidget(self.users_table)

        self.load_users()

    def load_users(self):
        users = self.db.get_users()
        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user[0])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user[1]))
            self.users_table.setItem(row, 2, QTableWidgetItem(user[2]))

    def add_user(self):
        dialog = AddUserDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def change_password(self):
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a user first.")
            return

        username = self.users_table.item(current_row, 1).text()
        dialog = ChangePasswordDialog(username, self.db, self)
        dialog.exec()

    def delete_user(self):
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a user first.")
            return

        username = self.users_table.item(current_row, 1).text()
        if username == 'admin':
            QMessageBox.warning(self, "Delete Error", "Cannot delete admin user.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete',
                                   f"Are you sure you want to delete user '{username}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_user(username):
                QMessageBox.information(self, "Success", "User deleted successfully.")
                self.load_users()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete user.")

class AddUserDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add New User")
        self.setModal(True)

        layout = QFormLayout(self)

        self.username_edit = QLineEdit()
        layout.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Password:", self.password_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(['user', 'admin'])
        layout.addRow("Role:", self.role_combo)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Add")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required.")
            return

        if self.db.create_user(username, password, role):
            QMessageBox.information(self, "Success", "User created successfully.")
            super().accept()
        else:
            QMessageBox.warning(self, "Error", "Username already exists.")

class ChangePasswordDialog(QDialog):
    def __init__(self, username, db, parent=None):
        super().__init__(parent)
        self.username = username
        self.db = db
        self.setWindowTitle(f"Change Password for {username}")
        self.setModal(True)

        layout = QFormLayout(self)

        self.old_password_edit = QLineEdit()
        self.old_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Current Password:", self.old_password_edit)

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("New Password:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Confirm New Password:", self.confirm_password_edit)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Change")
        ok_btn.clicked.connect(self.change_password)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def change_password(self):
        old_password = self.old_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not old_password or not new_password:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Input Error", "New passwords do not match.")
            return

        if self.db.change_password(self.username, old_password, new_password):
            QMessageBox.information(self, "Success", "Password changed successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Current password is incorrect.")