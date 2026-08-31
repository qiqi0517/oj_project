import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
DATABASE_PATH = DATA_DIR / "oj.db"
TEMP_DIR = BASE_DIR / "temp"


SESSION_SECRET = os.getenv(
    "OJ_SESSION_SECRET",
    "development-only-secret"
)

INITIAL_ADMIN_USERNAME = os.getenv(
    "OJ_INITIAL_ADMIN_USERNAME",
    "admin",
)

INITIAL_ADMIN_PASSWORD = os.getenv(
    "OJ_INITIAL_ADMIN_PASSWORD",
    "admin-demo-password",
)


def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
