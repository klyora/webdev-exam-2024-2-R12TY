from __future__ import annotations

from urllib.parse import urlparse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_user, logout_user, current_user
from sqlalchemy import select

from . import db
from .models import User
from .security import check_password_hash

auth_bp = Blueprint("auth", __name__)


def _is_safe_redirect_url(target: str) -> bool:
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (
        (not test_url.netloc)
        or (test_url.netloc == ref_url.netloc and test_url.scheme in {"http", "https"})
    )


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("books.index"))
    next_url = request.args.get("next") or ""
    return render_template("login.html", next_url=next_url)


@auth_bp.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("books.index"))

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    remember = bool(request.form.get("remember"))

    user = db.session.scalar(select(User).where(User.username == username))

    if not user or not check_password_hash(user.password_hash, password):
        flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
        next_url = request.form.get("next") or ""
        return render_template("login.html", next_url=next_url, username=username), 401

    login_user(user, remember=remember)

    next_url = request.form.get("next") or ""
    if next_url and _is_safe_redirect_url(next_url):
        return redirect(next_url)
    return redirect(url_for("books.index"))


@auth_bp.get("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        ref = request.headers.get("Referer")
        if ref and _is_safe_redirect_url(ref):
            return redirect(ref)
    return redirect(url_for("books.index"))
