from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QTabWidget, QComboBox, QPushButton, QGroupBox, QHeaderView, QDateEdit,
    QSizePolicy, QScrollArea, QMessageBox, QInputDialog, QLineEdit, QCompleter, QDialog, QFormLayout, QDoubleSpinBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QTextDocument, QFontDatabase, QPageSize, QPageLayout, QColor
from PyQt6.QtCore import QMarginsF
from PyQt6.QtPrintSupport import QPrinter
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item
import os
import sys
import base64


class AccountsReports(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        # Apply custom styles for tabs, group boxes, and calendar
        self.setStyleSheet("""
            QTabWidget::pane { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; }
            QTabBar::tab { background: rgba(0, 0, 0, 0.2); color: #cccccc; padding: 10px 20px; border: 1px solid rgba(255, 255, 255, 0.2); border-bottom: none; border-radius: 6px 6px 0 0; }
            QTabBar::tab:selected { background: rgba(0, 0, 0, 0.4); color: #ffffff; }
            QTabBar::tab:hover { background: rgba(0, 0, 0, 0.3); color: #ffffff; }
            QGroupBox { border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; background: rgba(0, 0, 0, 0.2); }
            QGroupBox::title { color: #ffffff; font-weight: bold; padding: 5px 10px; }
            QDateEdit { background: rgba(0, 0, 0, 0.3); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px; padding: 5px; }
            QDateEdit::drop-down { background: rgba(0, 0, 0, 0.3); border: none; }
            QDateEdit::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #ffffff; margin-top: 2px; }
            QCalendarWidget { background: rgba(0, 0, 0, 0.9); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; }
            QCalendarWidget QTableView { background: rgba(0, 0, 0, 0.8); color: #ffffff; gridline-color: rgba(255, 255, 255, 0.2); }
            QCalendarWidget QHeaderView::section { background: rgba(0, 0, 0, 0.6); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); }
            QCalendarWidget QAbstractItemView:enabled { background: rgba(0, 0, 0, 0.8); color: #ffffff; selection-background-color: rgba(255, 255, 255, 0.2); selection-color: #ffffff; }
            QCalendarWidget QWidget { background: rgba(0, 0, 0, 0.9); color: #ffffff; }
            QCalendarWidget QToolButton { background: rgba(0, 0, 0, 0.6); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px; }
            QCalendarWidget QToolButton:hover { background: rgba(0, 0, 0, 0.7); }
        """)

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
        title = QLabel("Accounts & Financial Reports")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px; color: #ffffff;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

        self.combined_ledger_tab()
        self.profit_loss_tab()
        self.sales_records_tab()
        self.customer_history_tab()

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def combined_ledger_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Date filters
        filter_group = QGroupBox("Date Range & Filters")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.addWidget(QLabel("From:"))
        self.ledger_from = QDateEdit()
        self.ledger_from.setCalendarPopup(True)
        self.ledger_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.ledger_from)
        filter_layout.addWidget(QLabel("To:"))
        self.ledger_to = QDateEdit()
        self.ledger_to.setCalendarPopup(True)
        self.ledger_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.ledger_to)

        # Customer filter
        filter_layout.addWidget(QLabel("Customer:"))
        self.ledger_customer_combo = QComboBox()
        self.ledger_customer_combo.setEditable(True)
        self.ledger_customer_combo.addItem("All Customers", None)
        self.load_customers_for_ledger()
        filter_layout.addWidget(self.ledger_customer_combo)

        btn = QPushButton("Refresh")
        btn.clicked.connect(self.load_combined_ledger)
        filter_layout.addWidget(btn)
        layout.addWidget(filter_group)

        # Search functionality
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search by Customer/Description:"))
        self.ledger_search = QLineEdit()
        self.ledger_search.setPlaceholderText("Enter customer name or description...")
        self.ledger_search.textChanged.connect(self.filter_combined_ledger)
        search_layout.addWidget(self.ledger_search)
        layout.addLayout(search_layout)

        # Combined ledger table
        self.combined_table = QTableWidget()
        setup_professional_table(self.combined_table, ["Date", "Type", "Customer/Description", "Debit", "Credit", "Balance", "Actions"], ['date', 'text', 'text', 'numeric', 'numeric', 'numeric', 'action'])
        self.combined_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.combined_table)

        # Manual ledger entry and print buttons
        manual_layout = QHBoxLayout()
        manual_layout.addStretch()
        manual_btn = QPushButton("Add Manual Ledger Entry")
        manual_btn.clicked.connect(self.add_manual_ledger_entry)
        manual_layout.addWidget(manual_btn)

        print_btn = QPushButton("Print Customer Ledger")
        print_btn.clicked.connect(self.print_customer_ledger)
        manual_layout.addWidget(print_btn)

        layout.addLayout(manual_layout)

        self.tabs.addTab(tab, "Combined Ledger")

        # Load initial data
        self.load_combined_ledger()
        self.all_ledger_rows = []  # Store all rows for filtering

    def on_tab_changed(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "Combined Ledger":
            self.load_combined_ledger()
        elif tab_text == "Sales Records":
            self.load_sales_records()
        elif tab_text == "Profit & Loss":
            self.load_profit_loss()
        elif tab_text == "Customer History":
            # No load needed, as it's on demand
            pass

    def record_payment_for_customer(self, customer_id, current_balance):
        """Record payment for a specific customer"""
        # Get customer name
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM Customers WHERE id = ?", (customer_id,))
        customer = cur.fetchone()
        conn.close()

        if not customer:
            QMessageBox.warning(self, "Error", "Customer not found.")
            return

        customer_name = customer[0]

        # Get payment amount
        amount, ok = QInputDialog.getDouble(self, f"Record Payment - {customer_name}",
                                          f"Current Balance: Rs. {current_balance:.2f}\nEnter payment amount:",
                                          0, 0, current_balance, 2)
        if not ok or amount <= 0:
            return

        # Get description
        description, ok = QInputDialog.getText(self, "Record Payment", "Enter payment description:")
        if not ok or not description.strip():
            description = "Payment received"

        # Record payment
        conn = self.db.get_connection()
        cur = conn.cursor()

        # Insert payment entry (credit reduces balance)
        new_balance = current_balance - amount
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        cur.execute("""
            INSERT INTO CustomerLedger (customer_id, date, description, debit, credit, balance)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (customer_id, current_date, description, amount, new_balance))

        conn.commit()
        conn.close()

        # Generate payment receipt
        receipt_id = cur.lastrowid  # Get the ID of the inserted payment entry
        self.generate_payment_receipt(receipt_id, customer_name, current_balance, amount, new_balance, description)

        QMessageBox.information(self, "Success", f"Payment of Rs. {amount:.2f} recorded for {customer_name}.")
        self.load_combined_ledger()  # Refresh the ledger

    def add_manual_ledger_entry(self):
        """Add manual ledger entry for customers with existing balances"""
        dialog = ManualLedgerDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_combined_ledger()  # Refresh after adding

    def print_customer_ledger(self):
        """Print ledger for selected customer"""
        customer_id = self.ledger_customer_combo.currentData()
        customer_name = self.ledger_customer_combo.currentText()

        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a specific customer to print ledger.")
            return

        self.generate_customer_ledger_pdf(customer_id, customer_name)

    def profit_loss_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        btn = QPushButton("Refresh Report")
        btn.clicked.connect(self.load_profit_loss)
        refresh_layout.addWidget(btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

        # Reports table
        self.reports_table = QTableWidget()
        setup_professional_table(self.reports_table, ["Category", "Sales Revenue", "Cost of Goods", "Profit"], ['text', 'numeric', 'numeric', 'numeric'])
        self.reports_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.reports_table)

        # Total profit
        self.total_profit = QLabel("Total Profit: Rs. 0.00")
        self.total_profit.setStyleSheet("font-size: 14pt; font-weight: bold; color: #28a745; margin-top: 10px;")
        layout.addWidget(self.total_profit)

        self.tabs.addTab(tab, "Profit & Loss")

        # Load initial data
        self.load_profit_loss()

    def sales_records_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Date filters
        filter_group = QGroupBox("Date Range")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.addWidget(QLabel("From:"))
        self.sales_from = QDateEdit()
        self.sales_from.setCalendarPopup(True)
        self.sales_from.setDate(QDate.currentDate().addYears(-1))
        filter_layout.addWidget(self.sales_from)
        filter_layout.addWidget(QLabel("To:"))
        self.sales_to = QDateEdit()
        self.sales_to.setCalendarPopup(True)
        self.sales_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.sales_to)
        btn = QPushButton("Refresh")
        btn.clicked.connect(self.load_sales_records)
        filter_layout.addWidget(btn)
        layout.addWidget(filter_group)

        # Sales records table
        self.sales_table = QTableWidget()
        setup_professional_table(self.sales_table, ["ID", "Date", "Buyer", "Contact", "Total", "Status", "Invoice"], ['id', 'date', 'text', 'text', 'numeric', 'status', 'action'])
        self.sales_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.sales_table)

        self.tabs.addTab(tab, "Sales Records")

    def customer_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Customer selection
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Select Customer:"))
        self.history_customer_combo = QComboBox()
        self.history_customer_combo.setEditable(True)
        self.load_customers_for_history()
        customer_layout.addWidget(self.history_customer_combo)

        btn = QPushButton("Load History")
        btn.clicked.connect(self.load_customer_history)
        customer_layout.addWidget(btn)
        layout.addLayout(customer_layout)

        # History table
        self.history_table = QTableWidget()
        setup_professional_table(self.history_table, ["Date", "Description", "Debit", "Credit", "Balance"], ['date', 'text', 'numeric', 'numeric', 'numeric'])
        self.history_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.history_table)

        # Print button
        print_layout = QHBoxLayout()
        print_layout.addStretch()
        print_btn = QPushButton("Print Customer History")
        print_btn.clicked.connect(self.print_customer_history)
        print_layout.addWidget(print_btn)
        layout.addLayout(print_layout)

        self.tabs.addTab(tab, "Customer History")


    # ================= HELPERS =================
    def date_edit(self, offset):
        d = QDateEdit()
        d.setCalendarPopup(True)
        d.setDate(QDate.currentDate().addMonths(offset))
        return d

    # ================= DATABASE =================
    def load_customers(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Customers ORDER BY name")
        self.all_customers = cur.fetchall()
        conn.close()
        self.customer_combo.clear()
        customer_names = [name for cid, name in self.all_customers]
        self.customer_combo.addItems(customer_names)
        # Set up completer for better search
        completer = QCompleter(customer_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.customer_combo.setCompleter(completer)

    def load_customers_for_ledger(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Customers ORDER BY name")
        customers = cur.fetchall()
        conn.close()
        for cid, name in customers:
            self.ledger_customer_combo.addItem(name, cid)
        # Set up completer for better search
        customer_names = [name for cid, name in customers]
        completer = QCompleter(customer_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.ledger_customer_combo.setCompleter(completer)

    def load_customers_for_history(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Customers ORDER BY name")
        customers = cur.fetchall()
        conn.close()
        self.history_customer_combo.clear()
        self.history_customer_combo.addItem("Select Customer", None)
        for cid, name in customers:
            self.history_customer_combo.addItem(name, cid)
        # Set up completer for better search
        customer_names = [name for cid, name in customers]
        completer = QCompleter(customer_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.history_customer_combo.setCompleter(completer)

    def load_customer_history(self):
        customer_id = self.history_customer_combo.currentData()
        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, description, debit, credit, balance
            FROM CustomerLedger WHERE customer_id=? ORDER BY date
        """, (customer_id,))
        rows = cur.fetchall()
        conn.close()
        self.history_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.history_table.setItem(r, 0, create_professional_table_item(row[0], 'date'))
            self.history_table.setItem(r, 1, create_professional_table_item(row[1], 'text'))
            self.history_table.setItem(r, 2, create_professional_table_item(row[2], 'numeric'))
            self.history_table.setItem(r, 3, create_professional_table_item(row[3], 'numeric'))
            self.history_table.setItem(r, 4, create_professional_table_item(row[4], 'numeric'))

    def print_customer_history(self):
        customer_id = self.history_customer_combo.currentData()
        customer_name = self.history_customer_combo.currentText()
        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return
        self.generate_customer_ledger_pdf(customer_id, customer_name)

    def load_ledger(self):
        customer_name = self.customer_combo.currentText().strip()
        if not customer_name:
            QMessageBox.warning(self, "Error", "Please enter a customer name.")
            return

        # Check if customer exists
        cid = None
        for id_val, name in self.all_customers:
            if name == customer_name:
                cid = id_val
                break

        # If not found, add new customer
        if cid is None:
            reply = QMessageBox.question(self, "Add Customer",
                                       f"Customer '{customer_name}' not found. Add as new customer?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                conn = self.db.get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO Customers (name) VALUES (?)", (customer_name,))
                cid = cur.lastrowid
                conn.commit()
                conn.close()
                # Reload customers
                self.load_customers()
                # Set the new customer as current
                self.customer_combo.setCurrentText(customer_name)
            else:
                return

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, description, debit, credit, balance
            FROM CustomerLedger WHERE customer_id=? ORDER BY date
        """, (cid,))
        self.all_ledger_rows = cur.fetchall()
        conn.close()
        self.filter_ledger()

    def filter_ledger(self):
        search_text = self.search_edit.text().lower()
        if not hasattr(self, 'all_ledger_rows'):
            return

        # Filter rows based on search
        if search_text:
            filtered_rows = [row for row in self.all_ledger_rows if search_text in str(row[1]).lower()]  # search in description
        else:
            filtered_rows = self.all_ledger_rows

        self.ledger_table.setRowCount(len(filtered_rows))
        total_debit = 0.0
        total_credit = 0.0
        for r, row in enumerate(filtered_rows):
            self.ledger_table.setItem(r, 0, create_professional_table_item(row[0], 'date'))
            self.ledger_table.setItem(r, 1, create_professional_table_item(row[1], 'text'))
            self.ledger_table.setItem(r, 2, create_professional_table_item(row[2], 'numeric'))
            self.ledger_table.setItem(r, 3, create_professional_table_item(row[3], 'numeric'))
            self.ledger_table.setItem(r, 4, create_professional_table_item(row[4], 'numeric'))
            total_debit += row[2] or 0
            total_credit += row[3] or 0

        # Update summary labels
        remaining = total_debit - total_credit
        self.total_debit_label.setText(f"Total Amount: Rs. {total_debit:.2f}")
        self.total_credit_label.setText(f"Amount Paid: Rs. {total_credit:.2f}")
        self.remaining_label.setText(f"Amount Remaining: Rs. {remaining:.2f}")

    def record_payment(self):
        customer_name = self.customer_combo.currentText().strip()
        if not customer_name:
            QMessageBox.warning(self, "Error", "Please enter a customer name.")
            return

        # Find customer ID
        cid = None
        for id_val, name in self.all_customers:
            if name == customer_name:
                cid = id_val
                break

        if cid is None:
            QMessageBox.warning(self, "Error", "Customer not found. Please load the ledger first to add the customer.")
            return

        # Get payment amount
        amount, ok = QInputDialog.getDouble(self, "Record Payment", "Enter payment amount:", 0, 0, 1000000, 2)
        if not ok or amount <= 0:
            return

        # Get description
        description, ok = QInputDialog.getText(self, "Record Payment", "Enter payment description:")
        if not ok or not description.strip():
            description = "Payment received"

        # Get current balance
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM CustomerLedger WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (cid,))
        last_balance = cur.fetchone()
        last_balance = last_balance[0] if last_balance else 0.0

        # Insert payment entry (credit reduces balance)
        new_balance = last_balance - amount
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        cur.execute("""
            INSERT INTO CustomerLedger (customer_id, date, description, debit, credit, balance)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (cid, current_date, description, amount, new_balance))

        conn.commit()
        conn.close()

        # Generate payment receipt
        customer_name = self.customer_combo.currentText()
        receipt_id = cur.lastrowid  # Get the ID of the inserted payment entry
        self.generate_payment_receipt(receipt_id, customer_name, last_balance, amount, new_balance, description)

        QMessageBox.information(self, "Success", "Payment recorded successfully.")
        self.load_ledger()  # Refresh the ledger

    def load_profit_loss(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.name, SUM(si.total_price)
            FROM SalesItems si
            JOIN Products p ON si.product_id=p.id
            JOIN Categories c ON p.category_id=c.id
            GROUP BY c.id
        """)
        sales = dict(cur.fetchall())
        cur.execute("""
            SELECT c.name, SUM(pb.cost_price*pb.quantity)
            FROM ProductBatches pb
            JOIN Products p ON pb.product_id=p.id
            JOIN Categories c ON p.category_id=c.id
            GROUP BY c.id
        """)
        costs = dict(cur.fetchall())

        # Calculate total expenses
        cur.execute("SELECT SUM(amount) FROM PayrollTransactions")
        payroll_expenses = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(amount) FROM Expenses")
        other_expenses = cur.fetchone()[0] or 0
        total_expenses = payroll_expenses + other_expenses

        conn.close()
        cats = set(sales) | set(costs)
        self.reports_table.setRowCount(len(cats))
        gross_profit = 0
        for r, c in enumerate(cats):
            s = sales.get(c, 0) or 0
            k = costs.get(c, 0) or 0
            profit = s - k
            gross_profit += profit
            self.reports_table.setItem(r, 0, create_professional_table_item(c, 'text'))
            self.reports_table.setItem(r, 1, create_professional_table_item(s, 'numeric'))
            self.reports_table.setItem(r, 2, create_professional_table_item(k, 'numeric'))
            self.reports_table.setItem(r, 3, create_professional_table_item(profit, 'numeric'))

        net_profit = gross_profit - total_expenses
        self.total_profit.setText(f"Gross Profit: Rs. {gross_profit:,.2f}\nTotal Expenses: Rs. {total_expenses:,.2f}\nNet Profit: Rs. {net_profit:,.2f}")


    def load_combined_ledger(self):
        f = self.ledger_from.date().toString("yyyy-MM-dd")
        t = self.ledger_to.date().toString("yyyy-MM-dd")
        customer_filter = self.ledger_customer_combo.currentData()

        conn = self.db.get_connection()
        cur = conn.cursor()

        # Get customer ledgers
        customer_query = """
            SELECT cl.date, 'Customer' as type, c.name || ' - ' || cl.description as description,
                    cl.debit, cl.credit, cl.balance, c.id as customer_id
            FROM CustomerLedger cl
            JOIN Customers c ON cl.customer_id = c.id
            WHERE cl.date BETWEEN ? AND ?
        """
        params = [f, t]
        if customer_filter:
            customer_query += " AND cl.customer_id = ?"
            params.append(customer_filter)

        cur.execute(customer_query + " ORDER BY cl.date", params)
        customer_rows = cur.fetchall()

        # Get general ledger
        general_query = """
            SELECT gl.date, CASE WHEN gl.type = 'income' THEN 'Income' ELSE 'Expense' END as type,
                    gl.description, CASE WHEN gl.type = 'income' THEN 0 ELSE gl.amount END as debit,
                    CASE WHEN gl.type = 'income' THEN gl.amount ELSE 0 END as credit, gl.balance, NULL as customer_id
            FROM GeneralLedger gl
            WHERE gl.date BETWEEN ? AND ?
        """
        cur.execute(general_query + " ORDER BY gl.date", [f, t])
        general_rows = cur.fetchall()

        conn.close()

        # Combine and sort by date (most recent first)
        all_rows = customer_rows + general_rows
        all_rows.sort(key=lambda x: x[0], reverse=True)  # Sort by date descending

        # Store all rows for filtering
        self.all_ledger_rows = all_rows

        # Display all rows initially
        self.display_ledger_rows(all_rows)

    def display_ledger_rows(self, rows):
        """Display the given rows in the table"""
        self.combined_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            date, trans_type, desc, debit, credit, balance, customer_id = row

            # Highlight debtors (customers with positive balance) - RED ALERT
            is_debtor = customer_id is not None and balance > 0

            self.combined_table.setItem(r, 0, create_professional_table_item(date, 'date'))
            self.combined_table.setItem(r, 1, create_professional_table_item(trans_type, 'text'))
            self.combined_table.setItem(r, 2, create_professional_table_item(desc, 'text'))
            self.combined_table.setItem(r, 3, create_professional_table_item(debit, 'numeric'))
            self.combined_table.setItem(r, 4, create_professional_table_item(credit, 'numeric'))
            self.combined_table.setItem(r, 5, create_professional_table_item(balance, 'numeric'))

            if is_debtor:
                # Red alert background for debtors
                red_alert = QColor(255, 100, 100)  # Bright red
                for col in range(6):
                    item = self.combined_table.item(r, col)
                    if item:
                        item.setBackground(red_alert)
                        item.setForeground(QColor(255, 255, 255))  # White text for contrast

                # Add action button for payment
                action_btn = QPushButton("Record Payment")
                action_btn.clicked.connect(lambda _, cid=customer_id, bal=balance: self.record_payment_for_customer(cid, bal))
                self.combined_table.setCellWidget(r, 6, action_btn)
            else:
                # Empty action cell for non-debtors
                empty_label = QLabel("")
                self.combined_table.setCellWidget(r, 6, empty_label)

    def filter_combined_ledger(self):
        """Filter ledger rows based on search text"""
        search_text = self.ledger_search.text().lower().strip()
        if not search_text:
            # Show all rows if no search text
            self.display_ledger_rows(self.all_ledger_rows)
            return

        # Filter rows where customer name or description contains search text
        filtered_rows = []
        for row in self.all_ledger_rows:
            date, trans_type, desc, debit, credit, balance, customer_id = row
            # Check if search text is in description (which includes customer name for customer transactions)
            if search_text in desc.lower():
                filtered_rows.append(row)

        self.display_ledger_rows(filtered_rows)

    def load_sales_records(self):
        f = self.sales_from.date().toString("yyyy-MM-dd")
        t = self.sales_to.date().toString("yyyy-MM-dd")
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, date, buyer_name, buyer_contact, total_amount, status
            FROM SalesTransactions WHERE date BETWEEN ? AND ? ORDER BY date DESC
        """, (f, t))
        rows = cur.fetchall()
        conn.close()
        self.sales_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.sales_table.setItem(r, 0, create_professional_table_item(row[0], 'id'))
            self.sales_table.setItem(r, 1, create_professional_table_item(row[1], 'date'))
            self.sales_table.setItem(r, 2, create_professional_table_item(row[2], 'text'))
            self.sales_table.setItem(r, 3, create_professional_table_item(row[3], 'text'))
            self.sales_table.setItem(r, 4, create_professional_table_item(row[4], 'numeric'))
            self.sales_table.setItem(r, 5, create_professional_table_item(row[5], 'status', {'paid': 'green', 'pending': 'yellow', 'cancelled': 'red'}))
            btn = QPushButton("View")
            btn.clicked.connect(lambda _, sid=row[0]: self.view_invoice(sid))
            self.sales_table.setCellWidget(r, 6, btn)

    # ================= INVOICE PDF =================
    def view_invoice(self, sale_id):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date,buyer_name,buyer_contact,total_amount FROM SalesTransactions WHERE id=?", (sale_id,))
        sale = cur.fetchone()
        cur.execute("""
            SELECT p.name, si.quantity, si.unit_price, si.total_price
            FROM SalesItems si JOIN Products p ON si.product_id=p.id
            WHERE si.sale_id=?
        """, (sale_id,))
        items = cur.fetchall()
        conn.close()
        if sale:
            self.generate_bill(sale_id, items, sale[3], sale[0], sale[1], sale[2])

    def generate_bill(self, sale_id, items, total, sale_date, buyer_name, buyer_contact):
        file = f"invoice_{sale_id}.pdf"

        # Load Noto Nastaliq Urdu font
        if getattr(sys, 'frozen', False):
            font_path = os.path.join(sys._MEIPASS, 'fonts', 'NotoNastaliqUrdu-VariableFont_wght.ttf')
        else:
            font_path = "fonts/NotoNastaliqUrdu-VariableFont_wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

        # Load logo image
        logo_img_tag = ""
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, 'header.png')
        else:
            logo_path = 'header.png'

        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                logo_img_tag = f'<img src="data:image/png;base64,{logo_data}" alt="Eagle Traders Logo" style="height: 60px;">'

        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .invoice {{
                    font-size: 20px;
                    font-weight: bold;
                }}
                .details {{
                    margin-bottom: 20px;
                }}
                .details p {{
                    margin: 5px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f0f0f0;
                    font-weight: bold;
                }}
                .qty, .unit, .total {{
                    text-align: right;
                }}
                .total-row {{
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                }}
                .urdu {{
                    font-family: '{font_family}', Arial;
                    direction: rtl;
                    text-align: right;
                    font-size: 14px;
                    margin-top: 20px;
                }}
                .signature {{
                    margin-top: 40px;
                    text-align: right;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 20%; text-align: left; vertical-align: top;">
                            {logo_img_tag}
                        </td>
                        <td style="width: 80%; text-align: center;">
                            <div class="title">Eagle Traders</div>
                            <p>Danish Colony Nowshera Road Mardan</p>
                            <p>Phone: +92 330 - 6500009 | Email: Eagletraders009@gmail.com</p>
                            <div class="invoice">INVOICE</div>
                        </td>
                    </tr>
                </table>
            </div>
            <div class="details">
                <p><strong>Invoice #:</strong> {sale_id}</p>
                <p><strong>Date:</strong> {sale_date}</p>
                <p><strong>Buyer:</strong> {buyer_name}</p>
                <p><strong>Contact:</strong> {buyer_contact}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Product</th>
                        <th class="qty">Qty</th>
                        <th class="unit">Unit</th>
                        <th class="total">Total</th>
                    </tr>
                </thead>
                <tbody>
        """

        for i, it in enumerate(items, 1):
            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{it[0]}</td>
                        <td class="qty">{it[1]}</td>
                        <td class="unit">{it[2]:.2f}</td>
                        <td class="total">{it[3]:.2f}</td>
                    </tr>
            """

        html += f"""
                </tbody>
            </table>
            <div class="total-row">
                <p><strong>Total: Rs. {total:.2f}</strong></p>
            </div>
            <div class="footer">
                <p>Thank you for your business.</p>
                <div class="urdu">
                    اعلانِ دستبرداری: خریدا گیا سامان خریداری کے وقت چیک کر لیں۔
                    <br><br>
                    خریدی گئی چیزیں میعاد ختم ہونے سے 30 دن پہلے یا جلد واپس کی جا سکتی ہیں۔
                </div>
                <div class="signature">
                    <p>________________________</p>
                    <p>Authorized Signature</p>
                </div>
            </div>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1;">
                <img src="data:image/png;base64,{logo_data}" alt="Logo" style="height: 500px; opacity: 0.1;">
            </div>
        </body>
        </html>
        """

        # Create QTextDocument
        doc = QTextDocument()
        doc.setHtml(html)

        # Set up printer for PDF
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file)

        # Set A4 page size
        page_size = QPageSize(QPageSize.PageSizeId.A4)
        layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, QMarginsF(25.4, 25.4, 25.4, 25.4))  # 1 inch margins
        printer.setPageLayout(layout)

        # Print document to PDF
        doc.print(printer)

        # Open the PDF
        os.startfile(file)

    def generate_payment_receipt(self, receipt_id, customer_name, previous_balance, amount_paid, remaining_balance, description):
        filename = f"payment_receipt_{receipt_id}.pdf"

        # Load Urdu font
        if getattr(sys, 'frozen', False):
            font_path = os.path.join(sys._MEIPASS, 'fonts', 'NotoNastaliqUrdu-VariableFont_wght.ttf')
        else:
            font_path = "fonts/NotoNastaliqUrdu-VariableFont_wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        urdu_font_family = ""
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                urdu_font_family = families[0]
        else:
            urdu_font_family = "Arial"

        # Load logo image
        logo_img_tag = ""
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, 'header.png')
        else:
            logo_path = 'header.png'

        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                logo_img_tag = f'<img src="data:image/png;base64,{logo_data}" alt="Logo" style="height: 60px; opacity: 0.2;">'

        # Create HTML content
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

        .details {{
            margin-bottom: 20px;
        }}

        .details p {{
            margin: 5px 0;
        }}

        .amounts {{
            margin-top: 20px;
        }}

        .amounts table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .amounts th, .amounts td {{
            border: 1px solid #000;
            padding: 8px;
            text-align: left;
        }}

        .amounts th {{
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
            {logo_img_tag}
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
        <td align="center"><strong style="font-size:14pt;">PAYMENT RECEIPT</strong></td>
        </tr>
        </table>

        <!-- DETAILS -->
        <div class="section details">
        <p><strong>Receipt No:</strong> {receipt_id}</p>
        <p><strong>Date:</strong> {QDate.currentDate().toString("yyyy-MM-dd")}</p>
        <p><strong>Customer:</strong> {customer_name}</p>
        <p><strong>Description:</strong> {description}</p>
        </div>

        <!-- AMOUNTS -->
        <div class="section amounts">
        <table>
        <tr>
        <th>Description</th>
        <th class="right">Amount</th>
        </tr>
        <tr>
        <td>Previous Outstanding Balance</td>
        <td class="right">Rs. {previous_balance:.2f}</td>
        </tr>
        <tr>
        <td>Amount Paid</td>
        <td class="right">Rs. {amount_paid:.2f}</td>
        </tr>
        <tr>
        <td><strong>Remaining Balance</strong></td>
        <td class="right"><strong>Rs. {remaining_balance:.2f}</strong></td>
        </tr>
        </table>
        </div>

        <!-- TERMS -->
        <div class="section">
        <strong>Payment Terms</strong><br>
        1. Payment received in full satisfaction of the amount stated.<br>
        2. Any discrepancies must be reported within 7 days.<br>

        <div class="urdu">
        ادائیگی کی رسید: اوپر بیان کردہ رقم کی مکمل ادائیگی ہو چکی ہے۔
        </div>
        </div>

        <!-- SIGNATURE -->
        <table class="section">
        <tr>
        <td width="50%">Received By<br><br>____________________</td>
        <td width="50%" align="right">Customer Signature<br><br>____________________</td>
        </tr>
        </table>

        <!-- FOOTER -->
        <div class="footer">
        Thank you for your payment!
        </div>

        </body>
        </html>
        """

        # Create QTextDocument and print to PDF
        document = QTextDocument()
        document.setHtml(html)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        document.print(printer)

        # Open the PDF
        os.startfile(filename)

    def generate_customer_ledger_pdf(self, customer_id, customer_name):
        """Generate PDF ledger for a specific customer"""
        filename = f"customer_ledger_{customer_id}.pdf"

        # Load Urdu font
        if getattr(sys, 'frozen', False):
            font_path = os.path.join(sys._MEIPASS, 'fonts', 'NotoNastaliqUrdu-VariableFont_wght.ttf')
        else:
            font_path = "fonts/NotoNastaliqUrdu-VariableFont_wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        urdu_font_family = ""
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                urdu_font_family = families[0]
        else:
            urdu_font_family = "Arial"

        # Load logo image
        logo_img_tag = ""
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, 'header.png')
        else:
            logo_path = 'header.png'

        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                logo_img_tag = f'<img src="data:image/png;base64,{logo_data}" alt="Logo" style="height: 60px; opacity: 0.2;">'

        # Get customer ledger data
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, description, debit, credit, balance
            FROM CustomerLedger
            WHERE customer_id = ?
            ORDER BY date
        """, (customer_id,))
        ledger_entries = cur.fetchall()
        conn.close()

        # Calculate totals
        total_debit = sum(entry[2] or 0 for entry in ledger_entries)
        total_credit = sum(entry[3] or 0 for entry in ledger_entries)
        current_balance = ledger_entries[-1][4] if ledger_entries else 0.0

        # Opening balance (balance of first entry minus debit or plus credit, but since ordered, first balance is after first transaction)
        opening_balance = 0.0
        if ledger_entries:
            first_entry = ledger_entries[0]
            if first_entry[2]:  # debit
                opening_balance = first_entry[4] - first_entry[2]
            elif first_entry[3]:  # credit
                opening_balance = first_entry[4] + first_entry[3]

        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}

        body {{
            font-family: Arial, sans-serif;
            font-size: 10pt;
            color: #000;
            line-height: 1.4;
        }}

        .header {{
            text-align: center;
            margin: 0 auto;
            margin-bottom: 20px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 18pt;
        }}

        .header p {{
            margin: 2px 0;
            font-size: 9pt;
        }}

        .title {{
            text-align: center;
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 15px;
        }}

        .customer-info {{
            margin-bottom: 15px;
        }}

        .customer-info p {{
            margin: 3px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
            margin-bottom: 15px;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 4px;
            text-align: left;
        }}

        th {{
            background: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }}

        .numeric {{
            text-align: right;
        }}

        .total-row {{
            font-weight: bold;
            background: #e8e8e8;
        }}

        .summary {{
            margin-top: 15px;
            font-size: 10pt;
        }}

        .summary p {{
            margin: 5px 0;
        }}

        .urdu {{
            font-family: "{urdu_font_family}";
            direction: rtl;
            text-align: right;
            font-size: 9pt;
            line-height: 1.6;
            margin-top: 10px;
        }}

        .footer {{
            text-align: center;
            font-size: 8pt;
            margin-top: 20px;
        }}
        </style>
        </head>

        <body>

        <!-- HEADER -->
        <table class="header">
        <tr>
        <td style="text-align: left; vertical-align: top; width: 20%;">
            {logo_img_tag}
        </td>
        <td style="text-align: center; width: 80%;">
            <h1>Eagle Traders Wholesale</h1>
            <p>Danish Colony Nowshera Road Mardan</p>
            <p>Phone: +92 330 - 6500009 | Email: Eagletraders009@gmail.com</p>
        </td>
        </tr>
        </table>

        <!-- TITLE -->
        <div class="title">CUSTOMER LEDGER STATEMENT</div>

        <!-- CUSTOMER INFO -->
        <div class="customer-info">
        <p><strong>Customer:</strong> {customer_name}</p>
        <p><strong>Statement Date:</strong> {QDate.currentDate().toString("yyyy-MM-dd")}</p>
        <p><strong>Period:</strong> All Transactions</p>
        <p><strong>Opening Balance:</strong> Rs. {opening_balance:.2f}</p>
        </div>

        <!-- LEDGER TABLE -->
        <table>
        <thead>
            <tr>
                <th style="width: 15%;">Date</th>
                <th style="width: 45%;">Description</th>
                <th style="width: 15%;" class="numeric">Debit</th>
                <th style="width: 15%;" class="numeric">Credit</th>
                <th style="width: 15%;" class="numeric">Balance</th>
            </tr>
        </thead>
        <tbody>
        <!-- Opening Balance Row -->
        <tr>
            <td colspan="4"><strong>Opening Balance</strong></td>
            <td class="numeric"><strong>{opening_balance:.2f}</strong></td>
        </tr>
        """

        current_month = None
        for entry in ledger_entries:
            date, desc, debit, credit, balance = entry
            entry_date = QDate.fromString(date, "yyyy-MM-dd")
            month_year = entry_date.toString("MMMM yyyy")
            if month_year != current_month:
                current_month = month_year
                html += f"""
            <tr>
                <td colspan="5" style="background-color: #f0f0f0; font-weight: bold; text-align: center;">{month_year}</td>
            </tr>
            """
            html += f"""
            <tr>
                <td>{date}</td>
                <td>{desc}</td>
                <td class="numeric">{f"{debit:.2f}" if debit else ''}</td>
                <td class="numeric">{f"{credit:.2f}" if credit else ''}</td>
                <td class="numeric">{balance:.2f}</td>
            </tr>
            """

        html += f"""
        </tbody>
        </table>

        <!-- SUMMARY -->
        <div class="summary">
        <p><strong>Total Debit:</strong> Rs. {total_debit:.2f}</p>
        <p><strong>Total Credit:</strong> Rs. {total_credit:.2f}</p>
        <p><strong>Current Balance:</strong> Rs. {current_balance:.2f}</p>
        </div>

        <!-- URDU TEXT -->
        <div class="urdu">
        کسٹمر لیجر اسٹیٹمنٹ: اوپر بیان کردہ تمام ٹرانزیکشنز کا ریکارڈ ہے۔
        </div>

        <!-- FOOTER -->
        <div class="footer">
        This is a computer generated statement. No signature required.
        </div>

        </body>
        </html>
        """

        # Create QTextDocument and print to PDF
        document = QTextDocument()
        document.setHtml(html)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        document.print(printer)

        # Open the PDF
        os.startfile(filename)


class ManualLedgerDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Manual Ledger Entry")
        self.setModal(True)
        self.setFixedSize(500, 300)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Customer selection
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.load_customers()
        form_layout.addRow("Customer:", self.customer_combo)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_edit)

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("e.g., Opening balance, Previous dues")
        form_layout.addRow("Description:", self.desc_edit)

        # Amount (debit - what customer owes)
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0, 10000000)
        self.amount_edit.setDecimals(2)
        form_layout.addRow("Amount Owed (Debit):", self.amount_edit)

        layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Add Entry")
        ok_btn.clicked.connect(self.add_entry)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.customer_combo.setFocus()

    def load_customers(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Customers ORDER BY name")
        customers = cur.fetchall()
        conn.close()
        for cid, name in customers:
            self.customer_combo.addItem(name, cid)

    def add_entry(self):
        customer_name = self.customer_combo.currentText().strip()
        if not customer_name:
            QMessageBox.warning(self, "Error", "Please enter a customer name.")
            return

        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.desc_edit.text().strip()
        amount = self.amount_edit.value()

        if not description or amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter description and amount.")
            return

        # Use a single connection for all operations
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            # Check if customer exists
            cur.execute("SELECT id FROM Customers WHERE name = ?", (customer_name,))
            existing = cur.fetchone()
            if existing:
                customer_id = existing[0]
            else:
                # Add new customer
                cur.execute("INSERT INTO Customers (name) VALUES (?)", (customer_name,))
                customer_id = cur.lastrowid
                # Reload customers in parent
                if hasattr(self.parent(), 'load_customers_for_ledger'):
                    self.parent().load_customers_for_ledger()

            # Get current balance for this customer
            cur.execute("SELECT balance FROM CustomerLedger WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,))
            last_balance = cur.fetchone()
            last_balance = last_balance[0] if last_balance else 0.0

            # Add debit entry (increases balance)
            new_balance = last_balance + amount
            cur.execute("""
                INSERT INTO CustomerLedger (customer_id, date, description, debit, credit, balance)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (customer_id, date, description, amount, new_balance))

            conn.commit()
            QMessageBox.information(self, "Success", f"Manual ledger entry added for {customer_name}.")
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to add entry: {str(e)}")
        finally:
            conn.close()
