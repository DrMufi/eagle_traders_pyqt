import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea,
    QDialog, QFormLayout, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QComboBox, QTableWidget
from PyQt6.QtCore import QObject
from database import Database
from product_management import ProductManagement
from inventory_management import InventoryManagement
from barcode_sticker import BarcodeSticker
from dashboard import Dashboard
from sales_pos import SalesPOS
from accounts_reports import AccountsReports
from expense_management import ExpenseManagement
from backup_restore import BackupRestoreWidget
from low_stock_alerts import LowStockAlertsWidget
from user_management import UserManagement


class LoginDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = None
        self.user_role = None
        self.setWindowTitle("Login - Eagle Traders")
        self.setModal(True)
        self.setFixedSize(350, 200)

        layout = QVBoxLayout(self)

        title = QLabel("Eagle Traders Management System")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setText("admin")  # Default for convenience
        form_layout.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)

        layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        login_btn.setDefault(True)
        buttons.addWidget(login_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        self.username_edit.setFocus()

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        user = self.db.authenticate_user(username, password)
        if user:
            self.user_id, self.user_role = user
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")


class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authentication Required")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        label = QLabel("Enter password to access Accounts module:")
        layout.addWidget(label)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.password_edit.setFocus()

    def get_password(self):
        return self.password_edit.text()

class MainWindow(QMainWindow):
    def __init__(self):
        print("MainWindow init start")
        super().__init__()
        print("Super init done")
        self.db = Database()
        print("Database created")

        # Login first
        login_dialog = LoginDialog(self.db, self)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)  # Exit if login cancelled

        self.current_user_id = login_dialog.user_id
        self.current_user_role = login_dialog.user_role
        print(f"Logged in as user {self.current_user_id} with role {self.current_user_role}")

        self.init_ui()
        print("UI initialized")

    def init_ui(self):
        print("init_ui start")
        self.setWindowTitle('Eagle Traders Management System')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 1)

        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 3)

        # Create pages
        self.create_pages()

        # Load style
        self.load_style()

        # Initialize animation
        self.current_animation = None
        print("init_ui end")

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-right: 2px solid #007bff;
                min-width: 200px;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for sidebar content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #e9ecef;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #007bff;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0056b3;
            }
        """)

        # Container widget for scrollable content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 20, 10, 20)
        scroll_layout.setSpacing(10)

        title = QLabel('Eagle Traders')
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #007bff; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title)

        # Base buttons available to all users
        buttons = [
            ('🏠 Dashboard', self.show_dashboard),
            ('📦 Product Management', self.show_product_management),
            ('📦 Inventory Management', self.show_inventory),
            ('💰 Sales', self.show_sales),
            ('🏷️ Barcode', self.show_barcode),
            ('⚠️ Low Stock Alerts', self.show_low_stock_alerts),
        ]

        # Admin-only buttons
        if self.current_user_role == 'admin':
            admin_buttons = [
                ('🏷️ Categories', self.show_categories),
                ('🏢 Suppliers', self.show_suppliers),
                ('📊 Accounts', self.show_accounts),
                ('💸 Expenses', self.show_expenses),
                ('👥 User Management', self.show_user_management),
                ('💾 Backup & Restore', self.show_backup_restore),
            ]
            buttons.extend(admin_buttons)

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: left;
                    font-size: 12pt;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
            btn.clicked.connect(callback)
            scroll_layout.addWidget(btn)

        # Removed theme selector as we now use fixed dark theme from style.qss

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        return sidebar

    def create_pages(self):
        print("create_pages start")
        # Dashboard
        dashboard = Dashboard(self.db)
        self.content_stack.addWidget(dashboard)
        print("dashboard added")

        # Products
        products = ProductManagement(self.db)
        self.content_stack.addWidget(products)
        print("products added")

        # Categories
        from category_management import CategoryManagement
        categories = CategoryManagement(self.db)
        self.content_stack.addWidget(categories)
        print("categories added")

        # Suppliers
        from supplier_management import SupplierManagement
        suppliers = SupplierManagement(self.db)
        self.content_stack.addWidget(suppliers)
        print("suppliers added")

        # Sales
        sales = SalesPOS(self.db)
        self.content_stack.addWidget(sales)
        print("sales added")

        # Accounts
        accounts = AccountsReports(self.db)
        self.content_stack.addWidget(accounts)
        print("accounts added")

        # Expenses
        expenses = ExpenseManagement(self.db)
        self.content_stack.addWidget(expenses)
        print("expenses added")

        # Barcode & Sticker
        barcode = BarcodeSticker(self.db)
        self.content_stack.addWidget(barcode)
        print("barcode added")

        # Inventory
        inventory = InventoryManagement(self.db)
        self.content_stack.addWidget(inventory)
        print("inventory added")

        # Low Stock Alerts
        low_stock_alerts = LowStockAlertsWidget(self.db)
        self.content_stack.addWidget(low_stock_alerts)
        print("low_stock_alerts added")

        # User Management (only for admin)
        if self.current_user_role == 'admin':
            user_management = UserManagement(self.db)
            self.content_stack.addWidget(user_management)
            print("user_management added")

        # Backup & Restore
        backup_restore = BackupRestoreWidget(self.db)
        self.content_stack.addWidget(backup_restore)
        print("backup_restore added")
        print("create_pages end")

    def show_dashboard(self):
        self.animate_switch(0)

    def show_product_management(self):
        self.animate_switch(1)
        # Refresh categories and suppliers in case new ones were added
        product_widget = self.content_stack.widget(1)
        if hasattr(product_widget, 'refresh_categories'):
            product_widget.refresh_categories()
        if hasattr(product_widget, 'refresh_suppliers'):
            product_widget.refresh_suppliers()

    def show_inventory(self):
        self.animate_switch(8)
        # Refresh inventory in case new products were added
        inventory_widget = self.content_stack.widget(8)
        if hasattr(inventory_widget, 'refresh_inventory'):
            inventory_widget.refresh_inventory()

    def show_categories(self):
        if self.current_user_role == 'admin':
            self.animate_switch(2)
        else:
            QMessageBox.warning(self, "Access Denied", "Only administrators can manage categories.")

    def show_suppliers(self):
        if self.current_user_role == 'admin':
            self.animate_switch(3)
        else:
            QMessageBox.warning(self, "Access Denied", "Only administrators can manage suppliers.")

    def show_sales(self):
        self.animate_switch(4)
        # Refresh products list in case new products were added
        sales_widget = self.content_stack.widget(4)
        if hasattr(sales_widget, 'refresh_products'):
            sales_widget.refresh_products()

    def show_accounts(self):
        if self.current_user_role == 'admin':
            self.animate_switch(5)
        else:
            QMessageBox.warning(self, "Access Denied", "Only administrators can access accounts and reports.")

    def show_expenses(self):
        if self.current_user_role == 'admin':
            self.animate_switch(6)
        else:
            QMessageBox.warning(self, "Access Denied", "Only administrators can manage expenses.")

    def show_barcode(self):
        self.animate_switch(7)

    def show_low_stock_alerts(self):
        self.animate_switch(9)

    def show_user_management(self):
        if self.current_user_role != 'admin':
            QMessageBox.warning(self, "Access Denied", "Only administrators can access user management.")
            return
        # Find the index of user management widget
        for i in range(self.content_stack.count()):
            if isinstance(self.content_stack.widget(i), UserManagement):
                self.animate_switch(i)
                break

    def show_backup_restore(self):
        if self.current_user_role == 'admin':
            # Find the index of backup restore widget
            for i in range(self.content_stack.count()):
                if isinstance(self.content_stack.widget(i), BackupRestoreWidget):
                    self.animate_switch(i)
                    break
        else:
            QMessageBox.warning(self, "Access Denied", "Only administrators can access backup and restore.")

    def load_style(self):
        print("load_style start")
        try:
            if getattr(sys, 'frozen', False):
                style_path = os.path.join(sys._MEIPASS, 'style.qss')
            else:
                style_path = 'style.qss'
            with open(style_path, 'r') as f:
                self.setStyleSheet(f.read())
            print("style loaded from file")
        except FileNotFoundError:
            print("style.qss not found, using fallback")
            # Fallback to default dark theme if style.qss not found
            self.setStyleSheet("""
QMainWindow { background: #1e1e1e; color: #ffffff; }
QWidget { background: #1e1e1e; color: #ffffff; font-size: 11pt; }
QPushButton { background: #007acc; color: #ffffff; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; font-size: 11pt; min-width: 100px; }
QPushButton:hover { background: #005a9e; }
QPushButton:pressed { background: #004080; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #2d2d2d; color: #ffffff; border: 1px solid #404040; border-radius: 4px; padding: 8px 12px; font-size: 11pt; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #007acc; outline: none; }
QLabel { color: #ffffff; font-size: 11pt; }
QTableWidget { background: #2d2d2d; color: #ffffff; gridline-color: #404040; border: 1px solid #404040; border-radius: 6px; alternate-background-color: #252525; selection-background-color: #007acc; font-size: 11pt; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid #404040; }
QTableWidget::item:selected { background: #007acc; color: #ffffff; }
QHeaderView::section { background: #1e1e1e; color: #ffffff; padding: 10px; border: none; border-right: 1px solid #404040; border-bottom: 1px solid #404040; font-weight: bold; font-size: 11pt; }
QGroupBox { font-weight: bold; border: 1px solid #404040; border-radius: 8px; margin-top: 1ex; background: #2d2d2d; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; color: #ffffff; font-size: 12pt; background: #1e1e1e; border-radius: 4px; }
QFrame { background: #2d2d2d; border: 1px solid #404040; border-radius: 6px; }
QScrollBar:vertical { background: #2d2d2d; width: 16px; border-radius: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #404040; border-radius: 8px; min-height: 40px; }
QScrollBar::handle:vertical:hover { background: #555555; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; border: none; height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; border: none; }
""")

    def change_theme(self, theme):
        if theme in self.themes:
            self.setStyleSheet(self.themes[theme])

    def animate_switch(self, index):
        self.content_stack.setCurrentIndex(index)

def main():
    print("Main function start")
    try:
        app = QApplication(sys.argv)
        print("App created")
        window = MainWindow()
        print("Window created")
        window.show()
        window.raise_()
        window.activateWindow()
        print("Window shown and activated")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()