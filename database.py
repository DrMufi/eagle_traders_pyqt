import sqlite3
import os
import sys
import shutil

class Database:
    def __init__(self, db_path='eagle_traders.db'):
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            bundle_dir = sys._MEIPASS
            db_source = os.path.join(bundle_dir, 'eagle_traders.db')
            # Use a writable location for the database
            app_dir = os.path.dirname(sys.executable)
            self.db_path = os.path.join(app_dir, 'eagle_traders.db')
            # If database doesn't exist in app_dir, copy from bundle
            if not os.path.exists(self.db_path):
                shutil.copy2(db_source, self.db_path)
        else:
            self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                supplier_id INTEGER,
                is_import BOOLEAN DEFAULT 0,
                unit_price REAL NOT NULL,
                barcode TEXT,
                current_stock INTEGER DEFAULT 0,
                min_stock_level INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES Categories(id),
                FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
            )
        ''')

        # Add columns if not exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE Products ADD COLUMN current_stock INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE Products ADD COLUMN min_stock_level INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProductBatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                expiry_month INTEGER,
                expiry_year INTEGER,
                purchase_date DATE,
                cost_price REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES Products(id),
                UNIQUE(product_id, batch_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS StockLedger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('in', 'out', 'adjustment')),
                quantity INTEGER NOT NULL,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                reference_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES Products(id),
                FOREIGN KEY (batch_id) REFERENCES ProductBatches(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SalesTransactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                buyer_name TEXT,
                buyer_contact TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'cancelled')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')

        # Add columns if not exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE SalesTransactions ADD COLUMN buyer_name TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE SalesTransactions ADD COLUMN buyer_contact TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE SalesItems ADD COLUMN discount_percent REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SalesItems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES SalesTransactions(id),
                FOREIGN KEY (product_id) REFERENCES Products(id),
                FOREIGN KEY (batch_id) REFERENCES ProductBatches(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                customer_id INTEGER,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES SalesTransactions(id),
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ReturnItems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (return_id) REFERENCES Returns(id),
                FOREIGN KEY (product_id) REFERENCES Products(id),
                FOREIGN KEY (batch_id) REFERENCES ProductBatches(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CustomerLedger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                balance REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SupplierLedger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                balance REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GeneralLedger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL,
                balance REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS BarcodeConfigurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            product_id INTEGER,
            weight TEXT,
            expiry TEXT,
            width INTEGER,
            height INTEGER,
            barcode TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES Products(id)
        )''')

        # Add barcode column if not exist
        try:
            cursor.execute("ALTER TABLE BarcodeConfigurations ADD COLUMN barcode TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        cursor.execute('''CREATE TABLE IF NOT EXISTS CustomBarcodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Add product_id column if not exist
        try:
            cursor.execute("ALTER TABLE CustomBarcodes ADD COLUMN product_id INTEGER REFERENCES Products(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        cursor.execute('''CREATE TABLE IF NOT EXISTS Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT,
            salary REAL,
            hire_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PayrollTransactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES Employees(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON Products(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_supplier ON Products(supplier_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_batches_product ON ProductBatches(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_ledger_product ON StockLedger(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_ledger_batch ON StockLedger(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_customer ON SalesTransactions(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_items_sale ON SalesItems(sale_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_sale ON Returns(sale_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_customer ON Returns(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_return_items_return ON ReturnItems(return_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_ledger_customer ON CustomerLedger(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_supplier_ledger_supplier ON SupplierLedger(supplier_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payroll_employee ON PayrollTransactions(employee_id)')

        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM Users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                         ("admin", "admin123", "admin"))

        conn.commit()
        conn.close()

    def authenticate_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, role FROM Users WHERE username = ? AND password = ?",
                      (username, password))
        user = cursor.fetchone()
        conn.close()
        return user  # Returns (id, role) or None

    def change_password(self, username, old_password, new_password):
        conn = self.get_connection()
        cursor = conn.cursor()
        # First verify old password
        cursor.execute("SELECT id FROM Users WHERE username = ? AND password = ?",
                      (username, old_password))
        if cursor.fetchone():
            cursor.execute("UPDATE Users SET password = ? WHERE username = ?",
                         (new_password, username))
            conn.commit()
            success = True
        else:
            success = False
        conn.close()
        return success

    def create_user(self, username, password, role='user'):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                         (username, password, role))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False  # Username already exists
        conn.close()
        return success

    def get_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM Users")
        users = cursor.fetchall()
        conn.close()
        return users

    def delete_user(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

if __name__ == '__main__':
    db = Database()
    print("Database initialized.")