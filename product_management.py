from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QRadioButton, QButtonGroup, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QMessageBox, QSpinBox, QDoubleSpinBox, QScrollArea, QHeaderView,
    QDialog, QDialogButtonBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSizePolicy
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item, ensure_table_visibility
import csv

class ProductManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_products()

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

        # Form group
        form_group = QGroupBox("Add/Edit Product")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit()
        self.name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_edit.setMinimumWidth(300)
        form_layout.addRow("Name:", self.name_edit)

        self.category_combo = QComboBox()
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.category_combo.setMinimumWidth(300)
        self.load_categories()
        form_layout.addRow("Category:", self.category_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.supplier_combo.setMinimumWidth(300)
        self.load_suppliers()
        self.supplier_combo.currentIndexChanged.connect(self.update_supplier_details)
        form_layout.addRow("Supplier:", self.supplier_combo)

        # Supplier details (read-only)
        self.supplier_address = QLineEdit()
        self.supplier_address.setReadOnly(True)
        self.supplier_address.setPlaceholderText("Supplier address will appear here")
        form_layout.addRow("Address:", self.supplier_address)

        self.supplier_phone = QLineEdit()
        self.supplier_phone.setReadOnly(True)
        self.supplier_phone.setPlaceholderText("Supplier phone will appear here")
        form_layout.addRow("Phone:", self.supplier_phone)

        self.supplier_email = QLineEdit()
        self.supplier_email.setReadOnly(True)
        self.supplier_email.setPlaceholderText("Supplier email will appear here")
        form_layout.addRow("Email:", self.supplier_email)

        # Type radio buttons
        type_layout = QHBoxLayout()
        self.home_radio = QRadioButton("Home")
        self.import_radio = QRadioButton("Import")
        self.type_group = QButtonGroup()
        self.type_group.addButton(self.home_radio, 0)
        self.type_group.addButton(self.import_radio, 1)
        self.home_radio.setChecked(True)
        self.type_group.buttonClicked.connect(self.on_type_changed)
        type_layout.addWidget(self.home_radio)
        type_layout.addWidget(self.import_radio)
        type_layout.addStretch()
        form_layout.addRow("Type:", type_layout)

        # Cost fields
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setMaximum(1000000)
        self.cost_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cost_spin.setMinimumWidth(200)
        self.cost_spin.valueChanged.connect(self.calculate_price)
        form_layout.addRow("Cost Price:", self.cost_spin)

        self.packing_spin = QDoubleSpinBox()
        self.packing_spin.setMaximum(1000000)
        self.packing_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.packing_spin.setMinimumWidth(200)
        self.packing_spin.valueChanged.connect(self.calculate_price)
        form_layout.addRow("Packing:", self.packing_spin)

        self.others_spin = QDoubleSpinBox()
        self.others_spin.setMaximum(1000000)
        self.others_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.others_spin.setMinimumWidth(200)
        self.others_spin.valueChanged.connect(self.calculate_price)
        form_layout.addRow("Others:", self.others_spin)

        self.carriage_spin = QDoubleSpinBox()
        self.carriage_spin.setMaximum(1000000)
        self.carriage_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.carriage_spin.setMinimumWidth(200)
        self.carriage_spin.valueChanged.connect(self.calculate_price)
        form_layout.addRow("Carriage:", self.carriage_spin)

        self.profit_spin = QDoubleSpinBox()
        self.profit_spin.setMaximum(1000)  # Max 1000%
        self.profit_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.profit_spin.setMinimumWidth(200)
        self.profit_spin.setSuffix(" %")
        self.profit_spin.valueChanged.connect(self.calculate_price)
        form_layout.addRow("Profit (%):", self.profit_spin)

        self.selling_price_edit = QLineEdit()
        self.selling_price_edit.setReadOnly(True)
        self.selling_price_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.selling_price_edit.setMinimumWidth(200)
        form_layout.addRow("Selling Price:", self.selling_price_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Product")
        self.add_btn.clicked.connect(self.add_product)
        button_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Update Product")
        self.update_btn.clicked.connect(self.update_product)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)

        # Bulk buttons
        bulk_layout = QHBoxLayout()
        self.bulk_add_btn = QPushButton("Bulk Add by Category")
        self.bulk_add_btn.clicked.connect(self.bulk_add_products)
        bulk_layout.addWidget(self.bulk_add_btn)

        self.import_csv_btn = QPushButton("Import from CSV")
        self.import_csv_btn.clicked.connect(self.import_from_csv)
        bulk_layout.addWidget(self.import_csv_btn)

        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        bulk_layout.addWidget(self.export_csv_btn)

        form_layout.addRow(button_layout)
        form_layout.addRow(bulk_layout)

        layout.addWidget(form_group)

        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_edit.setMinimumWidth(400)
        self.search_edit.setPlaceholderText("Search by ID or Name...")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Products table
        self.table = QTableWidget()
        setup_professional_table(self.table, ["ID", "Name", "Category", "Type", "Selling Price", "Stock", "Min Stock"], ['id', 'text', 'text', 'text', 'numeric', 'numeric', 'numeric'])
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.cellDoubleClicked.connect(self.edit_product)
        layout.addWidget(self.table)

        # Delete button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_product)
        layout.addWidget(delete_btn)

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # Initial setup
        self.on_type_changed()
        self.calculate_price()

    def hideEvent(self, event):
        # Clear form when leaving the page
        self.clear_form()
        super().hideEvent(event)

    def load_categories(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Categories")
        categories = cursor.fetchall()
        conn.close()
        self.category_combo.clear()
        self.category_combo.addItem("Select Category", None)
        for cat_id, name in categories:
            self.category_combo.addItem(name, cat_id)

    def refresh_categories(self):
        self.load_categories()

    def refresh_suppliers(self):
        self.load_suppliers()

    def load_suppliers(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Suppliers")
        suppliers = cursor.fetchall()
        conn.close()
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Select Supplier", None)
        for sup_id, name in suppliers:
            self.supplier_combo.addItem(name, sup_id)

    def update_supplier_details(self):
        """Update supplier details in real-time when supplier is selected"""
        supplier_id = self.supplier_combo.currentData()
        if supplier_id is None:
            # Clear details when no supplier selected
            self.supplier_address.clear()
            self.supplier_phone.clear()
            self.supplier_email.clear()
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT address, phone, email FROM Suppliers WHERE id = ?", (supplier_id,))
        supplier = cursor.fetchone()
        conn.close()

        if supplier:
            self.supplier_address.setText(supplier[0] or "")
            self.supplier_phone.setText(supplier[1] or "")
            self.supplier_email.setText(supplier[2] or "")
        else:
            # Clear if supplier not found
            self.supplier_address.clear()
            self.supplier_phone.clear()
            self.supplier_email.clear()

    def on_type_changed(self):
        is_home = self.home_radio.isChecked()
        self.packing_spin.setEnabled(is_home)
        self.others_spin.setEnabled(is_home)
        self.carriage_spin.setEnabled(True)  # Always enable carriage charges

        # Clear type-specific fields when switching
        if is_home:
            self.carriage_spin.setValue(0)  # Clear carriage for home products (though still enabled)
        else:
            self.packing_spin.setValue(0)  # Clear packing for import products
            self.others_spin.setValue(0)   # Clear others for import products

        self.calculate_price()

    def calculate_price(self):
        cost = self.cost_spin.value()
        packing = self.packing_spin.value()
        others = self.others_spin.value()
        carriage = self.carriage_spin.value()
        profit_percent = self.profit_spin.value()

        if self.home_radio.isChecked():
            # Home: Total cost = Cost + Packing + Others + Carriage
            total_cost = cost + packing + others + carriage
            # Selling price = total_cost + (total_cost * profit_percent / 100)
            selling_price = total_cost * (1 + profit_percent / 100)
        else:
            # Import: Total cost = Cost + Carriage
            total_cost = cost + carriage
            # Selling price = total_cost + (total_cost * profit_percent / 100)
            selling_price = total_cost * (1 + profit_percent / 100)

        self.selling_price_edit.setText(f"{selling_price:.2f}")

    def add_product(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required.")
            return

        category_id = self.category_combo.currentData()
        supplier_id = self.supplier_combo.currentData()
        is_import = 1 if self.import_radio.isChecked() else 0
        unit_price = float(self.selling_price_edit.text())

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Products (name, category_id, supplier_id, is_import, unit_price, current_stock, min_stock_level)
                VALUES (?, ?, ?, ?, ?, 0, 0)
            """, (name, category_id, supplier_id, is_import, unit_price))
            conn.commit()
            QMessageBox.information(self, "Success", "Product added successfully.")
            self.clear_form()
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")
        finally:
            conn.close()

    def load_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, c.name, CASE WHEN p.is_import THEN 'Import' ELSE 'Home' END, p.unit_price, p.current_stock, p.min_stock_level
            FROM Products p
            LEFT JOIN Categories c ON p.category_id = c.id
        """)
        products = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(products))
        for row, (prod_id, name, cat_name, prod_type, price, stock, min_stock) in enumerate(products):
            self.table.setItem(row, 0, create_professional_table_item(prod_id, 'id'))
            self.table.setItem(row, 1, create_professional_table_item(name, 'text'))
            self.table.setItem(row, 2, create_professional_table_item(cat_name or "", 'text'))
            self.table.setItem(row, 3, create_professional_table_item(prod_type, 'text'))
            self.table.setItem(row, 4, create_professional_table_item(price, 'numeric'))
            self.table.setItem(row, 5, create_professional_table_item(stock, 'numeric'))
            self.table.setItem(row, 6, create_professional_table_item(min_stock, 'numeric'))

    def edit_product(self, row, column):
        prod_id = int(self.table.item(row, 0).text())
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE id = ?", (prod_id,))
        product = cursor.fetchone()
        conn.close()

        if product:
            self.current_product_id = prod_id
            self.name_edit.setText(product[1])
            # category_id = product[3], supplier_id = product[4], is_import = product[5], unit_price = product[6]
            self.category_combo.setCurrentIndex(self.category_combo.findData(product[3]))
            self.supplier_combo.setCurrentIndex(self.supplier_combo.findData(product[4]))
            # Update supplier details after setting combo
            self.update_supplier_details()
            if product[5]:  # is_import
                self.import_radio.setChecked(True)
            else:
                self.home_radio.setChecked(True)
            # Set cost fields if needed, but for simplicity, skip
            self.selling_price_edit.setText(f"{product[6]:.2f}")
            self.add_btn.setEnabled(False)
            self.update_btn.setEnabled(True)

    def update_product(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required.")
            return

        category_id = self.category_combo.currentData()
        supplier_id = self.supplier_combo.currentData()
        is_import = 1 if self.import_radio.isChecked() else 0
        unit_price = float(self.selling_price_edit.text())

        # Get product ID from somewhere, perhaps store it when editing
        # For now, assume we have self.current_product_id
        if not hasattr(self, 'current_product_id') or not self.current_product_id:
            QMessageBox.warning(self, "Error", "No product selected for update.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Products SET name=?, category_id=?, supplier_id=?, is_import=?, unit_price=?
                WHERE id=?
            """, (name, category_id, supplier_id, is_import, unit_price, self.current_product_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Product updated successfully.")
            self.clear_form()
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update product: {str(e)}")
        finally:
            conn.close()

    def delete_product(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a product to delete.")
            return

        prod_id = int(self.table.item(current_row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this product?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Products WHERE id = ?", (prod_id,))
                conn.commit()
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")
            finally:
                conn.close()

    def filter_products(self):
        search_text = self.search_edit.text().lower()
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if id_item and name_item:
                id_text = id_item.text()
                name_text = name_item.text().lower()
                visible = search_text in id_text or search_text in name_text
                self.table.setRowHidden(row, not visible)

    def clear_form(self):
        self.name_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.supplier_combo.setCurrentIndex(0)
        self.supplier_address.clear()
        self.supplier_phone.clear()
        self.supplier_email.clear()
        self.home_radio.setChecked(True)
        self.cost_spin.setValue(0)
        self.packing_spin.setValue(0)
        self.others_spin.setValue(0)
        self.carriage_spin.setValue(0)
        self.profit_spin.setValue(0)
        self.selling_price_edit.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        if hasattr(self, 'current_product_id'):
            del self.current_product_id

    def bulk_add_products(self):
        dialog = BulkAddDialog(self.db, self)
        dialog.exec()
        self.load_products()

    def import_from_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Products from CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                conn = self.db.get_connection()
                cursor = conn.cursor()
                added = 0
                for row in reader:
                    name = row.get('name', '').strip()
                    category_name = row.get('category', '').strip()
                    supplier_name = row.get('supplier', '').strip()
                    is_import_str = row.get('type', 'Home').strip().lower()
                    is_import = 1 if is_import_str == 'import' else 0
                    unit_price = float(row.get('unit_price', 0))
                    current_stock = int(row.get('current_stock', 0))
                    min_stock_level = int(row.get('min_stock_level', 0))
                    barcode = row.get('barcode', '').strip()

                    # Get category_id
                    cursor.execute("SELECT id FROM Categories WHERE name = ?", (category_name,))
                    cat_result = cursor.fetchone()
                    category_id = cat_result[0] if cat_result else None

                    # Get supplier_id
                    cursor.execute("SELECT id FROM Suppliers WHERE name = ?", (supplier_name,))
                    sup_result = cursor.fetchone()
                    supplier_id = sup_result[0] if sup_result else None

                    if name and category_id is not None:
                        cursor.execute("""
                            INSERT INTO Products (name, category_id, supplier_id, is_import, unit_price, barcode, current_stock, min_stock_level)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (name, category_id, supplier_id, is_import, unit_price, barcode, current_stock, min_stock_level))
                        added += 1
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", f"Imported {added} products successfully.")
                self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Products to CSV", "products.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.name, c.name as category, s.name as supplier, CASE WHEN p.is_import THEN 'Import' ELSE 'Home' END as type,
                       p.unit_price, p.barcode, p.current_stock, p.min_stock_level
                FROM Products p
                LEFT JOIN Categories c ON p.category_id = c.id
                LEFT JOIN Suppliers s ON p.supplier_id = s.id
            """)
            products = cursor.fetchall()
            conn.close()

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'category', 'supplier', 'type', 'unit_price', 'barcode', 'current_stock', 'min_stock_level']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for prod in products:
                    writer.writerow({
                        'name': prod[0],
                        'category': prod[1] or '',
                        'supplier': prod[2] or '',
                        'type': prod[3],
                        'unit_price': prod[4],
                        'barcode': prod[5] or '',
                        'current_stock': prod[6],
                        'min_stock_level': prod[7]
                    })
            QMessageBox.information(self, "Success", "Products exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")


class BulkAddDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Bulk Add Products")
        self.setGeometry(200, 200, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Category selection (optional)
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Select Category (optional):"))
        self.category_combo = QComboBox()
        self.load_categories()
        cat_layout.addWidget(self.category_combo)
        layout.addLayout(cat_layout)

        # Supplier selection (optional)
        sup_layout = QHBoxLayout()
        sup_layout.addWidget(QLabel("Select Supplier (optional):"))
        self.supplier_combo = QComboBox()
        self.load_suppliers()
        sup_layout.addWidget(self.supplier_combo)
        layout.addLayout(sup_layout)

        # Products table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Cost Price", "Packing", "Others/Carriage", "Profit (%)"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ensure_table_visibility(self.table)
        self.table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.table)

        # Add first row by default
        self.add_row()

        # Buttons
        btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self.add_row)
        btn_layout.addWidget(add_row_btn)

        remove_row_btn = QPushButton("Remove Selected Row")
        remove_row_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(remove_row_btn)

        save_btn = QPushButton("Save Products")
        save_btn.clicked.connect(self.save_products)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def load_categories(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Categories")
        categories = cursor.fetchall()
        conn.close()
        self.category_combo.clear()
        self.category_combo.addItem("Select Category", None)
        for cat_id, name in categories:
            self.category_combo.addItem(name, cat_id)

    def load_suppliers(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Suppliers")
        suppliers = cursor.fetchall()
        conn.close()
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Select Supplier", None)
        for sup_id, name in suppliers:
            self.supplier_combo.addItem(name, sup_id)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Name edit
        name_edit = QLineEdit()
        name_edit.setFixedHeight(35)
        name_edit.textChanged.connect(lambda: self.on_name_changed(row))
        self.table.setCellWidget(row, 0, name_edit)
        # Add combo for type
        type_combo = QComboBox()
        type_combo.setFixedHeight(35)
        type_combo.addItems(["Home", "Import"])
        self.table.setCellWidget(row, 1, type_combo)
        # Add spin boxes for costs
        for col in [2, 3, 4]:
            spin = QDoubleSpinBox()
            spin.setMaximum(1000000)
            spin.setFixedHeight(35)
            self.table.setCellWidget(row, col, spin)
        # Profit spin box with percentage
        profit_spin = QDoubleSpinBox()
        profit_spin.setMaximum(1000)  # Max 1000%
        profit_spin.setSuffix(" %")
        profit_spin.setFixedHeight(35)
        self.table.setCellWidget(row, 5, profit_spin)

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def on_name_changed(self, row):
        name_edit = self.table.cellWidget(row, 0)
        if name_edit and name_edit.text().strip() and row == self.table.rowCount() - 1:
            self.add_row()

    def save_products(self):
        category_id = self.category_combo.currentData()
        supplier_id = self.supplier_combo.currentData()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        added = 0
        for row in range(self.table.rowCount()):
            name_edit = self.table.cellWidget(row, 0)
            if not name_edit:
                continue
            name = name_edit.text().strip()
            if not name:
                continue

            type_combo = self.table.cellWidget(row, 1)
            is_import = 1 if type_combo.currentText() == "Import" else 0

            cost_spin = self.table.cellWidget(row, 2)
            cost = cost_spin.value()

            packing_spin = self.table.cellWidget(row, 3)
            packing = packing_spin.value()

            others_carriage_spin = self.table.cellWidget(row, 4)
            others_carriage = others_carriage_spin.value()

            profit_spin = self.table.cellWidget(row, 5)
            profit_percent = profit_spin.value()

            if is_import:
                total_cost = cost + others_carriage
                unit_price = total_cost * (1 + profit_percent / 100)
            else:
                total_cost = cost + packing + others_carriage
                unit_price = total_cost * (1 + profit_percent / 100)

            try:
                cursor.execute("""
                    INSERT INTO Products (name, category_id, supplier_id, is_import, unit_price, current_stock, min_stock_level)
                    VALUES (?, ?, ?, ?, ?, 0, 0)
                """, (name, category_id, supplier_id, is_import, unit_price))
                added += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add product {name}: {str(e)}")
                conn.rollback()
                conn.close()
                return

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Success", f"Added {added} products successfully.")
        self.accept()