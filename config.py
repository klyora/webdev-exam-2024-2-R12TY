import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "elib"
STATIC_DIR = APP_DIR / "static"
_DEFAULT_COVERS = STATIC_DIR / "covers"


def _normalize_mysql_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("mysql://"):
        return "mysql+mysqlconnector://" + url[len("mysql://"):]
    if url.startswith("mysql+mysqldb://"):
        return "mysql+mysqlconnector://" + url[len("mysql+mysqldb://"):]
    if url.startswith("mysql+pymysql://"):
        return "mysql+mysqlconnector://" + url[len("mysql+pymysql://"):]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ENV = os.getenv("FLASK_ENV", "production")

    _env_url = _normalize_mysql_url(os.getenv("DATABASE_URL"))

    if not _env_url:
        MYSQL_USER = os.getenv("MYSQL_USER", "user")
        MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "qwerty")
        MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
        MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
        MYSQL_DB = os.getenv("MYSQL_DB", "std_0000_exam")

        ssl_ca = os.getenv("DB_SSL_CA")
        ssl_verify = os.getenv("DB_SSL_VERIFY", "true")

        query = "charset=utf8mb4"
        if ssl_ca:
            query += f"&ssl_ca={ssl_ca}&ssl_verify_cert={ssl_verify}"

        _env_url = (
            f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?{query}"
        )

    SQLALCHEMY_DATABASE_URI = _env_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "10"))

    COVERS_DIR = os.getenv("COVERS_DIR", str(_DEFAULT_COVERS))
    STATIC_FOLDER = str(STATIC_DIR)

    ALLOWED_COVER_MIME = {"image/jpeg", "image/png", "image/webp"}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "nl2br"]

    NH3_ALLOWED_TAGS = None
    NH3_ALLOWED_ATTRS = None
