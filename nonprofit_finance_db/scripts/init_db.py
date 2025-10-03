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

-- Get category IDs for parent categories
SET @cat_supplies := (SELECT id FROM categories WHERE name='Supplies' AND kind='EXPENSE');
SET @cat_travel := (SELECT id FROM categories WHERE name='Travel' AND kind='EXPENSE');
SET @cat_fundraising := (SELECT id FROM categories WHERE name='Fundraising' AND kind='EXPENSE');
SET @cat_office := (SELECT id FROM categories WHERE name='Office' AND kind='EXPENSE');
SET @cat_utilities := (SELECT id FROM categories WHERE name='Utilities' AND kind='EXPENSE');

-- Insert Utilities subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Gas Bill', 'EXPENSE', @cat_utilities),
  ('Electric Bill', 'EXPENSE', @cat_utilities),
  ('Water/Sewer', 'EXPENSE', @cat_utilities),
  ('Trash Pickup', 'EXPENSE', @cat_utilities);

-- Get gas and electric IDs for third level
SET @cat_gas := (SELECT id FROM categories WHERE name='Gas Bill' AND kind='EXPENSE');
SET @cat_electric := (SELECT id FROM categories WHERE name='Electric Bill' AND kind='EXPENSE');

-- Insert third level utility subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Housing Gas Bill', 'EXPENSE', @cat_gas),
  ('Church Gas Bill', 'EXPENSE', @cat_gas),
  ('Housing Electric Bill', 'EXPENSE', @cat_electric),
  ('Church Electric Bill', 'EXPENSE', @cat_electric);

-- Insert Supplies subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Office Supplies', 'EXPENSE', @cat_supplies),
  ('Kitchen Supplies', 'EXPENSE', @cat_supplies);

-- Insert Travel subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Airfare', 'EXPENSE', @cat_travel),
  ('Hotel', 'EXPENSE', @cat_travel),
  ('Meals', 'EXPENSE', @cat_travel),
  ('Ground Transportation', 'EXPENSE', @cat_travel);

-- Insert Fundraising subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Event Costs', 'EXPENSE', @cat_fundraising),
  ('Marketing Materials', 'EXPENSE', @cat_fundraising),
  ('Venue Rental', 'EXPENSE', @cat_fundraising);

-- Insert Office subcategories
INSERT INTO categories (name, kind, parent_id) VALUES
  ('Office Equipment', 'EXPENSE', @cat_office),
  ('Office Rent', 'EXPENSE', @cat_office),
  ('Office Maintenance', 'EXPENSE', @cat_office);

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