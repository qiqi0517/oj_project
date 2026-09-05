import os

API_BASE_URL: str = os.getenv("OJ_API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT: float = 5.0
APP_TITLE: str = "qiqiOJ 在线评测系统"
