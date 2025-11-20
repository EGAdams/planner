from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("DB_PORT", "3306"))
    user: str = os.getenv("NON_PROFIT_USER", "root")
    password: str = os.getenv("NON_PROFIT_PASSWORD", "")
    database: str = os.getenv("NON_PROFIT_DB_NAME", "nonprofit_finance")
    pool_size: int = int(os.getenv("POOL_SIZE", "5"))

    # Receipt scanning settings
    RECEIPT_UPLOAD_DIR: str = os.getenv("RECEIPT_UPLOAD_DIR", "/tmp/receipt_uploads")
    RECEIPT_TEMP_UPLOAD_DIR: str = os.getenv("RECEIPT_TEMP_UPLOAD_DIR", "/tmp/receipt_temp_uploads")
    RECEIPT_MAX_SIZE_MB: int = int(os.getenv("RECEIPT_MAX_SIZE_MB", "5"))
    RECEIPT_IMAGE_MAX_WIDTH_PX: int = int(os.getenv("RECEIPT_IMAGE_MAX_WIDTH_PX", "1600"))
    RECEIPT_IMAGE_MAX_HEIGHT_PX: int = int(os.getenv("RECEIPT_IMAGE_MAX_HEIGHT_PX", "1600"))
    RECEIPT_PARSE_TIMEOUT_SECONDS: int = int(os.getenv("RECEIPT_PARSE_TIMEOUT_SECONDS", "15"))
    RECEIPT_RETENTION_DAYS: int = int(os.getenv("RECEIPT_RETENTION_DAYS", "2555")) # 7 years

settings = Settings()