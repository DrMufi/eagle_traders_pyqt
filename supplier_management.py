from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item

class SupplierManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_suppliers()

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

        # Add/Edit Supplier
        form_group = QGroupBox("Add/Edit Supplier")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit()
        form_layout.addRow("Supplier Name:", self.name_edit)

        self.address_edit = QLineEdit()
        form_layout.addRow("Address:", self.address_edit)

        self.phone_edit = QLineEdit()
        form_layout.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        form_layout.addRow("Email:", self.email_edit)

        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Supplier")
        self.add_btn.clicked.connect(self.add_supplier)
        button_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Update Supplier")
        self.update_btn.clicked.connect(self.update_supplier)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)

        form_layout.addRow(button_layout)
        layout.addWidget(form_group)

        # Suppliers table
        self.table = QTableWidget()
        setup_professional_table(self.table, ["ID", "Name", "Address", "Phone", "Email"], ['id', 'text', 'text', 'text', 'text'])
        self.table.cellDoubleClicked.connect(self.edit_supplier)
        layout.addWidget(self.table)

        # Delete button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_supplier)
        layout.addWidget(delete_btn)

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def add_supplier(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Supplier name is required.")
            return

        address = self.address_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Suppliers (name, address, phone, email)
                VALUES (?, ?, ?, ?)
            """, (name, address, phone, email))
            conn.commit()
            QMessageBox.information(self, "Success", "Supplier added successfully.")
            self.clear_form()
            self.load_suppliers()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to add supplier: {}".format(str(e)))
        finally:
            conn.close()

    def load_suppliers(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, address, phone, email FROM Suppliers ORDER BY name")
        suppliers = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(suppliers))
        for row, (sup_id, name, address, phone, email) in enumerate(suppliers):
            self.table.setItem(row, 0, create_professional_table_item(sup_id, 'id'))
            self.table.setItem(row, 1, create_professional_table_item(name, 'text'))
            self.table.setItem(row, 2, create_professional_table_item(address or "", 'text'))
            self.table.setItem(row, 3, create_professional_table_item(phone or "", 'text'))
            self.table.setItem(row, 4, create_professional_table_item(email or "", 'text'))

    def edit_supplier(self, row, column):
        sup_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        address = self.table.item(row, 2).text()
        phone = self.table.item(row, 3).text()
        email = self.table.item(row, 4).text()

        self.name_edit.setText(name)
        self.address_edit.setText(address)
        self.phone_edit.setText(phone)
        self.email_edit.setText(email)
        self.current_id = sup_id
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)

    def update_supplier(self):
        if not hasattr(self, 'current_id'):
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Supplier name is required.")
            return

        address = self.address_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Suppliers SET name = ?, address = ?, phone = ?, email = ?
                WHERE id = ?
            """, (name, address, phone, email, self.current_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Supplier updated successfully.")
            self.clear_form()
            self.load_suppliers()
        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to update supplier: {}".format(str(e)))
        finally:
            conn.close()

    def delete_supplier(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a supplier to delete.")
            return

        sup_id = int(self.table.item(current_row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this supplier?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Suppliers WHERE id = ?", (sup_id,))
                conn.commit()
                self.load_suppliers()
            except Exception as e:
                QMessageBox.critical(self, "Error", "Failed to delete supplier: {}".format(str(e)))
            finally:
                conn.close()

    def clear_form(self):
        self.name_edit.clear()
        self.address_edit.clear()
        self.phone_edit.clear()
        self.email_edit.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        if hasattr(self, 'current_id'):
            delattr(self, 'current_id')