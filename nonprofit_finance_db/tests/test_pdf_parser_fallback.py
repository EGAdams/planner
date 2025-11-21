import types

from parsers.pdf_parser import PDFParser


class DummyExtractor:
    def parse_transactions(self, _file_path):
        return []

    def extract_text(self, _file_path):
        return "01/02/2024 - Check deposit 250.00\n01/03/2024 - Grocery -45.32"


class DummyGeminiFallback:
    def __init__(self):
        self.called = False

    def parse_transactions(self, _text):
        self.called = True
        return [
            {"date": "2024-01-02", "description": "Check deposit", "amount": 250.00},
            {"date": "01/03/2024", "description": "Grocery", "amount": -45.32},
        ]


def test_pdf_parser_uses_gemini_when_docling_empty(monkeypatch):
    parser = PDFParser(org_id=99)

    # swap heavy dependencies with lightweight fakes
    parser.extractor = DummyExtractor()
    dummy_fallback = DummyGeminiFallback()
    parser.gemini_fallback = dummy_fallback

    result = parser.parse("irrelevant.pdf")

    assert dummy_fallback.called is True
    assert len(result) == 2
    amounts = sorted(txn["amount"] for txn in result)
    assert amounts == [-45.32, 250.0]

