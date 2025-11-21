"""
PDF Extractor Module

This module provides PDF document extraction capabilities using Docling.
It also exposes a Gemini 2.5 fallback for scenarios where Docling yields no
transactions.
"""

try:
    from .docling_extractor import DoclingPDFExtractor
except Exception as exc:  # pragma: no cover - docling optional in tests
    DoclingPDFExtractor = None
    __docling_import_error__ = exc
from .gemini_bank_fallback import GeminiBankFallback

__all__ = ["GeminiBankFallback"]
if DoclingPDFExtractor:
    __all__.append("DoclingPDFExtractor")
