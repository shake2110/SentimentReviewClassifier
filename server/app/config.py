import logging
import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent.parent
load_dotenv(SERVER_DIR / ".env")

log = logging.getLogger(__name__)
_DEV_SECRET = "dev-only-insecure-secret-change-me"


class Config:
    ENV = os.getenv("APP_ENV", "development")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    MONGO_DB = os.getenv("MONGO_DB", "aspectlens")
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "168"))
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", SERVER_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB request limit (image uploads)
    CORS_ORIGINS = [o.strip() for o in
                    os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]
    WARM_MODELS = os.getenv("WARM_MODELS", "1") == "1"

    @classmethod
    def validate(cls):
        if not cls.JWT_SECRET:
            if cls.ENV == "production":
                raise RuntimeError("JWT_SECRET must be set in production.")
            log.warning("JWT_SECRET is not set; using an insecure development secret.")
            cls.JWT_SECRET = _DEV_SECRET
