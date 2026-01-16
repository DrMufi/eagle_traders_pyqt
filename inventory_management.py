from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QHeaderView, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item, ensure_table_visibility

class InventoryManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_inventory()

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

        # Title
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Product:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name...")
        self.search_edit.textChanged.connect(self.filter_inventory)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Inventory table
        self.table = QTableWidget()
        setup_professional_table(self.table, ["ID", "Name", "Current Stock", "Min Stock", "Status", "Category"], ['id', 'text', 'numeric', 'numeric', 'status', 'text'])
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        adjust_btn = QPushButton("Adjust Stock")
        adjust_btn.clicked.connect(self.adjust_stock)
        button_layout.addWidget(adjust_btn)

        bulk_adjust_btn = QPushButton("Bulk Adjust Stock")
        bulk_adjust_btn.clicked.connect(self.bulk_adjust_stock)
        button_layout.addWidget(bulk_adjust_btn)

        set_min_btn = QPushButton("Set Min Stock")
        set_min_btn.clicked.connect(self.set_min_stock)
        button_layout.addWidget(set_min_btn)

        low_stock_btn = QPushButton("Low Stock Alert")
        low_stock_btn.clicked.connect(self.show_low_stock)
        button_layout.addWidget(low_stock_btn)

        ledger_btn = QPushButton("View Stock Ledger")
        ledger_btn.clicked.connect(self.view_ledger)
        button_layout.addWidget(ledger_btn)

        layout.addLayout(button_layout)

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def load_inventory(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.current_stock, p.min_stock_level, c.name
            FROM Products p
            LEFT JOIN Categories c ON p.category_id = c.id
        """)
        products = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(products))
        for row, (prod_id, name, stock, min_stock, cat_name) in enumerate(products):
            self.table.setItem(row, 0, create_professional_table_item(prod_id, 'id'))
            self.table.setItem(row, 1, create_professional_table_item(name, 'text'))
            self.table.setItem(row, 2, create_professional_table_item(stock, 'numeric'))
            self.table.setItem(row, 3, create_professional_table_item(min_stock, 'numeric'))
            status = "Low Stock" if stock <= min_stock else "OK"
            self.table.setItem(row, 4, create_professional_table_item(status, 'status', {'Low Stock': 'red', 'OK': 'green'}))
            self.table.setItem(row, 5, create_professional_table_item(cat_name or "", 'text'))

    def refresh_inventory(self):
        self.load_inventory()

    def filter_inventory(self):
        search_text = self.search_edit.text().lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if name_item:
                name_text = name_item.text().lower()
                visible = search_text in name_text
                self.table.setRowHidden(row, not visible)

    def adjust_stock(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Stock Adjustment")
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()
        self.adjust_product_combo = QComboBox()
        self.load_products_for_adjust_combo()
        form_layout.addRow("Product:", self.adjust_product_combo)

        self.adjust_quantity_spin = QSpinBox()
        self.adjust_quantity_spin.setMinimum(-1000000)
        self.adjust_quantity_spin.setMaximum(1000000)
        form_layout.addRow("Quantity Adjustment:", self.adjust_quantity_spin)

        self.adjust_reason_edit = QLineEdit()
        form_layout.addRow("Reason:", self.adjust_reason_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.perform_stock_adjustment(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def perform_stock_adjustment(self, dialog):
        product_id = self.adjust_product_combo.currentData()
        quantity = self.adjust_quantity_spin.value()
        reason = self.adjust_reason_edit.text().strip()

        if not product_id:
            QMessageBox.warning(dialog, "Error", "Select a product.")
            return

        if quantity == 0:
            QMessageBox.warning(dialog, "Error", "Quantity must not be zero.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # Update product stock
            cursor.execute("UPDATE Products SET current_stock = current_stock + ? WHERE id = ?", (quantity, product_id))
            # Insert into StockLedger
            movement_type = 'in' if quantity > 0 else 'out' if quantity < 0 else 'adjustment'
            cursor.execute("""
                INSERT INTO StockLedger (product_id, movement_type, quantity, reason)
                VALUES (?, ?, ?, ?)
            """, (product_id, movement_type, abs(quantity), reason))
            conn.commit()
            QMessageBox.information(dialog, "Success", "Stock adjusted successfully.")
            dialog.accept()
            self.load_inventory()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to adjust stock: {str(e)}")
        finally:
            conn.close()

    def set_min_stock(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Minimum Stock Level")
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()
        self.min_product_combo = QComboBox()
        self.load_products_for_min_combo()
        form_layout.addRow("Product:", self.min_product_combo)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMaximum(1000000)
        form_layout.addRow("Min Stock Level:", self.min_stock_spin)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.perform_set_min_stock(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def perform_set_min_stock(self, dialog):
        product_id = self.min_product_combo.currentData()
        min_stock = self.min_stock_spin.value()

        if not product_id:
            QMessageBox.warning(dialog, "Error", "Select a product.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Products SET min_stock_level = ? WHERE id = ?", (min_stock, product_id))
            conn.commit()
            QMessageBox.information(dialog, "Success", "Min stock level set successfully.")
            dialog.accept()
            self.load_inventory()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to set min stock: {str(e)}")
        finally:
            conn.close()

    def load_products_for_adjust_combo(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Products ORDER BY name")
        products = cursor.fetchall()
        conn.close()
        self.adjust_product_combo.clear()
        for prod_id, name in products:
            self.adjust_product_combo.addItem(name, prod_id)

    def load_products_for_min_combo(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Products ORDER BY name")
        products = cursor.fetchall()
        conn.close()
        self.min_product_combo.clear()
        for prod_id, name in products:
            self.min_product_combo.addItem(name, prod_id)

    def show_low_stock(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, current_stock, min_stock_level FROM Products
            WHERE current_stock <= min_stock_level
            ORDER BY name
        """)
        low_stock_products = cursor.fetchall()
        conn.close()

        if not low_stock_products:
            QMessageBox.information(self, "Low Stock Alert", "No products are low on stock.")
            return

        message = "Low Stock Products:\n\n"
        for name, stock, min_stock in low_stock_products:
            message += f"{name}: Current {stock}, Min {min_stock}\n"
        QMessageBox.warning(self, "Low Stock Alert", message)

    def view_ledger(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Stock Ledger")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)

        # Filter by product
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Product:"))
        self.ledger_product_combo = QComboBox()
        self.ledger_product_combo.addItem("All Products", None)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Products ORDER BY name")
        products = cursor.fetchall()
        conn.close()
        for prod_id, name in products:
            self.ledger_product_combo.addItem(name, prod_id)
        self.ledger_product_combo.currentIndexChanged.connect(self.load_ledger)
        filter_layout.addWidget(self.ledger_product_combo)
        layout.addLayout(filter_layout)

        # Ledger table
        self.ledger_table = QTableWidget()
        setup_professional_table(self.ledger_table, ["ID", "Product", "Movement", "Quantity", "Reason", "Date"], ['id', 'text', 'status', 'numeric', 'text', 'date'])
        layout.addWidget(self.ledger_table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        self.load_ledger()
        dialog.exec()

    def load_ledger(self):
        product_id = self.ledger_product_combo.currentData()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if product_id:
            cursor.execute("""
                SELECT sl.id, p.name, sl.movement_type, sl.quantity, sl.reason, sl.date
                FROM StockLedger sl
                JOIN Products p ON sl.product_id = p.id
                WHERE sl.product_id = ?
                ORDER BY sl.date DESC
            """, (product_id,))
        else:
            cursor.execute("""
                SELECT sl.id, p.name, sl.movement_type, sl.quantity, sl.reason, sl.date
                FROM StockLedger sl
                JOIN Products p ON sl.product_id = p.id
                ORDER BY sl.date DESC
            """)
        entries = cursor.fetchall()
        conn.close()

        self.ledger_table.setRowCount(len(entries))
        for row, (entry_id, prod_name, movement, qty, reason, date) in enumerate(entries):
            self.ledger_table.setItem(row, 0, create_professional_table_item(entry_id, 'id'))
            self.ledger_table.setItem(row, 1, create_professional_table_item(prod_name, 'text'))
            self.ledger_table.setItem(row, 2, create_professional_table_item(movement, 'status', {'in': 'green', 'out': 'red', 'adjustment': 'yellow'}))
            self.ledger_table.setItem(row, 3, create_professional_table_item(qty, 'numeric'))
            self.ledger_table.setItem(row, 4, create_professional_table_item(reason or "", 'text'))
            self.ledger_table.setItem(row, 5, create_professional_table_item(date, 'date'))

    def bulk_adjust_stock(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Stock Adjustment")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        # Instructions
        layout.addWidget(QLabel("Select products and enter adjustment quantities:"))

        # Table for bulk adjustment
        self.bulk_table = QTableWidget()
        self.bulk_table.setColumnCount(4)
        self.bulk_table.setHorizontalHeaderLabels(["Product", "Current Stock", "Adjustment", "New Stock"])
        header = self.bulk_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ensure_table_visibility(self.bulk_table)
        layout.addWidget(self.bulk_table)

        # Load products into table
        self.load_bulk_products()

        # Reason input
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("Reason for adjustment:"))
        self.bulk_reason_edit = QLineEdit()
        reason_layout.addWidget(self.bulk_reason_edit)
        layout.addLayout(reason_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.perform_bulk_adjustment(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def load_bulk_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, current_stock FROM Products ORDER BY name")
        products = cursor.fetchall()
        conn.close()

        self.bulk_table.setRowCount(len(products))
        for row, (prod_id, name, current_stock) in enumerate(products):
            # Product name
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, prod_id)
            self.bulk_table.setItem(row, 0, name_item)

            # Current stock (read-only)
            current_item = QTableWidgetItem(str(current_stock))
            current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.bulk_table.setItem(row, 1, current_item)

            # Adjustment input
            adjust_spin = QSpinBox()
            adjust_spin.setMinimum(-1000000)
            adjust_spin.setMaximum(1000000)
            self.bulk_table.setCellWidget(row, 2, adjust_spin)

            # New stock (calculated, read-only)
            new_stock_item = QTableWidgetItem(str(current_stock))
            new_stock_item.setFlags(new_stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.bulk_table.setItem(row, 3, new_stock_item)

            # Connect spin box to update new stock
            adjust_spin.valueChanged.connect(lambda value, r=row: self.update_bulk_new_stock(r))

    def update_bulk_new_stock(self, row):
        current_stock = int(self.bulk_table.item(row, 1).text())
        adjust_spin = self.bulk_table.cellWidget(row, 2)
        adjustment = adjust_spin.value()
        new_stock = current_stock + adjustment
        self.bulk_table.item(row, 3).setText(str(new_stock))

    def perform_bulk_adjustment(self, dialog):
        reason = self.bulk_reason_edit.text().strip()
        adjustments = []

        for row in range(self.bulk_table.rowCount()):
            prod_id = self.bulk_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            adjust_spin = self.bulk_table.cellWidget(row, 2)
            quantity = adjust_spin.value()
            if quantity != 0:
                adjustments.append((prod_id, quantity))

        if not adjustments:
            QMessageBox.warning(dialog, "No Changes", "No stock adjustments were made.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            for prod_id, quantity in adjustments:
                # Update product stock
                cursor.execute("UPDATE Products SET current_stock = current_stock + ? WHERE id = ?", (quantity, prod_id))
                # Insert into StockLedger
                movement_type = 'in' if quantity > 0 else 'out'
                cursor.execute("""
                    INSERT INTO StockLedger (product_id, movement_type, quantity, reason)
                    VALUES (?, ?, ?, ?)
                """, (prod_id, movement_type, abs(quantity), reason))

            conn.commit()
            QMessageBox.information(dialog, "Success", f"Stock adjusted for {len(adjustments)} products.")
            dialog.accept()
            self.load_inventory()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to adjust stock: {str(e)}")
        finally:
            conn.close()