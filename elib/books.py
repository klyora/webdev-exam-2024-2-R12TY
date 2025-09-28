from __future__ import annotations

from typing import List, Optional

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
from .models import Book, Genre, BookGenre, Cover, Review
from .decorators import roles_required, role_required
from .utils import (
    parse_page_arg,
    calc_md5,
    save_cover_file,
    remove_cover_file,
    markdown_to_html_safe,
)

books_bp = Blueprint("books", __name__)


@books_bp.get("/")
def index():
    page = parse_page_arg(request.args.get("page"), default=1)
    page_size = current_app.config.get("PAGE_SIZE", 10)

    q = (
        select(Book)
        .options(
            joinedload(Book.cover),
            joinedload(Book.genres).joinedload(BookGenre.genre),
        )
        .order_by(desc(Book.year), desc(Book.id))
    )

    total = db.session.scalar(select(func.count(Book.id))) or 0

    result = db.session.execute(
        q.limit(page_size).offset((page - 1) * page_size)
    )
    books = result.unique().scalars().all()

    can_add = current_user.is_authenticated and getattr(current_user.role, "name", None) == "Admin"
    role_name = getattr(getattr(current_user, "role", None), "name", None)

    return render_template(
        "index.html",
        books=books,
        page=page,
        page_size=page_size,
        total=total,
        can_add=can_add,
        role_name=role_name,
    )


@books_bp.get("/books/new")
@role_required("Admin")
def book_new():
    genres = db.session.scalars(select(Genre).order_by(Genre.name.asc())).all()
    return render_template("book_form.html", mode="create", genres=genres)



@books_bp.post("/books")
@role_required("Admin")
def book_create():
    title = (request.form.get("title") or "").strip()
    short_description_raw = (request.form.get("short_description") or "").strip()
    year = request.form.get("year")
    publisher = (request.form.get("publisher") or "").strip()
    author = (request.form.get("author") or "").strip()
    pages = request.form.get("pages")
    genre_ids = request.form.getlist("genres")

    cover_file = request.files.get("cover")
    if not cover_file or cover_file.filename == "":
        flash("Не загружена обложка книги.", "danger")
        return _render_book_form_backfill("create")

    try:
        year_i = int(year)
        pages_i = int(pages)
        if not (1000 <= year_i <= 2100) or pages_i <= 0:
            raise ValueError
    except Exception:
        flash("Проверьте корректность полей «год» и «объём (страниц)».", "danger")
        return _render_book_form_backfill("create")

    mime_type = cover_file.mimetype or ""
    allowed = current_app.config.get("ALLOWED_COVER_MIME", set())
    if allowed and mime_type not in allowed:
        flash("Недопустимый тип файла обложки. Разрешены: JPEG/PNG/WebP.", "danger")
        return _render_book_form_backfill("create")

    file_bytes = cover_file.read()
    if not file_bytes:
        flash("Файл обложки пустой.", "danger")
        return _render_book_form_backfill("create")

    md5_hex = calc_md5(file_bytes)
    existing_cover: Optional[Cover] = db.session.scalar(select(Cover).where(Cover.md5 == md5_hex))

    try:
        if existing_cover:
            cover = existing_cover
        else:
            cover = Cover(filename="__tmp__", mime_type=mime_type, md5=md5_hex)
            db.session.add(cover)
            db.session.flush()

        book = Book(
            title=title,
            short_description=short_description_raw,
            year=year_i,
            publisher=publisher,
            author=author,
            pages=pages_i,
            cover_id=cover.id,
        )
        db.session.add(book)
        db.session.flush()

        if genre_ids:
            valid_genre_ids = [int(g) for g in genre_ids if str(g).isdigit()]
            if valid_genre_ids:
                rows = db.session.scalars(select(Genre.id).where(Genre.id.in_(valid_genre_ids))).all()
                for gid in rows:
                    db.session.add(BookGenre(book_id=book.id, genre_id=gid))

        if not existing_cover:
            filename, full_path = save_cover_file(
                cover_id=cover.id,
                file_bytes=file_bytes,
                mime_type=mime_type,
                original_filename=cover_file.filename,
            )
            cover.filename = filename

        db.session.commit()
        flash("Книга успешно добавлена.", "success")
        return redirect(url_for("books.book_view", book_id=book.id))

    except Exception:
        db.session.rollback()
        flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
        return _render_book_form_backfill("create")


@books_bp.get("/books/<int:book_id>/edit")
@roles_required("Admin", "Moderator")
def book_edit(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))
    genres = db.session.scalars(select(Genre).order_by(Genre.name.asc())).all()
    selected_genres = {bg.genre_id for bg in book.genres}
    return render_template("book_form.html", mode="edit", book=book, genres=genres, selected_genres=selected_genres)


@books_bp.post("/books/<int:book_id>")
@roles_required("Admin", "Moderator")
def book_update(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))

    title = (request.form.get("title") or "").strip()
    short_description_raw = (request.form.get("short_description") or "").strip()
    year = request.form.get("year")
    publisher = (request.form.get("publisher") or "").strip()
    author = (request.form.get("author") or "").strip()
    pages = request.form.get("pages")
    genre_ids = request.form.getlist("genres")

    try:
        year_i = int(year)
        pages_i = int(pages)
        if not (1000 <= year_i <= 2100) or pages_i <= 0:
            raise ValueError
    except Exception:
        flash("Проверьте корректность полей «год» и «объём (страниц)».", "danger")
        return redirect(url_for("books.book_edit", book_id=book.id))

    try:
        book.title = title
        book.short_description = short_description_raw
        book.year = year_i
        book.publisher = publisher
        book.author = author
        book.pages = pages_i

        db.session.query(BookGenre).filter(BookGenre.book_id == book.id).delete(synchronize_session=False)
        valid_genre_ids = [int(g) for g in genre_ids if str(g).isdigit()]
        if valid_genre_ids:
            rows = db.session.scalars(select(Genre.id).where(Genre.id.in_(valid_genre_ids))).all()
            for gid in rows:
                db.session.add(BookGenre(book_id=book.id, genre_id=gid))

        db.session.commit()
        flash("Изменения сохранены.", "success")
        return redirect(url_for("books.book_view", book_id=book.id))
    except Exception:
        db.session.rollback()
        flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
        return redirect(url_for("books.book_edit", book_id=book.id))


@books_bp.post("/books/<int:book_id>/delete")
@role_required("Admin")
def book_delete(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))

    cover_id = book.cover_id
    cover_filename = book.cover.filename if book.cover else None

    try:
        db.session.delete(book)
        db.session.flush()

        still_used = db.session.scalar(
            select(func.count()).select_from(Book).where(Book.cover_id == cover_id)
        )

        if not still_used:
            cover = db.session.get(Cover, cover_id)
            if cover:
                db.session.delete(cover)
            if cover_filename:
                remove_cover_file(cover_filename)

        db.session.commit()
        flash("Книга успешно удалена.", "success")
    except Exception:
        db.session.rollback()
        flash("Не удалось удалить книгу. Повторите попытку позже.", "danger")

    return redirect(url_for("books.index"))


@books_bp.get("/books/<int:book_id>")
def book_view(book_id: int):
    stmt = (
        select(Book)
        .options(
            joinedload(Book.cover),
            joinedload(Book.genres).joinedload(BookGenre.genre),
            joinedload(Book.reviews).joinedload(Review.user),
        )
        .where(Book.id == book_id)
    )
    book = db.session.execute(stmt).unique().scalar_one_or_none()
    if not book:
        flash("Книга не найдена.", "warning")
        return redirect(url_for("books.index"))

    description_html = markdown_to_html_safe(book.short_description or "")

    my_review = None
    if current_user.is_authenticated:
        for r in book.reviews:
            if r.user_id == current_user.id:
                my_review = r
                break

    return render_template(
        "book_view.html",
        book=book,
        description_html=description_html,
        my_review=my_review,
    )


def _render_book_form_backfill(mode: str):
    genres = db.session.scalars(select(Genre).order_by(Genre.name.asc())).all()
    form = request.form
    return render_template("book_form.html", mode=mode, genres=genres, form=form), 400