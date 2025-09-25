from typing import Any, Optional, Tuple, List
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from app.config import settings

_pool: Optional[MySQLConnectionPool] = None

def _ensure_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name="np_pool",
            pool_size=settings.pool_size,
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=settings.password,
            database=settings.database,
            autocommit=False,
        )
    return _pool

def get_connection():
    pool = _ensure_pool()
    return pool.get_connection()

def query_one(sql: str, params: Optional[Tuple[Any, ...]] = None):
    with get_connection() as cnx:
        with cnx.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def query_all(sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[dict]:
    with get_connection() as cnx:
        with cnx.cursor(dictionary=True) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def execute(sql: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid if available, else affected rows."""
    with get_connection() as cnx:
        with cnx.cursor() as cur:
            cur.execute(sql, params or ())
            last_id = cur.lastrowid
            cnx.commit()
            return last_id if last_id else cur.rowcount