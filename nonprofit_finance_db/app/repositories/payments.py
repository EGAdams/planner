from typing import List
from .base import BaseRepository
from app.db import query_all

class PaymentRepository(BaseRepository):
    table = "payments"

    def sum_by_type(self, org_id: int, start: str, end: str) -> List[dict]:
        sql = """
        SELECT p.type AS payment_type, SUM(p.amount) AS total
        FROM payments p
        WHERE p.org_id=%s AND p.payment_date BETWEEN %s AND %s
        GROUP BY p.type
        ORDER BY total DESC
        """
        return query_all(sql, (org_id, start, end))