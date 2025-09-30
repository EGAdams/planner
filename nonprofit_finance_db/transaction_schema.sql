-- Transaction tables for bank statement ingestion
-- Based on the models in app/models/transaction.py

USE nonprofit_finance;

-- Import batches table to track file imports
CREATE TABLE IF NOT EXISTS import_batches (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    org_id BIGINT UNSIGNED NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_format ENUM('CSV', 'PDF', 'OFX') NOT NULL,
    import_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_transactions INT NOT NULL DEFAULT 0,
    successful_imports INT NOT NULL DEFAULT 0,
    failed_imports INT NOT NULL DEFAULT 0,
    duplicate_count INT NOT NULL DEFAULT 0,
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING',
    error_log TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_import_batches_org (org_id),
    INDEX idx_import_batches_status (status),
    INDEX idx_import_batches_date (import_date),
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Transactions table to store all bank transactions
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    org_id BIGINT UNSIGNED NOT NULL,
    transaction_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    description TEXT NOT NULL,
    transaction_type ENUM('DEBIT', 'CREDIT', 'TRANSFER') NOT NULL,
    account_number VARCHAR(50) NULL,
    bank_reference VARCHAR(100) NULL,
    balance_after DECIMAL(15,2) NULL,
    category_id BIGINT UNSIGNED NULL,
    import_batch_id BIGINT UNSIGNED NULL,
    raw_data JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_transactions_org (org_id),
    INDEX idx_transactions_date (transaction_date),
    INDEX idx_transactions_type (transaction_type),
    INDEX idx_transactions_account (account_number),
    INDEX idx_transactions_batch (import_batch_id),
    INDEX idx_transactions_category (category_id),
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Duplicate flags table to track potential duplicates
CREATE TABLE IF NOT EXISTS duplicate_flags (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    transaction_id BIGINT UNSIGNED NOT NULL,
    duplicate_transaction_id BIGINT UNSIGNED NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    match_criteria JSON NOT NULL,
    status ENUM('PENDING', 'CONFIRMED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    reviewed_by VARCHAR(100) NULL,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_duplicate_flags_transaction (transaction_id),
    INDEX idx_duplicate_flags_duplicate (duplicate_transaction_id),
    INDEX idx_duplicate_flags_status (status),
    INDEX idx_duplicate_flags_confidence (confidence_score),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (duplicate_transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    UNIQUE KEY uq_duplicate_pair (transaction_id, duplicate_transaction_id)
) ENGINE=InnoDB;

-- Account information table to store extracted account metadata
CREATE TABLE IF NOT EXISTS account_info (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    org_id BIGINT UNSIGNED NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    account_type VARCHAR(100) NULL,
    bank_name VARCHAR(100) NULL,
    statement_start_date DATE NULL,
    statement_end_date DATE NULL,
    import_batch_id BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_account_info_org (org_id),
    INDEX idx_account_info_account (account_number),
    INDEX idx_account_info_bank (bank_name),
    INDEX idx_account_info_batch (import_batch_id),
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE SET NULL,
    UNIQUE KEY uq_account_org_batch (org_id, account_number, import_batch_id)
) ENGINE=InnoDB;

-- Views for reporting and analysis

-- View to get transaction summaries by month
CREATE OR REPLACE VIEW vw_monthly_transaction_summary AS
SELECT
    org_id,
    DATE_FORMAT(transaction_date, '%Y-%m') AS month_year,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM transactions
GROUP BY org_id, DATE_FORMAT(transaction_date, '%Y-%m'), transaction_type;

-- View to get import batch summaries
CREATE OR REPLACE VIEW vw_import_batch_summary AS
SELECT
    ib.id,
    ib.org_id,
    ib.filename,
    ib.file_format,
    ib.import_date,
    ib.total_transactions,
    ib.successful_imports,
    ib.failed_imports,
    ib.duplicate_count,
    ib.status,
    COUNT(t.id) AS actual_transactions,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'DEBIT' THEN t.amount ELSE 0 END), 0) AS total_debits,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE 0 END), 0) AS total_credits
FROM import_batches ib
LEFT JOIN transactions t ON ib.id = t.import_batch_id
GROUP BY ib.id, ib.org_id, ib.filename, ib.file_format, ib.import_date,
         ib.total_transactions, ib.successful_imports, ib.failed_imports,
         ib.duplicate_count, ib.status;

-- Show table creation results
SHOW TABLES LIKE '%transaction%';
SHOW TABLES LIKE '%import%';
SHOW TABLES LIKE '%duplicate%';
SHOW TABLES LIKE '%account%';