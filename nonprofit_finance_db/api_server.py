#!/usr/bin/env python3
"""
FastAPI server for Daily Expense Categorizer
Serves transaction data from MySQL database
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CategoryUpdate(BaseModel):
    category_id: int

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

# Helper function
def convert_value(val):
    """Convert database values to JSON-serializable types"""
    if isinstance(val, (date, datetime)):
        return val.strftime('%Y-%m-%d')
    elif isinstance(val, Decimal):
        return float(val)
    return val

# Routes
@app.get("/")
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
        # Build SQL query with JOINs for category name
        sql = """
            SELECT
                t.id,
                t.transaction_date as date,
                t.description as vendor,
                ABS(t.amount) as amount,
                c.name as category,
                t.category_id,
                COALESCE(t.transaction_type, '') as method,
                '' as paid_by
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
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

        # Convert rows to transaction format
        transactions = []
        for row in rows:
            transactions.append({
                "id": row['id'],
                "date": convert_value(row['date']),
                "vendor": row['vendor'] or "",
                "amount": convert_value(row['amount']),
                "category": row['category'],
                "category_id": row['category_id'],
                "method": row['method'] or "",
                "paid_by": row['paid_by'] or ""
            })

        return transactions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories", response_model=List[Category])
async def get_categories():
    """Get all active expense categories"""
    try:
        sql = """
            SELECT id, name
            FROM categories
            WHERE kind = 'EXPENSE' AND is_active = 1
            ORDER BY name
        """

        rows = query_all(sql, ())

        return [{"id": row['id'], "name": row['name']} for row in rows]

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
    print("🚀 Starting Daily Expense Categorizer API on http://localhost:8000")
    print("   API Documentation: http://localhost:8000/docs")
    print("   Endpoints:")
    print("   - GET  /api/transactions")
    print("   - GET  /api/categories")
    print("   - PUT  /api/transactions/<id>/category")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
