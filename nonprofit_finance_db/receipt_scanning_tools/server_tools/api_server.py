#!/usr/bin/env python3
"""
FastAPI server for Daily Expense Categorizer
Serves transaction data from MySQL database
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    EventSourceResponse = None
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
import os
import subprocess
import tempfile
from pathlib import Path

# Add app directory to path (go up to nonprofit_finance_db level)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add standalone receipt scanner to path
RECEIPT_SCANNER_BACKEND = Path(__file__).parent.parent / "receipt_scanner" / "backend"
sys.path.insert(0, str(RECEIPT_SCANNER_BACKEND))

from app.db import query_all, query_one, execute
from api.receipt_endpoints import router as receipt_router  # Now from standalone copy
from parsers import PDFParser

app = FastAPI(title="Daily Expense Categorizer API")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = (BASE_DIR.parent / "category-picker" / "public").resolve()
OFFICE_ASSISTANT_DIR = (BASE_DIR.parent / "office-assistant").resolve()
RECEIPT_SCANNER_FRONTEND = (BASE_DIR / "receipt_scanning_tools" / "receipt_scanner" / "frontend").resolve()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipt_router, prefix="/api")

if FRONTEND_DIR.is_dir():
    app.mount(
        "/ui",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="category-picker-ui",
    )

if OFFICE_ASSISTANT_DIR.is_dir():
    @app.get("/", include_in_schema=False)
    async def get_daily_expense_categorizer():
        return FileResponse(OFFICE_ASSISTANT_DIR / "daily_expense_categorizer.html")

    @app.get("/daily_expense_categorizer.html", include_in_schema=False)
    async def get_daily_expense_categorizer_direct():
        return FileResponse(OFFICE_ASSISTANT_DIR / "daily_expense_categorizer.html")

    app.mount(
        "/office",
        StaticFiles(directory=str(OFFICE_ASSISTANT_DIR), html=True),
        name="office-assistant",
    )

# Mount standalone receipt scanner frontend
if RECEIPT_SCANNER_FRONTEND.is_dir():
    @app.get("/receipt-scanner", include_in_schema=False)
    async def get_receipt_scanner():
        return FileResponse(RECEIPT_SCANNER_FRONTEND / "receipt-scanner.html")

    app.mount(
        "/receipt-scanner-app",
        StaticFiles(directory=str(RECEIPT_SCANNER_FRONTEND), html=True),
        name="receipt-scanner",
    )

# Models
class CategoryUpdate(BaseModel):
    category_id: Optional[int] = None

class Expense(BaseModel):
    id: int
    date: str
    vendor: str
    amount: float
    category: Optional[str] = None
    category_id: Optional[int] = None
    method: str
    paid_by: Optional[str] = None

class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

class PDFImportRequest(BaseModel):
    filePath: str

class DownloadFile(BaseModel):
    filename: str
    path: str
    downloadTime: str

# Helper function
def convert_value(val):
    """Convert database values to JSON-serializable types"""
    if isinstance(val, (date, datetime)):
        return val.strftime('%Y-%m-%d')
    elif isinstance(val, Decimal):
        return float(val)
    return val

# Routes
@app.get("/api")
async def root():
    return {"message": "Daily Expense Categorizer API", "status": "running"}


@app.get("/api/expenses", response_model=List[Expense])
async def get_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get all expenses with optional date filtering
    Query params:
    - start_date: YYYY-MM-DD (optional)
    - end_date: YYYY-MM-DD (optional)
    """
    try:
        # First, get all categories to build full paths
        categories_sql = "SELECT id, name, parent_id FROM categories"
        all_categories = query_all(categories_sql, ())

        # Build a map of category_id -> full_path
        category_map = {cat['id']: cat for cat in all_categories}

        def get_full_path(cat_id):
            if not cat_id or cat_id not in category_map:
                return None
            path = []
            current_id = cat_id
            visited = set()  # Track visited categories to prevent infinite loops
            # Traverse up the hierarchy
            while current_id is not None:
                # Detect circular reference
                if current_id in visited:
                    break  # Stop if we've seen this category before
                visited.add(current_id)

                cat = category_map.get(current_id)
                if not cat:
                    break
                path.insert(0, cat['name'])  # Insert at beginning
                current_id = cat.get('parent_id')
            return ' / '.join(path)

        # Build SQL query for expenses
        sql = """
            SELECT
                e.id,
                e.expense_date as date,
                e.description as vendor,
                e.amount,
                e.category_id,
                e.method,
                c.name as paid_by
            FROM expenses e
            LEFT JOIN contacts c ON e.paid_by_contact_id = c.id
        """

        conditions = ["e.org_id = 1"]  # Filter by default org_id
        params = []

        if start_date:
            conditions.append("e.expense_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("e.expense_date <= %s")
            params.append(end_date)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY e.expense_date, e.id"

        rows = query_all(sql, tuple(params))

        # Convert rows to expense format with full category path
        expenses = []
        for row in rows:
            expenses.append({
                "id": row['id'],
                "date": convert_value(row['date']),
                "vendor": row['vendor'] or "",
                "amount": convert_value(row['amount']),
                "category": get_full_path(row['category_id']),
                "category_id": row['category_id'],
                "method": row['method'] or "",
                "paid_by": row['paid_by'] or ""
            })

        return expenses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Transaction endpoints - Returns BOTH bank transactions AND manual expenses
@app.get("/api/transactions", response_model=List[Expense])
async def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get all transactions including both bank transactions and manual expenses
    Query params:
    - start_date: YYYY-MM-DD (optional)
    - end_date: YYYY-MM-DD (optional)
    """
    try:
        # First, get expenses (manual entries)
        expenses = await get_expenses(start_date, end_date)

        # Now get bank transactions from transactions table
        sql = """
            SELECT
                id,
                transaction_date as date,
                description as vendor,
                amount,
                transaction_type as method
            FROM transactions
            WHERE org_id = 1
        """

        conditions = []
        params = []

        if start_date:
            conditions.append("transaction_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("transaction_date <= %s")
            params.append(end_date)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        sql += " ORDER BY transaction_date, id"

        rows = query_all(sql, tuple(params))

        # Convert transactions to expense format
        transactions = []
        for row in rows:
            transactions.append({
                "id": row['id'],
                "date": convert_value(row['date']),
                "vendor": row['vendor'] or "",
                "amount": abs(convert_value(row['amount'])),  # Use absolute value
                "category": None,  # Transactions don't have categories
                "category_id": None,
                "method": row['method'] or "BANK",
                "paid_by": ""
            })

        # Combine expenses and transactions
        all_items = expenses + transactions

        # Sort by date
        all_items.sort(key=lambda x: x['date'])

        return all_items

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/transactions/{transaction_id}/category")
async def update_transaction_category(transaction_id: int, update: CategoryUpdate):
    """
    Update the category for a transaction (alias for update_expense_category)
    Body: {"category_id": 123}
    """
    return await update_expense_category(transaction_id, update)


@app.get("/api/categories", response_model=List[Category])
async def get_categories():
    """Get all active expense categories with hierarchy"""
    try:
        sql = """
            SELECT id, name, parent_id
            FROM categories
            WHERE kind = 'EXPENSE' AND is_active = 1
            ORDER BY parent_id, name
        """
        print(f"Executing SQL for categories: {sql}")
        rows = query_all(sql, ())
        print(f"get_categories returned {len(rows)} rows.")
        return [{"id": row['id'], "name": row['name'], "parent_id": row.get('parent_id')} for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/expenses/{expense_id}/category")
async def update_expense_category(expense_id: int, update: CategoryUpdate):
    """
    Update the category for an expense
    Body: {"category_id": 123}
    """
    try:
        # Check if expense exists
        expense = query_one("SELECT id FROM expenses WHERE id = %s", (expense_id,))

        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")

        # Update the category
        execute("UPDATE expenses SET category_id = %s WHERE id = %s",
                (update.category_id, expense_id))

        return {"success": True, "expense_id": expense_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-downloads", response_model=List[DownloadFile])
async def get_recent_downloads():
    """
    Get recent PDF downloads from the Downloads folder
    Returns files from the last hour, or the last 3 files if none in the last hour
    """
    try:
        # Windows Downloads folder path (WSL2 mapped path)
        downloads_path = Path("/mnt/c/Users/NewUser/Downloads")

        if not downloads_path.exists():
            return []

        # Get all PDF files
        pdf_files = []
        for file_path in downloads_path.glob("*.pdf"):
            if file_path.is_file():
                stat = file_path.stat()
                pdf_files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "mtime": datetime.fromtimestamp(stat.st_mtime),
                    "downloadTime": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # Sort by modification time, newest first
        pdf_files.sort(key=lambda x: x["mtime"], reverse=True)

        # Check if any files are from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_files = [f for f in pdf_files if f["mtime"] > one_hour_ago]

        if recent_files:
            # Return recent files from last hour
            return [
                {
                    "filename": f["filename"],
                    "path": f["path"],
                    "downloadTime": f["downloadTime"]
                }
                for f in recent_files
            ]
        else:
            # Return last 3 files
            return [
                {
                    "filename": f["filename"],
                    "path": f["path"],
                    "downloadTime": f["downloadTime"]
                }
                for f in pdf_files[:3]
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading downloads: {str(e)}")


async def _handle_parse_bank_pdf(file: UploadFile, org_id: int = 1) -> Dict[str, Any]:
    """Shared handler for parse-bank-pdf routes."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        parser = PDFParser(org_id)
        if not parser.validate_format(tmp_path):
            raise HTTPException(status_code=400, detail="Invalid or unreadable PDF")

        transactions = parser.parse(tmp_path) or []
        account_info = parser.extract_account_info(tmp_path) or {}

        def _classify(txn: Dict[str, Any]) -> str:
            hint = str(txn.get("bank_item_type") or "").upper()
            if hint in ("CHECK", "WITHDRAWAL", "DEPOSIT"):
                return hint
            desc = str(txn.get("description") or "").lower()
            if "check" in desc:
                return "CHECK"
            amount = txn.get("amount")
            if amount is None:
                return "UNKNOWN"
            return "DEPOSIT" if amount > 0 else "WITHDRAWAL"

        def _compute_breakdown(txns: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
            breakdown = {
                "checks": {"count": 0, "total": 0.0},
                "withdrawals": {"count": 0, "total": 0.0},
                "deposits": {"count": 0, "total": 0.0},
            }
            for txn in txns:
                amount = txn.get("amount")
                if amount is None:
                    continue
                bucket = _classify(txn)
                if bucket == "CHECK":
                    breakdown["checks"]["count"] += 1
                    breakdown["checks"]["total"] += abs(amount)
                elif bucket == "DEPOSIT":
                    breakdown["deposits"]["count"] += 1
                    breakdown["deposits"]["total"] += abs(amount)
                else:
                    breakdown["withdrawals"]["count"] += 1
                    breakdown["withdrawals"]["total"] += abs(amount)

            for key in breakdown:
                breakdown[key]["total"] = round(breakdown[key]["total"], 2)
            return breakdown

        def _close(a: Optional[float], b: Optional[float], tol: float = 0.01) -> bool:
            if a is None or b is None:
                return False
            return abs(a - b) <= tol

        account_summary = account_info.get("summary", {}) if isinstance(account_info, dict) else {}
        breakdown = _compute_breakdown(transactions)

        computed_ending = None
        if account_summary.get("beginning_balance") is not None:
            computed_ending = round(
                account_summary["beginning_balance"]
                - breakdown["checks"]["total"]
                - breakdown["withdrawals"]["total"]
                + breakdown["deposits"]["total"],
                2,
            )

        errors = []
        if account_summary:
            for key in ("checks", "withdrawals", "deposits"):
                expected_group = account_summary.get(key) or {}
                expected_count = expected_group.get("count")
                expected_total = expected_group.get("total")
                if expected_count is not None and expected_count != breakdown[key]["count"]:
                    errors.append(f"{key} count mismatch")
                if expected_total is not None and not _close(expected_total, breakdown[key]["total"]):
                    errors.append(f"{key} total mismatch")

            if account_summary.get("ending_balance") is not None and computed_ending is not None:
                if not _close(account_summary["ending_balance"], computed_ending):
                    errors.append("ending balance mismatch")

        verification = {
            "expected": account_summary,
            "calculated": breakdown,
            "beginning_balance_expected": account_summary.get("beginning_balance"),
            "ending_balance_expected": account_summary.get("ending_balance"),
            "ending_balance_calculated": computed_ending,
            "passes": bool(account_summary) and not errors,
            "errors": errors,
        }

        total_amount = sum(t.get("amount", 0) for t in transactions if t.get("amount") is not None)
        total_debits = sum(abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) < 0)
        total_credits = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)
        statement_total = None
        if isinstance(account_info, dict):
            statement_total = account_summary.get("ending_balance") or account_info.get("statement_total")

        totals = {
            "sum": round(total_amount, 2),
            "debits": round(total_debits, 2),
            "credits": round(total_credits, 2),
            "count": len(transactions),
            "statement_total": statement_total,
            "breakdown": breakdown,
        }

        return {
            "transactions": transactions,
            "totals": totals,
            "account_info": account_info,
            "verification": verification,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@app.post("/api/parse-bank-pdf")
async def parse_bank_pdf(file: UploadFile = File(...), org_id: int = 1) -> Dict[str, Any]:
    """
    Parse a PDF bank statement without importing it.
    Uses Docling first, then Gemini 2.5 fallback to extract transactions.
    """
    return await _handle_parse_bank_pdf(file, org_id)


# Allow legacy/non-prefixed path to avoid 404s when frontend base is misconfigured.
@app.post("/parse-bank-pdf")
async def parse_bank_pdf_legacy(file: UploadFile = File(...), org_id: int = 1) -> Dict[str, Any]:
    return await _handle_parse_bank_pdf(file, org_id)

@app.post("/api/import-pdf")
async def import_pdf(request: PDFImportRequest):
    """
    Import a PDF bank statement into the database with streaming progress updates
    Body: {"filePath": "/path/to/statement.pdf"}
    """
    file_path = request.filePath

    # Validate file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    # Validate it's a PDF
    if not file_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # If SSE is available, use streaming; otherwise fall back to regular response
    if SSE_AVAILABLE:
        async def generate_progress():
            """Generator that yields progress updates as SSE events"""
            import asyncio
            import json

            script_path = Path(__file__).parent / "scripts" / "import_pdf_statement.py"

            # Use the same Python interpreter that's running this server (should be from venv)
            python_executable = sys.executable

            # Use subprocess to run the import script
            process = subprocess.Popen(
                [python_executable, "-u", str(script_path), file_path],  # -u for unbuffered
                cwd=str(Path(__file__).parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )

            stdout_lines = []

            try:
                # Stream output line by line
                while True:
                    line = process.stdout.readline()
                    if not line:
                        # Check if process has finished
                        if process.poll() is not None:
                            break
                        # If process still running but no output, wait a bit
                        await asyncio.sleep(0.1)
                        continue

                    line = line.rstrip()
                    stdout_lines.append(line)

                    # Send progress update for each line immediately
                    if line:  # Only send non-empty lines
                        event_data = json.dumps({'type': 'log', 'message': line})
                        yield f"{event_data}\n\n"  # EventSourceResponse already adds "data: " prefix
                    await asyncio.sleep(0)  # Allow other tasks to run

                # Wait for process to complete
                return_code = process.wait(timeout=120)

                # Read any stderr
                stderr_output = process.stderr.read()

                if return_code != 0:
                    error_msg = stderr_output or '\n'.join(stdout_lines) or "Import script failed"
                    yield f"{json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return

                # Parse statistics from output
                stats = {
                    "success": True,
                    "total_transactions": 0,
                    "successful_imports": 0,
                    "failed_imports": 0,
                    "duplicate_count": 0
                }

                for line in stdout_lines:
                    if "Total transactions found:" in line:
                        try:
                            stats["total_transactions"] = int(line.split(':')[-1].strip())
                        except ValueError:
                            pass
                    elif "Successfully imported:" in line:
                        try:
                            stats["successful_imports"] = int(line.split(':')[-1].strip())
                        except ValueError:
                            pass
                    elif "Failed imports:" in line:
                        try:
                            stats["failed_imports"] = int(line.split(':')[-1].strip())
                        except ValueError:
                            pass
                    elif "Duplicates detected:" in line:
                        try:
                            stats["duplicate_count"] = int(line.split(':')[-1].strip())
                        except ValueError:
                            pass

                # Send final completion event
                yield f"{json.dumps({'type': 'complete', 'stats': stats})}\n\n"

            except subprocess.TimeoutExpired:
                yield f"{json.dumps({'type': 'error', 'message': 'Import process timed out'})}\n\n"
            except Exception as e:
                yield f"{json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return EventSourceResponse(generate_progress())

    else:
        # Fallback to old non-streaming implementation
        try:
            script_path = Path(__file__).parent / "scripts" / "import_pdf_statement.py"

            # Use the same Python interpreter that's running this server (should be from venv)
            python_executable = sys.executable

            # Use subprocess to run the import script and capture output line by line
            process = subprocess.Popen(
                [python_executable, "-u", str(script_path), file_path],  # -u for unbuffered
                cwd=str(Path(__file__).parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Collect all output
            stdout_lines = []

            # Read output in real-time
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                stdout_lines.append(line.rstrip())

            # Wait for process to complete
            return_code = process.wait(timeout=120)

            # Read any stderr
            stderr_output = process.stderr.read()

            # Check if the script succeeded
            if return_code != 0:
                error_msg = stderr_output or '\n'.join(stdout_lines) or "Import script failed"
                raise HTTPException(status_code=500, detail=f"Import failed: {error_msg}")

            # Extract statistics from output
            stats = {
                "success": True,
                "total_transactions": 0,
                "successful_imports": 0,
                "failed_imports": 0,
                "duplicate_count": 0,
                "output_lines": stdout_lines
            }

            for line in stdout_lines:
                if "Total transactions found:" in line:
                    try:
                        stats["total_transactions"] = int(line.split(':')[-1].strip())
                    except ValueError:
                        pass
                elif "Successfully imported:" in line:
                    try:
                        stats["successful_imports"] = int(line.split(':')[-1].strip())
                    except ValueError:
                        pass
                elif "Failed imports:" in line:
                    try:
                        stats["failed_imports"] = int(line.split(':')[-1].strip())
                    except ValueError:
                        pass
                elif "Duplicates detected:" in line:
                    try:
                        stats["duplicate_count"] = int(line.split(':')[-1].strip())
                    except ValueError:
                        pass

            return stats

        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Import process timed out")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error importing PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("[API] Starting Daily Expense Categorizer on http://localhost:8080")
    print("   Main App:          http://localhost:8080/")
    print("   API Documentation: http://localhost:8080/docs")
    print("   API Endpoints:")
    print("   - GET  /api/expenses")
    print("   - GET  /api/categories")
    print("   - PUT  /api/expenses/<id>/category")
    print("   - GET  /api/recent-downloads")
    print("   - POST /api/import-pdf")
    if FRONTEND_DIR.is_dir():
        print("   Category Picker:  http://localhost:8080/ui")
    if OFFICE_ASSISTANT_DIR.is_dir():
        print("   Office Assistant: http://localhost:8080/office")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8080, reload=False)
