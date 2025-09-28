from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from flask_login import UserMixin
from sqlalchemy import (
    CheckConstraint,
    UniqueConstraint,
    Integer,
    String,
    Text,
    ForeignKey,
    select,
    func,
    and_,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    column_property,
)

from . import db


TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = (TABLE_KW,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role", cascade="all,delete", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (TABLE_KW,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    role: Mapped["Role"] = relationship(back_populates="users")

    reviews: Mapped[List["Review"]] = relationship(
        back_populates="user", cascade="all,delete-orphan", passive_deletes=True
    )

    def get_id(self) -> str:
        return str(self.id)

    @property
    def full_name(self) -> str:
        parts = [self.last_name or "", self.first_name or "", self.middle_name or ""]
        return " ".join(p for p in parts if p).strip()

    def has_role(self, *roles: str) -> bool:
        return bool(self.role and self.role.name in roles)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role.name if self.role else None}>"


class Cover(db.Model):
    __tablename__ = "covers"
    __table_args__ = (TABLE_KW,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    md5: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    book: Mapped[Optional["Book"]] = relationship(back_populates="cover", uselist=False)

    def __repr__(self) -> str:
        return f"<Cover id={self.id} mime={self.mime_type} md5={self.md5}>"


class Genre(db.Model):
    __tablename__ = "genres"
    __table_args__ = (TABLE_KW,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    books: Mapped[List["BookGenre"]] = relationship(
        back_populates="genre", cascade="all,delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name!r}>"


class Book(db.Model):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1000 AND 2100", name="chk_books_year"),
        CheckConstraint("pages > 0", name="chk_books_pages"),
        TABLE_KW,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)

    cover_id: Mapped[int] = mapped_column(
        ForeignKey("covers.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    cover: Mapped["Cover"] = relationship(back_populates="book")

    genres: Mapped[List["BookGenre"]] = relationship(
        back_populates="book", cascade="all,delete-orphan", passive_deletes=True
    )

    reviews: Mapped[List["Review"]] = relationship(
        back_populates="book", cascade="all,delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r} year={self.year}>"


class BookGenre(db.Model):
    __tablename__ = "book_genres"
    __table_args__ = (
        UniqueConstraint("book_id", "genre_id", name="uq_book_genre"),
        TABLE_KW,
    )

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True
    )

    book: Mapped["Book"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship(back_populates="books")

    def __repr__(self) -> str:
        return f"<BookGenre book_id={self.book_id} genre_id={self.genre_id}>"


class ReviewStatus(db.Model):
    __tablename__ = "review_statuses"
    __table_args__ = (TABLE_KW,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    reviews: Mapped[List["Review"]] = relationship(back_populates="status")

    def __repr__(self) -> str:
        return f"<ReviewStatus id={self.id} name={self.name!r}>"


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 0 AND 5", name="chk_reviews_rating"),
        UniqueConstraint("book_id", "user_id", name="uq_reviews_book_user"),
        TABLE_KW,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=None, server_default=func.current_timestamp(), nullable=False
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey("review_statuses.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    book: Mapped["Book"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship(back_populates="reviews")
    status: Mapped["ReviewStatus"] = relationship(back_populates="reviews")

    RATING_LABELS = {
        5: "отлично",
        4: "хорошо",
        3: "удовлетворительно",
        2: "неудовлетворительно",
        1: "плохо",
        0: "ужасно",
    }

    @property
    def rating_label(self) -> str:
        return self.RATING_LABELS.get(self.rating, str(self.rating))

    def __repr__(self) -> str:
        return f"<Review id={self.id} book_id={self.book_id} user_id={self.user_id} rating={self.rating}>"


Book.avg_rating = column_property(
    select(func.avg(Review.rating))
    .where(Review.book_id == Book.id)
    .correlate_except(Review)
    .scalar_subquery()
)

Book.reviews_count = column_property(
    select(func.count(Review.id))
    .where(Review.book_id == Book.id)
    .correlate_except(Review)
    .scalar_subquery()
)

approved_status_id_sq = select(ReviewStatus.id).where(ReviewStatus.name == "Одобрена").scalar_subquery()

Book.avg_rating_approved = column_property(
    select(func.avg(Review.rating))
    .where(and_(Review.book_id == Book.id, Review.status_id == approved_status_id_sq))
    .correlate_except(Review)
    .scalar_subquery()
)

Book.reviews_count_approved = column_property(
    select(func.count(Review.id))
    .where(and_(Review.book_id == Book.id, Review.status_id == approved_status_id_sq))
    .correlate_except(Review)
    .scalar_subquery()
)