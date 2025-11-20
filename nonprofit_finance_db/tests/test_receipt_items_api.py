import unittest
from unittest import mock

from fastapi.testclient import TestClient

from nonprofit_finance_db.api_server import app


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


if __name__ == "__main__":
    unittest.main()
