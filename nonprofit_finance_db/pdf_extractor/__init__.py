"""
PDF Extractor Module

This module provides PDF document extraction capabilities using Docling.
It's designed with a single responsibility: parsing PDF documents and extracting
structured data including text, tables, and metadata.
"""

from .docling_extractor import DoclingPDFExtractor

__all__ = ["DoclingPDFExtractor"]