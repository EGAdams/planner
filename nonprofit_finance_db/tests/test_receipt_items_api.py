import unittest
from unittest import mock

from fastapi.testclient import TestClient

from nonprofit_finance_db.api_server import app
from nonprofit_finance_db.app.models.receipt_models import (
    ReceiptExtractionResult,
    ReceiptTotals,
    ReceiptPartyInfo,
    ReceiptMeta,
)
from nonprofit_finance_db.app.config import settings


class DummyExpenseRepo:
    def __init__(self):
        self.insert_calls = []
        self.delete_calls = []

    def insert(self, data):
        self.insert_calls.append(data)
        return 321

    def delete(self, expense_id):
        self.delete_calls.append(expense_id)
        return 1

    def update(self, expense_id, data):
        return 1


class ReceiptItemApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dummy_repo = DummyExpenseRepo()
        patcher = mock.patch(
            "nonprofit_finance_db.app.api.receipt_endpoints.expense_repo",
            self.dummy_repo,
        )
        patcher2 = mock.patch(
            "app.api.receipt_endpoints.expense_repo",
            self.dummy_repo,
        )
        self.addCleanup(patcher.stop)
        self.addCleanup(patcher2.stop)
        patcher.start()
        patcher2.start()

    def test_create_receipt_item_endpoint(self):
        payload = {
            "org_id": 1,
            "merchant_name": "Test Store",
            "expense_date": "2024-01-01",
            "amount": 12.34,
            "category_id": 10,
            "description": "Item desc",
            "method": "CARD",
            "receipt_url": None,
        }

        resp = self.client.post("/api/receipt-items", json=payload)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["expense_id"], 321)
        self.assertTrue(self.dummy_repo.insert_calls)

    def test_delete_receipt_item_endpoint(self):
        resp = self.client.delete("/api/receipt-items/999")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["expense_id"], 999)
        self.assertEqual(self.dummy_repo.delete_calls, [999])

    def test_receipt_extraction_defaults_payment_method(self):
        result = ReceiptExtractionResult(
            transaction_date="2024-02-03",
            payment_method=None,
            party=ReceiptPartyInfo(
                merchant_name="Store",
                merchant_phone=None,
                merchant_address=None,
                store_location=None,
            ),
            items=[],
            totals=ReceiptTotals(
                subtotal=1.0,
                tax_amount=0.0,
                tip_amount=0.0,
                discount_amount=0.0,
                total_amount=1.0,
            ),
            meta=ReceiptMeta(
                currency="USD",
                receipt_number=None,
                model_name=None,
                model_provider=None,
                engine_version=None,
                raw_text=None,
            ),
        )

        self.assertEqual(result.payment_method, "OTHER")

    def test_parse_receipt_timeout_returns_504(self):
        with mock.patch(
            "app.api.receipt_endpoints.receipt_parser.process_receipt",
            side_effect=TimeoutError(
                f"Receipt parsing exceeded {settings.RECEIPT_PARSE_TIMEOUT_SECONDS} seconds"
            ),
        ):
            resp = self.client.post(
                "/api/parse-receipt",
                files={"file": ("receipt.jpg", b"data", "image/jpeg")},
            )

        self.assertEqual(resp.status_code, 504)
        detail = resp.json().get("detail", "")
        self.assertIn("Receipt parsing exceeded", detail)


if __name__ == "__main__":
    unittest.main()
