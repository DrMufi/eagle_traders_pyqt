from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout,
    QMessageBox, QSpinBox, QDoubleSpinBox, QListWidget, QListWidgetItem, QHeaderView, QInputDialog, QScrollArea, QSizePolicy, QDialog, QDialogButtonBox, QCompleter
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QMarginsF, QUrl
from PyQt6.QtGui import QColor, QTextDocument, QFontDatabase, QPageSize, QPageLayout, QDesktopServices
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item
import datetime
import os
import sys

class SalesPOS(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.cart = []  # list of [product_id, name, qty, unit_price, discount_percent, total]
        self.all_products = []  # list of (id, name, barcode, unit_price)
        self.load_all_products()
        self.init_ui()

    def load_all_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, barcode, unit_price FROM Products ORDER BY name")
        self.all_products = cursor.fetchall()
        conn.close()

    def load_customers_for_sales(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Customers ORDER BY name")
        customers = cursor.fetchall()
        conn.close()
        self.buyer_name_edit.clear()
        self.buyer_name_edit.addItem("", None)  # Empty
        for cid, name in customers:
            self.buyer_name_edit.addItem(name, cid)
        # Completer
        # customer_names = [name for cid, name in customers]
        # completer = QCompleter(customer_names)
        # completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # self.buyer_name_edit.setCompleter(completer)

    def on_buyer_changed(self):
        name = self.buyer_name_edit.currentText().strip()
        if not name:
            self.buyer_contact_edit.clear()
            self.customer_history_table.setRowCount(0)
            return
        # Find customer
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone FROM Customers WHERE name = ?", (name,))
        customer = cursor.fetchone()
        if customer:
            cid, phone = customer
            self.buyer_contact_edit.setText(phone or "")
            # Load history
            cursor.execute("""
                SELECT date, total_amount, status
                FROM SalesTransactions
                WHERE buyer_name = ?
                ORDER BY date DESC
            """, (name,))
            history = cursor.fetchall()
            self.customer_history_table.setRowCount(len(history))
            for r, (date, total, status) in enumerate(history):
                self.customer_history_table.setItem(r, 0, QTableWidgetItem(date))
                self.customer_history_table.setItem(r, 1, QTableWidgetItem(f"{total:.2f}"))
                self.customer_history_table.setItem(r, 2, QTableWidgetItem(status))
        else:
            self.buyer_contact_edit.clear()
            self.customer_history_table.setRowCount(0)
        conn.close()

    def refresh_products(self):
        self.load_all_products()
        self.filter_products()

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

        # Product selection
        select_group = QGroupBox("Add Product to Cart")
        select_layout = QVBoxLayout(select_group)

        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Product:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search products...")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)
        select_layout.addLayout(search_layout)

        # Barcode input
        barcode_layout = QHBoxLayout()
        barcode_layout.addWidget(QLabel("Barcode:"))
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText("Scan or enter barcode...")
        self.barcode_edit.returnPressed.connect(self.add_by_barcode)
        barcode_layout.addWidget(self.barcode_edit)
        select_layout.addLayout(barcode_layout)

        # Product list
        self.product_list = QListWidget()
        self.product_list.setMinimumHeight(150)
        self.product_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.product_list.itemDoubleClicked.connect(self.select_product)
        select_layout.addWidget(self.product_list)

        # Quantity and add
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(1000)
        qty_layout.addWidget(self.qty_spin)

        add_btn = QPushButton("Add to Cart")
        add_btn.clicked.connect(self.add_to_cart)
        add_btn.setProperty("hover_scale", False)
        add_btn.enterEvent = lambda e: self.animate_button_hover(add_btn, True)
        add_btn.leaveEvent = lambda e: self.animate_button_hover(add_btn, False)
        qty_layout.addWidget(add_btn)

        add_selected_btn = QPushButton("Add Selected")
        add_selected_btn.clicked.connect(self.add_selected_to_cart)
        qty_layout.addWidget(add_selected_btn)

        qty_layout.addStretch()
        select_layout.addLayout(qty_layout)

        layout.addWidget(select_group)

        # Cart table
        self.cart_table = QTableWidget()
        setup_professional_table(self.cart_table, ["Product", "Qty", "Unit Price", "Discount %", "Total", "Remove"], ['text', 'numeric', 'numeric', 'numeric', 'numeric', 'action'])
        self.cart_table.setMouseTracking(True)
        self.cart_table.mouseMoveEvent = self.table_mouse_move
        self.cart_table.setMinimumHeight(200)
        self.cart_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.cart_table)

        # Buyer details
        buyer_group = QGroupBox("Buyer Details")
        buyer_layout = QHBoxLayout(buyer_group)
        buyer_layout.addWidget(QLabel("Buyer Name:"))
        self.buyer_name_edit = QComboBox()
        self.buyer_name_edit.setEditable(True)
        self.buyer_name_edit.setMinimumWidth(250)
        buyer_layout.addWidget(self.buyer_name_edit)
        self.load_customers_for_sales()
        # Remove completer to allow free input
        # completer = QCompleter(customer_names)
        # completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # self.buyer_name_edit.setCompleter(completer)
        self.buyer_name_edit.currentTextChanged.connect(self.on_buyer_changed)
        buyer_layout.addWidget(QLabel("Contact:"))
        self.buyer_contact_edit = QLineEdit()
        self.buyer_contact_edit.setPlaceholderText("Enter contact info")
        self.buyer_contact_edit.setMinimumWidth(200)
        buyer_layout.addWidget(self.buyer_contact_edit)
        layout.addWidget(buyer_group)

        # Customer history
        history_group = QGroupBox("Customer History")
        history_layout = QVBoxLayout(history_group)
        self.customer_history_table = QTableWidget()
        self.customer_history_table.setColumnCount(3)
        self.customer_history_table.setHorizontalHeaderLabels(["Date", "Total", "Status"])
        self.customer_history_table.setMaximumHeight(150)
        history_layout.addWidget(self.customer_history_table)
        layout.addWidget(history_group)

        # Total and checkout
        total_layout = QHBoxLayout()
        total_layout.addStretch()

        self.total_label = QLabel("Total: Rs. 0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        total_layout.addWidget(self.total_label)

        return_btn = QPushButton("Process Return")
        return_btn.clicked.connect(self.process_return)
        total_layout.addWidget(return_btn)

        checkout_btn = QPushButton("Checkout & Print Bill")
        checkout_btn.clicked.connect(self.checkout)
        total_layout.addWidget(checkout_btn)

        layout.addLayout(total_layout)

        # Initial filter (show all)
        self.filter_products()

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)


    def filter_products(self):
        search_text = self.search_edit.text().lower()
        self.product_list.clear()

        for item in self.all_products:
            if len(item) >= 4:
                prod_id, name, code, price = item
                if search_text in name.lower() or search_text in str(code).lower():
                    item_text = f"{name} ({code}) - Rs. {price:.2f}"
                    list_item = QListWidgetItem(item_text)
                    list_item.setData(Qt.ItemDataRole.UserRole, prod_id)
                    self.product_list.addItem(list_item)

    def select_product(self, item):
        pass

    def add_by_barcode(self):
        barcode = self.barcode_edit.text().strip()
        if not barcode:
            return

        # Find product by barcode
        for prod_id, name, code, price in self.all_products:
            if str(code) == barcode:
                self.add_product_to_cart(prod_id, 1)
                self.barcode_edit.clear()
                return

        QMessageBox.warning(self, "Not Found", f"Product with barcode '{barcode}' not found.")
        self.barcode_edit.clear()

    def add_selected_to_cart(self):
        selected_items = self.product_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select products from the list.")
            return

        qty = self.qty_spin.value()
        added = 0
        for item in selected_items:
            prod_id = item.data(Qt.ItemDataRole.UserRole)
            self.add_product_to_cart(prod_id, qty)
            added += 1

        QMessageBox.information(self, "Added", f"Added {added} product(s) to cart.")
        self.product_list.clearSelection()

    def add_to_cart(self):
        current_item = self.product_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Select a product from the list.")
            return

        prod_id = current_item.data(Qt.ItemDataRole.UserRole)
        qty = self.qty_spin.value()
        self.add_product_to_cart(prod_id, qty)

    def add_product_to_cart(self, prod_id, qty):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, unit_price FROM Products WHERE id = ?", (prod_id,))
        product = cursor.fetchone()
        conn.close()

        if not product or len(product) < 2:
            return

        name, unit_price = product

        # Update if already in cart
        for item in self.cart:
            if item[0] == prod_id:
                item[2] += qty
                item[5] = item[2] * item[3] * (1 - item[4] / 100)
                break
        else:
            total = qty * unit_price
            self.cart.append([prod_id, name, qty, unit_price, 0.0, total])

        self.update_cart_table()
        self.update_total()

    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            _, name, qty, price, discount, total = item
            self.cart_table.setItem(row, 0, create_professional_table_item(name, 'text'))
            self.cart_table.setItem(row, 1, create_professional_table_item(qty, 'numeric'))
            self.cart_table.setItem(row, 2, create_professional_table_item(price, 'numeric'))

            discount_spin = QDoubleSpinBox()
            discount_spin.setRange(0, 100)
            discount_spin.setValue(discount)
            discount_spin.setSuffix(" %")
            discount_spin.setFixedHeight(35)
            discount_spin.valueChanged.connect(lambda value, r=row: self.update_discount(r, value))
            self.cart_table.setCellWidget(row, 3, discount_spin)

            self.cart_table.setItem(row, 4, create_professional_table_item(total, 'numeric'))

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 5, remove_btn)

    def update_discount(self, row, value):
        if 0 <= row < len(self.cart):
            self.cart[row][4] = value
            self.cart[row][5] = self.cart[row][2] * self.cart[row][3] * (1 - value / 100)
            self.update_cart_table()
            self.update_total()

    def remove_from_cart(self, row):
        if 0 <= row < len(self.cart):
            del self.cart[row]
            self.update_cart_table()
            self.update_total()

    def update_total(self):
        total = sum(item[5] for item in self.cart)
        self.total_label.setText(f"Total: Rs. {total:.2f}")

    def animate_button_hover(self, button, hover):
        scale = 1.05 if hover else 1.0
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(200)
        start_rect = button.geometry()
        dx = int(start_rect.width() * (scale - 1) / 2)
        dy = int(start_rect.height() * (scale - 1) / 2)
        dw = int(start_rect.width() * (scale - 1))
        dh = int(start_rect.height() * (scale - 1))
        end_rect = start_rect.adjusted(-dx, -dy, dw, dh)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()

    def table_mouse_move(self, event):
        row = self.cart_table.rowAt(event.pos().y())
        for r in range(self.cart_table.rowCount()):
            for c in range(self.cart_table.columnCount()):
                item = self.cart_table.item(r, c)
                if item:
                    item.setBackground(QColor('lightblue') if r == row else QColor('transparent'))

    def checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty.")
            return

        buyer_name = self.buyer_name_edit.currentText().strip()
        if not buyer_name:
            QMessageBox.warning(self, "Required", "Buyer's name is required.")
            return
        buyer_contact = self.buyer_contact_edit.text().strip()

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Check if customer exists, else create
        cursor.execute("SELECT id FROM Customers WHERE name = ?", (buyer_name,))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer[0]
        else:
            cursor.execute("INSERT INTO Customers (name, phone) VALUES (?, ?)", (buyer_name, buyer_contact))
            customer_id = cursor.lastrowid

        total = sum(item[5] for item in self.cart)

        # Payment
        payment_dialog = PaymentDialog(total, self)
        result = payment_dialog.exec()
        if result != 1:  # QDialog.Accepted is 1
            return

        amount_received = payment_dialog.get_amount_received()

        change = 0.0
        balance_due = 0.0
        if amount_received >= total:
            change = amount_received - total
        else:
            balance_due = total - amount_received

        try:
            cursor.execute(
                "INSERT INTO SalesTransactions (customer_id, buyer_name, buyer_contact, total_amount, status) VALUES (?, ?, ?, ?, 'completed')",
                (customer_id, buyer_name, buyer_contact, total)
            )
            sale_id = cursor.lastrowid

            for item in self.cart:
                prod_id, name, qty, price, discount, item_total = item
                cursor.execute(
                    "INSERT INTO SalesItems (sale_id, product_id, quantity, unit_price, total_price, discount_percent) VALUES (?, ?, ?, ?, ?, ?)",
                    (sale_id, prod_id, qty, price, item_total, discount)
                )

                # Reduce stock
                cursor.execute(
                    "SELECT id, quantity FROM ProductBatches WHERE product_id = ? AND quantity > 0 ORDER BY expiry_month, expiry_year LIMIT 1",
                    (prod_id,)
                )
                batch = cursor.fetchone()
                if batch:
                    batch_id, batch_qty = batch
                    new_qty = batch_qty - qty
                    if new_qty >= 0:
                        cursor.execute("UPDATE ProductBatches SET quantity = ? WHERE id = ?", (new_qty, batch_id))
                        cursor.execute(
                            "INSERT INTO StockLedger (product_id, batch_id, movement_type, quantity, reason, reference_id) VALUES (?, ?, 'out', ?, 'sale', ?)",
                            (prod_id, batch_id, qty, sale_id)
                        )

            # Update General Ledger
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            description = f"Sale Transaction #{sale_id} - {buyer_name}"
            cursor.execute("SELECT balance FROM GeneralLedger ORDER BY id DESC LIMIT 1")
            last_balance = cursor.fetchone()
            last_balance = last_balance[0] if last_balance else 0.0
            new_balance = last_balance + total
            cursor.execute(
                "INSERT INTO GeneralLedger (date, description, type, amount, balance) VALUES (?, ?, 'income', ?, ?)",
                (current_date, description, total, new_balance)
            )

            # Update Customer Ledger
            cursor.execute("SELECT balance FROM CustomerLedger WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,))
            last_cust_balance = cursor.fetchone()
            last_cust_balance = last_cust_balance[0] if last_cust_balance else 0.0
            new_cust_balance = last_cust_balance + total - amount_received  # Debit total, credit received
            cursor.execute(
                "INSERT INTO CustomerLedger (customer_id, date, description, debit, credit, balance) VALUES (?, ?, ?, ?, ?, ?)",
                (customer_id, current_date, description, total, amount_received, new_cust_balance)
            )

            conn.commit()
            QMessageBox.information(self, "Success", "Sale completed successfully.")
            self.generate_bill(sale_id, self.cart, total, buyer_name, buyer_contact, amount_received, change, balance_due)
            self.cart.clear()
            self.update_cart_table()
            self.update_total()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to complete sale: {str(e)}")
        finally:
            conn.close()

    def generate_bill(self, sale_id, items, total, buyer_name, buyer_contact, amount_received, change, balance_due):
        # Create customer folder and subfolders
        customer_folder = f"customers/{buyer_name.replace(' ', '_').replace('/', '_')}"
        sales_folder = os.path.join(customer_folder, "sales")
        ledger_folder = os.path.join(customer_folder, "ledger")
        os.makedirs(sales_folder, exist_ok=True)
        os.makedirs(ledger_folder, exist_ok=True)

        filename = f"{sales_folder}/bill_{sale_id}.pdf"

        # Load Urdu font
        font_id = QFontDatabase.addApplicationFont("fonts/NotoNastaliqUrdu-VariableFont_wght.ttf")
        urdu_font_family = ""
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                urdu_font_family = families[0]
        else:
            urdu_font_family = "Arial"  # Fallback

        # Read the template
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            bundle_dir = sys._MEIPASS
            template_path = os.path.join(bundle_dir, 'invoice.html')
        else:
            template_path = 'invoice.html'
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Build items HTML
        items_html = ""
        for i, item in enumerate(items, 1):
            _, name, qty, price, discount, line_total = item
            items_html += f"""
                        <tr>
                            <td class="text-center font-medium">{i}</td>
                            <td class="font-bold text-slate-800 text-lg">{name}</td>
                            <td class="text-right">{qty}</td>
                            <td class="text-right font-semibold">Rs. {price:.2f}</td>
                            <td class="text-right">{discount:.1f}%</td>
                            <td class="text-right font-bold">Rs. {line_total:.2f}</td>
                        </tr>
"""

        # Replace placeholders
        subtotal = total
        tax = 0.0
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        html = html.replace("{sale_id}", str(sale_id))
        html = html.replace("{date}", date)
        html = html.replace("{buyer_name}", buyer_name)
        html = html.replace("{buyer_contact}", buyer_contact)
        html = html.replace("{items_html}", items_html)
        html = html.replace("{subtotal:.2f}", f"{subtotal:.2f}")
        html = html.replace("{tax:.2f}", f"{tax:.2f}")
        html = html.replace("{total:.2f}", f"{total:.2f}")
        html = html.replace("{amount_received:.2f}", f"{amount_received:.2f}")
        html = html.replace("{change:.2f}", f"{change:.2f}")
        html = html.replace("{balance_due:.2f}", f"{balance_due:.2f}")

        # Create PDF
        document = QTextDocument()
        document.setHtml(html)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        document.print(printer)
        QDesktopServices.openUrl(QUrl.fromLocalFile(filename))


    def process_return(self):
        """Open return processing dialog"""
        dialog = ReturnDialog(self.db, self)
        dialog.exec()


class PaymentDialog(QDialog):
    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.total = total
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Payment")
        self.setModal(True)
        self.resize(350, 200)

        layout = QVBoxLayout(self)

        # Total amount
        total_label = QLabel(f"Total Amount: Rs. {self.total:.2f}")
        total_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(total_label)

        # Amount received input
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Amount Received:"))
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0, 1000000)  # Allow large payments
        self.amount_edit.setValue(self.total)
        self.amount_edit.setSuffix(" Rs.")
        self.amount_edit.setDecimals(2)
        self.amount_edit.valueChanged.connect(self.update_payment_info)
        amount_layout.addWidget(self.amount_edit)
        layout.addLayout(amount_layout)

        # Payment info
        self.change_label = QLabel("Change: Rs. 0.00")
        self.change_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.change_label)

        self.balance_label = QLabel("Balance Due: Rs. 0.00")
        self.balance_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.balance_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.update_payment_info()

    def update_payment_info(self):
        amount = self.amount_edit.value()
        if amount >= self.total:
            change = amount - self.total
            self.change_label.setText(f"Change: Rs. {change:.2f}")
            self.balance_label.setText("Balance Due: Rs. 0.00")
        else:
            balance = self.total - amount
            self.change_label.setText("Change: Rs. 0.00")
            self.balance_label.setText(f"Balance Due: Rs. {balance:.2f}")

    def get_amount_received(self):
        return self.amount_edit.value()


class ReturnDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.return_items = []
        self.selected_sale = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Process Return")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Sale selection
        sale_group = QGroupBox("Select Sale Transaction")
        sale_layout = QVBoxLayout(sale_group)

        # Search sale
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Sale (ID, Customer, Date):"))
        self.sale_search = QLineEdit()
        self.sale_search.textChanged.connect(self.filter_sales)
        search_layout.addWidget(self.sale_search)
        sale_layout.addLayout(search_layout)

        # Sales table
        self.sales_table = QTableWidget()
        setup_professional_table(self.sales_table, ["ID", "Date", "Customer", "Total", "Status"], ['id', 'date', 'text', 'numeric', 'status'])
        self.sales_table.itemDoubleClicked.connect(self.select_sale)
        sale_layout.addWidget(self.sales_table)

        layout.addWidget(sale_group)

        # Return items
        items_group = QGroupBox("Items to Return")
        items_layout = QVBoxLayout(items_group)

        self.return_table = QTableWidget()
        setup_professional_table(self.return_table, ["Product", "Sold Qty", "Return Qty", "Unit Price", "Total"], ['text', 'numeric', 'numeric', 'numeric', 'numeric'])
        items_layout.addWidget(self.return_table)

        layout.addWidget(items_group)

        # Reason and total
        details_layout = QHBoxLayout()

        reason_group = QGroupBox("Return Details")
        reason_layout = QVBoxLayout(reason_group)
        reason_layout.addWidget(QLabel("Return Reason:"))
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("Enter reason for return")
        reason_layout.addWidget(self.reason_edit)
        details_layout.addWidget(reason_group)

        total_group = QGroupBox("Return Summary")
        total_layout = QVBoxLayout(total_group)
        self.return_total_label = QLabel("Return Total: Rs. 0.00")
        self.return_total_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        total_layout.addWidget(self.return_total_label)
        details_layout.addWidget(total_group)

        layout.addLayout(details_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        process_btn = QPushButton("Process Return")
        process_btn.clicked.connect(self.process_return)
        buttons_layout.addWidget(process_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        self.load_sales()

    def load_sales(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT st.id, st.date, c.name, st.total_amount, st.status
            FROM SalesTransactions st
            LEFT JOIN Customers c ON st.customer_id = c.id
            ORDER BY st.date DESC
        """)
        self.all_sales = cur.fetchall()
        conn.close()
        self.filter_sales()

    def filter_sales(self):
        search_text = self.sale_search.text().lower()
        filtered_sales = [sale for sale in self.all_sales if search_text in str(sale[0]).lower() or
                         search_text in (sale[2] or '').lower() or search_text in sale[1]]

        self.sales_table.setRowCount(len(filtered_sales))
        for r, sale in enumerate(filtered_sales):
            self.sales_table.setItem(r, 0, create_professional_table_item(sale[0], 'id'))
            self.sales_table.setItem(r, 1, create_professional_table_item(sale[1], 'date'))
            self.sales_table.setItem(r, 2, create_professional_table_item(sale[2] or "Walk-in", 'text'))
            self.sales_table.setItem(r, 3, create_professional_table_item(sale[3], 'numeric'))
            self.sales_table.setItem(r, 4, create_professional_table_item(sale[4], 'status'))

    def select_sale(self, item):
        row = item.row()
        sale_id = self.sales_table.item(row, 0).text()
        self.load_sale_items(sale_id)

    def load_sale_items(self, sale_id):
        self.selected_sale = sale_id
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, si.quantity, si.unit_price, si.total_price, si.id
            FROM SalesItems si
            JOIN Products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        items = cur.fetchall()
        conn.close()

        self.return_table.setRowCount(len(items))
        self.return_items = []
        for r, item in enumerate(items):
            name, qty, price, total, item_id = item
            self.return_table.setItem(r, 0, create_professional_table_item(name, 'text'))
            self.return_table.setItem(r, 1, create_professional_table_item(qty, 'numeric'))
            self.return_table.setItem(r, 2, create_professional_table_item(0, 'numeric'))  # Return qty
            self.return_table.setItem(r, 3, create_professional_table_item(price, 'numeric'))
            self.return_table.setItem(r, 4, create_professional_table_item(0.0, 'numeric'))

            self.return_items.append({
                'item_id': item_id,
                'product_name': name,
                'sold_qty': qty,
                'return_qty': 0,
                'unit_price': price,
                'total': 0.0
            })

        # Connect spin boxes for return quantities
        for r in range(len(items)):
            return_qty_spin = QSpinBox()
            return_qty_spin.setMaximum(self.return_items[r]['sold_qty'])
            return_qty_spin.valueChanged.connect(lambda value, row=r: self.update_return_qty(row, value))
            self.return_table.setCellWidget(r, 2, return_qty_spin)

    def update_return_qty(self, row, qty):
        if row < len(self.return_items):
            self.return_items[row]['return_qty'] = qty
            self.return_items[row]['total'] = qty * self.return_items[row]['unit_price']
            self.return_table.item(row, 4).setText(f"{self.return_items[row]['total']:.2f}")

            # Update total
            total = sum(item['total'] for item in self.return_items)
            self.return_total_label.setText(f"Return Total: Rs. {total:.2f}")

    def process_return(self):
        if not self.selected_sale:
            QMessageBox.warning(self, "Error", "Please select a sale transaction first.")
            return

        return_items = [item for item in self.return_items if item['return_qty'] > 0]
        if not return_items:
            QMessageBox.warning(self, "Error", "Please select items to return.")
            return

        reason = self.reason_edit.text().strip()
        if not reason:
            QMessageBox.warning(self, "Error", "Please enter a return reason.")
            return

        total_return = sum(item['total'] for item in return_items)

        # Confirm
        reply = QMessageBox.question(self, "Confirm Return",
                                   f"Process return of Rs. {total_return:.2f}?\n\nThis will:\n"
                                   f"- Add items back to inventory\n"
                                   f"- Credit customer account\n"
                                   f"- Generate return receipt",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self.db.get_connection()
            cur = conn.cursor()

            # Insert return record
            cur.execute("""
                INSERT INTO Returns (sale_id, customer_id, date, total_amount, reason)
                SELECT ?, customer_id, date('now'), ?, ? FROM SalesTransactions WHERE id = ?
            """, (self.selected_sale, total_return, reason, self.selected_sale))
            return_id = cur.lastrowid

            # Insert return items and update inventory
            for item in return_items:
                # Insert return item
                cur.execute("""
                    INSERT INTO ReturnItems (return_id, product_id, batch_id, quantity, unit_price)
                    SELECT ?, si.product_id, si.batch_id, ?, ?
                    FROM SalesItems si WHERE si.id = ?
                """, (return_id, item['return_qty'], item['unit_price'], item['item_id']))

                # Add back to inventory
                cur.execute("""
                    UPDATE ProductBatches
                    SET quantity = quantity + ?
                    WHERE id = (SELECT batch_id FROM SalesItems WHERE id = ?)
                """, (item['return_qty'], item['item_id']))

            # Update customer ledger (credit for return)
            cur.execute("SELECT customer_id FROM SalesTransactions WHERE id = ?", (self.selected_sale,))
            customer_id = cur.fetchone()[0]
            if customer_id:
                current_date = datetime.datetime.now().strftime('%Y-%m-%d')
                cur.execute("SELECT balance FROM CustomerLedger WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,))
                last_balance = cur.fetchone()
                last_balance = last_balance[0] if last_balance else 0.0
                new_balance = last_balance - total_return  # Credit reduces balance
                cur.execute("""
                    INSERT INTO CustomerLedger (customer_id, date, description, debit, credit, balance)
                    VALUES (?, ?, ?, 0, ?, ?)
                """, (customer_id, current_date, f"Return #{return_id} - {reason}", total_return, new_balance))

            conn.commit()
            QMessageBox.information(self, "Success", "Return processed successfully.")
            self.generate_return_receipt(return_id, return_items, total_return, reason)
            self.accept()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to process return: {str(e)}")
        finally:
            conn.close()

    def generate_return_receipt(self, return_id, items, total, reason):
        # Get customer name from return
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.name FROM Returns r
            JOIN SalesTransactions st ON r.sale_id = st.id
            JOIN Customers c ON st.customer_id = c.id
            WHERE r.id = ?
        """, (return_id,))
        customer_name = cur.fetchone()
        conn.close()
        if customer_name:
            customer_name = customer_name[0]
            customer_folder = f"customers/{customer_name.replace(' ', '_').replace('/', '_')}"
            refunds_folder = os.path.join(customer_folder, "refunds")
            os.makedirs(refunds_folder, exist_ok=True)
            filename = f"{refunds_folder}/return_receipt_{return_id}.pdf"
        else:
            filename = f"return_receipt_{return_id}.pdf"

        # Load Urdu font
        font_id = QFontDatabase.addApplicationFont("fonts/NotoNastaliqUrdu-VariableFont_wght.ttf")
        urdu_font_family = ""
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                urdu_font_family = families[0]
        else:
            urdu_font_family = "Arial"

        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}

        body {{
            font-family: Arial, sans-serif;
            font-size: 11pt;
            color: #000;
        }}

        .header {{
            text-align: center;
            margin: 0 auto;
        }}

        .header h1 {{
            margin: 0;
            font-size: 20pt;
        }}

        .header p {{
            margin: 4px 0;
            font-size: 10pt;
        }}

        .section {{
            margin-top: 15px;
            page-break-inside: avoid;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 6px;
            text-align: left;
        }}

        th {{
            background: #f2f2f2;
            text-align: center;
        }}

        .right {{
            text-align: right;
        }}

        .center {{
            text-align: center;
        }}

        .urdu {{
            font-family: "{urdu_font_family}";
            direction: rtl;
            text-align: right;
            font-size: 10.5pt;
            line-height: 1.7;
            margin-top: 8px;
        }}

        .footer {{
            text-align: center;
            font-size: 9pt;
            margin-top: 20px;
        }}
        </style>
        </head>

        <body>

        <!-- HEADER -->
        <table class="header">
        <tr>
        <td style="text-align: left; vertical-align: top; width: 20%;">
            <img src="Logo.png" alt="Logo" style="height: 60px; opacity: 0.2;">
        </td>
        <td style="text-align: center; width: 80%;">
            <h1>Eagle Traders</h1>
            <p>Danish Colony Nowshera Road Mardan</p>
            <p>Phone: +92 330 - 6500009 | Email: Eagletraders009@gmail.com</p>
        </td>
        </tr>
        </table>

        <!-- RECEIPT TITLE -->
        <table class="section">
        <tr>
        <td align="center"><strong style="font-size:14pt;">RETURN RECEIPT</strong></td>
        </tr>
        </table>

        <!-- DETAILS -->
        <div class="section">
        <p><strong>Return No:</strong> {return_id}</p>
        <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d')}</p>
        <p><strong>Reason:</strong> {reason}</p>
        </div>

        <!-- ITEMS -->
        <table class="section">
        <tr>
        <th>Product</th>
        <th class="center">Return Qty</th>
        <th class="right">Unit Price</th>
        <th class="right">Total</th>
        </tr>
        """

        for item in items:
            html += f"""
            <tr>
            <td>{item['product_name']}</td>
            <td class="center">{item['return_qty']}</td>
            <td class="right">Rs. {item['unit_price']:.2f}</td>
            <td class="right">Rs. {item['total']:.2f}</td>
            </tr>
            """

        html += f"""
        </table>

        <!-- TOTAL -->
        <div class="section" style="text-align: right; font-weight: bold; font-size: 14pt;">
        <p>Return Total: Rs. {total:.2f}</p>
        </div>

        <!-- TERMS -->
        <div class="section">
        <strong>Return Terms</strong><br>
        1. Items have been inspected and accepted for return.<br>
        2. Refund will be processed within 3-5 business days.<br>

        <div class="urdu">
        واپسی کی رسید: اوپر بیان کردہ سامان کی واپسی قبول کر لی گئی ہے۔
        </div>
        </div>

        <!-- SIGNATURE -->
        <table class="section">
        <tr>
        <td width="50%">Processed By<br><br>____________________</td>
        <td width="50%" align="right">Customer Signature<br><br>____________________</td>
        </tr>
        </table>

        <!-- FOOTER -->
        <div class="footer">
        Thank you for your business!
        </div>

        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: -1;">
            <img src="Logo.png" alt="Logo" style="height: 500px; opacity: 0.3;">
        </div>

        </body>
        </html>
        """

        # Create PDF
        document = QTextDocument()
        document.setHtml(html)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        document.print(printer)
        QDesktopServices.openUrl(QUrl.fromLocalFile(filename))
