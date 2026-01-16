"""
Notification Manager for Eagle Traders
Provides toast notifications and system alerts
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont


class ToastNotification(QWidget):
    """Simple toast notification widget"""

    def __init__(self, title, message, notification_type="info", duration=3000, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.notification_type = notification_type

        # Set window properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip |
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.init_ui(title, message)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide)
        self.hide_timer.setSingleShot(True)

    def init_ui(self, title, message):
        # Main container
        container = QFrame(self)
        container.setStyleSheet(self.get_style_for_type())
        container.setFixedWidth(350)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel(self.get_icon_for_type())
        icon_label.setFont(QFont('Arial', 16))
        layout.addWidget(icon_label)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")

        message_label = QLabel(message)
        message_label.setFont(QFont('Arial', 10))
        message_label.setStyleSheet("color: #f0f0f0;")
        message_label.setWordWrap(True)

        content_layout.addWidget(title_label)
        content_layout.addWidget(message_label)
        layout.addLayout(content_layout, 1)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                padding: 0px 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

        # Set size
        self.adjustSize()

    def get_style_for_type(self):
        if self.notification_type == "success":
            return """
                QFrame {
                    background: rgba(40, 167, 69, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                }
            """
        elif self.notification_type == "warning":
            return """
                QFrame {
                    background: rgba(255, 193, 7, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                }
            """
        elif self.notification_type == "error":
            return """
                QFrame {
                    background: rgba(220, 53, 69, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                }
            """
        else:  # info
            return """
                QFrame {
                    background: rgba(0, 123, 255, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                }
            """

    def get_icon_for_type(self):
        if self.notification_type == "success":
            return "✅"
        elif self.notification_type == "warning":
            return "⚠️"
        elif self.notification_type == "error":
            return "❌"
        else:  # info
            return "ℹ️"

    def show_notification(self):
        # Position at bottom-right of screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20,
                 screen.height() - self.height() - 50)

        self.show()
        self.hide_timer.start(self.duration)


def show_info_notification(title, message, duration=3000):
    """Convenience function for info notifications"""
    notification = ToastNotification(title, message, "info", duration)
    notification.show_notification()


def show_success_notification(title, message, duration=3000):
    """Convenience function for success notifications"""
    notification = ToastNotification(title, message, "success", duration)
    notification.show_notification()


def show_warning_notification(title, message, duration=3000):
    """Convenience function for warning notifications"""
    notification = ToastNotification(title, message, "warning", duration)
    notification.show_notification()


def show_error_notification(title, message, duration=3000):
    """Convenience function for error notifications"""
    notification = ToastNotification(title, message, "error", duration)
    notification.show_notification()