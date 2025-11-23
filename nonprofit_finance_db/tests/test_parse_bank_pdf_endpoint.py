import io

import pytest
from fastapi.testclient import TestClient

import api_server


class DummyPDFParser:
    def __init__(self, org_id: int):
        self.org_id = org_id
        self.validate_called = False
        self.parse_called = False

    def validate_format(self, _path: str) -> bool:
        self.validate_called = True
        return True

    def parse(self, _path: str):
        self.parse_called = True
        return [
            {"date": "2024-01-01", "description": "Check #1001", "amount": -200.0, "bank_item_type": "CHECK"},
            {"date": "2024-01-02", "description": "Groceries", "amount": -50.0, "bank_item_type": "WITHDRAWAL"},
            {"date": "2024-01-03", "description": "Deposit", "amount": 300.0, "bank_item_type": "DEPOSIT"},
            {"date": "2024-01-04", "description": "Refund", "amount": 150.0},  # implicit deposit
        ]

    def extract_account_info(self, _path: str):
        return {
            "account_number": "****1234",
            "summary": {
                "beginning_balance": 1000.00,
                "ending_balance": 1200.00,
                "checks": {"count": 1, "total": 200.00},
                "withdrawals": {"count": 1, "total": 50.00},
                "deposits": {"count": 2, "total": 450.00},
            },
        }


@pytest.fixture(autouse=True)
def patch_parser(monkeypatch):
    monkeypatch.setattr(api_server, "PDFParser", DummyPDFParser)


def test_parse_bank_pdf_endpoint(monkeypatch):
    client = TestClient(api_server.app)
    pdf_bytes = b"%PDF-FAKE"
    files = {"file": ("statement.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    resp = client.post("/api/parse-bank-pdf", files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["transactions"]) == 4
    assert data["totals"]["sum"] == 200.0
    assert data["totals"]["debits"] == 250.0
    assert data["totals"]["credits"] == 450.0

    breakdown = data["verification"]["calculated"]
    assert breakdown["checks"]["count"] == 1
    assert breakdown["checks"]["total"] == 200.0
    assert breakdown["withdrawals"]["count"] == 1
    assert breakdown["withdrawals"]["total"] == 50.0
    assert breakdown["deposits"]["count"] == 2
    assert breakdown["deposits"]["total"] == 450.0
    assert data["verification"]["ending_balance_calculated"] == 1200.0
    assert data["verification"]["passes"] is True


def test_parse_bank_pdf_rejects_non_pdf():
    client = TestClient(api_server.app)
    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    resp = client.post("/api/parse-bank-pdf", files=files)
    assert resp.status_code == 400
