import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from pydantic import BaseModel, ValidationError
import sys
from pathlib import Path
# Add parent backend directory to path for standalone imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.receipt_models import ReceiptExtractionResult, PaymentMethod, ReceiptItem, ReceiptTotals, ReceiptPartyInfo, ReceiptMeta
from config import settings

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
        
        # Try models in order of preference (best OCR accuracy first)
        # Updated to use Gemini 2.5/2.0 models (1.5 models are deprecated)
        # Using flash first to avoid pro quota limits
        model_names = [
            'gemini-2.5-flash',  # Try flash first (separate quota)
            'gemini-2.0-flash',
            'gemini-2.5-pro',
            'gemini-pro-latest'
        ]
        
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"Successfully initialized Gemini model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {e}")
                continue
        
        if not self.model:
            raise ValueError(f"Could not initialize any Gemini model. Tried: {model_names}")

    async def parse_receipt(self, image_data: bytes, image_mime_type: str) -> ReceiptExtractionResult:
        prompt = self._get_prompt()
        image_part = {
            'mime_type': image_mime_type,
            'data': image_data
        }
        
        contents = [prompt, image_part]

        try:
            # Lower temperature for more deterministic, accurate OCR
            response = await self.model.generate_content_async(contents,
                                                                generation_config={
                                                                    "response_mime_type": "application/json",
                                                                    "temperature": 0.1,
                                                                    "top_p": 0.8,
                                                                    "top_k": 20
                                                                })
            
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
        You are an expert at extracting structured data from receipt images with EXTREME ACCURACY.
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
        
        CRITICAL OCR ACCURACY RULES:
        
        **DIGIT CONFUSION PREVENTION** (MOST IMPORTANT):
        - Be EXTREMELY careful distinguishing these commonly confused digits:
          * 4 vs 9 (4 is angular, 9 is curved at top)
          * 3 vs 8 (3 has two curves, 8 has two loops)
          * 5 vs 6 (5 has flat top, 6 is fully curved)
          * 0 vs 8 (0 is oval, 8 has two loops)
          * 1 vs 7 (7 has horizontal top bar)
        - When you see a price, ZOOM IN mentally and examine each digit carefully
        - Cross-reference prices with the line total: if quantity=1 and unit_price doesn't match line_total, you made an OCR error
        - Grocery items typically cost $0.99-$15.99, use this context to validate readings
        
        **VERIFICATION STEPS** (MANDATORY):
        1. After extracting each item, verify: quantity × unit_price = line_total
        2. After extracting all items, verify: sum of line_totals ≈ subtotal (within $0.50)
        3. If verification fails, RE-READ the receipt more carefully before finalizing
        4. Pay special attention to items with prices ending in .49, .99, .89, .79 - these are common grocery prices
        
        **EXTRACTION RULES**:
        - ONLY extract items that are CLEARLY VISIBLE on the receipt as purchased items or discounts
        - DO NOT create "balancing" items, "unidentified" items, or phantom items to make totals match
        - DO NOT invent items like "UNIDENTIFIED ITEM", "MISC FEE", or similar
        - If the totals don't match the sum of items after careful verification, that's OK - just extract what you see accurately
        - Negative prices are OK for discounts/coupons (e.g., "COUPON -$1.39")
        - For `payment_method`, choose from the exact enum values: "CASH", "CARD", "BANK", "OTHER"
        - If a field is optional and not found, set it to `null`
        - `line_total` should be `quantity * unit_price`
        - `currency` should default to "USD" if not explicitly found
        - Provide `model_name`, `model_provider`, `engine_version` in `meta` if available from the tool
        - Do not include any other text or explanation, just the JSON object
        
        **FINAL CHECK**: Before returning the JSON, ask yourself: "Did I carefully examine each digit in every price? Did I verify the math?"
        """