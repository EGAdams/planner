import sys
from pathlib import Path

# Add the current directory to sys.path so we can import from nonprofit_finance_db
sys.path.insert(0, str(Path.cwd()))

try:
    from nonprofit_finance_db.app.config import settings
    print(f"DB_HOST: {settings.host}")
    print(f"DB_PORT: {settings.port}")
    print(f"NON_PROFIT_USER: {settings.user}")
    print(f"NON_PROFIT_PASSWORD: {settings.password}")
    print(f"NON_PROFIT_DB_NAME: {settings.database}")
except Exception as e:
    print(f"Error importing settings: {e}")
