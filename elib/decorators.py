from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required


def roles_required(*allowed_roles: str) -> Callable:
    def decorator(view_func: Callable):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login", next=request.url))

            user_role = getattr(getattr(current_user, "role", None), "name", None)
            if user_role not in allowed_roles:
                flash("У вас недостаточно прав для выполнения данного действия.", "danger")
                return redirect(url_for("books.index"))
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def role_required(role: str) -> Callable:
    return roles_required(role)


def any_authenticated() -> Callable:
    def decorator(view_func: Callable):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
