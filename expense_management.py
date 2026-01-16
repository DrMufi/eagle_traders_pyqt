from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QTabWidget, QComboBox, QPushButton, QGroupBox, QHeaderView, QDateEdit,
    QSizePolicy, QScrollArea, QMessageBox, QInputDialog, QLineEdit, QFormLayout,
    QDialog, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item
import os
import sys


class ExpenseManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        # Apply custom styles
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
        title = QLabel("Expense Management")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px; color: #ffffff;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.salaries_tab()
        self.expenses_tab()

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def salaries_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary card for total salaries paid
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout(summary_group)
        self.total_salaries_label = QLabel("Total Salaries Paid: Rs. 0.00")
        self.total_salaries_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #28a745; padding: 10px;")
        summary_layout.addWidget(self.total_salaries_label)
        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # Employees section
        emp_group = QGroupBox("Employees")
        emp_layout = QVBoxLayout(emp_group)

        # Add employee button
        add_emp_layout = QHBoxLayout()
        add_emp_layout.addStretch()
        add_emp_btn = QPushButton("Add Employee")
        add_emp_btn.clicked.connect(self.add_employee)
        add_emp_layout.addWidget(add_emp_btn)
        emp_layout.addLayout(add_emp_layout)

        # Employees table
        self.employees_table = QTableWidget()
        setup_professional_table(self.employees_table, ["ID", "Name", "Position", "Salary", "Hire Date"], ['id', 'text', 'text', 'numeric', 'date'])
        self.employees_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        emp_layout.addWidget(self.employees_table)

        layout.addWidget(emp_group)

        # Payroll section
        payroll_group = QGroupBox("Payroll Transactions")
        payroll_layout = QVBoxLayout(payroll_group)

        # Add payroll button
        add_payroll_layout = QHBoxLayout()
        add_payroll_layout.addStretch()
        add_payroll_btn = QPushButton("Add Payroll Transaction")
        add_payroll_btn.clicked.connect(self.add_payroll_transaction)
        add_payroll_layout.addWidget(add_payroll_btn)
        payroll_layout.addLayout(add_payroll_layout)

        # Payroll table
        self.payroll_table = QTableWidget()
        setup_professional_table(self.payroll_table, ["ID", "Employee", "Date", "Amount", "Description"], ['id', 'text', 'date', 'numeric', 'text'])
        self.payroll_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        payroll_layout.addWidget(self.payroll_table)

        layout.addWidget(payroll_group)

        self.tabs.addTab(tab, "Salaries")

        # Load data
        self.load_employees()
        self.load_payroll()
        self.update_salaries_summary()

    def expenses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary card for total expenses
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout(summary_group)
        self.total_expenses_label = QLabel("Total Expenses: Rs. 0.00")
        self.total_expenses_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #dc3545; padding: 10px;")
        summary_layout.addWidget(self.total_expenses_label)
        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # Add expense section
        add_group = QGroupBox("Add Expense")
        add_layout = QFormLayout(add_group)

        self.expense_date = QDateEdit()
        self.expense_date.setDate(QDate.currentDate())
        self.expense_date.setCalendarPopup(True)
        add_layout.addRow("Date:", self.expense_date)

        self.expense_category = QComboBox()
        self.expense_category.setEditable(True)
        self.expense_category.addItems(["Utilities", "Food", "Fuel", "Rent", "Maintenance", "Office Supplies", "Other"])
        add_layout.addRow("Category:", self.expense_category)

        self.expense_description = QLineEdit()
        add_layout.addRow("Description:", self.expense_description)

        self.expense_amount = QDoubleSpinBox()
        self.expense_amount.setRange(0, 1000000)
        self.expense_amount.setDecimals(2)
        add_layout.addRow("Amount:", self.expense_amount)

        add_btn = QPushButton("Add Expense")
        add_btn.clicked.connect(self.add_expense)
        add_layout.addRow(add_btn)

        layout.addWidget(add_group)

        # Expenses table
        self.expenses_table = QTableWidget()
        setup_professional_table(self.expenses_table, ["ID", "Date", "Category", "Description", "Amount"], ['id', 'date', 'text', 'text', 'numeric'])
        self.expenses_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.expenses_table)

        self.tabs.addTab(tab, "Expenses")

        # Load data
        self.load_expenses()
        self.update_expenses_summary()

    # ================= DATABASE METHODS =================
    def load_employees(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, position, salary, hire_date FROM Employees ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        self.employees_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.employees_table.setItem(r, 0, create_professional_table_item(row[0], 'id'))
            self.employees_table.setItem(r, 1, create_professional_table_item(row[1], 'text'))
            self.employees_table.setItem(r, 2, create_professional_table_item(row[2], 'text'))
            self.employees_table.setItem(r, 3, create_professional_table_item(row[3], 'numeric'))
            self.employees_table.setItem(r, 4, create_professional_table_item(row[4], 'date'))

    def load_payroll(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pt.id, e.name, pt.date, pt.amount, pt.description
            FROM PayrollTransactions pt
            JOIN Employees e ON pt.employee_id = e.id
            ORDER BY pt.date DESC
        """)
        rows = cur.fetchall()
        conn.close()
        self.payroll_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.payroll_table.setItem(r, 0, create_professional_table_item(row[0], 'id'))
            self.payroll_table.setItem(r, 1, create_professional_table_item(row[1], 'text'))
            self.payroll_table.setItem(r, 2, create_professional_table_item(row[2], 'date'))
            self.payroll_table.setItem(r, 3, create_professional_table_item(row[3], 'numeric'))
            self.payroll_table.setItem(r, 4, create_professional_table_item(row[4], 'text'))

    def load_expenses(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, date, category, description, amount FROM Expenses ORDER BY date DESC")
        rows = cur.fetchall()
        conn.close()
        self.expenses_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.expenses_table.setItem(r, 0, create_professional_table_item(row[0], 'id'))
            self.expenses_table.setItem(r, 1, create_professional_table_item(row[1], 'date'))
            self.expenses_table.setItem(r, 2, create_professional_table_item(row[2], 'text'))
            self.expenses_table.setItem(r, 3, create_professional_table_item(row[3], 'text'))
            self.expenses_table.setItem(r, 4, create_professional_table_item(row[4], 'numeric'))

    def add_employee(self):
        dialog = AddEmployeeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, position, salary, hire_date = dialog.get_data()
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO Employees (name, position, salary, hire_date) VALUES (?, ?, ?, ?)",
                       (name, position, salary, hire_date))
            conn.commit()
            conn.close()
            self.load_employees()
            QMessageBox.information(self, "Success", "Employee added successfully.")

    def add_payroll_transaction(self):
        dialog = AddPayrollDialog(self, self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            employee_id, date, amount, description = dialog.get_data()
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO PayrollTransactions (employee_id, date, amount, description) VALUES (?, ?, ?, ?)",
                       (employee_id, date, amount, description))
            conn.commit()
            conn.close()
            self.load_payroll()
            self.update_salaries_summary()
            QMessageBox.information(self, "Success", "Payroll transaction added successfully.")

    def add_expense(self):
        date = self.expense_date.date().toString("yyyy-MM-dd")
        category = self.expense_category.currentText().strip()
        description = self.expense_description.text().strip()
        amount = self.expense_amount.value()

        if not category or amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter valid category and amount.")
            return

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                   (date, category, description, amount))
        conn.commit()
        conn.close()
        self.load_expenses()
        self.update_expenses_summary()
        # Clear fields
        self.expense_description.clear()
        self.expense_amount.setValue(0)
        QMessageBox.information(self, "Success", "Expense added successfully.")

    def update_salaries_summary(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(amount) FROM PayrollTransactions")
        total = cur.fetchone()[0] or 0
        conn.close()
        self.total_salaries_label.setText(f"Total Salaries Paid: Rs. {total:,.2f}")

    def update_expenses_summary(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(amount) FROM Expenses")
        total = cur.fetchone()[0] or 0
        conn.close()
        self.total_expenses_label.setText(f"Total Expenses: Rs. {total:,.2f}")


class AddEmployeeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Employee")
        self.setModal(True)
        self.setFixedSize(400, 250)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        self.position_edit = QLineEdit()
        form_layout.addRow("Position:", self.position_edit)

        self.salary_edit = QDoubleSpinBox()
        self.salary_edit.setRange(0, 1000000)
        self.salary_edit.setDecimals(2)
        form_layout.addRow("Salary:", self.salary_edit)

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setCalendarPopup(True)
        form_layout.addRow("Hire Date:", self.hire_date_edit)

        layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.name_edit.setFocus()

    def get_data(self):
        return (
            self.name_edit.text().strip(),
            self.position_edit.text().strip(),
            self.salary_edit.value(),
            self.hire_date_edit.date().toString("yyyy-MM-dd")
        )


class AddPayrollDialog(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Payroll Transaction")
        self.setModal(True)
        self.setFixedSize(400, 250)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.employee_combo = QComboBox()
        self.load_employees()
        form_layout.addRow("Employee:", self.employee_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_edit)

        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0, 1000000)
        self.amount_edit.setDecimals(2)
        form_layout.addRow("Amount:", self.amount_edit)

        self.description_edit = QLineEdit()
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.employee_combo.setFocus()

    def load_employees(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Employees ORDER BY name")
        employees = cur.fetchall()
        conn.close()
        for emp_id, name in employees:
            self.employee_combo.addItem(name, emp_id)

    def get_data(self):
        employee_name = self.employee_combo.currentText()
        employee_id = self.employee_combo.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_edit.value()
        description = self.description_edit.text().strip()
        return employee_id, date, amount, description