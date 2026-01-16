from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QProgressBar, QGroupBox,
    QScrollArea, QSpacerItem, QSizePolicy, QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QIcon
from database import Database
from ui_factory import setup_professional_table, create_professional_table_item
from notification_manager import show_info_notification, show_success_notification, show_warning_notification, show_error_notification
import datetime


class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authentication Required")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        label = QLabel("Enter password to view sales details:")
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


class AnimatedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.target_value = 0
        self._current_value = 0
        self.animation = QPropertyAnimation(self, b"current_value")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.valueChanged.connect(self.update_text)

    @pyqtProperty(int)
    def current_value(self):
        return self._current_value

    @current_value.setter
    def current_value(self, value):
        self._current_value = value
        self.update_text()

    def setTargetValue(self, value):
        if isinstance(value, str):
            self.setText(value)
            return
        self.target_value = value
        self.animation.setStartValue(self._current_value)
        self.animation.setEndValue(value)
        self.animation.start()

    def update_text(self, value=None):
        if value is None:
            value = self._current_value
        if isinstance(self.target_value, int):
            self.setText(str(int(value)))
        else:
            self.setText("{:.2f}".format(value))

class Dashboard(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.authenticated = False
        self.init_ui()
        self.load_metrics()

    def init_ui(self):
        # Main scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container widget for scroll area
        container = QWidget()
        scroll_area.setWidget(container)
        container.setStyleSheet("background: transparent;")

        # Main layout for container
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Header section with modern design
        header_card = self.create_modern_card()
        header_layout = QVBoxLayout(header_card)

        title = QLabel('🏢 Eagle Traders Dashboard')
        title.setFont(QFont('Arial', 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 5px;")

        subtitle = QLabel('Real-time business insights and quick actions')
        subtitle.setFont(QFont('Arial', 14))
        subtitle.setStyleSheet("color: #cccccc; margin-bottom: 15px;")

        # Current date and time
        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont('Arial', 12))
        self.datetime_label.setStyleSheet("color: #888888;")
        self.update_datetime()

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(self.datetime_label)
        header_layout.addStretch()

        main_layout.addWidget(header_card)

        # Key Metrics Section - Modern grid
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)

        self.metrics_cards = []
        self.metric_labels = []
        metrics_data = [
            ("📦 Total Products", "products", "#667eea"),
            ("⚠️ Low Stock Items", "low_stock", "#f093fb"),
            ("💰 Total Revenue", "revenue", "#4facfe"),
            ("📈 Monthly Sales", "monthly_sales", "#43e97b"),
            ("👥 Active Customers", "customers", "#fa709a"),
            ("📊 Profit Margin", "profit", "#a8edea")
        ]

        for title, key, color in metrics_data:
            card, value_label = self.create_metric_card(title, "0", color, key)
            self.metrics_cards.append(card)
            self.metric_labels.append((value_label, key))
            metrics_layout.addWidget(card)

        main_layout.addLayout(metrics_layout)

        # Analytics and Activity Section
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(20)

        # Sales Chart Card
        chart_card = self.create_modern_card()
        chart_layout = QVBoxLayout(chart_card)

        chart_title = QLabel('📊 Sales Analytics')
        chart_title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        chart_title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")

        chart_subtitle = QLabel('7-day sales performance trend')
        chart_subtitle.setFont(QFont('Arial', 12))
        chart_subtitle.setStyleSheet("color: #cccccc; margin-bottom: 15px;")

        self.chart_widget = ModernChartWidget()
        self.chart_widget.setMinimumHeight(280)

        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(chart_subtitle)
        chart_layout.addWidget(self.chart_widget)

        analytics_layout.addWidget(chart_card, 2)

        # Activity and Alerts Card
        activity_card = self.create_modern_card()
        activity_layout = QVBoxLayout(activity_card)

        activity_title = QLabel('📋 Recent Activity & Alerts')
        activity_title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        activity_title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")

        # Activity table
        self.activity_table = QTableWidget()
        setup_professional_table(self.activity_table, ["Time", "Type", "Description", "Amount"], ['date', 'text', 'text', 'numeric'])
        self.activity_table.setMaximumHeight(200)
        self.activity_table.setAlternatingRowColors(True)

        # Alerts section
        alerts_title = QLabel('🚨 System Alerts')
        alerts_title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        alerts_title.setStyleSheet("color: #ffffff; margin-top: 15px; margin-bottom: 10px;")

        self.alerts_list = QLabel('No active alerts')
        self.alerts_list.setFont(QFont('Arial', 11))
        self.alerts_list.setStyleSheet("color: #cccccc; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px;")

        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(self.activity_table)
        activity_layout.addWidget(alerts_title)
        activity_layout.addWidget(self.alerts_list)

        analytics_layout.addWidget(activity_card, 1)

        main_layout.addLayout(analytics_layout)

        # Quick Actions Section - Modern design
        actions_card = self.create_modern_card()
        actions_layout = QVBoxLayout(actions_card)

        actions_title = QLabel('⚡ Quick Actions')
        actions_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        actions_title.setStyleSheet("color: #ffffff; margin-bottom: 15px;")

        # Action buttons in grid
        actions_grid = QGridLayout()
        actions_grid.setSpacing(15)

        buttons_data = [
            ("➕ Add Product", "#28a745", self.quick_add_product),
            ("💰 New Sale", "#007bff", self.quick_new_sale),
            ("📊 View Reports", "#ffc107", self.quick_view_reports),
            ("🏷️ Generate Barcode", "#dc3545", self.quick_barcode),
            ("📦 Manage Inventory", "#17a2b8", self.quick_inventory),
            ("👥 Customer Ledger", "#e83e8c", self.quick_customers)
        ]

        row, col = 0, 0
        for text, color, callback in buttons_data:
            btn = self.create_action_button(text, color, callback)
            actions_grid.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        actions_layout.addWidget(actions_title)
        actions_layout.addLayout(actions_grid)

        main_layout.addWidget(actions_card)

        # Test Notifications (temporary for demo)
        test_card = self.create_modern_card()
        test_layout = QVBoxLayout(test_card)

        test_title = QLabel('🔔 Test Notifications')
        test_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        test_title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")

        test_btn_layout = QHBoxLayout()
        test_btn_layout.setSpacing(10)

        info_btn = self.create_action_button("Info", "#17a2b8", lambda: show_info_notification("Info", "This is an info notification"))
        success_btn = self.create_action_button("Success", "#28a745", lambda: show_success_notification("Success", "Operation completed successfully!"))
        warning_btn = self.create_action_button("Warning", "#ffc107", lambda: show_warning_notification("Warning", "Please check your input"))
        error_btn = self.create_action_button("Error", "#dc3545", lambda: show_error_notification("Error", "Something went wrong"))

        test_btn_layout.addWidget(info_btn)
        test_btn_layout.addWidget(success_btn)
        test_btn_layout.addWidget(warning_btn)
        test_btn_layout.addWidget(error_btn)
        test_btn_layout.addStretch()

        test_layout.addWidget(test_title)
        test_layout.addLayout(test_btn_layout)

        main_layout.addWidget(test_card)

        # Footer
        footer = QLabel('© 2026 Eagle Traders Management System')
        footer.setFont(QFont('Arial', 10))
        footer.setStyleSheet("color: #666666; text-align: center; margin-top: 20px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        # Set the scroll area as the main widget
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)

        # Timer for real-time updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_metrics)
        self.update_timer.start(30000)  # Update every 30 seconds

    def create_modern_card(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
                padding: 25px;
                margin: 5px;
            }
        """)
        return card

    def create_metric_card(self, title, value, color, key=None):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(135deg, {color}20 0%, {color}10 100%);
                border: 1px solid {color}40;
                border-radius: 12px;
                padding: 20px;
            }}
            QFrame:hover {{
                background: linear-gradient(135deg, {color}30 0%, {color}20 100%);
                border: 1px solid {color}60;
            }}
        """)

        # Make sales-related cards clickable for authentication
        if key in ['revenue', 'monthly_sales', 'profit']:
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = lambda event: self.authenticate_sales()

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")

        value_label = AnimatedLabel()
        value_label.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setTargetValue(value)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card, value_label

    def create_action_button(self, text, color, callback):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: linear-gradient(135deg, {color} 0%, {self.darken_color(color)} 100%);
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 10px;
                font-size: 12pt;
                min-width: 160px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background: linear-gradient(135deg, {self.darken_color(color)} 0%, {self.darken_color(self.darken_color(color))} 100%);
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def update_datetime(self):
        now = datetime.datetime.now()
        self.datetime_label.setText(f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    def create_card(self, title, subtitle):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 20px;
            }
        """)

        card_layout = QVBoxLayout(card)

        if title:
            title_label = QLabel(title)
            title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
            title_label.setStyleSheet("color: #ffffff; margin-bottom: 5px;")
            card_layout.addWidget(title_label)

            if subtitle:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setFont(QFont('Arial', 12))
                subtitle_label.setStyleSheet("color: #cccccc; margin-bottom: 15px;")
                card_layout.addWidget(subtitle_label)

        return card

    def darken_color(self, color):
        # Simple color darkening for hover effects
        if color == "#28a745":
            return "#218838"
        elif color == "#007bff":
            return "#0056b3"
        elif color == "#ffc107":
            return "#e0a800"
        elif color == "#dc3545":
            return "#c82333"
        return color

    def load_metrics(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Total Products
        cursor.execute("SELECT COUNT(*) FROM Products")
        total_products = cursor.fetchone()[0]

        # Low Stock Products
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id)
            FROM Products p
            LEFT JOIN ProductBatches pb ON p.id = pb.product_id
            GROUP BY p.id
            HAVING COALESCE(SUM(pb.quantity), 0) < 10
        """)
        low_stock_result = cursor.fetchall()
        low_stock_count = len(low_stock_result)

        # Total Sales Amount
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM SalesTransactions")
        total_sales = cursor.fetchone()[0]

        # Recent Sales (last 30 days)
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        cursor.execute("SELECT COUNT(*) FROM SalesTransactions WHERE date >= ?", (thirty_days_ago.strftime('%Y-%m-%d'),))
        recent_sales = cursor.fetchone()[0]

        # Active Customers
        cursor.execute("SELECT COUNT(DISTINCT customer_id) FROM SalesTransactions WHERE customer_id IS NOT NULL")
        active_customers = cursor.fetchone()[0]

        # Profit Margin (simplified calculation)
        cursor.execute("""
            SELECT COALESCE(SUM(si.total_price), 0) as sales,
                   COALESCE(SUM(pb.cost_price * pb.quantity), 0) as costs
            FROM SalesItems si
            LEFT JOIN ProductBatches pb ON si.batch_id = pb.id
        """)
        profit_data = cursor.fetchone()
        sales_total = profit_data[0] or 0
        costs_total = profit_data[1] or 0
        profit_margin = ((sales_total - costs_total) / sales_total * 100) if sales_total > 0 else 0

        # Sales data for chart (last 7 days)
        chart_data = []
        for i in range(6, -1, -1):
            day = datetime.datetime.now() - datetime.timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM SalesTransactions WHERE date >= ? AND date < ?",
                          (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
            daily_sales = cursor.fetchone()[0]
            chart_data.append(daily_sales)

        # Recent activity (last 10 transactions)
        cursor.execute("""
            SELECT st.date, 'Sale' as type, c.name as description, st.total_amount
            FROM SalesTransactions st
            LEFT JOIN Customers c ON st.customer_id = c.id
            ORDER BY st.date DESC
            LIMIT 10
        """)
        activities = cursor.fetchall()

        # System alerts
        alerts = []
        if low_stock_count > 0:
            alerts.append(f"⚠️ {low_stock_count} products are low in stock")
        if active_customers == 0:
            alerts.append("ℹ️ No sales recorded yet")

        conn.close()

        # Update datetime
        self.update_datetime()

        # Update chart
        self.chart_widget.set_data(chart_data)

        # Update activity table
        self.activity_table.setRowCount(len(activities))
        for row, (time, type_, description, amount) in enumerate(activities):
            self.activity_table.setItem(row, 0, create_professional_table_item(time, 'date'))
            self.activity_table.setItem(row, 1, create_professional_table_item(type_, 'text'))
            self.activity_table.setItem(row, 2, create_professional_table_item(description or "Walk-in Customer", 'text'))
            self.activity_table.setItem(row, 3, create_professional_table_item(f"Rs. {amount:.2f}", 'numeric'))

        # Update alerts
        if alerts:
            self.alerts_list.setText("\n".join(alerts))
            self.alerts_list.setStyleSheet("color: #ffcc00; padding: 10px; background: rgba(255,204,0,0.1); border-radius: 5px;")
        else:
            self.alerts_list.setText("✅ All systems operational")
            self.alerts_list.setStyleSheet("color: #28a745; padding: 10px; background: rgba(40,167,69,0.1); border-radius: 5px;")

        # Update metric cards
        metrics_values = {
            "products": str(total_products),
            "low_stock": str(low_stock_count),
            "revenue": f"Rs. {total_sales:,.2f}" if self.authenticated else "🔒 Login Required",
            "monthly_sales": str(recent_sales) if self.authenticated else "🔒 Login Required",
            "customers": str(active_customers),
            "profit": f"{profit_margin:.1f}%" if self.authenticated else "🔒 Login Required"
        }

        for value_label, key in self.metric_labels:
            value_label.setTargetValue(metrics_values.get(key, "0"))

    def authenticate_sales(self):
        # Since users are now logged in, allow access to sales details
        if not self.authenticated:
            self.authenticated = True
            self.load_metrics()  # Refresh to show actual values
            show_success_notification("Authentication", "Sales details now visible!")

    def add_metric_card(self, row, col, title, value, color):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setLineWidth(1)
        style = """
            QFrame {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                border-left: 4px solid {};
            }}
        """.format(color)
        card.setStyleSheet(style)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")

        value_label = AnimatedLabel()
        value_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setTargetValue(value)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.metrics_grid.addWidget(card, row, col)

    def quick_add_product(self):
        # Switch to products tab
        main_window = self.parent().parent().parent()
        main_window.show_product_management()

    def quick_new_sale(self):
        # Switch to sales tab
        main_window = self.parent().parent().parent()
        main_window.show_sales()

    def quick_view_reports(self):
        # Switch to accounts tab
        main_window = self.parent().parent().parent()
        main_window.show_accounts()

    def quick_barcode(self):
        # Switch to barcode tab
        main_window = self.parent().parent().parent()
        main_window.show_barcode()

    def quick_inventory(self):
        # Switch to inventory tab
        main_window = self.parent().parent().parent()
        main_window.show_inventory()

    def quick_customers(self):
        # Switch to accounts tab (customer ledger)
        main_window = self.parent().parent().parent()
        main_window.show_accounts()

class ModernChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = [0] * 7  # Last 7 days sales
        self.setMinimumHeight(250)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        if width <= 0 or height <= 0:
            painter.end()
            return

        # Background solid color
        painter.fillRect(0, 0, width, height, QColor("#1a1a2e"))

        # Grid lines
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = 40 + (height - 80) * i // 4
            painter.drawLine(60, y, width - 30, y)

        # Draw axes
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(60, 30, 60, height - 50)  # Y axis
        painter.drawLine(60, height - 50, width - 30, height - 50)  # X axis

        # Axis labels
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QColor("#cccccc"))

        # Y-axis labels
        max_val = max(self.data) if self.data else 1
        if max_val == 0:
            max_val = 1
        for i in range(5):
            val = int(max_val * (4 - i) / 4)
            y = 40 + (height - 80) * i // 4
            painter.drawText(20, y + 5, f"{val}")

        # X-axis labels (days)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i in range(7):
            x = 60 + (width - 90) * i // 6
            painter.drawText(x - 15, height - 30, days[i])

        if not self.data:
            return

        bar_width = max(20, (width - 90) // 7 - 8)

        for i, val in enumerate(self.data):
            bar_height = int((val / max_val) * (height - 80)) if max_val > 0 else 0
            if bar_height <= 0:
                continue
            x = int(60 + (width - 90) * i // 6 - bar_width // 2)
            y = int(height - 50 - bar_height)

            # Bar with solid color
            if val > max_val * 0.8:
                color = QColor("#ff6b6b")
            elif val > max_val * 0.5:
                color = QColor("#4ecdc4")
            else:
                color = QColor("#667eea")

            painter.setBrush(color)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawRoundedRect(x, y, bar_width, bar_height, 3.0, 3.0)

            # Value label on top of bar
            if bar_height > 20:
                painter.setPen(QColor("#ffffff"))
                painter.setFont(QFont('Arial', 8, QFont.Weight.Bold))
                painter.drawText(x, y - 5, f"{val:.0f}")
                painter.setFont(QFont('Arial', 9))

        # Title
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        painter.drawText(60, 25, "Sales Performance (Last 7 Days)")

        painter.end()
