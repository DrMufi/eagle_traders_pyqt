from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item

class CategoryManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        # Main scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll area
        container = QWidget()
        scroll_area.setWidget(container)

        # Main layout for container
        layout = QVBoxLayout(container)

        # Add/Edit Category
        form_group = QGroupBox("Add/Edit Category")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit()
        form_layout.addRow("Category Name:", self.name_edit)

        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Category")
        self.add_btn.clicked.connect(self.add_category)
        button_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Update Category")
        self.update_btn.clicked.connect(self.update_category)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)

        form_layout.addRow(button_layout)
        layout.addWidget(form_group)

        # Categories table
        self.table = QTableWidget()
        setup_professional_table(self.table, ["ID", "Name"], ['id', 'text'])
        self.table.cellDoubleClicked.connect(self.edit_category)
        layout.addWidget(self.table)

        # Delete button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_category)
        layout.addWidget(delete_btn)

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def add_category(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category name is required.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Categories (name) VALUES (?)", (name,))
            conn.commit()
            QMessageBox.information(self, "Success", "Category added successfully.")
            self.clear_form()
            self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to add category: {}".format(str(e)))
        finally:
            conn.close()

    def load_categories(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Categories ORDER BY name")
        categories = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(categories))
        for row, (cat_id, name) in enumerate(categories):
            self.table.setItem(row, 0, create_professional_table_item(cat_id, 'id'))
            self.table.setItem(row, 1, create_professional_table_item(name, 'text'))

    def edit_category(self, row, column):
        cat_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        self.name_edit.setText(name)
        self.current_id = cat_id
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)

    def update_category(self):
        if not hasattr(self, 'current_id'):
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category name is required.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Categories SET name = ? WHERE id = ?", (name, self.current_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Category updated successfully.")
            self.clear_form()
            self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to update category: {}".format(str(e)))
        finally:
            conn.close()

    def delete_category(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a category to delete.")
            return

        cat_id = int(self.table.item(current_row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this category?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Categories WHERE id = ?", (cat_id,))
                conn.commit()
                self.load_categories()
            except Exception as e:
                QMessageBox.critical(self, "Error", "Failed to delete category: {}".format(str(e)))
            finally:
                conn.close()

    def clear_form(self):
        self.name_edit.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        if hasattr(self, 'current_id'):
            delattr(self, 'current_id')