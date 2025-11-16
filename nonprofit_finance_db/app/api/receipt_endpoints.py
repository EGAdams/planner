import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
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
receipt_engine = GeminiReceiptEngine()
receipt_parser = ReceiptParser(receipt_engine)
receipt_metadata_repo = ReceiptMetadataRepository()
expense_repo = ExpenseRepository() # Assuming this is available

class ParseReceiptResponse(BaseModel):
    parsed_data: ReceiptExtractionResult
    temp_file_name: str

class SaveReceiptRequest(BaseModel):
    org_id: int
    merchant_name: str
    expense_date: date
    total_amount: float
    tax_amount: Optional[float] = 0.0
    category_id: int
    payment_method: PaymentMethod
    description: Optional[str] = None
    original_file_name: str # The original filename from the user upload
    temp_file_name: str    # The temporary filename saved on the server
    parsed_items: List[ReceiptItem] = []
    # Add other fields from ReceiptExtractionResult if needed for manual override

@router.post("/parse-receipt", response_model=ParseReceiptResponse)
async def parse_receipt_endpoint(file: UploadFile = File(...)):
    """
    Uploads a receipt image and parses it using the AI engine.
    Returns the structured data and a temporary file reference.
    """
    try:
        parsed_data, temp_file_name = await receipt_parser.process_receipt(file)
        
        return ParseReceiptResponse(parsed_data=parsed_data, temp_file_name=temp_file_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing receipt: {e}")

@router.post("/save-receipt")
async def save_receipt_endpoint(request: SaveReceiptRequest):
    """
    Saves the parsed receipt data and creates an expense entry in the database.
    Moves the temporary receipt file to permanent storage.
    """
    try:
        # Move temporary file to permanent storage
        # We need the original filename and mime_type to correctly determine the permanent path and extension
        # For now, we'll assume the original_file_name from the request is sufficient.
        # In a more robust system, the mime_type would also be passed or derived from the temp file.
        permanent_receipt_url = await receipt_parser.move_temp_file_to_permanent(
            request.temp_file_name,
            request.original_file_name,
            "application/octet-stream" # Placeholder, actual mime_type should be stored with temp file
        )

        # Create expense entry
        expense_id = expense_repo.insert({
            "org_id": request.org_id,
            "expense_date": request.expense_date,
            "amount": request.total_amount,
            "category_id": request.category_id,
            "description": request.description,
            "method": request.payment_method,
            "receipt_url": permanent_receipt_url, # Use the permanent URL
        })

        # Save receipt metadata (assuming we have the full parsed data from the frontend)
        # This part needs to be refined. The frontend should send the full parsed_data
        # or we need to retrieve it from a temporary storage using receipt_file_path.
        # For now, let's assume we have enough info to save metadata.
        # In a real app, the parsed_data would be stored temporarily after /parse-receipt
        # and retrieved here.
        
        # Placeholder for metadata - needs actual parsed data
        receipt_metadata_repo.create(
            expense_id=expense_id,
            model_name="gemini-1.5-flash", # Hardcoded for now
            model_provider="google",
            engine_version=None,
            parsing_confidence=None,
            field_confidence=None,
            raw_response=None,
        )

        # Clean up temporary file
        receipt_parser.cleanup_temp_file(request.temp_file_name)

        return JSONResponse(content={
            "expense_id": expense_id,
            "receipt_url": permanent_receipt_url,
            "status": "created",
            "message": "Expense saved successfully"
        }, status_code=201)
    except Exception as e:
        # If an error occurs, attempt to clean up the temp file
        receipt_parser.cleanup_temp_file(request.temp_file_name)
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
