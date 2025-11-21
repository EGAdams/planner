from pdf_extractor.docling_extractor import DoclingPDFExtractor


def test_withdrawal_tables_are_negative():
    extractor = DoclingPDFExtractor(org_id=1)
    tables = [[
        [
            ["Withdrawals / Debits.Date", "Withdrawals / Debits.Amount", "Description"],
            ["04/24", "200.00", "ATM WITHDRAWAL"],
            ["04/25", "33.82", "DEBIT CARD PURCHASE"],
        ]
    ]]

    txns = extractor._parse_transactions_from_tables(tables, None, None)
    amounts = [t["amount"] for t in txns]

    assert amounts == [-200.0, -33.82]


def test_deposit_tables_stay_positive():
    extractor = DoclingPDFExtractor(org_id=1)
    tables = [[
        [
            ["Deposits / Credits.Date", "Deposits / Credits.Amount", "Description"],
            ["05/02", "100.00", "TRANSFER FROM SAVINGS"],
        ]
    ]]

    txns = extractor._parse_transactions_from_tables(tables, None, None)
    assert [t["amount"] for t in txns] == [100.0]


def test_generic_rows_use_description_keywords_for_sign():
    extractor = DoclingPDFExtractor(org_id=1)
    tables = [[
        [
            ["Date", "Amount", "Description"],
            ["05/13", "14.99", "Check #9339"],
            ["05/14", "200.00", "DEBIT CARD PURCHASE AT STORE"],
            ["05/15", "50.00", "REFUND - CARD CREDIT"],
        ]
    ]]

    txns = extractor._parse_transactions_from_tables(tables, None, None)
    amounts = [t["amount"] for t in txns]

    assert amounts == [-14.99, -200.0, 50.0]


def test_multiple_checks_in_one_row_are_split():
    extractor = DoclingPDFExtractor(org_id=1)
    tables = [[
        [
            ["Checks", "Date Paid", "Amount", "Number", "Date Paid", "Amount"],
            ["9338 i", "05/16", "200.00", "9340 i", "04/22", "200.00", "9341 i", "05/14", "200.00"],
        ]
    ]]

    txns = extractor._parse_transactions_from_tables(tables, None, None)
    amounts = [t["amount"] for t in txns]
    descriptions = [t["description"] for t in txns]

    assert amounts == [-200.0, -200.0, -200.0]
    assert descriptions == ["Check #9338", "Check #9340", "Check #9341"]
