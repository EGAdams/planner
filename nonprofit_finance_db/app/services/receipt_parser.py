import os
from datetime import datetime
from typing import Tuple
from PIL import Image
from io import BytesIO
import mimetypes
import aiofiles
from fastapi import UploadFile

from app.config import settings
from app.models.receipt_models import ReceiptExtractionResult
from app.services.receipt_engine import ReceiptEngine, GeminiReceiptEngine

class ReceiptParser:
    def __init__(self, receipt_engine: ReceiptEngine):
        self.receipt_engine = receipt_engine
        self.upload_dir = settings.RECEIPT_UPLOAD_DIR
        self.temp_upload_dir = settings.RECEIPT_TEMP_UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.temp_upload_dir, exist_ok=True)

    async def process_receipt(self, file: UploadFile) -> Tuple[ReceiptExtractionResult, str]:
        # Read image data first to get size for validation
        image_data = await file.read()
        original_filename = file.filename
        mime_type = file.content_type
        file_size = len(image_data)

        # 1. Validate file
        self._validate_file(file, file_size)

        # 2. Save to temporary location
        temp_file_path = await self._save_temporary_receipt_file(image_data, original_filename, mime_type)

        # 3. Compress/normalize image (if it's an image) - read from temp file
        # For now, we'll process the original image_data, but in a more complex scenario
        # we might process the temp file.
        processed_image_data, processed_mime_type = await self._process_image(image_data, mime_type)

        # 4. Parse with AI engine
        parsed_data = await self.receipt_engine.parse_receipt(processed_image_data, processed_mime_type)

        return parsed_data, temp_file_path

    def _validate_file(self, file: UploadFile, file_size: int):
        if file.content_type not in ["image/jpeg", "image/png", "image/webp", "application/pdf"]:
            raise ValueError("Unsupported file type. Only JPG, PNG, WebP, and PDF are allowed.")
        
        max_size_bytes = settings.RECEIPT_MAX_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValueError(f"File size exceeds the maximum limit of {settings.RECEIPT_MAX_SIZE_MB} MB.")
        
        pass

    async def _process_image(self, image_data: bytes, mime_type: str) -> Tuple[bytes, str]:
        if mime_type.startswith("image/"):
            img = Image.open(BytesIO(image_data))
            
            # Resize if larger than max dimensions (settings.RECEIPT_IMAGE_MAX_WIDTH_PX, etc.)
            # Increased limits for better OCR accuracy
            max_width = settings.RECEIPT_IMAGE_MAX_WIDTH_PX * 2  # Double the resolution
            max_height = settings.RECEIPT_IMAGE_MAX_HEIGHT_PX * 2
            
            # Only downsize if image is too large, never upscale
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            output_buffer = BytesIO()
            # Use higher quality JPEG for better OCR
            if mime_type == "image/webp":
                img.save(output_buffer, format="WEBP", quality=95)  # Increased from 85
                return output_buffer.getvalue(), "image/webp"
            else:
                img.save(output_buffer, format="JPEG", quality=95)  # Increased from 85
                return output_buffer.getvalue(), "image/jpeg"
        elif mime_type == "application/pdf":
            # For PDFs, we might want to extract the first page as an image
            # This requires a PDF processing library like PyPDFium2 or similar
            # For now, we'll pass the PDF directly to the engine if it supports it.
            # If the engine expects an image, this part needs more robust implementation.
            # Assuming Gemini can handle PDF directly for now.
            return image_data, mime_type
        return image_data, mime_type # Fallback

    async def _save_temporary_receipt_file(self, image_data: bytes, original_filename: str, mime_type: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        
        # Sanitize filename
        base_name = os.path.splitext(original_filename)[0]
        sanitized_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        
        ext = mimetypes.guess_extension(mime_type)
        if not ext:
            ext = ".jpg" if mime_type.startswith("image/") else ".pdf"

        temp_filename = f"temp_receipt_{timestamp}_{sanitized_name}{ext}"
        full_temp_path = os.path.join(self.temp_upload_dir, temp_filename)
        
        async with aiofiles.open(full_temp_path, 'wb') as out_file:
            await out_file.write(image_data)
            
        return temp_filename # Return just the filename for temporary reference

    async def move_temp_file_to_permanent(self, temp_filename: str, original_filename: str, mime_type: str) -> str:
        temp_full_path = os.path.join(self.temp_upload_dir, temp_filename)
        if not os.path.exists(temp_full_path):
            raise FileNotFoundError(f"Temporary file not found: {temp_full_path}")

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        year_month = datetime.now().strftime("%Y/%m")
        
        # Sanitize filename
        base_name = os.path.splitext(original_filename)[0]
        sanitized_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        
        ext = mimetypes.guess_extension(mime_type)
        if not ext:
            ext = ".jpg" if mime_type.startswith("image/") else ".pdf"

        permanent_filename = f"receipt_{timestamp}_{sanitized_name}{ext}"
        
        storage_dir = os.path.join(self.upload_dir, year_month)
        os.makedirs(storage_dir, exist_ok=True)
        
        permanent_full_path = os.path.join(storage_dir, permanent_filename)
        
        os.rename(temp_full_path, permanent_full_path)
        
        return os.path.join("receipts", year_month, permanent_filename)

    def cleanup_temp_file(self, temp_filename: str):
        temp_full_path = os.path.join(self.temp_upload_dir, temp_filename)
        if os.path.exists(temp_full_path):
            os.remove(temp_full_path)
            print(f"Cleaned up temporary file: {temp_full_path}")
