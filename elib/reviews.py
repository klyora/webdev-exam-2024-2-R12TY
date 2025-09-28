from __future__ import annotations

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import current_user
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from . import db
from .models import Book, Review, ReviewStatus, User
from .decorators import any_authenticated, roles_required
from .utils import markdown_to_html_safe, parse_page_arg


reviews_bp = Blueprint("reviews", __name__)


def _user_already_reviewed(book_id: int, user_id: int) -> bool:
    exists = db.session.scalar(
        select(Review.id).where(Review.book_id == book_id, Review.user_id == user_id).limit(1)
    )
    return bool(exists)


@reviews_bp.get("/books/<int:book_id>/reviews/new")
@any_authenticated()
def review_new(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))

    if _user_already_reviewed(book_id, current_user.id):
        flash("Вы уже оставляли рецензию на эту книгу.", "info")
        return redirect(url_for("books.book_view", book_id=book_id))

    return render_template("review_form.html", book=book, default_rating=5)


@reviews_bp.route("/books/<int:book_id>/reviews", methods=["POST"])
@any_authenticated()
def review_create(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))

    if _user_already_reviewed(book_id, current_user.id):
        flash("Вы уже оставляли рецензию на эту книгу.", "info")
        return redirect(url_for("books.book_view", book_id=book_id))

    try:
        rating = int(request.form.get("rating", "5"))
        if rating < 0 or rating > 5:
            raise ValueError
    except Exception:
        flash("Некорректная оценка. Допустимо от 0 до 5.", "danger")
        return render_template("review_form.html", book=book, default_rating=5), 400

    text_raw = (request.form.get("text") or "").strip()
    if not text_raw:
        flash("Введите текст рецензии.", "danger")
        return render_template("review_form.html", book=book, default_rating=rating), 400

    try:
        pending_id = db.session.scalar(
            select(ReviewStatus.id).where(ReviewStatus.name == "На рассмотрении")
        )
        if not pending_id:
            flash("Системная ошибка: статусы рецензий не инициализированы.", "danger")
            return render_template("review_form.html", book=book, default_rating=rating), 500

        review = Review(
            book_id=book.id,
            user_id=current_user.id,
            rating=rating,
            text=text_raw,
            status_id=pending_id,
        )
        db.session.add(review)
        db.session.commit()
        flash("Рецензия отправлена на модерацию.", "success")
        return redirect(url_for("books.book_view", book_id=book.id))
    except Exception:
        db.session.rollback()
        flash("Не удалось сохранить рецензию. Проверьте введённые данные.", "danger")
        return render_template("review_form.html", book=book, default_rating=rating), 400


@reviews_bp.get("/my/reviews")
@any_authenticated()
def my_reviews():
    page = parse_page_arg(request.args.get("page"), 1)
    page_size = current_app.config.get("PAGE_SIZE", 10)

    total = db.session.scalar(
        select(func.count(Review.id)).where(Review.user_id == current_user.id)
    ) or 0

    stmt = (
        select(Review)
        .options(joinedload(Review.book), joinedload(Review.status))
        .where(Review.user_id == current_user.id)
        .order_by(desc(Review.created_at))
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = db.session.execute(stmt).unique().scalars().all()

    return render_template("my_reviews.html", items=items, page=page, page_size=page_size, total=total)


@reviews_bp.get("/moderation/reviews")
@roles_required("Moderator", "Admin")
def moderation_queue():
    page = parse_page_arg(request.args.get("page"), 1)
    page_size = current_app.config.get("PAGE_SIZE", 10)

    pending_id = db.session.scalar(
        select(ReviewStatus.id).where(ReviewStatus.name == "На рассмотрении")
    )
    if not pending_id:
        flash("Статусы рецензий не инициализированы.", "danger")
        return redirect(url_for("books.index"))

    total = db.session.scalar(
        select(func.count(Review.id)).where(Review.status_id == pending_id)
    ) or 0

    stmt = (
        select(Review)
        .options(joinedload(Review.book), joinedload(Review.user))
        .where(Review.status_id == pending_id)
        .order_by(desc(Review.created_at))
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = db.session.execute(stmt).unique().scalars().all()

    return render_template("moderation_list.html", items=items, page=page, page_size=page_size, total=total)


@reviews_bp.get("/moderation/reviews/<int:review_id>")
@roles_required("Moderator", "Admin")
def moderation_review(review_id: int):
    r = db.session.scalar(
        select(Review)
        .options(joinedload(Review.book), joinedload(Review.user), joinedload(Review.status))
        .where(Review.id == review_id)
    )
    if not r:
        flash("Рецензия не найдена.", "warning")
        return redirect(url_for("reviews.moderation_queue"))

    text_html = markdown_to_html_safe(r.text or "")
    return render_template("moderation_review.html", r=r, text_html=text_html)


@reviews_bp.post("/moderation/reviews/<int:review_id>/approve")
@roles_required("Moderator", "Admin")
def moderation_approve(review_id: int):
    r = db.session.get(Review, review_id)
    if not r:
        flash("Рецензия не найдена.", "warning")
        return redirect(url_for("reviews.moderation_queue"))

    approved_id = db.session.scalar(
        select(ReviewStatus.id).where(ReviewStatus.name == "Одобрена")
    )
    if not approved_id:
        flash("Статусы рецензий не инициализированы.", "danger")
        return redirect(url_for("reviews.moderation_queue"))

    r.status_id = approved_id
    db.session.commit()
    flash("Рецензия одобрена.", "success")
    return redirect(url_for("reviews.moderation_queue"))


@reviews_bp.post("/moderation/reviews/<int:review_id>/reject")
@roles_required("Moderator", "Admin")
def moderation_reject(review_id: int):
    r = db.session.get(Review, review_id)
    if not r:
        flash("Рецензия не найдена.", "warning")
        return redirect(url_for("reviews.moderation_queue"))

    rejected_id = db.session.scalar(
        select(ReviewStatus.id).where(ReviewStatus.name == "Отклонена")
    )
    if not rejected_id:
        flash("Статусы рецензий не инициализированы.", "danger")
        return redirect(url_for("reviews.moderation_queue"))

    r.status_id = rejected_id
    db.session.commit()
    flash("Рецензия отклонена.", "warning")
    return redirect(url_for("reviews.moderation_queue"))
