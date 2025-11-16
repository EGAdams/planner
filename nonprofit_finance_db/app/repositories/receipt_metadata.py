from typing import Any, Dict, Optional, Tuple
from app.repositories.base import BaseRepository
from app.models.receipt_models import ReceiptExtractionResult
from app.db.pool import query_one, execute # Import query_one and execute

class ReceiptMetadataRepository(BaseRepository):
    table = "receipt_metadata"

    def create(self, expense_id: int, model_name: str, model_provider: str,
               engine_version: Optional[str], parsing_confidence: Optional[float],
               field_confidence: Optional[Dict[str, Any]], raw_response: Optional[Dict[str, Any]]) -> int:
        data = {
            "expense_id": expense_id,
            "model_name": model_name,
            "model_provider": model_provider,
            "engine_version": engine_version,
            "parsing_confidence": parsing_confidence,
            "field_confidence": field_confidence,
            "raw_response": raw_response,
        }
        # Filter out None values to let DB defaults apply or handle NULLs correctly
        data = {k: v for k, v in data.items() if v is not None}
        return self.insert(data)

    def get_by_expense_id(self, expense_id: int) -> Optional[dict]:
        sql = f"SELECT * FROM {self.table} WHERE expense_id=%s"
        return query_one(sql, (expense_id,))

    def update_by_expense_id(self, expense_id: int, data: Dict[str, Any]) -> int:
        sets = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {self.table} SET {sets} WHERE expense_id=%s"
        return execute(sql, (*data.values(), expense_id))

    def delete_by_expense_id(self, expense_id: int) -> int:
        sql = f"DELETE FROM {self.table} WHERE expense_id=%s"
        return execute(sql, (expense_id,))
