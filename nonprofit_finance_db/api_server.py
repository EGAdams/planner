#!/usr/bin/env python3
"""
FastAPI server for Daily Expense Categorizer
Serves transaction data from MySQL database
"""
from fastapi import FastAPI, HTTPException
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
from typing import Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
import os
import subprocess
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import query_all, query_one, execute

app = FastAPI(title="Daily Expense Categorizer API")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = (BASE_DIR.parent / "category-picker" / "public").resolve()
OFFICE_ASSISTANT_DIR = (BASE_DIR.parent / "office-assistant").resolve()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Models
class CategoryUpdate(BaseModel):
    category_id: Optional[int] = None

class Transaction(BaseModel):
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

@app.get("/api/transactions", response_model=List[Transaction])
async def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get all transactions (expenses) with optional date filtering
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

        # Build SQL query for transactions
        sql = """
            SELECT
                t.id,
                t.transaction_date as date,
                t.description as vendor,
                ABS(t.amount) as amount,
                t.category_id,
                COALESCE(t.transaction_type, '') as method,
                '' as paid_by
            FROM transactions t
        """

        conditions = ["t.transaction_type = 'CREDIT'"]  # Only show expenses (transactions marked as CREDIT in your DB)
        params = []

        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)

        sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY t.transaction_date, t.id"

        rows = query_all(sql, tuple(params))

        # Convert rows to transaction format with full category path
        transactions = []
        for row in rows:
            transactions.append({
                "id": row['id'],
                "date": convert_value(row['date']),
                "vendor": row['vendor'] or "",
                "amount": convert_value(row['amount']),
                "category": get_full_path(row['category_id']),
                "category_id": row['category_id'],
                "method": row['method'] or "",
                "paid_by": row['paid_by'] or ""
            })

        return transactions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        rows = query_all(sql, ())

        return [{"id": row['id'], "name": row['name'], "parent_id": row.get('parent_id')} for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{transaction_id}/category")
async def update_category(transaction_id: int, update: CategoryUpdate):
    """
    Update the category for a transaction
    Body: {"category_id": 123}
    """
    try:
        # Check if transaction exists
        transaction = query_one("SELECT id FROM transactions WHERE id = %s", (transaction_id,))

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Update the category
        execute("UPDATE transactions SET category_id = %s WHERE id = %s",
                (update.category_id, transaction_id))

        return {"success": True, "transaction_id": transaction_id}

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
    print("🚀 Starting Daily Expense Categorizer on http://localhost:8080")
    print("   Main App:         http://localhost:8080/")
    print("   API Documentation: http://localhost:8080/docs")
    print("   API Endpoints:")
    print("   - GET  /api/transactions")
    print("   - GET  /api/categories")
    print("   - PUT  /api/transactions/<id>/category")
    print("   - GET  /api/recent-downloads")
    print("   - POST /api/import-pdf")
    if FRONTEND_DIR.is_dir():
        print("   Category Picker:  http://localhost:8080/ui")
    if OFFICE_ASSISTANT_DIR.is_dir():
        print("   Office Assistant: http://localhost:8080/office")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8080, reload=True)
