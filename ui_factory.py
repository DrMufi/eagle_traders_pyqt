"""
UI Factory Module for Consistent Widget Styling

This module provides factory functions for creating PyQt6 widgets with consistent
styling that matches the application's modern gradient theme.
"""

from PyQt6.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QFormLayout, QTextEdit, QCheckBox, QRadioButton, QGroupBox, QProgressBar,
    QSlider, QDateEdit, QTimeEdit, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGraphicsOpacityEffect


class UITheme:
    """Theme constants for consistent styling"""

    # Color palette
    PRIMARY_COLOR = "#007acc"
    SECONDARY_COLOR = "#005a9e"
    BACKGROUND = "#1e1e1e"
    SURFACE = "#2d2d2d"
    TEXT = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    BORDER = "#404040"
    SUCCESS_COLOR = "#28a745"
    WARNING_COLOR = "#ffc107"
    ERROR_COLOR = "#dc3545"
    INFO_COLOR = "#17a2b8"

    # Common styles (now centralized in QSS, but kept for reference)
    BUTTON_STYLE = f"""
        QPushButton {{
            background: {PRIMARY_COLOR};
            color: {TEXT};
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 11pt;
        }}
        QPushButton:hover {{
            background: {SECONDARY_COLOR};
        }}
        QPushButton:pressed {{
            background: #004080;
        }}
        QPushButton:disabled {{
            background: {BORDER};
            color: #808080;
        }}
    """

    INPUT_STYLE = f"""
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 11pt;
            color: {TEXT};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
            border-color: {PRIMARY_COLOR};
        }}
        QComboBox::drop-down {{
            border: none;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }}
    """

    LABEL_STYLE = f"""
        QLabel {{
            color: {TEXT};
            font-size: 11pt;
            font-weight: 500;
        }}
        QLabel.title {{
            font-size: 18pt;
            font-weight: bold;
            color: {TEXT};
            margin-bottom: 10px;
        }}
        QLabel.subtitle {{
            font-size: 14pt;
            font-weight: bold;
            color: {TEXT_SECONDARY};
        }}
    """

    TABLE_STYLE = f"""
        QTableWidget {{
            gridline-color: transparent;
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 6px;
            alternate-background-color: #252525;
        }}
        QTableWidget::item {{
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: {TEXT};
        }}
        QTableWidget::item:selected {{
            background: {PRIMARY_COLOR};
            color: white;
        }}
        QTableWidget::item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        QHeaderView::section {{
            background: #333333;
            color: white;
            padding: 12px;
            border: none;
            border-bottom: 2px solid #555555;
            font-weight: bold;
            font-size: 11pt;
        }}
    """

    DIALOG_STYLE = f"""
        QDialog {{
            background: {BACKGROUND};
            border-radius: 8px;
        }}
    """


class UIAnimations:
    """Reusable animation helpers for UI components"""

    @staticmethod
    def fade_in(widget, duration=200):
        """Fade in a widget"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        return animation

    @staticmethod
    def apply_button_animations(button):
        """Apply hover and press animations to a button"""
        def on_enter(event):
            scale_anim = QPropertyAnimation(button, b"geometry")
            scale_anim.setDuration(120)
            start_rect = button.geometry()
            end_rect = start_rect.adjusted(-2, -2, 2, 2)
            scale_anim.setStartValue(start_rect)
            scale_anim.setEndValue(end_rect)
            scale_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            scale_anim.start()

        def on_leave(event):
            scale_anim = QPropertyAnimation(button, b"geometry")
            scale_anim.setDuration(120)
            start_rect = button.geometry()
            end_rect = start_rect.adjusted(2, 2, -2, -2)
            scale_anim.setStartValue(start_rect)
            scale_anim.setEndValue(end_rect)
            scale_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            scale_anim.start()

        def on_press():
            if not button.graphicsEffect():
                effect = QGraphicsOpacityEffect(button)
                button.setGraphicsEffect(effect)
            opacity_anim = QPropertyAnimation(button.graphicsEffect(), b"opacity")
            opacity_anim.setDuration(80)
            opacity_anim.setStartValue(1.0)
            opacity_anim.setEndValue(0.8)
            opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            opacity_anim.start()

        def on_release():
            if button.graphicsEffect():
                opacity_anim = QPropertyAnimation(button.graphicsEffect(), b"opacity")
                opacity_anim.setDuration(80)
                opacity_anim.setStartValue(0.8)
                opacity_anim.setEndValue(1.0)
                opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                opacity_anim.start()

        button.enterEvent = on_enter
        button.leaveEvent = on_leave
        button.pressed.connect(on_press)
        button.released.connect(on_release)

    @staticmethod
    def slide_transition(widget, direction="left", duration=200):
        """Slide transition for tab/page changes"""
        # For simplicity, use fade; slide would require more complex geometry animation
        return UIAnimations.fade_in(widget, duration)


def create_button(text, parent=None, clicked_callback=None, style=None):
    """Create a styled QPushButton with animations"""
    button = QPushButton(text, parent)
    button.setStyleSheet(style or UITheme.BUTTON_STYLE)
    UIAnimations.apply_button_animations(button)
    if clicked_callback:
        button.clicked.connect(clicked_callback)
    return button


def create_label(text, parent=None, style=None, is_title=False, is_subtitle=False):
    """Create a styled QLabel"""
    label = QLabel(text, parent)
    if is_title:
        label.setObjectName("title")
    elif is_subtitle:
        label.setObjectName("subtitle")
    label.setStyleSheet(style or UITheme.LABEL_STYLE)
    return label


def create_line_edit(placeholder="", parent=None, style=None):
    """Create a styled QLineEdit"""
    line_edit = QLineEdit(parent)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setStyleSheet(style or UITheme.INPUT_STYLE)
    return line_edit


def create_combo_box(parent=None, style=None):
    """Create a styled QComboBox"""
    combo = QComboBox(parent)
    combo.setStyleSheet(style or UITheme.INPUT_STYLE)
    return combo


def create_spin_box(parent=None, style=None, min_val=None, max_val=None, value=None):
    """Create a styled QSpinBox"""
    spin = QSpinBox(parent)
    if min_val is not None:
        spin.setMinimum(min_val)
    if max_val is not None:
        spin.setMaximum(max_val)
    if value is not None:
        spin.setValue(value)
    spin.setStyleSheet(style or UITheme.INPUT_STYLE)
    return spin


def create_table_widget(parent=None, style=None):
    """Create a styled QTableWidget"""
    table = QTableWidget(parent)
    table.setStyleSheet(style or UITheme.TABLE_STYLE)
    return table


def ensure_table_visibility(table):
    """
    Ensure table is visible by clearing invalid graphics effects,
    setting safe defaults, and guaranteeing headers are shown.
    """
    # Clear any graphics effects that might cause invisibility
    if table.graphicsEffect():
        table.setGraphicsEffect(None)

    # Ensure headers are visible
    table.horizontalHeader().setVisible(True)
    table.verticalHeader().setVisible(False)

    # Reapply safe stylesheet
    table.setStyleSheet(UITheme.TABLE_STYLE)

    # Ensure table has valid dimensions
    if table.columnCount() == 0:
        table.setColumnCount(1)  # Fallback, but should be set by setup

    # Ensure row height is set
    table.verticalHeader().setDefaultSectionSize(35)


def setup_professional_table(table, headers, column_types=None):
    """
    Setup a QTableWidget with professional, enterprise-grade configuration.

    Args:
        table: QTableWidget instance
        headers: list of header strings
        column_types: list of column type strings ('id', 'date', 'text', 'numeric', 'status', 'action')
                     If None, defaults to 'text' for all
    """
    from PyQt6.QtWidgets import QHeaderView
    from PyQt6.QtCore import Qt

    # Basic configuration
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setSortingEnabled(True)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setDefaultSectionSize(35)  # Consistent row height

    # Column types default
    if column_types is None:
        column_types = ['text'] * len(headers)

    # Apply column configurations
    for col, col_type in enumerate(column_types):
        if col_type in ['id', 'date', 'numeric']:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        elif col_type == 'text':
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        elif col_type == 'action':
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(col, 100)  # Fixed width for actions
        elif col_type == 'status':
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

    # Stretch last non-action column
    for col in range(len(headers) - 1, -1, -1):
        if column_types[col] != 'action':
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            break

    # Ensure table visibility and remove any invalid effects
    ensure_table_visibility(table)


def set_table_empty_state(table, message="No records found"):
    """Set a placeholder message when table has no data"""
    table.setRowCount(1)
    empty_item = QTableWidgetItem(message)
    empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
    empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
    table.setItem(0, 0, empty_item)
    # Span across all columns
    table.setSpan(0, 0, 1, table.columnCount())


def create_professional_table_item(value, col_type='text', status_colors=None):
    """
    Create a QTableWidgetItem with proper formatting and alignment.

    Args:
        value: the value to display
        col_type: 'id', 'date', 'text', 'numeric', 'status', 'action'
        status_colors: dict for status colors, e.g. {'paid': 'green', 'pending': 'yellow'}
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor

    item = QTableWidgetItem()

    if col_type == 'numeric' and isinstance(value, (int, float)):
        text = f"{value:,.2f}"
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    elif col_type == 'status':
        text = str(value or '')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        if status_colors and text.lower() in status_colors:
            color_name = status_colors[text.lower()]
            if color_name == 'green':
                item.setForeground(QColor('#28a745'))
            elif color_name == 'yellow':
                item.setForeground(QColor('#ffc107'))
            elif color_name == 'red':
                item.setForeground(QColor('#dc3545'))
    else:
        text = str(value or '')
        if col_type == 'text':
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        elif col_type in ['id', 'date']:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    item.setText(text)
    return item


def create_table_item(text, editable=True):
    """Create a styled QTableWidgetItem"""
    item = QTableWidgetItem(text)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def create_dialog(title, parent=None, style=None):
    """Create a styled QDialog"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet(style or UITheme.DIALOG_STYLE)
    return dialog


def create_group_box(title, parent=None, style=None):
    """Create a styled QGroupBox"""
    group = QGroupBox(title, parent)
    group.setStyleSheet(style or UITheme.GROUP_BOX_STYLE)
    return group


def create_text_edit(parent=None, style=None):
    """Create a styled QTextEdit"""
    text_edit = QTextEdit(parent)
    text_edit.setStyleSheet(style or UITheme.INPUT_STYLE)
    return text_edit


def create_checkbox(text, parent=None, checked=False):
    """Create a styled QCheckBox"""
    checkbox = QCheckBox(text, parent)
    checkbox.setChecked(checked)
    checkbox.setStyleSheet(f"""
        QCheckBox {{
            color: {UITheme.TEXT};
            font-size: 11pt;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {UITheme.BORDER};
            border-radius: 3px;
            background: {UITheme.SURFACE};
        }}
        QCheckBox::indicator:checked {{
            background: {UITheme.PRIMARY_COLOR};
            border: 1px solid {UITheme.PRIMARY_COLOR};
        }}
    """)
    return checkbox


def create_radio_button(text, parent=None, checked=False):
    """Create a styled QRadioButton"""
    radio = QRadioButton(text, parent)
    radio.setChecked(checked)
    radio.setStyleSheet(f"""
        QRadioButton {{
            color: {UITheme.TEXT};
            font-size: 11pt;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {UITheme.BORDER};
            border-radius: 8px;
            background: {UITheme.SURFACE};
        }}
        QRadioButton::indicator:checked {{
            background: {UITheme.PRIMARY_COLOR};
            border: 1px solid {UITheme.PRIMARY_COLOR};
        }}
    """)
    return radio


def create_progress_bar(parent=None, style=None):
    """Create a styled QProgressBar"""
    progress = QProgressBar(parent)
    progress.setStyleSheet(style or f"""
        QProgressBar {{
            border: 1px solid {UITheme.BORDER};
            border-radius: 4px;
            text-align: center;
            background: {UITheme.SURFACE};
        }}
        QProgressBar::chunk {{
            background: {UITheme.PRIMARY_COLOR};
            border-radius: 3px;
        }}
    """)
    return progress


def create_slider(parent=None, orientation=Qt.Orientation.Horizontal, style=None):
    """Create a styled QSlider"""
    slider = QSlider(orientation, parent)
    slider.setStyleSheet(style or f"""
        QSlider::groove:horizontal {{
            border: 1px solid {UITheme.BORDER};
            height: 8px;
            background: {UITheme.SURFACE};
            margin: 2px 0;
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {UITheme.PRIMARY_COLOR};
            border: 1px solid {UITheme.PRIMARY_COLOR};
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {UITheme.SECONDARY_COLOR};
        }}
    """)
    return slider


def create_date_edit(parent=None, style=None):
    """Create a styled QDateEdit"""
    date_edit = QDateEdit(parent)
    date_edit.setStyleSheet(style or UITheme.INPUT_STYLE)
    return date_edit


def create_time_edit(parent=None, style=None):
    """Create a styled QTimeEdit"""
    time_edit = QTimeEdit(parent)
    time_edit.setStyleSheet(style or UITheme.INPUT_STYLE)
    return time_edit


def create_datetime_edit(parent=None, style=None):
    """Create a styled QDateTimeEdit"""
    datetime_edit = QDateTimeEdit(parent)
    datetime_edit.setStyleSheet(style or UITheme.INPUT_STYLE)
    return datetime_edit


def apply_theme_to_widget(widget, theme_type="default"):
    """Apply theme styling to an existing widget"""
    if isinstance(widget, QPushButton):
        widget.setStyleSheet(UITheme.BUTTON_STYLE)
        UIAnimations.apply_button_animations(widget)
    elif isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit)):
        widget.setStyleSheet(UITheme.INPUT_STYLE)
    elif isinstance(widget, QLabel):
        widget.setStyleSheet(UITheme.LABEL_STYLE)
    elif isinstance(widget, QTableWidget):
        widget.setStyleSheet(UITheme.TABLE_STYLE)
    elif isinstance(widget, QDialog):
        widget.setStyleSheet(UITheme.DIALOG_STYLE)
    elif isinstance(widget, QGroupBox):
        widget.setStyleSheet(UITheme.GROUP_BOX_STYLE)
    elif isinstance(widget, QTextEdit):
        widget.setStyleSheet(UITheme.INPUT_STYLE)
    elif isinstance(widget, QProgressBar):
        widget.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {UITheme.BORDER};
                border-radius: 4px;
                text-align: center;
                background: {UITheme.SURFACE};
            }}
            QProgressBar::chunk {{
                background: {UITheme.PRIMARY_COLOR};
                border-radius: 3px;
            }}
        """)
    elif isinstance(widget, QSlider):
        widget.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {UITheme.BORDER};
                height: 8px;
                background: {UITheme.SURFACE};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {UITheme.PRIMARY_COLOR};
                border: 1px solid {UITheme.PRIMARY_COLOR};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {UITheme.SECONDARY_COLOR};
            }}
        """)


def set_font_size(widget, size):
    """Set font size for a widget"""
    font = widget.font()
    font.setPointSize(size)
    widget.setFont(font)


def set_font_weight(widget, weight):
    """Set font weight for a widget"""
    font = widget.font()
    font.setWeight(weight)
    widget.setFont(font)