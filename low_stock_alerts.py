"""
Low Stock Alerts System for Eagle Traders
Monitors inventory levels and provides alerts for low stock items
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QGroupBox, QCheckBox, QSpinBox,
    QComboBox, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item
from notification_manager import show_warning_notification
import datetime


class LowStockChecker(QThread):
    """Thread for checking low stock items"""
    alerts_found = pyqtSignal(list)  # List of low stock items

    def __init__(self, db, threshold=10):
        super().__init__()
        self.db = db
        self.threshold = threshold
        self.running = True

    def run(self):
        while self.running:
            try:
                low_stock_items = self.check_low_stock()
                if low_stock_items:
                    self.alerts_found.emit(low_stock_items)
            except Exception as e:
                print(f"Low stock check error: {e}")

            # Check every 5 minutes
            self.sleep(300)

    def stop(self):
        self.running = False

    def check_low_stock_once(self):
        """Check for products below threshold (single check)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, c.name as category,
                   COALESCE(SUM(pb.quantity), 0) as total_stock,
                   p.min_stock_level
            FROM Products p
            LEFT JOIN ProductBatches pb ON p.id = pb.product_id
            LEFT JOIN Categories c ON p.category_id = c.id
            GROUP BY p.id, p.name, c.name, p.min_stock_level
            HAVING COALESCE(SUM(pb.quantity), 0) <= ?
        """, (self.threshold,))

        low_stock_items = []
        for row in cursor.fetchall():
            product_id, name, category, stock, min_level = row
            low_stock_items.append({
                'id': product_id,
                'name': name,
                'category': category or 'Uncategorized',
                'current_stock': stock,
                'min_level': min_level or 0
            })

        conn.close()
        return low_stock_items


class LowStockAlertsWidget(QWidget):
    """Widget for managing low stock alerts"""

    def __init__(self, db):
        print("LowStockAlertsWidget init start")
        super().__init__()
        self.db = db
        self.checker_thread = None
        self.alerts_enabled = True
        self.threshold = 10
        self.init_ui()
        print("LowStockAlertsWidget init_ui done")
        self.load_alerts()
        print("LowStockAlertsWidget load_alerts done")
        # self.start_monitoring()  # Disabled for debugging
        print("LowStockAlertsWidget init end")

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Low Stock Alerts")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #ffffff; margin-bottom: 20px;")
        layout.addWidget(title)

        # Settings section
        settings_group = QGroupBox("Alert Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Enable/disable alerts
        self.enable_check = QCheckBox("Enable low stock alerts")
        self.enable_check.setChecked(True)
        self.enable_check.setStyleSheet("color: #ffffff; font-size: 12pt;")
        self.enable_check.stateChanged.connect(self.toggle_alerts)
        settings_layout.addWidget(self.enable_check)

        # Threshold setting
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Low stock threshold:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 1000)
        self.threshold_spin.setValue(10)
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(QLabel("units"))
        threshold_layout.addStretch()
        settings_layout.addLayout(threshold_layout)

        # Manual check button
        check_btn = QPushButton("Check Now")
        check_btn.clicked.connect(self.manual_check)
        settings_layout.addWidget(check_btn)

        layout.addWidget(settings_group)

        # Current alerts section
        alerts_group = QGroupBox("Current Low Stock Alerts")
        alerts_layout = QVBoxLayout(alerts_group)

        self.alerts_table = QTableWidget()
        setup_professional_table(self.alerts_table, [
            "Product", "Category", "Current Stock", "Min Level", "Status", "Actions"
        ], ['text', 'text', 'numeric', 'numeric', 'text', 'action'])
        self.alerts_table.setMaximumHeight(400)

        alerts_layout.addWidget(self.alerts_table)
        layout.addWidget(alerts_group)

        # Statistics section
        stats_group = QGroupBox("Stock Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("Loading statistics...")
        self.stats_label.setStyleSheet("color: #cccccc; font-size: 11pt;")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(stats_group)

    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.checker_thread is None:
            self.checker_thread = LowStockChecker(self.db, self.threshold)
            self.checker_thread.alerts_found.connect(self.on_alerts_found)
            self.checker_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.checker_thread:
            self.checker_thread.stop()
            self.checker_thread.wait()
            self.checker_thread = None

    def toggle_alerts(self, state):
        """Enable/disable alerts"""
        self.alerts_enabled = state == Qt.CheckState.Checked
        if self.alerts_enabled:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def update_threshold(self, value):
        """Update the low stock threshold"""
        self.threshold = value
        if self.checker_thread:
            self.checker_thread.threshold = value
        self.manual_check()  # Re-check with new threshold

    def manual_check(self):
        """Perform manual low stock check"""
        low_stock_items = self.check_low_stock_once()
        if low_stock_items:
            self.on_alerts_found(low_stock_items)

    def on_alerts_found(self, alerts):
        """Handle found alerts"""
        if not self.alerts_enabled:
            return

        # Show notification if there are alerts
        if alerts:
            product_names = [item['name'] for item in alerts[:3]]  # Show first 3
            if len(alerts) > 3:
                product_names.append(f"and {len(alerts) - 3} more")
            products_str = ", ".join(product_names)

            show_warning_notification(
                "Low Stock Alert",
                f"{len(alerts)} products are low in stock: {products_str}"
            )

        # Update the alerts table
        self.update_alerts_table(alerts)

    def update_alerts_table(self, alerts):
        """Update the alerts table with current low stock items"""
        self.alerts_table.setRowCount(len(alerts))

        for row, item in enumerate(alerts):
            # Product name
            self.alerts_table.setItem(row, 0, create_professional_table_item(item['name'], 'text'))

            # Category
            self.alerts_table.setItem(row, 1, create_professional_table_item(item['category'], 'text'))

            # Current stock
            self.alerts_table.setItem(row, 2, create_professional_table_item(item['current_stock'], 'numeric'))

            # Min level
            self.alerts_table.setItem(row, 3, create_professional_table_item(item['min_level'], 'numeric'))

            # Status
            status = "Critical" if item['current_stock'] == 0 else "Low"
            status_item = create_professional_table_item(status, 'text')
            if status == "Critical":
                status_item.setBackground(Qt.GlobalColor.red)
                status_item.setForeground(Qt.GlobalColor.white)
            else:
                status_item.setBackground(Qt.GlobalColor.yellow)
                status_item.setForeground(Qt.GlobalColor.black)
            self.alerts_table.setItem(row, 4, status_item)

            # Actions button
            action_btn = QPushButton("View Details")
            action_btn.clicked.connect(lambda _, pid=item['id']: self.view_product_details(pid))
            self.alerts_table.setCellWidget(row, 5, action_btn)

    def view_product_details(self, product_id):
        """View detailed information about a low stock product"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.description, c.name as category,
                   COALESCE(SUM(pb.quantity), 0) as total_stock,
                   p.min_stock_level
            FROM Products p
            LEFT JOIN ProductBatches pb ON p.id = pb.product_id
            LEFT JOIN Categories c ON p.category_id = c.id
            WHERE p.id = ?
            GROUP BY p.id, p.name, p.description, c.name, p.min_stock_level
        """, (product_id,))

        product = cursor.fetchone()
        conn.close()

        if product:
            name, description, category, stock, min_level = product
            QMessageBox.information(
                self, "Product Details",
                f"Product: {name}\n"
                f"Category: {category or 'Uncategorized'}\n"
                f"Description: {description or 'No description'}\n"
                f"Current Stock: {stock}\n"
                f"Minimum Level: {min_level or 0}\n"
                f"Status: {'Out of Stock' if stock == 0 else 'Low Stock'}"
            )

    def load_alerts(self):
        """Load current alerts on startup"""
        self.manual_check()
        self.load_statistics()

    def check_low_stock_once(self):
        """Check for products below threshold (single check)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, c.name as category,
                   COALESCE(SUM(pb.quantity), 0) as total_stock,
                   p.min_stock_level
            FROM Products p
            LEFT JOIN ProductBatches pb ON p.id = pb.product_id
            LEFT JOIN Categories c ON p.category_id = c.id
            GROUP BY p.id, p.name, c.name, p.min_stock_level
            HAVING COALESCE(SUM(pb.quantity), 0) <= ?
        """, (self.threshold,))

        low_stock_items = []
        for row in cursor.fetchall():
            product_id, name, category, stock, min_level = row
            low_stock_items.append({
                'id': product_id,
                'name': name,
                'category': category or 'Uncategorized',
                'current_stock': stock,
                'min_level': min_level or 0
            })

        conn.close()
        return low_stock_items

    def check_low_stock(self):
        """Check for products below threshold (for thread)"""
        return self.check_low_stock_once()

    def load_statistics(self):
        """Load stock statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Total products
        cursor.execute("SELECT COUNT(*) FROM Products")
        total_products = cursor.fetchone()[0]

        # Products with stock
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id)
            FROM Products p
            JOIN ProductBatches pb ON p.id = pb.product_id
            WHERE pb.quantity > 0
        """)
        products_with_stock = cursor.fetchone()[0]

        # Total stock value (simplified)
        cursor.execute("""
            SELECT COALESCE(SUM(pb.quantity * pb.cost_price), 0)
            FROM ProductBatches pb
        """)
        total_value = cursor.fetchone()[0]

        # Low stock products
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id)
            FROM Products p
            LEFT JOIN ProductBatches pb ON p.id = pb.product_id
            GROUP BY p.id
            HAVING COALESCE(SUM(pb.quantity), 0) <= ?
        """, (self.threshold,))
        low_stock_count = len(cursor.fetchall())

        conn.close()

        stats_text = f"""
        Total Products: {total_products}
        Products with Stock: {products_with_stock}
        Low Stock Products: {low_stock_count}
        Total Inventory Value: Rs. {total_value:,.2f}
        """

        self.stats_label.setText(stats_text.strip())

    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_monitoring()
        event.accept()