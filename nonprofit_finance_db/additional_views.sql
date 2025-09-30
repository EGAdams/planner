-- Additional database views for enhanced transaction data analysis
-- These views complement the existing transaction viewing capabilities

USE nonprofit_finance;

-- Daily transaction summary view
CREATE OR REPLACE VIEW vw_daily_transaction_summary AS
SELECT
    org_id,
    transaction_date,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM transactions
GROUP BY org_id, transaction_date, transaction_type
ORDER BY transaction_date DESC, transaction_type;

-- Weekly transaction summary view (grouped by week)
CREATE OR REPLACE VIEW vw_weekly_transaction_summary AS
SELECT
    org_id,
    YEAR(transaction_date) AS year,
    WEEK(transaction_date, 1) AS week_number, -- Monday-based weeks
    DATE(DATE_SUB(transaction_date, INTERVAL WEEKDAY(transaction_date) DAY)) AS week_start_date,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM transactions
GROUP BY org_id, YEAR(transaction_date), WEEK(transaction_date, 1), transaction_type
ORDER BY year DESC, week_number DESC, transaction_type;

-- Account-level transaction summary
CREATE OR REPLACE VIEW vw_account_transaction_summary AS
SELECT
    org_id,
    account_number,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credits,
    SUM(CASE WHEN transaction_type = 'DEBIT' THEN amount ELSE 0 END) AS total_debits,
    SUM(CASE WHEN transaction_type = 'TRANSFER' THEN amount ELSE 0 END) AS total_transfers,
    SUM(amount) AS net_amount,
    MIN(transaction_date) AS first_transaction_date,
    MAX(transaction_date) AS last_transaction_date,
    COUNT(DISTINCT transaction_date) AS transaction_days
FROM transactions
WHERE account_number IS NOT NULL
GROUP BY org_id, account_number
ORDER BY total_transactions DESC;

-- Large transactions view (transactions above average + 1 standard deviation)
CREATE OR REPLACE VIEW vw_large_transactions AS
SELECT
    t.id,
    t.org_id,
    t.transaction_date,
    t.amount,
    t.description,
    t.transaction_type,
    t.account_number,
    ROUND((t.amount - stats.avg_amount) / stats.std_amount, 2) AS std_deviations_from_mean
FROM transactions t
CROSS JOIN (
    SELECT
        AVG(amount) AS avg_amount,
        STDDEV(amount) AS std_amount
    FROM transactions
    WHERE org_id = 1  -- Adjust org_id as needed
) stats
WHERE t.amount > (stats.avg_amount + stats.std_amount)
ORDER BY t.amount DESC;

-- Recent transactions view (last 30 days)
CREATE OR REPLACE VIEW vw_recent_transactions AS
SELECT
    id,
    org_id,
    transaction_date,
    amount,
    description,
    transaction_type,
    account_number,
    bank_reference,
    balance_after,
    import_batch_id,
    created_at,
    DATEDIFF(CURDATE(), transaction_date) AS days_ago
FROM transactions
WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY transaction_date DESC, id DESC;

-- Transaction frequency by description patterns
CREATE OR REPLACE VIEW vw_transaction_patterns AS
SELECT
    org_id,
    CASE
        WHEN description LIKE '%ONLINE TRANSFER%' THEN 'Online Transfer'
        WHEN description LIKE '%ONLINE PYMT%' THEN 'Online Payment'
        WHEN description LIKE '%ATM%' THEN 'ATM Transaction'
        WHEN description LIKE '%DEBIT CARD%' THEN 'Debit Card'
        WHEN description LIKE '%CHECK%' THEN 'Check'
        WHEN description LIKE '%DEPOSIT%' THEN 'Deposit'
        WHEN description LIKE '%FEE%' OR description LIKE '%CHARGE%' THEN 'Fee/Charge'
        WHEN description LIKE '%INTEREST%' THEN 'Interest'
        ELSE 'Other'
    END AS transaction_pattern,
    transaction_type,
    COUNT(*) AS frequency,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM transactions
GROUP BY org_id, transaction_pattern, transaction_type
HAVING frequency > 0
ORDER BY frequency DESC, total_amount DESC;

-- Monthly balance progression view (using balance_after when available)
CREATE OR REPLACE VIEW vw_monthly_balance_progression AS
SELECT
    org_id,
    account_number,
    DATE_FORMAT(transaction_date, '%Y-%m') AS month_year,
    COUNT(*) AS transaction_count,
    SUM(amount) AS net_change,
    MAX(balance_after) AS ending_balance,
    MIN(balance_after) AS lowest_balance,
    AVG(balance_after) AS avg_balance
FROM transactions
WHERE balance_after IS NOT NULL
GROUP BY org_id, account_number, DATE_FORMAT(transaction_date, '%Y-%m')
ORDER BY month_year DESC, account_number;

-- Import batch performance view
CREATE OR REPLACE VIEW vw_import_performance AS
SELECT
    ib.id AS batch_id,
    ib.org_id,
    ib.filename,
    ib.file_format,
    ib.import_date,
    ib.status,
    ib.total_transactions,
    ib.successful_imports,
    ib.failed_imports,
    ib.duplicate_count,
    ROUND((ib.successful_imports / ib.total_transactions) * 100, 2) AS success_rate,
    COUNT(t.id) AS actual_db_records,
    CASE
        WHEN COUNT(t.id) = ib.successful_imports THEN 'Consistent'
        ELSE 'Mismatch'
    END AS data_consistency,
    MIN(t.transaction_date) AS earliest_transaction,
    MAX(t.transaction_date) AS latest_transaction,
    SUM(t.amount) AS total_amount_imported
FROM import_batches ib
LEFT JOIN transactions t ON ib.id = t.import_batch_id
GROUP BY ib.id, ib.org_id, ib.filename, ib.file_format, ib.import_date,
         ib.status, ib.total_transactions, ib.successful_imports,
         ib.failed_imports, ib.duplicate_count
ORDER BY ib.import_date DESC;

-- Duplicate detection analysis view
CREATE OR REPLACE VIEW vw_duplicate_analysis AS
SELECT
    df.id AS flag_id,
    df.transaction_id,
    df.duplicate_transaction_id,
    df.confidence_score,
    df.status AS flag_status,
    t1.transaction_date AS original_date,
    t1.amount AS original_amount,
    t1.description AS original_description,
    t2.transaction_date AS duplicate_date,
    t2.amount AS duplicate_amount,
    t2.description AS duplicate_description,
    ABS(DATEDIFF(t1.transaction_date, t2.transaction_date)) AS date_difference_days,
    ABS(t1.amount - t2.amount) AS amount_difference
FROM duplicate_flags df
JOIN transactions t1 ON df.transaction_id = t1.id
JOIN transactions t2 ON df.duplicate_transaction_id = t2.id
ORDER BY df.confidence_score DESC, df.created_at DESC;

-- Show all newly created views
SELECT 'Database views created successfully' AS status;

SHOW TABLES LIKE 'vw_%';

-- Sample queries to demonstrate the views
SELECT 'Sample: Daily Summary for Last 7 Days' AS query_type;
SELECT * FROM vw_daily_transaction_summary
WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
LIMIT 10;

SELECT 'Sample: Account Summary' AS query_type;
SELECT * FROM vw_account_transaction_summary LIMIT 5;

SELECT 'Sample: Transaction Patterns' AS query_type;
SELECT * FROM vw_transaction_patterns
ORDER BY frequency DESC
LIMIT 10;