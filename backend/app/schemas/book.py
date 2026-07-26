from pydantic import BaseModel

from app.schemas.genre import GenreOut


class BookOut(BaseModel):
    id: int
    google_books_id: str
    title: str
    authors: str
    cover_url: str | None
    published_date: str | None
    average_rating: float
    ratings_count: int

    model_config = {"from_attributes": True}


class BookDetailOut(BookOut):
    description: str | None
    publisher: str | None
    page_count: int | None
    language: str
    isbn_13: str | None
    genres: list[GenreOut] = []


class ImportBookRequest(BaseModel):
    google_books_id: str
