from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("DB_PORT", "3306"))
    user: str = os.getenv("NON_PROFIT_USER", "root")
    password: str = os.getenv("NON_PROFIT_PASSWORD", "")
    database: str = os.getenv("NON_PROFIT_DB_NAME", "nonprofit_finance")
    pool_size: int = int(os.getenv("POOL_SIZE", "5"))

settings = Settings()