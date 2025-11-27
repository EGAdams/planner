
# Nonprofit Finance DB — Build & Use Guide (MySQL + Python)

This guide is for your assistant to **build and use** the new MySQL database with a clean Python package that provides **Create / Read / Update / Delete** (CRUD) operations and a couple of demos.

It includes:
- Full **directory structure**
- All required `__init__.py` files
- Ready-to-run **Python code** (repositories/DAOs, models, connection pool)
- A script to **initialize the database** (creates schema + seed data)
- A **demo** script showing CRUD usage
- Minimal dependencies

> **Prereqs**
> - MySQL 8.0+ running locally or reachable over the network
> - Python 3.9+ (3.11 recommended)
> - An account on MySQL with privileges to create databases

---

## 1) Directory Structure

Create this tree (all files provided below):

```
nonprofit_finance_db/
├─ .env.example
├─ requirements.txt
├─ README.md  (this file)
├─ scripts/
│  ├─ init_db.py
│  ├─ demo.py
│  └─ run_report.py
└─ app/
   ├─ __init__.py
   ├─ config.py
   ├─ db/
   │  ├─ __init__.py
   │  └─ pool.py
   ├─ models/
   │  ├─ __init__.py
   │  ├─ base.py
   │  ├─ organization.py
   │  ├─ contact.py
   │  ├─ category.py
   │  ├─ expense.py
   │  ├─ payment.py
   │  └─ report.py
   └─ repositories/
      ├─ __init__.py
      ├─ base.py
      ├─ organizations.py
      ├─ contacts.py
      ├─ categories.py
      ├─ expenses.py
      ├─ payments.py
      └─ reports.py
```

---

## 2) Setup

```bash
# From the directory where you want the project
mkdir -p nonprofit_finance_db && cd nonprofit_finance_db

# (Optional) create venv
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Create files from this README (copy content below) or use your automation
# Then install deps:
pip install -r requirements.txt
```

**Env file:** copy `.env.example` → `.env` and fill credentials.

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=changeme
DB_NAME=nonprofit_finance
POOL_SIZE=5
```

---

## 3) Initialize Database (schema + sample data)

This runs a safe, idempotent initializer that **drops and recreates** the database `nonprofit_finance`, creates tables and views, and inserts sample data.

```bash
python scripts/init_db.py
```

If it prints `✅ Database initialized`, you’re good.

---

## 4) Demo: basic CRUD

```bash
python scripts/demo.py
```

What it does:
- Lists current balances per org (from `vw_balance_by_org`)
- Creates a new expense
- Reads it back, updates it, and deletes it
- Shows monthly summaries

---

## 5) Python Packages & Code

> **All `__init__.py` files are included**. Your automation should create each file with the exact content shown.

### `requirements.txt`

```txt
mysql-connector-python==9.0.0
python-dotenv==1.0.1
```

### `.env.example`

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=changeme
DB_NAME=nonprofit_finance
POOL_SIZE=5
```

---

### `app/__init__.py`

```python
# Makes 'app' a package.
```

### `app/config.py`

```python
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("DB_PORT", "3306"))
    user: str = os.getenv("DB_USER", "root")
    password: str = os.getenv("DB_PASSWORD", "")
    database: str = os.getenv("DB_NAME", "nonprofit_finance")
    pool_size: int = int(os.getenv("POOL_SIZE", "5"))

settings = Settings()
```

---

### `app/db/__init__.py`

```python
# Export the get_connection function for convenience
from .pool import get_connection, query_one, query_all, execute
__all__ = ["get_connection", "query_one", "query_all", "execute"]
```

### `app/db/pool.py`

```python
from typing import Any, Optional, Tuple, List
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from app.config import settings

_pool: Optional[MySQLConnectionPool] = None

def _ensure_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name="np_pool",
            pool_size=settings.pool_size,
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=settings.password,
            database=settings.database,
            autocommit=False,
        )
    return _pool

def get_connection():
    pool = _ensure_pool()
    return pool.get_connection()

def query_one(sql: str, params: Optional[Tuple[Any, ...]] = None):
    with get_connection() as cnx:
        with cnx.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def query_all(sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[dict]:
    with get_connection() as cnx:
        with cnx.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def execute(sql: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid if available, else affected rows."""
    with get_connection() as cnx:
        with cnx.cursor() as cur:
            cur.execute(sql, params or ())
            last_id = cur.lastrowid
            cnx.commit()
            return last_id if last_id else cur.rowcount
```

---

### `app/models/__init__.py`

```python
# Re-export models for convenience
from .base import ID
from .organization import Organization
from .contact import Contact
from .category import Category
from .expense import Expense
from .payment import Payment
from .report import Report

__all__ = [
    "ID",
    "Organization",
    "Contact",
    "Category",
    "Expense",
    "Payment",
    "Report",
]
```

### `app/models/base.py`

```python
from typing import NewType
ID = NewType("ID", int)
```

### `app/models/organization.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Organization:
    id: Optional[ID]
    name: str
    type: str  # 'NONPROFIT' | 'PERSONAL'
```

### `app/models/contact.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Contact:
    id: Optional[ID]
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_type: str = "PERSON"  # 'PERSON' | 'ORG'
```

### `app/models/category.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Category:
    id: Optional[ID]
    name: str
    kind: str  # 'EXPENSE' | 'INCOME'
    is_active: bool = True
```

### `app/models/expense.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Expense:
    id: Optional[ID]
    org_id: int
    expense_date: str  # YYYY-MM-DD
    amount: float
    category_id: int
    description: Optional[str] = None
    paid_by_contact_id: Optional[int] = None
    method: str = "OTHER"  # 'CASH' | 'CARD' | 'BANK' | 'OTHER'
    receipt_url: Optional[str] = None
```

### `app/models/payment.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Payment:
    id: Optional[ID]
    org_id: int
    payment_date: str  # YYYY-MM-DD
    amount: float
    source_contact_id: Optional[int]
    type: str  # 'DONATION' | 'GRANT' | 'REIMBURSEMENT' | 'OTHER'
    notes: Optional[str] = None
```

### `app/models/report.py`

```python
from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Report:
    id: Optional[ID]
    title: str
    date_created: str  # YYYY-MM-DD
    start_date: str    # YYYY-MM-DD
    end_date: str      # YYYY-MM-DD
    notes: Optional[str] = None
    file_url: Optional[str] = None
```

---

### `app/repositories/__init__.py`

```python
from .organizations import OrganizationRepository
from .contacts import ContactRepository
from .categories import CategoryRepository
from .expenses import ExpenseRepository
from .payments import PaymentRepository
from .reports import ReportRepository

__all__ = [
    "OrganizationRepository",
    "ContactRepository",
    "CategoryRepository",
    "ExpenseRepository",
    "PaymentRepository",
    "ReportRepository",
]
```

### `app/repositories/base.py`

```python
from typing import Any, Dict, List, Optional, Tuple
from app.db import query_one, query_all, execute

class BaseRepository:
    table: str
    pk: str = "id"

    def get(self, _id: int) -> Optional[dict]:
        sql = f"SELECT * FROM {self.table} WHERE {self.pk}=%s"
        return query_one(sql, (_id,))

    def list(self, where: str = "", params: Tuple = (), limit: int = 100, offset: int = 0) -> List[dict]:
        sql = f"SELECT * FROM {self.table}"
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
        return query_all(sql, (*params, limit, offset))

    def delete(self, _id: int) -> int:
        sql = f"DELETE FROM {self.table} WHERE {self.pk}=%s"
        return execute(sql, (_id,))

    def insert(self, data: Dict[str, Any]) -> int:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        return execute(sql, tuple(data.values()))

    def update(self, _id: int, data: Dict[str, Any]) -> int:
        sets = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {self.table} SET {sets} WHERE {self.pk}=%s"
        return execute(sql, (*data.values(), _id))
```

### `app/repositories/organizations.py`

```python
from .base import BaseRepository

class OrganizationRepository(BaseRepository):
    table = "organizations"
```

### `app/repositories/contacts.py`

```python
from .base import BaseRepository

class ContactRepository(BaseRepository):
    table = "contacts"
```

### `app/repositories/categories.py`

```python
from .base import BaseRepository

class CategoryRepository(BaseRepository):
    table = "categories"
```

### `app/repositories/expenses.py`

```python
from typing import List
from .base import BaseRepository
from app.db import query_all

class ExpenseRepository(BaseRepository):
    table = "expenses"

    def list_by_period(self, org_id: int, start: str, end: str) -> List[dict]:
        where = "org_id=%s AND expense_date BETWEEN %s AND %s"
        return self.list(where, (org_id, start, end), limit=1000)

    def sum_by_category(self, org_id: int, start: str, end: str) -> List[dict]:
        sql = """
        SELECT c.name AS category, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON c.id=e.category_id
        WHERE e.org_id=%s AND e.expense_date BETWEEN %s AND %s
        GROUP BY c.name
        ORDER BY total DESC
        """
        return query_all(sql, (org_id, start, end))
```

### `app/repositories/payments.py`

```python
from typing import List
from .base import BaseRepository
from app.db import query_all

class PaymentRepository(BaseRepository):
    table = "payments"

    def sum_by_type(self, org_id: int, start: str, end: str) -> List[dict]:
        sql = """
        SELECT p.type AS payment_type, SUM(p.amount) AS total
        FROM payments p
        WHERE p.org_id=%s AND p.payment_date BETWEEN %s AND %s
        GROUP BY p.type
        ORDER BY total DESC
        """
        return query_all(sql, (org_id, start, end))
```

### `app/repositories/reports.py`

```python
from .base import BaseRepository

class ReportRepository(BaseRepository):
    table = "reports"
```

---

## 6) Scripts

### `scripts/init_db.py`

This script **drops & recreates** the database, tables, views, and inserts sample data exactly as designed.

```python
import mysql.connector
from app.config import settings

SCHEMA_SQL = r"""
-- Nonprofit finance starter DB (MySQL 8.0+)
DROP DATABASE IF EXISTS nonprofit_finance;
CREATE DATABASE nonprofit_finance CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE nonprofit_finance;

CREATE TABLE organizations (
  id        BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name      VARCHAR(120) NOT NULL UNIQUE,
  type      ENUM('NONPROFIT','PERSONAL') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE contacts (
  id           BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name         VARCHAR(160) NOT NULL,
  email        VARCHAR(190) NULL,
  phone        VARCHAR(40)  NULL,
  contact_type ENUM('PERSON','ORG') NOT NULL DEFAULT 'PERSON',
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_contacts_name (name)
) ENGINE=InnoDB;

CREATE TABLE categories (
  id         BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(100) NOT NULL,
  kind       ENUM('EXPENSE','INCOME') NOT NULL,
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uq_categories_name_kind (name, kind)
) ENGINE=InnoDB;

CREATE TABLE expenses (
  id                 BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  org_id             BIGINT UNSIGNED NOT NULL,
  expense_date       DATE NOT NULL,
  amount             DECIMAL(12,2) NOT NULL,
  category_id        BIGINT UNSIGNED NOT NULL,
  description        VARCHAR(255),
  paid_by_contact_id BIGINT UNSIGNED NULL,
  method             ENUM('CASH','CARD','BANK','OTHER') NOT NULL DEFAULT 'OTHER',
  receipt_url        VARCHAR(500),
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_expense_amount_pos CHECK (amount >= 0),
  CONSTRAINT fk_expenses_org    FOREIGN KEY (org_id)      REFERENCES organizations(id),
  CONSTRAINT fk_expenses_cat    FOREIGN KEY (category_id) REFERENCES categories(id),
  CONSTRAINT fk_expenses_paidby FOREIGN KEY (paid_by_contact_id) REFERENCES contacts(id),
  INDEX idx_expenses_org_date (org_id, expense_date),
  INDEX idx_expenses_cat (category_id)
) ENGINE=InnoDB;

CREATE TABLE payments (
  id                BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  org_id            BIGINT UNSIGNED NOT NULL,
  payment_date      DATE NOT NULL,
  amount            DECIMAL(12,2) NOT NULL,
  source_contact_id BIGINT UNSIGNED NULL,
  type              ENUM('DONATION','GRANT','REIMBURSEMENT','OTHER') NOT NULL,
  notes             VARCHAR(255),
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_payment_amount_pos CHECK (amount >= 0),
  CONSTRAINT fk_payments_org    FOREIGN KEY (org_id)            REFERENCES organizations(id),
  CONSTRAINT fk_payments_source FOREIGN KEY (source_contact_id) REFERENCES contacts(id),
  INDEX idx_payments_org_date (org_id, payment_date),
  INDEX idx_payments_type (type)
) ENGINE=InnoDB;

CREATE TABLE reports (
  id           BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  title        VARCHAR(160) NOT NULL,
  date_created DATE NOT NULL,
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  notes        VARCHAR(255),
  file_url     VARCHAR(500),
  CONSTRAINT chk_report_dates CHECK (start_date <= end_date)
) ENGINE=InnoDB;

CREATE OR REPLACE VIEW vw_balance_by_org AS
SELECT
  o.id AS org_id,
  o.name AS org_name,
  o.type AS org_type,
  IFNULL((SELECT SUM(p.amount) FROM payments p WHERE p.org_id = o.id),0) AS total_payments,
  IFNULL((SELECT SUM(e.amount) FROM expenses e WHERE e.org_id = o.id),0) AS total_expenses,
  IFNULL((SELECT SUM(p.amount) FROM payments p WHERE p.org_id = o.id),0) -
  IFNULL((SELECT SUM(e.amount) FROM expenses e WHERE e.org_id = o.id),0) AS net_balance
FROM organizations o;

CREATE OR REPLACE VIEW vw_monthly_expense_summary AS
SELECT
  o.name AS org_name,
  DATE_FORMAT(e.expense_date, '%Y-%m-01') AS month_start,
  c.name AS category,
  SUM(e.amount) AS total_amount
FROM expenses e
JOIN organizations o ON o.id = e.org_id
JOIN categories c ON c.id = e.category_id AND c.kind = 'EXPENSE'
GROUP BY o.name, DATE_FORMAT(e.expense_date, '%Y-%m-01'), c.name;

CREATE OR REPLACE VIEW vw_monthly_payment_summary AS
SELECT
  o.name AS org_name,
  DATE_FORMAT(p.payment_date, '%Y-%m-01') AS month_start,
  p.type AS payment_type,
  SUM(p.amount) AS total_amount
FROM payments p
JOIN organizations o ON o.id = p.org_id
GROUP BY o.name, DATE_FORMAT(p.payment_date, '%Y-%m-01'), p.type;

CREATE OR REPLACE VIEW vw_report_financials AS
SELECT
  r.id AS report_id,
  r.title,
  r.start_date,
  r.end_date,
  (SELECT IFNULL(SUM(e.amount),0)
     FROM expenses e
     JOIN organizations o ON o.id = e.org_id
    WHERE e.expense_date BETWEEN r.start_date AND r.end_date
      AND o.type = 'NONPROFIT') AS nonprofit_expenses,
  (SELECT IFNULL(SUM(e.amount),0)
     FROM expenses e
     JOIN organizations o ON o.id = e.org_id
    WHERE e.expense_date BETWEEN r.start_date AND r.end_date
      AND o.type = 'PERSONAL') AS personal_expenses,
  (SELECT IFNULL(SUM(p.amount),0)
     FROM payments p
    WHERE p.payment_date BETWEEN r.start_date AND r.end_date) AS total_payments,
  (SELECT IFNULL(SUM(p.amount),0)
     FROM payments p
    WHERE p.payment_date BETWEEN r.start_date AND r.end_date
      AND p.type = 'DONATION') AS donations,
  (SELECT IFNULL(SUM(p.amount),0)
     FROM payments p
    WHERE p.payment_date BETWEEN r.start_date AND r.end_date
      AND p.type = 'GRANT') AS grants,
  ((SELECT IFNULL(SUM(p.amount),0) FROM payments p
     WHERE p.payment_date BETWEEN r.start_date AND r.end_date)
   -
   (SELECT IFNULL(SUM(e.amount),0) FROM expenses e
     WHERE e.expense_date BETWEEN r.start_date AND r.end_date)) AS net_all_orgs
FROM reports r;

INSERT INTO organizations (name, type) VALUES
  ('GoodWorks Nonprofit', 'NONPROFIT'),
  ('Personal (You)',      'PERSONAL');

INSERT INTO contacts (name, email, phone, contact_type) VALUES
  ('John Donor',       'john.donor@example.org', NULL, 'PERSON'),
  ('City Print Shop',  'info@cityprint.example',  NULL, 'ORG'),
  ('State Grant Office', 'grants@state.example',  NULL, 'ORG'),
  ('Jane Volunteer',   NULL, NULL, 'PERSON');

INSERT INTO categories (name, kind) VALUES
  ('Supplies',     'EXPENSE'),
  ('Travel',       'EXPENSE'),
  ('Fundraising',  'EXPENSE'),
  ('Office',       'EXPENSE'),
  ('Utilities',    'EXPENSE'),
  ('Donations',    'INCOME'),
  ('Grants',       'INCOME'),
  ('Program Rev',  'INCOME'),
  ('Reimbursements','INCOME');

SET @org_np := (SELECT id FROM organizations WHERE name = 'GoodWorks Nonprofit');
SET @org_me := (SELECT id FROM organizations WHERE name = 'Personal (You)');

SET @cat_supplies := (SELECT id FROM categories WHERE name='Supplies' AND kind='EXPENSE');
SET @cat_travel   := (SELECT id FROM categories WHERE name='Travel' AND kind='EXPENSE');
SET @cat_office   := (SELECT id FROM categories WHERE name='Office' AND kind='EXPENSE');
SET @cat_fund     := (SELECT id FROM categories WHERE name='Fundraising' AND kind='EXPENSE');

SET @c_print  := (SELECT id FROM contacts WHERE name='City Print Shop');
SET @c_donor  := (SELECT id FROM contacts WHERE name='John Donor');
SET @c_grant  := (SELECT id FROM contacts WHERE name='State Grant Office');

INSERT INTO expenses (org_id, expense_date, amount, category_id, description, paid_by_contact_id, method, receipt_url)
VALUES
  (@org_np, '2025-07-15',  145.75, @cat_supplies, 'Flyers for summer fundraiser', @c_print, 'CARD', 'https://drive.example/receipt/001'),
  (@org_np, '2025-08-02',  320.00, @cat_travel,   'Mileage to outreach event',    NULL,     'OTHER', NULL),
  (@org_np, '2025-08-18',   89.50, @cat_office,   'Printer ink + paper',          NULL,     'CARD',  NULL),
  (@org_np, '2025-09-10',  560.00, @cat_fund,     'Venue deposit for gala',       NULL,     'BANK',  NULL),
  (@org_me, '2025-08-05',   48.20, @cat_supplies, 'Personal: office supplies',    NULL,     'CARD',  NULL),
  (@org_me, '2025-09-01',  120.00, @cat_travel,   'Personal: travel to meeting',  NULL,     'OTHER', NULL);

INSERT INTO payments (org_id, payment_date, amount, source_contact_id, type, notes)
VALUES
  (@org_np, '2025-07-20',  1000.00, @c_donor, 'DONATION',     'Summer appeal'),
  (@org_np, '2025-08-25',  5000.00, @c_grant, 'GRANT',        'Quarterly disbursement'),
  (@org_np, '2025-09-12',   250.00, @c_donor, 'DONATION',     'Gala pre-donation'),
  (@org_np, '2025-09-18',   200.00, NULL,      'REIMBURSEMENT','Shared event cost repaid');

INSERT INTO reports (title, date_created, start_date, end_date, notes, file_url)
VALUES
  ('Q3 2025 Summary', '2025-09-23', '2025-07-01', '2025-09-30',
   'Covers Jul–Sep 2025 activity', NULL);
"""

def main():
    root_cnx = mysql.connector.connect(
        host=settings.host, port=settings.port,
        user=settings.user, password=settings.password,
        autocommit=True,
    )
    cur = root_cnx.cursor()
    try:
        for stmt in [s.strip() for s in SCHEMA_SQL.split(';')]:
            if not stmt or stmt.startswith('--'):
                continue
            cur.execute(stmt)
        print("✅ Database initialized: nonprofit_finance")
    finally:
        cur.close()
        root_cnx.close()

if __name__ == "__main__":
    main()
```

---

### `scripts/demo.py`

```python
from app.repositories import (
    OrganizationRepository, ExpenseRepository, PaymentRepository
)
from app.db import query_all
from datetime import date

def print_balances():
    rows = query_all("SELECT * FROM vw_balance_by_org")
    print("
== Balances ==")
    for r in rows:
        print(f"{r['org_name']}: payments={r['total_payments']:.2f}, expenses={r['total_expenses']:.2f}, net={r['net_balance']:.2f}")

def main():
    orgs = OrganizationRepository()
    expenses = ExpenseRepository()
    payments = PaymentRepository()

    print_balances()

    # Create a new expense for the nonprofit org
    org_np = orgs.list("name=%s", ("GoodWorks Nonprofit",), limit=1)
    if not org_np:
        raise SystemExit("GoodWorks org missing; run scripts/init_db.py first.")
    org_id = org_np[0]['id']

    # Use an existing category (Supplies)
    cat = query_all("SELECT id FROM categories WHERE name=%s AND kind='EXPENSE' LIMIT 1", ("Supplies",))
    cat_id = cat[0]['id']

    print("
Creating a new expense ...")
    new_id = expenses.insert({
        "org_id": org_id,
        "expense_date": date.today().isoformat(),
        "amount": 42.50,
        "category_id": cat_id,
        "description": "Demo: office supplies",
        "method": "CARD",
    })
    print("Inserted expense id:", new_id)

    # Read it back
    row = expenses.get(new_id)
    print("Inserted row:", row)

    # Update
    expenses.update(new_id, {"amount": 44.00, "description": "Demo: updated amount"})
    print("Updated row:", expenses.get(new_id))

    # Delete
    expenses.delete(new_id)
    print("Deleted. Exists now?", expenses.get(new_id))

    print_balances()

    # Monthly summaries
    print("
== Monthly expense summary ==")
    rows = query_all("SELECT * FROM vw_monthly_expense_summary ORDER BY month_start DESC, total_amount DESC LIMIT 10")
    for r in rows:
        print(r)

    print("
== Monthly payment summary ==")
    rows = query_all("SELECT * FROM vw_monthly_payment_summary ORDER BY month_start DESC, total_amount DESC LIMIT 10")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
```

---

### `scripts/run_report.py`

Example: show totals within a date range using repositories.

```python
from app.repositories import ExpenseRepository, PaymentRepository
import sys

def main(start: str, end: str, org_id: int):
    exp_repo = ExpenseRepository()
    pay_repo = PaymentRepository()

    print(f"Report window: {start} .. {end} (org_id={org_id})
")
    print("Expenses by category:")
    for row in exp_repo.sum_by_category(org_id, start, end):
        print(row)

    print("
Payments by type:")
    for row in pay_repo.sum_by_type(org_id, start, end):
        print(row)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/run_report.py YYYY-MM-DD YYYY-MM-DD ORG_ID")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
```

---

## 7) Common Operations

- **Create**: use `insert({...})` on the relevant repository.
- **Read**: `get(id)` or `list(where=..., params=...)`.
- **Update**: `update(id, {...})` (only the provided fields are updated).
- **Delete**: `delete(id)`.

Repositories available:
- `OrganizationRepository` (organizations)
- `ContactRepository` (contacts)
- `CategoryRepository` (categories)
- `ExpenseRepository` (expenses)
- `PaymentRepository` (payments)
- `ReportRepository` (reports)

Views for analysis:
- `vw_balance_by_org`
- `vw_monthly_expense_summary`
- `vw_monthly_payment_summary`
- `vw_report_financials`

---

## 8) Notes

- The initializer drops & recreates the `nonprofit_finance` DB. If you don’t want that behavior in production, remove those statements and run once.
- For production, consider:
  - Connection secrets via a secure secret store
  - Migration tool (e.g., Alembic or schema version table)
  - Proper logging, retries, and error handling
  - Least-privilege DB user

---

## 9) Quick Checklist for the Assistant

1. Create the directory: `nonprofit_finance_db/` and populate files from this README.
2. `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent).
3. `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set MySQL creds.
5. Run: `python scripts/init_db.py` → expect “✅ Database initialized”.
6. Run: `python scripts/demo.py` → verify CRUD works.
7. Optional: `python scripts/run_report.py 2025-07-01 2025-09-30 1`

That’s it. 🚀
