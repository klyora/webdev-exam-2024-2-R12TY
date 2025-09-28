from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации."
login_manager.login_message_category = "warning"


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, static_folder=config_class.STATIC_FOLDER)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .filters import register_filters
    register_filters(app)

    from . import models

    from .auth import auth_bp
    from .books import books_bp
    from .reviews import reviews_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reviews_bp)


    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        full_name = None
        if current_user.is_authenticated:
            parts = [current_user.last_name or "", current_user.first_name or "", current_user.middle_name or ""]
            full_name = " ".join(p for p in parts if p).strip()
        return {
            "PAGE_SIZE": app.config.get("PAGE_SIZE", 10),
            "current_user_full_name": full_name,
            "author_signature": "Группа 231-352 — Привалов Иван Васильевич",
        }

    @app.errorhandler(403)
    def forbidden(_e):
        from flask import redirect, url_for, flash
        flash("У вас недостаточно прав для выполнения данного действия.", "danger")
        return redirect(url_for("books.index"))

    @app.errorhandler(404)
    def not_found(_e):
        p = request.path or ""
        if p == "/favicon.ico" or p.startswith("/static/"):
            return ("", 404)
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def payload_too_large(_e):
        from flask import redirect, url_for, flash
        flash("Файл слишком большой. Максимальный размер — 10 МБ.", "warning")
        return redirect(url_for("books.index"))

    return app


@login_manager.user_loader
def load_user(user_id: str):
    from .models import User
    if not user_id:
        return None
    return db.session.get(User, int(user_id))

