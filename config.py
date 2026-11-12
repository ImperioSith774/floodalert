import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "floodalert-dev-key-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    SQLITE_PATH = os.environ.get("SQLITE_PATH", os.path.join(BASE_DIR, "database", "floodalert.db"))

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB por request
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB por imagen
