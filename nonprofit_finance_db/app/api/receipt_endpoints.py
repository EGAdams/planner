from __future__ import annotations

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import date

from app.config import settings
from app.services.receipt_parser import ReceiptParser
from app.services.receipt_engine import GeminiReceiptEngine
from app.models.receipt_models import ReceiptExtractionResult, PaymentMethod, ReceiptItem, ReceiptTotals, ReceiptPartyInfo, ReceiptMeta
from app.repositories.receipt_metadata import ReceiptMetadataRepository
from app.repositories.expenses import ExpenseRepository

router = APIRouter()

# Initialize services and repositories
receipt_parser: ReceiptParser | None = None
receipt_parser_error: str | None = None
receipt_metadata_repo = ReceiptMetadataRepository()
expense_repo = ExpenseRepository() # Assuming this is available


def get_receipt_parser() -> ReceiptParser:
    """Return the shared ReceiptParser, initializing it lazily."""
    global receipt_parser, receipt_parser_error
    if receipt_parser is not None:
        return receipt_parser
    try:
        receipt_parser = ReceiptParser(GeminiReceiptEngine())
        receipt_parser_error = None
        return receipt_parser
    except Exception as exc:
        receipt_parser = None
        receipt_parser_error = str(exc)
        raise HTTPException(
            status_code=503,
            detail=f"Receipt parsing temporarily unavailable: {receipt_parser_error}",
        )

class ParseReceiptResponse(BaseModel):
    parsed_data: ReceiptExtractionResult
    temp_file_name: str

class SaveReceiptRequest(BaseModel):
    org_id: int
    merchant_name: str
    expense_date: date
    total_amount: float
    tax_amount: Optional[float] = 0.0
    category_id: Optional[int] = None
    payment_method: PaymentMethod = "OTHER"
    description: Optional[str] = None
    original_file_name: str # The original filename from the user upload
    temp_file_name: str    # The temporary filename saved on the server
    parsed_items: List[ReceiptItem] = []
    # Add other fields from ReceiptExtractionResult if needed for manual override


class ReceiptItemCategorizationRequest(BaseModel):
    org_id: int
    merchant_name: str
    expense_date: date
    amount: float
    category_id: int
    description: Optional[str] = None
    method: PaymentMethod
    receipt_url: Optional[str] = None

@router.post("/parse-receipt", response_model=ParseReceiptResponse)
async def parse_receipt_endpoint(file: UploadFile = File(...)):
    """
    Uploads a receipt image and parses it using the AI engine.
    Returns the structured data and a temporary file reference.
    """
    parser = get_receipt_parser()
    temp_file_name: Optional[str] = None
    try:
        parsed_data, temp_file_name = await parser.process_receipt(file)
        
        return ParseReceiptResponse(parsed_data=parsed_data, temp_file_name=temp_file_name)
    except TimeoutError as e:
        if temp_file_name:
            parser.cleanup_temp_file(temp_file_name)
        raise HTTPException(status_code=504, detail=str(e))
    except ValueError as e:
        if temp_file_name:
            parser.cleanup_temp_file(temp_file_name)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if temp_file_name:
            parser.cleanup_temp_file(temp_file_name)
        raise HTTPException(status_code=500, detail=f"Error parsing receipt: {e}")


@router.post("/receipt-items")
async def create_receipt_item(request: ReceiptItemCategorizationRequest):
    """
    Persist a single categorized receipt line item as an expense entry.
    Only categorized lines are written; uncategorized items are ignored.
    """
    try:
        expense_id = expense_repo.insert({
            "org_id": request.org_id,
            "expense_date": request.expense_date,
            "amount": request.amount,
            "category_id": request.category_id,
            "description": request.description or request.merchant_name,
            "method": request.method,
            "receipt_url": request.receipt_url,
        })
        return {"expense_id": expense_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving categorized item: {e}")


@router.delete("/receipt-items/{expense_id}")
async def delete_receipt_item(expense_id: int):
    """Remove a previously stored categorized receipt line item."""
    try:
        expense_repo.delete(expense_id)
        return {"success": True, "expense_id": expense_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting categorized item: {e}")


@router.post("/save-receipt")
async def save_receipt_endpoint(request: SaveReceiptRequest):
    """
    Saves the parsed receipt data and creates an expense entry in the database.
    Moves the temporary receipt file to permanent storage.
    """
    parser = get_receipt_parser()
    try:
        permanent_receipt_url = await parser.move_temp_file_to_permanent(
            request.temp_file_name,
            request.original_file_name,
            "application/octet-stream"
        )

        categorized_items = [
            item for item in request.parsed_items
            if getattr(item, "category_id", None) is not None
        ]

        if not categorized_items:
            parser.cleanup_temp_file(request.temp_file_name)
            raise HTTPException(
                status_code=400,
                detail="No categorized items provided; uncategorized lines are ignored."
            )

        created_expense_ids: List[int] = []
        for item in categorized_items:
            data = {
                "org_id": request.org_id,
                "expense_date": request.expense_date,
                "amount": item.line_total,
                "category_id": item.category_id,
                "description": item.description or request.merchant_name,
                "method": request.payment_method,
                "receipt_url": permanent_receipt_url,
            }

            item_expense_id = getattr(item, "expense_id", None)
            if item_expense_id:
                expense_repo.update(item_expense_id, data)
                expense_id = item_expense_id
            else:
                expense_id = expense_repo.insert(data)

            created_expense_ids.append(expense_id)

        primary_expense_id = created_expense_ids[0]
        receipt_metadata_repo.create(
            expense_id=primary_expense_id,
            model_name="gemini-1.5-flash",
            model_provider="google",
            engine_version=None,
            parsing_confidence=None,
            field_confidence=None,
            raw_response=None,
        )

        parser.cleanup_temp_file(request.temp_file_name)

        return JSONResponse(content={
            "expense_ids": created_expense_ids,
            "receipt_url": permanent_receipt_url,
            "status": "created",
            "message": "Categorized expenses saved successfully"
        }, status_code=201)
    except HTTPException:
        raise
    except Exception as e:
        # If an error occurs, attempt to clean up the temp file
        parser.cleanup_temp_file(request.temp_file_name)
        raise HTTPException(status_code=500, detail=f"Error saving expense: {e}")

@router.get("/receipts/file/{year}/{month}/{filename}")
async def serve_receipt_file(year: str, month: str, filename: str):
    """
    Serves a stored receipt file.
    """
    file_path = os.path.join(settings.RECEIPT_UPLOAD_DIR, year, month, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Receipt file not found")
    
    # Basic security check: ensure file is within the designated upload directory
    # and not an arbitrary path.
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.RECEIPT_UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Access denied.")

    return FileResponse(file_path)

@router.get("/receipts/{expense_id}")
async def get_receipt_metadata(expense_id: int):
    """
    Retrieves receipt metadata by expense ID.
    """
    metadata = receipt_metadata_repo.get_by_expense_id(expense_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Receipt metadata not found")
    return metadata

@router.delete("/receipts/{expense_id}")
async def delete_receipt(expense_id: int):
    """
    Deletes a receipt and its associated metadata and expense entry.
    """
    # First, get the expense to find the receipt_url
    expense = expense_repo.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    receipt_url = expense.get("receipt_url")
    if receipt_url:
        full_path = os.path.join(settings.RECEIPT_UPLOAD_DIR, receipt_url.replace("receipts/", "", 1))
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"Deleted receipt file: {full_path}")

    # Delete metadata
    receipt_metadata_repo.delete_by_expense_id(expense_id)
    # Delete expense
    expense_repo.delete(expense_id)

    return JSONResponse(content={"message": "Receipt and expense deleted successfully"}, status_code=200)
