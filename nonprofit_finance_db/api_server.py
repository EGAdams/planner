#!/usr/bin/env python3
"""
FastAPI server for Daily Expense Categorizer
Serves transaction data from MySQL database
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import sys
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
            # Traverse up the hierarchy
            while current_id is not None:
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

        conditions = []
        params = []

        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)

        if conditions:
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Daily Expense Categorizer on http://localhost:8080")
    print("   Main App:         http://localhost:8080/")
    print("   API Documentation: http://localhost:8080/docs")
    print("   API Endpoints:")
    print("   - GET  /api/transactions")
    print("   - GET  /api/categories")
    print("   - PUT  /api/transactions/<id>/category")
    if FRONTEND_DIR.is_dir():
        print("   Category Picker:  http://localhost:8080/ui")
    if OFFICE_ASSISTANT_DIR.is_dir():
        print("   Office Assistant: http://localhost:8080/office")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8080, reload=True)
