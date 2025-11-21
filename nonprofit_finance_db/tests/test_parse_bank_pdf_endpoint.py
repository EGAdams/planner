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
            {"date": "2024-01-01", "description": "Deposit", "amount": 100.0},
            {"date": "2024-01-02", "description": "Rent", "amount": -50.0},
        ]

    def extract_account_info(self, _path: str):
        return {"account_number": "****1234"}


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
    assert len(data["transactions"]) == 2
    assert data["totals"]["sum"] == 50.0
    assert data["totals"]["debits"] == 50.0
    assert data["totals"]["credits"] == 100.0


def test_parse_bank_pdf_rejects_non_pdf():
    client = TestClient(api_server.app)
    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    resp = client.post("/api/parse-bank-pdf", files=files)
    assert resp.status_code == 400
