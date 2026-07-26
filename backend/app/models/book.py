from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_books_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str] = mapped_column(String(500), nullable=False)  # comma-separated
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    published_date: Mapped[str | None] = mapped_column(String(20))  # Google returns partial dates like "2021-03"
    publisher: Mapped[str | None] = mapped_column(String(255))
    page_count: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(10), default="en")
    isbn_13: Mapped[str | None] = mapped_column(String(20), index=True)

    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    ratings_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    genres: Mapped[list["Genre"]] = relationship("Genre", secondary="book_genres", back_populates="books")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="book")
