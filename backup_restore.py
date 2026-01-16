"""
Database Backup and Restore functionality for Eagle Traders
"""

import os
import shutil
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox,
    QFileDialog, QGroupBox, QCheckBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from database import Database
from notification_manager import show_success_notification, show_error_notification


class BackupThread(QThread):
    """Thread for performing database backup"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, db_path, backup_path):
        super().__init__()
        self.db_path = db_path
        self.backup_path = backup_path

    def run(self):
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.dirname(self.backup_path)
            os.makedirs(backup_dir, exist_ok=True)

            # Perform backup
            shutil.copy2(self.db_path, self.backup_path)

            self.progress.emit(100)
            self.finished.emit(True, f"Backup created successfully: {os.path.basename(self.backup_path)}")

        except Exception as e:
            self.finished.emit(False, f"Backup failed: {str(e)}")


class RestoreThread(QThread):
    """Thread for performing database restore"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, backup_path, db_path):
        super().__init__()
        self.backup_path = backup_path
        self.db_path = db_path

    def run(self):
        try:
            # Create a backup of current database before restore
            if os.path.exists(self.db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pre_restore_backup = f"{self.db_path}.pre_restore_{timestamp}"
                shutil.copy2(self.db_path, pre_restore_backup)

            # Perform restore
            shutil.copy2(self.backup_path, self.db_path)

            # Verify the restored database
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()

            self.progress.emit(100)
            self.finished.emit(True, f"Database restored successfully from: {os.path.basename(self.backup_path)}")

        except Exception as e:
            self.finished.emit(False, f"Restore failed: {str(e)}")


class BackupRestoreWidget(QWidget):
    """Widget for managing database backups and restores"""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.backup_thread = None
        self.restore_thread = None
        self.init_ui()
        self.load_backup_history()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Database Backup & Restore")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #ffffff; margin-bottom: 20px;")
        layout.addWidget(title)

        # Backup section
        backup_group = QGroupBox("Create Backup")
        backup_layout = QVBoxLayout(backup_group)

        backup_info = QLabel("Create a backup of your current database to prevent data loss.")
        backup_info.setStyleSheet("color: #cccccc; margin-bottom: 15px;")
        backup_layout.addWidget(backup_info)

        # Backup options
        options_layout = QHBoxLayout()

        self.auto_backup_check = QCheckBox("Enable automatic backups")
        self.auto_backup_check.setChecked(True)
        self.auto_backup_check.setStyleSheet("color: #ffffff;")
        options_layout.addWidget(self.auto_backup_check)

        options_layout.addWidget(QLabel("Interval (days):"))
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 30)
        self.backup_interval.setValue(7)
        options_layout.addWidget(self.backup_interval)

        options_layout.addStretch()
        backup_layout.addLayout(options_layout)

        # Backup buttons
        btn_layout = QHBoxLayout()
        self.manual_backup_btn = QPushButton("Create Manual Backup")
        self.manual_backup_btn.clicked.connect(self.create_manual_backup)
        btn_layout.addWidget(self.manual_backup_btn)

        self.backup_progress = QProgressBar()
        self.backup_progress.setVisible(False)
        btn_layout.addWidget(self.backup_progress)

        backup_layout.addLayout(btn_layout)
        layout.addWidget(backup_group)

        # Restore section
        restore_group = QGroupBox("Restore Database")
        restore_layout = QVBoxLayout(restore_group)

        restore_warning = QLabel("⚠️ Warning: Restoring will replace your current database. A backup of the current database will be created automatically.")
        restore_warning.setStyleSheet("color: #ffcc00; margin-bottom: 15px;")
        restore_layout.addWidget(restore_warning)

        # Restore options
        restore_btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Select Backup File & Restore")
        self.restore_btn.clicked.connect(self.restore_database)
        restore_btn_layout.addWidget(self.restore_btn)

        self.restore_progress = QProgressBar()
        self.restore_progress.setVisible(False)
        restore_btn_layout.addWidget(self.restore_progress)

        restore_layout.addLayout(restore_btn_layout)
        layout.addWidget(restore_group)

        # Backup history
        history_group = QGroupBox("Backup History")
        history_layout = QVBoxLayout(history_group)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Filename", "Date Created", "Size", "Actions"])
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.setMaximumHeight(300)

        history_layout.addWidget(self.backup_table)
        layout.addWidget(history_group)

        # Auto backup timer
        self.auto_backup_timer = QTimer()
        self.auto_backup_timer.timeout.connect(self.create_auto_backup)

        # Start auto backup if enabled
        if self.auto_backup_check.isChecked():
            self.start_auto_backup()

    def create_manual_backup(self):
        """Create a manual backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"eagle_traders_backup_{timestamp}.db"

        backup_path, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", default_name,
            "Database Files (*.db);;All Files (*)"
        )

        if not backup_path:
            return

        self.backup_progress.setVisible(True)
        self.backup_progress.setValue(0)
        self.manual_backup_btn.setEnabled(False)

        self.backup_thread = BackupThread(self.db.db_path, backup_path)
        self.backup_thread.progress.connect(self.backup_progress.setValue)
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()

    def create_auto_backup(self):
        """Create automatic backup"""
        if not self.auto_backup_check.isChecked():
            return

        backup_dir = os.path.join(os.path.dirname(self.db.db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"auto_backup_{timestamp}.db")

        self.backup_thread = BackupThread(self.db.db_path, backup_path)
        self.backup_thread.finished.connect(self.on_auto_backup_finished)
        self.backup_thread.start()

    def restore_database(self):
        """Restore database from backup"""
        backup_path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "",
            "Database Files (*.db);;All Files (*)"
        )

        if not backup_path:
            return

        # Confirm restore
        reply = QMessageBox.question(
            self, "Confirm Restore",
            "This will replace your current database with the selected backup. "
            "A backup of the current database will be created automatically.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.restore_progress.setVisible(True)
        self.restore_progress.setValue(0)
        self.restore_btn.setEnabled(False)

        self.restore_thread = RestoreThread(backup_path, self.db.db_path)
        self.restore_thread.progress.connect(self.restore_progress.setValue)
        self.restore_thread.finished.connect(self.on_restore_finished)
        self.restore_thread.start()

    def on_backup_finished(self, success, message):
        """Handle backup completion"""
        self.backup_progress.setVisible(False)
        self.manual_backup_btn.setEnabled(True)

        if success:
            show_success_notification("Backup Created", message)
            self.load_backup_history()
        else:
            show_error_notification("Backup Failed", message)

    def on_auto_backup_finished(self, success, message):
        """Handle auto backup completion"""
        if success:
            print(f"Auto backup completed: {message}")
        else:
            print(f"Auto backup failed: {message}")

    def on_restore_finished(self, success, message):
        """Handle restore completion"""
        self.restore_progress.setVisible(False)
        self.restore_btn.setEnabled(True)

        if success:
            show_success_notification("Database Restored", message)
            # Reload data in all modules would be needed here
            QMessageBox.information(self, "Restart Required",
                                  "Database has been restored successfully. "
                                  "Please restart the application to load the restored data.")
        else:
            show_error_notification("Restore Failed", message)

    def load_backup_history(self):
        """Load and display backup history"""
        backup_dir = os.path.join(os.path.dirname(self.db.db_path), "backups")

        if not os.path.exists(backup_dir):
            self.backup_table.setRowCount(0)
            return

        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(backup_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    mtime = os.path.getmtime(file_path)
                    date_created = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    backups.append((file, date_created, self.format_size(size), file_path))

        # Sort by date (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)

        self.backup_table.setRowCount(len(backups))
        for row, (filename, date_created, size, file_path) in enumerate(backups):
            self.backup_table.setItem(row, 0, QTableWidgetItem(filename))
            self.backup_table.setItem(row, 1, QTableWidgetItem(date_created))
            self.backup_table.setItem(row, 2, QTableWidgetItem(size))

            # Restore button
            restore_btn = QPushButton("Restore")
            restore_btn.clicked.connect(lambda _, path=file_path: self.restore_from_history(path))
            self.backup_table.setCellWidget(row, 3, restore_btn)

    def restore_from_history(self, backup_path):
        """Restore from backup history"""
        reply = QMessageBox.question(
            self, "Confirm Restore",
            f"Restore database from: {os.path.basename(backup_path)}?\n\n"
            "This will replace your current database.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.restore_progress.setVisible(True)
            self.restore_progress.setValue(0)
            self.restore_btn.setEnabled(False)

            self.restore_thread = RestoreThread(backup_path, self.db.db_path)
            self.restore_thread.progress.connect(self.restore_progress.setValue)
            self.restore_thread.finished.connect(self.on_restore_finished)
            self.restore_thread.start()

    def start_auto_backup(self):
        """Start automatic backup timer"""
        if self.auto_backup_check.isChecked():
            interval_ms = self.backup_interval.value() * 24 * 60 * 60 * 1000  # Convert days to milliseconds
            self.auto_backup_timer.start(interval_ms)

    def stop_auto_backup(self):
        """Stop automatic backup timer"""
        self.auto_backup_timer.stop()

    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"