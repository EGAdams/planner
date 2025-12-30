# Finance Report Plan

Plan for extracting curated financial insights from the nonprofit MySQL database and surfacing them through Google Sheets dashboards.

## 1. Purpose & Success Criteria
- Deliver a stable, near-real-time view of income, expenses, and import health using data already ingested into `nonprofit_finance`.
- Provide views that can be filtered by organization, account, category, and time window without exposing raw credentials.
- Automate refreshes so the Google Sheets report requires minimal manual intervention and can be trusted during board or donor reviews.

## 2. Source Data Inventory
- **Database**: MySQL (`nonprofit_finance`); credentials live in `/home/adamsl/planner/.env` and are already consumed by the app settings module.
- **Key tables** (see `transaction_schema.sql` and `app/models/*`):
  - `transactions`: canonical ledger rows with amount, transaction_date, type, org_id, category_id, account metadata, and links back to imports.
  - `import_batches`: file-level metadata (filename, format, success/failure counts, duplicate counts) for understanding ingestion quality.
  - `duplicate_flags`: stores resolved/pending duplicate detection results.
  - `account_info`: per-batch account metadata (account number, statement range).
  - Supporting tables: `categories`, `organizations`, and any custom mapping tables referenced by repositories.
- **Existing reporting views**: `vw_monthly_transaction_summary` and `vw_import_batch_summary` already roll up by month/import batch; we can build on these instead of duplicating logic.

## 3. Access & Environment Prep
1. Load DB credentials via `python-dotenv` or by exporting `NON_PROFIT_*` variables; confirm read-only connectivity using `python scripts/init_db.py --check` or a simple SELECT through the app’s repository layer.
2. Create a dedicated read-only MySQL user for reporting (least privilege).
3. Document the connection parameters in a local `.env.report` file used only for the export script (keep it out of version control).

## 4. Reporting Requirements Breakdown
| View | Questions Answered | Primary Source |
| --- | --- | --- |
| **Raw Transactions** | What actually hit the bank? Filterable by org/account/date/category. | `transactions` joined with `categories`, `organizations`, `account_info`. |
| **Monthly Summary** | What are inflows/outflows per month and their net? | `vw_monthly_transaction_summary` plus custom net cash calculations. |
| **Category Breakdown** | Where is money being spent/received (programs vs admin, donations vs grants)? | Aggregated `transactions` by `category_id` with `kind`. |
| **Import Health** | Are pipelines succeeding? How many duplicates/failures exist per batch? | `import_batches`, `vw_import_batch_summary`, `duplicate_flags`. |
| **Exception Watchlist** | Flag uncategorized, high-value, or duplicate-pending entries needing manual review. | `transactions` filtered by `category_id IS NULL`, `duplicate_flags.status='PENDING'`. |

## 5. Extraction & Transformation Strategy
1. **Baseline Queries**  
   - Parameterize by `org_id`, optional date range, and include a `last_updated` timestamp so Sheets users know data recency.  
   - Sample starting point:
     ```sql
     SELECT t.id, t.org_id, o.name AS organization, t.transaction_date, t.transaction_type,
            t.amount, c.name AS category, c.kind, t.description, t.account_number,
            ib.filename AS source_file, ib.import_date, ai.bank_name, ai.statement_start_date, ai.statement_end_date
     FROM transactions t
     JOIN organizations o ON o.id = t.org_id
     LEFT JOIN categories c ON c.id = t.category_id
     LEFT JOIN import_batches ib ON ib.id = t.import_batch_id
     LEFT JOIN account_info ai ON ai.import_batch_id = t.import_batch_id
     WHERE t.org_id = %(org_id)s AND t.transaction_date BETWEEN %(start)s AND %(end)s;
     ```
   - Summaries can reference `vw_monthly_transaction_summary` and union debit/credit totals to derive `net_cash_flow`.
2. **Derived Metrics**  
   - Add calculated columns (e.g., `running_balance` per account) via SQL window functions or compute client-side before writing to Sheets.
   - Normalize descriptions (strip bank prefixes) by reusing any helper utilities already in `ingestion/` or `app/repositories/`.
3. **Data Validation Hooks**  
   - Cross-check sum of raw transactions vs. totals recorded in `import_batches.total_transactions` to detect drift.
   - Map duplicate status counts to confirm `duplicate_flags` coverage per batch.

## 6. Google Sheets Architecture
1. **Create Sheets Workspace**
   - Main file: `Nonprofit Finance Report`.
   - Tabs: `Config`, `Raw_Transactions`, `Monthly_Summary`, `Category_Breakdown`, `Import_Health`, `Exceptions`, `Data_Dictionary`.
2. **Tab Layouts**
   - `Config`: org selector, start/end date, refresh timestamps (populated by export script).
   - `Raw_Transactions`: append-only data with filters enabled; freeze header rows; include data validation for transaction_type.
   - `Monthly_Summary`: pivot-style table referencing aggregated dataset; include charts (line for net cash, stacked column for credit/debit).
   - `Category_Breakdown`: pivot on `category -> month`, with sparklines or bar charts.
   - `Import_Health`: highlight batches with high failure/duplicate counts; embed conditional formatting.
   - `Exceptions`: filtered list of uncategorized or pending duplicate transactions for follow-up.
   - `Data_Dictionary`: describes every column and its origin.
3. **Data Flow Options**
   - Option A: Use Python + `gspread`/Google Sheets API with a service account shared to the Sheet.
   - Option B: Use Google Apps Script that calls the API endpoint we expose (requires enabling HTTPS endpoint from this repo).
   - We’ll start with Option A because repo already interfaces with MySQL via Python and can reuse env handling.

## 7. Automation Workflow
1. **Service Account Setup**
   - Create a Google Cloud project, enable Sheets API, generate a service-account key JSON, and store it securely (e.g., `~/.config/nonprofit-finance/service-account.json` excluded from git).
   - Share the target Sheet with the service account email (editor role).
2. **Export Script Skeleton**
   - New CLI command (e.g., `python scripts/export_finance_report.py --org-id 1 --sheet-id <id>`).
   - Steps:
     1. Load config (org/time window/tabs to refresh) from CLI arguments or a YAML file checked into `configs/`.
     2. Execute each SQL query, convert to Pandas DataFrames, enforce schema (dates -> ISO strings, decimals -> two decimals).
     3. Clear the destination tab range, batch-update values via Sheets API.
     4. Write metadata (last refresh time, record counts) to the `Config` tab.
   - Dry-run mode prints counts without touching Sheets.
3. **Scheduling**
   - Add a cron entry or systemd timer on the deployment host (e.g., hourly).  
   - Long term: integrate with GitHub Actions or an Airflow DAG if infrastructure exists.

## 8. Data Quality & Governance
- **Reconciliation**: After each export run, compare aggregated totals (per month/per category) with cached results to spot anomalies.
- **Audit Trail**: Log export start/end times and record counts to `logs/report_exports.log`; optionally persist to a new `report_exports` table.
- **Error Handling**: If a tab update fails, rollback by reloading from the previous CSV snapshot (keep last export CSVs under `backups/report_exports/`).
- **Security**: Keep `.env` and Google credentials outside the repo; ensure the service account has access only to the required Sheet.

## 9. Implementation Phases
1. **Week 1 – Discovery & Prototyping**
   - Validate schema, confirm queries produce desired columns, define Google Sheets layout mock.
2. **Week 2 – Automation Backbone**
   - Implement export script, authenticate with Sheets API, refresh `Raw_Transactions` + `Monthly_Summary`.
3. **Week 3 – Enrichment & QA**
   - Add remaining tabs, conditional formatting, exception reports, and automated validation checks.
4. **Week 4 – Handoff & Documentation**
   - Write runbooks, schedule cron, and train stakeholders on using filters/pivots.

## 10. Open Questions
- Do we need consolidated reporting across multiple organizations in a single Sheet or separate workbooks per org?
- How far back should historical data go? (Impacts query window and sheet size limits.)
- Are there additional classifications (e.g., restricted vs unrestricted funds) that live outside `categories` and need supplemental mapping tables?

Answering these will finalize the query parameters and Sheet structure before we implement the automation.
