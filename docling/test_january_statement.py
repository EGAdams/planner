#!/usr/bin/env python3
"""Print Docling parsing results for the January ROL statement as JSON."""
import json
import logging
import sys
from pathlib import Path
from contextlib import redirect_stdout

from docling.document_converter import DocumentConverter


def build_preview(markdown_text: str, max_lines: int = 12) -> str:
    """Return the first few non-empty lines as a compact preview snippet."""
    non_empty_lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    preview_lines = non_empty_lines[:max_lines]
    return "\n".join(preview_lines)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    pdf_path = repo_root / "january_rol_statement.PDF"

    logging.basicConfig(level=logging.INFO, stream=sys.stderr, force=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Expected PDF not found at {pdf_path}")

    converter = DocumentConverter()
    with redirect_stdout(sys.stderr):
        result = converter.convert(str(pdf_path))

    if result.document is None:
        raise RuntimeError("Docling did not return a document object.")

    document = result.document
    markdown_output = document.export_to_markdown()

    num_pages_attr = getattr(document, "num_pages", None)
    if callable(num_pages_attr):
        page_count = num_pages_attr()
    elif isinstance(num_pages_attr, int):
        page_count = num_pages_attr
    else:
        pages_attr = getattr(document, "pages", None)
        page_count = len(pages_attr) if pages_attr is not None else None

    table_count = len(getattr(document, "tables", []) or [])

    payload = {
        "document": pdf_path.name,
        "page_count": page_count,
        "table_count": table_count,
        "markdown_character_count": len(markdown_output),
        "errors": [str(err) for err in (result.errors or [])],
        "markdown_preview": build_preview(markdown_output),
        "markdown": markdown_output,
    }

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
