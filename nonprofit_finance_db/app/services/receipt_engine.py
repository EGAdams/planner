import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from app.models.receipt_models import ReceiptExtractionResult, PaymentMethod, ReceiptItem, ReceiptTotals, ReceiptPartyInfo, ReceiptMeta
from app.config import settings

class ReceiptEngine(ABC):
    """Abstract base class for receipt parsing engines."""

    @abstractmethod
    async def parse_receipt(self, image_data: bytes, image_mime_type: str) -> ReceiptExtractionResult:
        """
        Parses a receipt image and extracts structured data.

        Args:
            image_data: The raw bytes of the receipt image.
            image_mime_type: The MIME type of the image (e.g., "image/jpeg", "application/pdf").

        Returns:
            A ReceiptExtractionResult object containing the parsed data.
        """
        pass

class GeminiReceiptEngine(ReceiptEngine):
    """
    Receipt parsing engine using Google's Gemini API.
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        # Using gemini-flash-latest - Pro model not available in current API version
        # Flash is less accurate but still good, and much faster/cheaper
        self.model = genai.GenerativeModel('gemini-flash-latest')

    async def parse_receipt(self, image_data: bytes, image_mime_type: str) -> ReceiptExtractionResult:
        prompt = self._get_prompt()
        image_part = {
            'mime_type': image_mime_type,
            'data': image_data
        }
        
        contents = [prompt, image_part]

        try:
            response = await self.model.generate_content_async(contents,
                                                                generation_config={"response_mime_type": "application/json"})
            
            # Assuming the response is directly the JSON string
            json_response = response.text
            
            # Validate and parse with Pydantic
            parsed_data = ReceiptExtractionResult.model_validate_json(json_response)
            
            # Populate meta information
            parsed_data.meta.model_name = self.model.model_name
            parsed_data.meta.model_provider = "google"
            # parsed_data.meta.engine_version = ... (Gemini API doesn't expose this directly in model_name)

            return parsed_data
        except ValidationError as e:
            print(f"Pydantic validation error: {e.json()}")
            raise
        except Exception as e:
            print(f"Error parsing receipt with Gemini: {e}")
            raise

    def _get_prompt(self) -> str:
        # This prompt instructs Gemini to extract structured data from a receipt image.
        # It's crucial to be very specific about the desired JSON format.
        return """
        You are an expert at extracting structured data from receipt images.
        Your task is to parse the provided receipt image and return the extracted information
        as a JSON object that strictly conforms to the following Pydantic model schema:

        ```json
        {
            "transaction_date": "YYYY-MM-DD",
            "payment_method": "CASH" | "CARD" | "BANK" | "OTHER",
            "party": {
                "merchant_name": "string",
                "merchant_phone": "string | null",
                "merchant_address": "string | null",
                "store_location": "string | null"
            },
            "items": [
                {
                    "description": "string",
                    "quantity": "float",
                    "unit_price": "float",
                    "line_total": "float"
                }
            ],
            "totals": {
                "subtotal": "float",
                "tax_amount": "float | null",
                "tip_amount": "float | null",
                "discount_amount": "float | null",
                "total_amount": "float"
            },
            "meta": {
                "currency": "string",
                "receipt_number": "string | null",
                "model_name": "string | null",
                "model_provider": "string | null",
                "engine_version": "string | null",
                "raw_text": "string | null"
            }
        }
        ```
        
        CRITICAL RULES:
        - ONLY extract items that are CLEARLY VISIBLE on the receipt as purchased items or discounts
        - DO NOT create "balancing" items, "unidentified" items, or phantom items to make totals match
        - DO NOT invent items like "UNIDENTIFIED ITEM", "MISC FEE", or similar
        - If the totals don't match the sum of items, that's OK - just extract what you see
        - Be VERY CAREFUL with OCR - double-check prices and quantities
        - Negative prices are OK for discounts/coupons (e.g., "COUPON -$1.39")
        - For `payment_method`, choose from the exact enum values: "CASH", "CARD", "BANK", "OTHER"
        - If a field is optional and not found, set it to `null`
        - `line_total` should be `quantity * unit_price`
        - `currency` should default to "USD" if not explicitly found
        - Provide `model_name`, `model_provider`, `engine_version` in `meta` if available from the tool
        - Do not include any other text or explanation, just the JSON object
        - Take your time to read prices carefully - OCR errors are common with similar-looking digits (e.g., 8 vs 9)
        """