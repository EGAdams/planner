"""
Gemini 2.5-backed fallback extractor for bank statements.

This is invoked only when Docling returns no usable transactions.
It takes Docling's extracted text and asks Gemini to emit a minimal JSON array
of transactions so we can still proceed with ingestion.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Sequence

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiBankFallback:
    def __init__(self, model_names: Sequence[str] | None = None) -> None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set for Gemini fallback")

        genai.configure(api_key=api_key)
        candidates = model_names or [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest",
        ]
        self.model = self._init_model(candidates)

    def _init_model(self, candidates: Sequence[str]):
        last_error = None
        for name in candidates:
            try:
                logger.info("Initializing Gemini fallback model: %s", name)
                return genai.GenerativeModel(name)
            except Exception as exc:  # pragma: no cover - defensive log path
                last_error = exc
                logger.warning("Failed to init Gemini model %s: %s", name, exc)
        raise RuntimeError(f"Could not initialize any Gemini model: {last_error}")

    def parse_transactions(self, statement_text: str) -> List[Dict[str, Any]]:
        """
        Parse transaction lines from statement text via Gemini.

        Args:
            statement_text: Plain/markdown text extracted from the PDF.

        Returns:
            List of transaction dicts with keys: date, description, amount.
        """
        if not statement_text or not statement_text.strip():
            return []

        prompt = self._prompt()
        trimmed = statement_text[-15000:]  # keep tail where transactions often appear
        contents = [prompt, trimmed]

        try:
            response = self.model.generate_content(
                contents,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0,
                },
            )
            payload = response.text or ""
            data = json.loads(payload)
            transactions = data if isinstance(data, list) else data.get("transactions", [])
            return self._coerce_transactions(transactions)
        except Exception as exc:
            logger.error("Gemini fallback parsing failed: %s", exc)
            return []

    def _coerce_transactions(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []
        for row in rows:
            try:
                date_val = row.get("date") or row.get("transaction_date")
                amount_val = row.get("amount")
                desc_val = row.get("description") or row.get("memo") or ""
                if not date_val or amount_val is None:
                    continue
                cleaned.append(
                    {
                        "date": date_val,
                        "amount": amount_val,
                        "description": str(desc_val),
                    }
                )
            except Exception:
                continue
        return cleaned

    def _prompt(self) -> str:
        return (
            "Extract bank statement transactions and output ONLY JSON.\n"
            "Respond with an array of objects: "
            "[{ \"date\": \"YYYY-MM-DD or MM/DD/YYYY\", "
            "\"description\": \"text\", "
            "\"amount\": number }]\n"
            "- Use negative amounts for debits/withdrawals, positive for credits/deposits.\n"
            "- Do not invent rows; only include real transactions.\n"
            "- If you cannot find transactions, return an empty array."
        )

