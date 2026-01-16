from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QGroupBox, QFormLayout, QMessageBox, QSpinBox, QScrollArea,
    QTabWidget, QTableWidget, QTableWidgetItem, QInputDialog, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QPainter, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import barcode
from barcode.writer import ImageWriter
import io
import sqlite3

class BarcodeSticker(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.all_custom_barcodes = []
        self.init_ui()

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

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Generate Barcode Tab
        self.create_generate_tab()

        # Saved Configurations Tab
        self.create_saved_tab()

        # Custom Barcodes Tab
        self.create_custom_tab()

        # Set the scroll area as the main widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_generate_tab(self):
        generate_tab = QWidget()
        self.tab_widget.addTab(generate_tab, "Generate Barcode")

        layout = QVBoxLayout(generate_tab)

        # Product selection
        select_group = QGroupBox("Select Product")
        select_layout = QFormLayout(select_group)

        # Product search
        product_search_layout = QHBoxLayout()
        product_search_layout.addWidget(QLabel("Search Product:"))
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Type to search products...")
        self.product_search.textChanged.connect(self.filter_products)
        product_search_layout.addWidget(self.product_search)
        select_layout.addRow(product_search_layout)

        self.product_combo = QComboBox()
        self.product_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.product_combo.setMinimumWidth(300)
        self.load_products()
        select_layout.addRow("Product:", self.product_combo)

        self.weight_edit = QLineEdit()
        select_layout.addRow("Weight:", self.weight_edit)

        self.expiry_edit = QLineEdit()
        select_layout.addRow("Expiry:", self.expiry_edit)

        barcode_layout = QHBoxLayout()
        self.barcode_combo = QComboBox()
        self.barcode_combo.addItem("Manual", None)
        barcode_layout.addWidget(self.barcode_combo)

        self.manual_barcode_edit = QLineEdit()
        self.manual_barcode_edit.setPlaceholderText("Enter manual barcode")
        barcode_layout.addWidget(self.manual_barcode_edit)

        select_layout.addRow("Barcode:", barcode_layout)
        self.barcode_combo.currentIndexChanged.connect(self.on_barcode_combo_changed)
        self.load_custom_barcodes_for_combo()

        # Sticker size controls
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 1000)
        self.width_spin.setValue(300)
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 1000)
        self.height_spin.setValue(150)
        size_layout.addWidget(self.height_spin)

        select_layout.addRow("Sticker Size:", size_layout)

        layout.addWidget(select_group)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Barcode")
        self.generate_btn.clicked.connect(self.generate_barcode)
        buttons_layout.addWidget(self.generate_btn)

        self.save_config_btn = QPushButton("Save Configuration")
        self.save_config_btn.clicked.connect(self.save_configuration)
        buttons_layout.addWidget(self.save_config_btn)

        layout.addLayout(buttons_layout)

        # Barcode display
        self.barcode_label = QLabel()
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.barcode_label)

        # Print button
        self.print_btn = QPushButton("Print Sticker")
        self.print_btn.clicked.connect(self.print_sticker)
        self.print_btn.setEnabled(False)
        layout.addWidget(self.print_btn)

        layout.addStretch()

    def create_saved_tab(self):
        saved_tab = QWidget()
        self.tab_widget.addTab(saved_tab, "Saved Configurations")

        layout = QVBoxLayout(saved_tab)

        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.config_search = QLineEdit()
        self.config_search.setPlaceholderText("Search by name or product...")
        self.config_search.textChanged.connect(self.filter_configurations)
        search_layout.addWidget(self.config_search)
        layout.addLayout(search_layout)

        # Configurations table
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(4)
        self.config_table.setHorizontalHeaderLabels(["Name", "Product", "Barcode", "Created"])
        self.config_table.horizontalHeader().setStretchLastSection(True)
        self.config_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.config_table)

        # Buttons
        buttons_layout = QHBoxLayout()
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self.load_configuration)
        buttons_layout.addWidget(load_btn)

        delete_btn = QPushButton("Delete Configuration")
        delete_btn.clicked.connect(self.delete_configuration)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.load_configurations()

    def create_custom_tab(self):
        custom_tab = QWidget()
        self.tab_widget.addTab(custom_tab, "Custom Barcodes")

        layout = QVBoxLayout(custom_tab)

        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.custom_search = QLineEdit()
        self.custom_search.setPlaceholderText("Search by name or code...")
        self.custom_search.textChanged.connect(self.filter_custom_barcodes)
        search_layout.addWidget(self.custom_search)
        layout.addLayout(search_layout)

        # Custom barcodes table
        self.custom_table = QTableWidget()
        self.custom_table.setColumnCount(4)
        self.custom_table.setHorizontalHeaderLabels(["Name", "Code", "Product", "Created"])
        self.custom_table.horizontalHeader().setStretchLastSection(True)
        self.custom_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.custom_table)

        # Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Custom Barcode")
        add_btn.clicked.connect(self.add_custom_barcode)
        buttons_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Custom Barcode")
        edit_btn.clicked.connect(self.edit_custom_barcode)
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Custom Barcode")
        delete_btn.clicked.connect(self.delete_custom_barcode)
        buttons_layout.addWidget(delete_btn)

        generate_sticker_btn = QPushButton("Generate Sticker")
        generate_sticker_btn.clicked.connect(self.generate_custom_sticker)
        buttons_layout.addWidget(generate_sticker_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.load_custom_barcodes()

    def load_custom_barcodes(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cb.id, cb.name, cb.code, p.name, cb.created_at FROM CustomBarcodes cb LEFT JOIN Products p ON cb.product_id = p.id ORDER BY cb.created_at DESC")
        self.all_custom_barcodes = cursor.fetchall()
        conn.close()
        self.filter_custom_barcodes()

    def filter_custom_barcodes(self):
        search_text = self.custom_search.text().lower()
        filtered_barcodes = [bc for bc in self.all_custom_barcodes
                            if search_text in bc[1].lower() or search_text in bc[2].lower() or (bc[3] and search_text in bc[3].lower())]

        self.custom_table.setRowCount(len(filtered_barcodes))
        for row, (bc_id, name, code, prod_name, created) in enumerate(filtered_barcodes):
            self.custom_table.setItem(row, 0, QTableWidgetItem(name))
            self.custom_table.setItem(row, 1, QTableWidgetItem(code))
            self.custom_table.setItem(row, 2, QTableWidgetItem(prod_name or ""))
            self.custom_table.setItem(row, 3, QTableWidgetItem(created.split(' ')[0]))  # Date only

    def add_custom_barcode(self):
        name, ok = QInputDialog.getText(self, "Add Custom Barcode", "Enter barcode name:")
        if not ok or not name.strip():
            return
        code, ok = QInputDialog.getText(self, "Add Custom Barcode", "Enter barcode code:")
        if not ok or not code.strip():
            return

        # Product selection
        product_names = ["None"] + [name for _, name in self.all_products]
        selected_product, ok = QInputDialog.getItem(self, "Select Product", "Product:", product_names, 0, False)
        if not ok:
            return
        product_id = None if selected_product == "None" else next((id for id, name in self.all_products if name == selected_product), None)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO CustomBarcodes (name, code, product_id) VALUES (?, ?, ?)", (name.strip(), code.strip(), product_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Custom barcode added successfully.")
            self.load_custom_barcodes()
            self.load_custom_barcodes_for_combo()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Barcode name already exists.")
        finally:
            conn.close()

    def edit_custom_barcode(self):
        current_row = self.custom_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a custom barcode to edit.")
            return

        name = self.custom_table.item(current_row, 0).text()
        code = self.custom_table.item(current_row, 1).text()
        prod_name = self.custom_table.item(current_row, 2).text()

        new_name, ok = QInputDialog.getText(self, "Edit Custom Barcode", "Enter new name:", text=name)
        if not ok or not new_name.strip():
            return
        new_code, ok = QInputDialog.getText(self, "Edit Custom Barcode", "Enter new code:", text=code)
        if not ok or not new_code.strip():
            return

        # Get current product_id
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT product_id FROM CustomBarcodes WHERE name = ?", (name,))
        current_product_id = cursor.fetchone()[0]
        conn.close()

        # Product selection
        product_names = ["None"] + [name for _, name in self.all_products]
        current_product_name = "None" if not current_product_id else next((name for id, name in self.all_products if id == current_product_id), "None")
        index = product_names.index(current_product_name) if current_product_name in product_names else 0
        selected_product, ok = QInputDialog.getItem(self, "Select Product", "Product:", product_names, index, False)
        if not ok:
            return
        product_id = None if selected_product == "None" else next((id for id, name in self.all_products if name == selected_product), None)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE CustomBarcodes SET name = ?, code = ?, product_id = ? WHERE name = ?", (new_name.strip(), new_code.strip(), product_id, name))
            conn.commit()
            QMessageBox.information(self, "Success", "Custom barcode updated successfully.")
            self.load_custom_barcodes()
            self.load_custom_barcodes_for_combo()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Barcode name already exists.")
        finally:
            conn.close()

    def delete_custom_barcode(self):
        current_row = self.custom_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a custom barcode to delete.")
            return

        name = self.custom_table.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Confirm", f"Delete custom barcode '{name}'?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM CustomBarcodes WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            self.load_custom_barcodes()
            self.load_custom_barcodes_for_combo()
            QMessageBox.information(self, "Success", "Custom barcode deleted.")

    def generate_custom_sticker(self):
        current_row = self.custom_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a custom barcode to generate sticker.")
            return

        name = self.custom_table.item(current_row, 0).text()
        code = self.custom_table.item(current_row, 1).text()
        prod_name = self.custom_table.item(current_row, 2).text()

        # Get product_id if any
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT product_id FROM CustomBarcodes WHERE name = ?", (name,))
        product_id = cursor.fetchone()[0]
        conn.close()

        if product_id:
            # Use product name
            pass  # prod_name is already set
        else:
            prod_name = name  # Use custom name as product name

        barcode_data = code

        try:
            # Generate Code128 barcode
            bc = barcode.get('code128', barcode_data, writer=ImageWriter())
            fp = io.BytesIO()
            bc.write(fp)
            fp.seek(0)

            barcode_pixmap = QPixmap()
            barcode_pixmap.loadFromData(fp.getvalue())
        except Exception as e:
            QMessageBox.critical(self, "Barcode Error", f"Failed to generate barcode: {str(e)}")
            return

        # Get sticker dimensions (use defaults)
        sticker_width = 300
        sticker_height = 150

        # Create combined pixmap
        combined_pixmap = QPixmap(sticker_width, sticker_height)
        combined_pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(combined_pixmap)
        painter.setFont(QFont('Arial', 10))

        # Draw text above
        info_text = f"{prod_name}"
        text_height = 20
        painter.drawText(0, 0, sticker_width, text_height, Qt.AlignmentFlag.AlignCenter, info_text)

        # Draw barcode
        barcode_y = text_height + 5
        barcode_max_height = int(sticker_height * 0.6)
        scaled_barcode = barcode_pixmap.scaled(sticker_width - 20, barcode_max_height, Qt.AspectRatioMode.KeepAspectRatio)
        barcode_x = (sticker_width - scaled_barcode.width()) // 2
        painter.drawPixmap(barcode_x, barcode_y, scaled_barcode)

        # Draw code below
        manual_y = barcode_y + scaled_barcode.height() + 10
        painter.setFont(QFont('Arial', 8))
        manual_text = f"Code: {barcode_data}"
        painter.drawText(0, manual_y, sticker_width, 15, Qt.AlignmentFlag.AlignCenter, manual_text)

        painter.end()

        self.barcode_label.setPixmap(combined_pixmap)
        self.print_btn.setEnabled(True)
        self.barcode_data = barcode_data
        self.prod_name = prod_name
        self.weight = ""
        self.expiry = ""
        self.combined_pixmap = combined_pixmap

        # Switch to generate tab to show
        self.tab_widget.setCurrentIndex(0)

    def load_custom_barcodes_for_combo(self):
        self.barcode_combo.clear()
        self.barcode_combo.addItem("Manual", None)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, code FROM CustomBarcodes ORDER BY name")
        for name, code in cursor.fetchall():
            self.barcode_combo.addItem(name, code)
        conn.close()

    def on_barcode_combo_changed(self):
        if self.barcode_combo.currentData() is None:
            self.manual_barcode_edit.setEnabled(True)
        else:
            self.manual_barcode_edit.setEnabled(False)
            self.manual_barcode_edit.clear()

    def load_configurations(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bc.id, bc.name, p.name, bc.barcode, bc.created_at
            FROM BarcodeConfigurations bc
            JOIN Products p ON bc.product_id = p.id
            ORDER BY bc.created_at DESC
        """)
        self.all_configs = cursor.fetchall()
        conn.close()
        self.filter_configurations()

    def filter_configurations(self):
        search_text = self.config_search.text().lower()
        filtered_configs = [config for config in self.all_configs
                           if search_text in config[1].lower() or search_text in config[2].lower() or (config[3] and search_text in config[3].lower())]

        self.config_table.setRowCount(len(filtered_configs))
        for row, (config_id, name, prod_name, barcode, created) in enumerate(filtered_configs):
            self.config_table.setItem(row, 0, QTableWidgetItem(name))
            self.config_table.setItem(row, 1, QTableWidgetItem(prod_name))
            self.config_table.setItem(row, 2, QTableWidgetItem(barcode or ""))
            self.config_table.setItem(row, 3, QTableWidgetItem(created.split(' ')[0]))  # Date only

    def load_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Products ORDER BY name")
        self.all_products = cursor.fetchall()
        conn.close()
        self.filter_products()

    def filter_products(self):
        search_text = self.product_search.text().lower()
        filtered_products = [(prod_id, name) for prod_id, name in self.all_products
                           if search_text in name.lower()]

        self.product_combo.clear()
        self.product_combo.addItem("Select Product", None)
        for prod_id, name in filtered_products:
            self.product_combo.addItem(name, prod_id)

    def generate_barcode(self):
        prod_id = self.product_combo.currentData()
        if not prod_id:
            QMessageBox.warning(self, "Error", "Select a product.")
            return

        weight = self.weight_edit.text().strip()
        expiry = self.expiry_edit.text().strip()

        # Get product name and barcode
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, barcode FROM Products WHERE id = ?", (prod_id,))
        row = cursor.fetchone()
        conn.close()
        prod_name, prod_barcode = row[0], row[1]

        # Determine barcode data
        selected_code = self.barcode_combo.currentData()
        if selected_code is None:
            manual_barcode = self.manual_barcode_edit.text().strip()
            if manual_barcode:
                barcode_data = manual_barcode
            elif prod_barcode:
                barcode_data = prod_barcode
            else:
                barcode_data = f"{prod_name}-{prod_id:06d}"
        else:
            barcode_data = selected_code

        try:
            # Generate Code128 barcode
            bc = barcode.get('code128', barcode_data, writer=ImageWriter())
            fp = io.BytesIO()
            bc.write(fp)
            fp.seek(0)

            barcode_pixmap = QPixmap()
            barcode_pixmap.loadFromData(fp.getvalue())
        except Exception as e:
            QMessageBox.critical(self, "Barcode Error", f"Failed to generate barcode: {str(e)}")
            return

        # Get sticker dimensions
        sticker_width = self.width_spin.value()
        sticker_height = self.height_spin.value()

        # Create a combined pixmap with adjustable size
        combined_pixmap = QPixmap(sticker_width, sticker_height)
        combined_pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(combined_pixmap)
        painter.setFont(QFont('Arial', 10))

        # Draw text above in one line
        info_text = f"{prod_name} | Expiry: {expiry} | Weight: {weight}"
        text_height = 20
        painter.drawText(0, 0, sticker_width, text_height, Qt.AlignmentFlag.AlignCenter, info_text)

        # Draw barcode in middle
        barcode_y = text_height + 5
        barcode_max_height = int(sticker_height * 0.6)  # 60% of height for barcode
        scaled_barcode = barcode_pixmap.scaled(sticker_width - 20, barcode_max_height, Qt.AspectRatioMode.KeepAspectRatio)
        barcode_x = (sticker_width - scaled_barcode.width()) // 2
        painter.drawPixmap(barcode_x, barcode_y, scaled_barcode)

        # Draw manual code below barcode
        manual_y = barcode_y + scaled_barcode.height() + 10
        painter.setFont(QFont('Arial', 8))
        manual_text = f"Code: {barcode_data}"
        painter.drawText(0, manual_y, sticker_width, 15, Qt.AlignmentFlag.AlignCenter, manual_text)

        painter.end()

        self.barcode_label.setPixmap(combined_pixmap)

        self.print_btn.setEnabled(True)
        self.barcode_data = barcode_data
        self.prod_name = prod_name
        self.weight = weight
        self.expiry = expiry
        self.combined_pixmap = combined_pixmap

    def save_configuration(self):
        name, ok = QInputDialog.getText(self, "Save Configuration", "Enter configuration name:")
        if not ok or not name.strip():
            return

        prod_id = self.product_combo.currentData()
        if not prod_id:
            QMessageBox.warning(self, "Error", "Select a product first.")
            return

        weight = self.weight_edit.text().strip()
        expiry = self.expiry_edit.text().strip()
        selected_code = self.barcode_combo.currentData()
        if selected_code is None:
            manual_barcode = self.manual_barcode_edit.text().strip()
        else:
            manual_barcode = selected_code
        width = self.width_spin.value()
        height = self.height_spin.value()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO BarcodeConfigurations (name, product_id, weight, expiry, width, height, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), prod_id, weight, expiry, width, height, manual_barcode))
            conn.commit()
            QMessageBox.information(self, "Success", "Configuration saved successfully.")
            self.load_configurations()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Configuration name already exists.")
        finally:
            conn.close()

    def load_configuration(self):
        current_row = self.config_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a configuration to load.")
            return

        config_name = self.config_table.item(current_row, 0).text()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bc.product_id, bc.weight, bc.expiry, bc.width, bc.height, bc.barcode, p.name
            FROM BarcodeConfigurations bc
            JOIN Products p ON bc.product_id = p.id
            WHERE bc.name = ?
        """, (config_name,))
        config = cursor.fetchone()
        conn.close()

        if config:
            prod_id, weight, expiry, width, height, barcode, prod_name = config
            self.product_combo.setCurrentIndex(self.product_combo.findData(prod_id))
            self.weight_edit.setText(weight or "")
            self.expiry_edit.setText(expiry or "")
            if barcode:
                index = self.barcode_combo.findData(barcode)
                if index >= 0:
                    self.barcode_combo.setCurrentIndex(index)
                else:
                    self.barcode_combo.setCurrentIndex(0)  # Manual
                    self.manual_barcode_edit.setText(barcode)
            else:
                self.barcode_combo.setCurrentIndex(0)
                self.manual_barcode_edit.clear()
            self.width_spin.setValue(width)
            self.height_spin.setValue(height)
            self.tab_widget.setCurrentIndex(0)  # Switch to generate tab
            QMessageBox.information(self, "Success", f"Configuration '{config_name}' loaded.")

    def delete_configuration(self):
        current_row = self.config_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Select a configuration to delete.")
            return

        config_name = self.config_table.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Confirm", f"Delete configuration '{config_name}'?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM BarcodeConfigurations WHERE name = ?", (config_name,))
            conn.commit()
            conn.close()
            self.load_configurations()
            QMessageBox.information(self, "Success", "Configuration deleted.")

    def print_sticker(self):
        if not hasattr(self, 'combined_pixmap'):
            return

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)

            # Draw the combined pixmap at actual size
            painter.drawPixmap(0, 0, self.combined_pixmap)

            painter.end()