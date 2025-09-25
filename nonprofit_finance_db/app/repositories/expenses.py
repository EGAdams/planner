from typing import List
from .base import BaseRepository
from app.db import query_all

class ExpenseRepository(BaseRepository):
    table = "expenses"

    def list_by_period(self, org_id: int, start: str, end: str) -> List[dict]:
        where = "org_id=%s AND expense_date BETWEEN %s AND %s"
        return self.list(where, (org_id, start, end), limit=1000)

    def sum_by_category(self, org_id: int, start: str, end: str) -> List[dict]:
        sql = """
        SELECT c.name AS category, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON c.id=e.category_id
        WHERE e.org_id=%s AND e.expense_date BETWEEN %s AND %s
        GROUP BY c.name
        ORDER BY total DESC
        """
        return query_all(sql, (org_id, start, end))