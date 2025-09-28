# elib/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _env_url = os.getenv("DATABASE_URL")
    _env_url = _normalize_mysql_url(_env_url)

    if not _env_url:
        db_user = os.getenv("DB_USER", "user")
        db_pass = os.getenv("DB_PASSWORD", "pass")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "elib")
        _env_url = (
            f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            f"?charset=utf8mb4"
        )

    SQLALCHEMY_DATABASE_URI = _env_url

    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "10"))
    COVERS_DIR = os.getenv("COVERS_DIR", str(BASE_DIR / "static" / "covers"))

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    pass
