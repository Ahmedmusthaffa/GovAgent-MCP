import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "company.db")

def seed():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Customers Table (Public to all roles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        contact_email TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        account_tier TEXT NOT NULL
    );
    """)

    # 2. Orders Table (Public to all roles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_amount REAL NOT NULL,
        status TEXT NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # 3. Executive Salaries Table (RESTRICTED - Managers / Admins only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS executive_salaries (
        employee_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        job_title TEXT NOT NULL,
        annual_salary_usd REAL NOT NULL,
        annual_bonus_usd REAL NOT NULL
    );
    """)

    # Clear old data if any
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM executive_salaries")

    # Insert Sample Customers
    customers_data = [
        (1, "Acme Corporation", "contact@acme.com", "+1-555-0101", "Enterprise Tier"),
        (2, "TechNova Global", "billing@technova.io", "+1-555-0102", "Growth Tier"),
        (3, "Pacific Logistics", "ops@pacificlogistics.com", "+1-555-0103", "Standard Tier"),
        (4, "Apex Healthcare Systems", "procurement@apexhealth.org", "+1-555-0104", "Enterprise Tier"),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers_data)

    # Insert Sample Orders
    orders_data = [
        (101, 1, 15400.0, "Delivered - Closed", "2026-11-18"),
        (102, 2, 420.0, "Disputed - Pending Refund", "2026-11-23"),
        (103, 3, 2800.0, "In Transit - Delayed", "2026-11-24"),
        (104, 4, 890.0, "Disputed - Pending Refund", "2026-11-24"),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders_data)

    # Insert Confidential Salaries
    salaries_data = [
        (1, "Sarah Jenkins", "Chief Executive Officer (CEO)", 350000.0, 85000.0),
        (2, "David Chen", "Chief Technology Officer (CTO)", 280000.0, 50000.0),
        (3, "Elena Vance", "VP of Engineering", 220000.0, 35000.0),
        (4, "Marcus Vance", "Chief Financial Officer (CFO)", 265000.0, 45000.0),
    ]
    cursor.executemany("INSERT INTO executive_salaries VALUES (?, ?, ?, ?, ?)", salaries_data)

    conn.commit()
    conn.close()
    print(f"[OK] Database successfully initialized at: {db_path}")

if __name__ == "__main__":
    seed()
