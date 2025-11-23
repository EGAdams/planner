from pdf_extractor.docling_extractor import DoclingPDFExtractor


def test_extracts_account_summary_from_statement_text():
    extractor = DoclingPDFExtractor(org_id=1)
    text = """04/22 Beginning Balance $74,260.12 Number of Days in Period 30
 4 Checks $(614.99)
 26 Withdrawals / Debits $(4,506.60)
 6 Deposits / Credits $10,794.00
 05/21 Ending Balance $79,932.53"""

    summary = extractor._extract_account_summary_from_text(text)

    assert summary["beginning_balance"] == 74260.12
    assert summary["ending_balance"] == 79932.53
    assert summary["checks"]["count"] == 4
    assert summary["checks"]["total"] == 614.99
    assert summary["withdrawals"]["count"] == 26
    assert summary["withdrawals"]["total"] == 4506.6
    assert summary["deposits"]["count"] == 6
    assert summary["deposits"]["total"] == 10794.0


def test_extracts_account_summary_when_amounts_precede_labels():
    extractor = DoclingPDFExtractor(org_id=1)
    text = """
    ## Account Summary - 7735938

    $74,260.12

    $(614.99)

    $(4,506.60)

    $10,794.00

    $79,932.53

    04/22

    4

    26

    6

    05/21

    Beginning Balance

    Checks

    Withdrawals / Debits

    Deposits / Credits

    Ending Balance
    """

    summary = extractor._extract_account_summary_from_text(text)

    assert summary["beginning_balance"] == 74260.12
    assert summary["ending_balance"] == 79932.53
    assert summary["checks"]["count"] == 4
    assert summary["checks"]["total"] == 614.99
    assert summary["withdrawals"]["count"] == 26
    assert summary["withdrawals"]["total"] == 4506.6
    assert summary["deposits"]["count"] == 6
    assert summary["deposits"]["total"] == 10794.0
