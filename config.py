import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "elib"
STATIC_DIR = APP_DIR / "static"
COVERS_DIR = STATIC_DIR / "covers"

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ENV = os.getenv("FLASK_ENV", "production")

    MYSQL_USER = os.getenv("MYSQL_USER", "user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "qwerty")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_DB = os.getenv("MYSQL_DB", "std_0000_exam")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "10"))

    STATIC_FOLDER = str(STATIC_DIR)
    COVERS_DIR = str(COVERS_DIR)
    ALLOWED_COVER_MIME = {"image/jpeg", "image/png", "image/webp"}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    MARKDOWN_EXTENSIONS = [
        "extra",
        "sane_lists",
        "nl2br",
    ]

    NH3_ALLOWED_TAGS = None
    NH3_ALLOWED_ATTRS = None
