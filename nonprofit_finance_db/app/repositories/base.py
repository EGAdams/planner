from typing import Any, Dict, List, Optional, Tuple
from app.db import query_one, query_all, execute

class BaseRepository:
    table: str
    pk: str = "id"

    def get(self, _id: int) -> Optional[dict]:
        sql = f"SELECT * FROM {self.table} WHERE {self.pk}=%s"
        return query_one(sql, (_id,))

    def list(self, where: str = "", params: Tuple = (), limit: int = 100, offset: int = 0) -> List[dict]:
        sql = f"SELECT * FROM {self.table}"
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
        return query_all(sql, (*params, limit, offset))

    def delete(self, _id: int) -> int:
        sql = f"DELETE FROM {self.table} WHERE {self.pk}=%s"
        return execute(sql, (_id,))

    def insert(self, data: Dict[str, Any]) -> int:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        return execute(sql, tuple(data.values()))

    def update(self, _id: int, data: Dict[str, Any]) -> int:
        sets = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {self.table} SET {sets} WHERE {self.pk}=%s"
        return execute(sql, (*data.values(), _id))