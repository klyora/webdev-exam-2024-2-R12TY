from __future__ import annotations

from werkzeug.security import generate_password_hash as _gen, check_password_hash as _chk


def generate_password_hash(password: str) -> str:
    """
    Хэшируем пароль для хранения в БД.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    return _gen(password)


def check_password_hash(stored_hash: str, candidate: str) -> bool:
    """
    Проверяем пароль пользователя при авторизации.
    """
    if not stored_hash or not candidate:
        return False
    return _chk(stored_hash, candidate)
