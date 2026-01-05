import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from PIL import Image
from datetime import date
import json
import shutil

from app.services.receipt_engine import ReceiptEngine, GeminiReceiptEngine
from app.services.receipt_parser import ReceiptParser
from app.models.receipt_models import ReceiptExtractionResult, PaymentMethod, ReceiptItem, ReceiptTotals, ReceiptPartyInfo, ReceiptMeta
from app.config import settings

# Mock settings for testing
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('nonprofit_finance_db.app.config.settings') as mock_settings:
        mock_settings.RECEIPT_UPLOAD_DIR = "/tmp/test_receipt_uploads"
        mock_settings.RECEIPT_TEMP_UPLOAD_DIR = "/tmp/test_receipt_temp_uploads"
        mock_settings.RECEIPT_MAX_SIZE_MB = 5
        mock_settings.RECEIPT_IMAGE_MAX_WIDTH_PX = 1600
        mock_settings.RECEIPT_IMAGE_MAX_HEIGHT_PX = 1600
        yield mock_settings
    # Clean up test directories after tests
    if os.path.exists("/tmp/test_receipt_uploads"):
        shutil.rmtree("/tmp/test_receipt_uploads")
    if os.path.exists("/tmp/test_receipt_temp_uploads"):
        shutil.rmtree("/tmp/test_receipt_temp_uploads")

@pytest.fixture
def mock_gemini_response():
    return {
        "transaction_date": "2023-10-26",
        "payment_method": "CARD",
        "party": {
            "merchant_name": "Example Store",
            "merchant_phone": None,
            "merchant_address": "123 Main St",
            "store_location": "Anytown"
        },
        "items": [
            {"description": "Item A", "quantity": 1.0, "unit_price": 10.0, "line_total": 10.0},
            {"description": "Item B", "quantity": 2.0, "unit_price": 5.0, "line_total": 10.0}
        ],
        "totals": {
            "subtotal": 20.0,
            "tax_amount": 1.5,
            "tip_amount": 0.0,
            "discount_amount": 0.0,
            "total_amount": 21.5
        },
        "meta": {
            "currency": "USD",
            "receipt_number": "R12345",
            "model_name": None,
            "model_provider": None,
            "engine_version": None,
            "raw_text": None
        }
    }

@pytest.fixture
def mock_upload_file(mocker):
    mock_file = mocker.MagicMock(spec=UploadFile)
    mock_file.filename = "test_receipt.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.file = BytesIO(b"fake image data")
    mock_file.read = AsyncMock(return_value=b"fake image data")
    return mock_file

@pytest.fixture
def mock_image_file():
    img_buffer = BytesIO()
    Image.new('RGB', (100, 100), color = 'red').save(img_buffer, format="JPEG")
    img_buffer.seek(0)
    return img_buffer.getvalue()

@pytest.fixture
def mock_large_image_file():
    img_buffer = BytesIO()
    Image.new('RGB', (2000, 2000), color = 'blue').save(img_buffer, format="JPEG")
    img_buffer.seek(0)
    return img_buffer.getvalue()

@pytest.mark.asyncio
async def test_gemini_receipt_engine_parse_receipt_success(mock_gemini_response, mock_image_file):
    with patch('google.generativeai.GenerativeModel') as MockGenerativeModel:
        mock_model_instance = MockGenerativeModel.return_value
        mock_response_object = MagicMock()
        mock_response_object.text = json.dumps(mock_gemini_response)
        mock_model_instance.generate_content_async = AsyncMock(return_value=mock_response_object)
        mock_model_instance.model_name = "gemini-1.5-flash"

        engine = GeminiReceiptEngine()
        result = await engine.parse_receipt(mock_image_file, "image/jpeg")

        assert isinstance(result, ReceiptExtractionResult)
        assert result.party.merchant_name == "Example Store"
        assert result.totals.total_amount == 21.5
        assert result.meta.model_name == "gemini-1.5-flash"
        mock_model_instance.generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_gemini_receipt_engine_parse_receipt_validation_error(mock_image_file):
    with patch('google.generativeai.GenerativeModel') as MockGenerativeModel:
        mock_model_instance = MockGenerativeModel.return_value
        mock_response_object = MagicMock()
        # Malformed JSON to trigger Pydantic validation error
        mock_response_object.text = '{"transaction_date": "invalid-date"}'
        mock_model_instance.generate_content_async = AsyncMock(return_value=mock_response_object)
        mock_model_instance.model_name = "gemini-1.5-flash"

        engine = GeminiReceiptEngine()
        with pytest.raises(Exception, match="Pydantic validation error"):
            await engine.parse_receipt(mock_image_file, "image/jpeg")

@pytest.mark.asyncio
async def test_receipt_parser_validate_file_unsupported_type(mock_upload_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    mock_upload_file.content_type = "text/plain"
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser._validate_file(mock_upload_file, 100)

@pytest.mark.asyncio
async def test_receipt_parser_validate_file_size_exceeded(mock_upload_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    with pytest.raises(ValueError, match="File size exceeds"):
        parser._validate_file(mock_upload_file, settings.RECEIPT_MAX_SIZE_MB * 1024 * 1024 + 1)

@pytest.mark.asyncio
async def test_receipt_parser_process_image_resizes(mock_large_image_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    processed_data, mime_type = await parser._process_image(mock_large_image_file, "image/jpeg")
    
    img = Image.open(BytesIO(processed_data))
    assert img.width <= settings.RECEIPT_IMAGE_MAX_WIDTH_PX
    assert img.height <= settings.RECEIPT_IMAGE_MAX_HEIGHT_PX
    assert mime_type == "image/jpeg"

@pytest.mark.asyncio
async def test_receipt_parser_save_temporary_receipt_file(mock_image_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    temp_filename = await parser._save_temporary_receipt_file(mock_image_file, "original.jpg", "image/jpeg")
    
    assert temp_filename.startswith("temp_receipt_")
    assert temp_filename.endswith(".jpg")
    assert os.path.exists(os.path.join(settings.RECEIPT_TEMP_UPLOAD_DIR, temp_filename))

@pytest.mark.asyncio
async def test_receipt_parser_move_temp_file_to_permanent(mock_image_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    temp_filename = await parser._save_temporary_receipt_file(mock_image_file, "original.jpg", "image/jpeg")
    
    permanent_path = await parser.move_temp_file_to_permanent(temp_filename, "original.jpg", "image/jpeg")
    
    assert permanent_path.startswith("receipts/")
    assert os.path.exists(os.path.join(settings.RECEIPT_UPLOAD_DIR, permanent_path.replace("receipts/", "", 1)))
    assert not os.path.exists(os.path.join(settings.RECEIPT_TEMP_UPLOAD_DIR, temp_filename))

@pytest.mark.asyncio
async def test_receipt_parser_cleanup_temp_file(mock_image_file):
    parser = ReceiptParser(GeminiReceiptEngine())
    temp_filename = await parser._save_temporary_receipt_file(mock_image_file, "original.jpg", "image/jpeg")
    
    parser.cleanup_temp_file(temp_filename)
    assert not os.path.exists(os.path.join(settings.RECEIPT_TEMP_UPLOAD_DIR, temp_filename))

@pytest.mark.asyncio
async def test_receipt_parser_process_receipt_e2e(mock_upload_file, mock_gemini_response):
    with patch('google.generativeai.GenerativeModel') as MockGenerativeModel:
        mock_model_instance = MockGenerativeModel.return_value
        mock_response_object = MagicMock()
        mock_response_object.text = json.dumps(mock_gemini_response)
        mock_model_instance.generate_content_async = AsyncMock(return_value=mock_response_object)
        mock_model_instance.model_name = "gemini-1.5-flash"

        parser = ReceiptParser(GeminiReceiptEngine())
        
        # Mock the file.read() to return the image data
        mock_upload_file.read = AsyncMock(return_value=Image.new('RGB', (100, 100), color = 'red').tobytes('jpeg', 'RGB'))
        
        parsed_data, temp_file_name = await parser.process_receipt(mock_upload_file)

        assert isinstance(parsed_data, ReceiptExtractionResult)
        assert parsed_data.party.merchant_name == "Example Store"
        assert temp_file_name.startswith("temp_receipt_")
        assert os.path.exists(os.path.join(settings.RECEIPT_TEMP_UPLOAD_DIR, temp_file_name))
        mock_model_instance.generate_content_async.assert_called_once()
