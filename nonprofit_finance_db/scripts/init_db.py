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
  parent_id  BIGINT UNSIGNED NULL,
  name       VARCHAR(100) NOT NULL,
  kind       ENUM('EXPENSE','INCOME') NOT NULL,
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (parent_id) REFERENCES categories(id),
  INDEX idx_categories_parent (parent_id)
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

-- Church/Housing category structure
INSERT INTO categories (id, name, kind, parent_id, is_active) VALUES
  (1, 'Church', 'EXPENSE', NULL, 1),
  (2, 'Housing', 'EXPENSE', NULL, 1),

  -- CHURCH categories
  (100, 'Facility Payment', 'EXPENSE', 1, 1),

  (110, 'Facility Upkeep', 'EXPENSE', 1, 1),
  (111, 'Trash', 'EXPENSE', 110, 1),
  (112, 'Furnishings', 'EXPENSE', 110, 1),
  (113, 'Tools', 'EXPENSE', 110, 1),
  (114, 'Cleaning', 'EXPENSE', 110, 1),
  (115, 'Other', 'EXPENSE', 110, 1),

  (120, 'Utilities', 'EXPENSE', 1, 1),
  (121, 'Church Gas Bill', 'EXPENSE', 120, 1),
  (122, 'Church Water Bill', 'EXPENSE', 120, 1),
  (123, 'Church Electric Bill', 'EXPENSE', 120, 1),
  (124, 'Church Phone/Internet Bill', 'EXPENSE', 120, 1),
  (125, 'Other', 'EXPENSE', 120, 1),

  (130, 'Food & Supplies', 'EXPENSE', 1, 1),
  (131, 'Family Fare', 'EXPENSE', 130, 1),
  (132, 'Meijer', 'EXPENSE', 130, 1),
  (133, 'Restaurants (members/guests)', 'EXPENSE', 130, 1),
  (134, 'Other', 'EXPENSE', 130, 1),

  (140, 'Office', 'EXPENSE', 1, 1),
  (141, 'Supplies', 'EXPENSE', 140, 1),
  (142, 'Apple', 'EXPENSE', 140, 1),
  (143, 'Amazon', 'EXPENSE', 140, 1),
  (144, 'Postage', 'EXPENSE', 140, 1),
  (145, 'Furnishings', 'EXPENSE', 140, 1),
  (146, 'Other', 'EXPENSE', 140, 1),

  (150, 'Education / Music / TV', 'EXPENSE', 1, 1),
  (151, 'CDs', 'EXPENSE', 150, 1),
  (152, 'DVDs', 'EXPENSE', 150, 1),
  (153, 'Books', 'EXPENSE', 150, 1),
  (154, 'Amazon', 'EXPENSE', 150, 1),
  (155, 'Other', 'EXPENSE', 150, 1),

  (160, 'Travel & Transportation', 'EXPENSE', 1, 1),
  (161, 'Fuel', 'EXPENSE', 160, 1),
  (162, 'RJ gas', 'EXPENSE', 161, 1),
  (163, 'RM gas', 'EXPENSE', 161, 1),
  (164, 'Vehicle Maintenance', 'EXPENSE', 160, 1),
  (165, 'RJ wash/oil', 'EXPENSE', 164, 1),
  (166, 'RM wash/oil', 'EXPENSE', 164, 1),
  (167, 'Car repair (RJ)', 'EXPENSE', 164, 1),
  (168, 'Car repair (RM)', 'EXPENSE', 164, 1),
  (169, 'Vehicle Ownership', 'EXPENSE', 160, 1),
  (170, 'Car payment (general)', 'EXPENSE', 169, 1),
  (171, 'RJ Car Payment', 'EXPENSE', 169, 1),
  (172, 'RM Car Payment', 'EXPENSE', 169, 1),
  (173, 'License Tags', 'EXPENSE', 169, 1),
  (174, 'RJ', 'EXPENSE', 173, 1),
  (175, 'RM', 'EXPENSE', 173, 1),
  (176, 'Other', 'EXPENSE', 173, 1),
  (177, 'Trips', 'EXPENSE', 160, 1),
  (178, 'Airfare', 'EXPENSE', 177, 1),
  (179, 'Tolls', 'EXPENSE', 177, 1),
  (180, 'AAA', 'EXPENSE', 177, 1),
  (181, 'Hotels', 'EXPENSE', 177, 1),
  (182, 'Ministry-related travel', 'EXPENSE', 177, 1),
  (183, 'Other', 'EXPENSE', 160, 1),

  (190, 'Gifts & Love Offerings', 'EXPENSE', 1, 1),
  (191, 'EG Adams (work for River of Life)', 'EXPENSE', 190, 1),
  (192, 'Individuals', 'EXPENSE', 190, 1),
  (193, 'C Baker', 'EXPENSE', 192, 1),
  (194, 'A Baker', 'EXPENSE', 192, 1),
  (195, 'K Cook', 'EXPENSE', 192, 1),
  (196, 'R Menninga', 'EXPENSE', 192, 1),
  (197, 'J Menninga', 'EXPENSE', 192, 1),
  (198, 'K Roark', 'EXPENSE', 192, 1),
  (199, 'H Schneider', 'EXPENSE', 192, 1),
  (200, 'R Exposito', 'EXPENSE', 192, 1),
  (201, 'K Vander Vliet', 'EXPENSE', 192, 1),
  (202, 'J McKay', 'EXPENSE', 192, 1),
  (203, 'Sound (R Slawson)', 'EXPENSE', 192, 1),
  (204, 'Guest Speakers', 'EXPENSE', 192, 1),
  (205, 'Special occasions (name/occasion)', 'EXPENSE', 192, 1),
  (210, 'Ministries & Organizations', 'EXPENSE', 190, 1),
  (211, 'Chosen People', 'EXPENSE', 210, 1),
  (212, 'Columbia Orphanage', 'EXPENSE', 210, 1),
  (213, 'Segals in Israel', 'EXPENSE', 210, 1),
  (214, 'Intercessors for America', 'EXPENSE', 210, 1),
  (215, 'Samaritans Purse', 'EXPENSE', 210, 1),
  (216, 'Mel Trotter', 'EXPENSE', 210, 1),
  (217, 'Guiding Light', 'EXPENSE', 210, 1),
  (218, 'Right to Life', 'EXPENSE', 210, 1),
  (219, 'Johnsons in Dominican Republic', 'EXPENSE', 210, 1),
  (220, 'Jews for Jesus', 'EXPENSE', 210, 1),
  (221, 'Jewish Voice', 'EXPENSE', 210, 1),
  (222, 'Salvation Army', 'EXPENSE', 210, 1),
  (223, 'Other', 'EXPENSE', 210, 1),

  (230, 'Insurance', 'EXPENSE', 1, 1),
  (231, 'Building', 'EXPENSE', 230, 1),
  (232, 'Boiler', 'EXPENSE', 230, 1),
  (233, 'Vehicles', 'EXPENSE', 230, 1),

  (240, 'Staff & Benefits', 'EXPENSE', 1, 1),
  (241, 'Senior Pastors', 'EXPENSE', 240, 1),
  (242, 'RJ — Priority Health (medical expenses)', 'EXPENSE', 241, 1),
  (243, 'RM — Priority Health (medical expenses)', 'EXPENSE', 241, 1),

  (250, 'Misc.', 'EXPENSE', 1, 1),

  -- HOUSING categories
  (300, 'Housing Payment', 'EXPENSE', 2, 1),
  (301, 'House Payment', 'EXPENSE', 300, 1),

  (310, 'Utilities', 'EXPENSE', 2, 1),
  (311, 'Housing Gas Bill', 'EXPENSE', 310, 1),
  (312, 'Housing Water Bill', 'EXPENSE', 310, 1),
  (313, 'Housing Trash Bill', 'EXPENSE', 310, 1),
  (314, 'Housing Electric Bill', 'EXPENSE', 310, 1),

  (320, 'Taxes & Insurance', 'EXPENSE', 2, 1),
  (321, 'House Taxes', 'EXPENSE', 320, 1),
  (322, 'House Insurance', 'EXPENSE', 320, 1),

  (330, 'Services', 'EXPENSE', 2, 1),
  (331, 'Service Professor', 'EXPENSE', 330, 1),

  (340, 'Upkeep', 'EXPENSE', 2, 1),
  (341, 'Décor / Furnishings', 'EXPENSE', 340, 1),
  (342, 'Tools', 'EXPENSE', 340, 1),
  (343, 'Repair', 'EXPENSE', 340, 1),
  (344, 'Outdoor & Lawn Care', 'EXPENSE', 340, 1),
  (345, 'Other', 'EXPENSE', 340, 1),

  (350, 'Misc.', 'EXPENSE', 2, 1),

  -- Keep INCOME categories simple for now
  (1000, 'Donations', 'INCOME', NULL, 1),
  (1001, 'Grants', 'INCOME', NULL, 1),
  (1002, 'Program Rev', 'INCOME', NULL, 1),
  (1003, 'Reimbursements', 'INCOME', NULL, 1);

SET @org_np := (SELECT id FROM organizations WHERE name = 'GoodWorks Nonprofit');
SET @org_me := (SELECT id FROM organizations WHERE name = 'Personal (You)');

SET @c_print  := (SELECT id FROM contacts WHERE name='City Print Shop');
SET @c_donor  := (SELECT id FROM contacts WHERE name='John Donor');
SET @c_grant  := (SELECT id FROM contacts WHERE name='State Grant Office');

-- Sample expenses using new category structure (optional - can be removed)
-- INSERT INTO expenses (org_id, expense_date, amount, category_id, description, paid_by_contact_id, method, receipt_url)
-- VALUES
--   (@org_np, '2025-07-15',  145.75, 141, 'Office supplies', @c_print, 'CARD', NULL),
--   (@org_np, '2025-08-02',  320.00, 162, 'Fuel - RJ gas',    NULL,     'OTHER', NULL);

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