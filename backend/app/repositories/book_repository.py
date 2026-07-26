from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.book_genre import BookGenre
from app.models.genre import Genre
from app.repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self):
        super().__init__(Book)

    async def get_by_google_id(self, db: AsyncSession, google_id: str) -> Book | None:
        result = await db.execute(select(Book).where(Book.google_books_id == google_id))
        return result.scalar_one_or_none()

    async def get_with_genres(self, db: AsyncSession, book_id: int) -> Book | None:
        result = await db.execute(
            select(Book)
            .where(Book.id == book_id)
            .options(selectinload(Book.genres))
        )
        return result.scalar_one_or_none()

    async def search(self, db: AsyncSession, query: str, *, limit: int = 20) -> list[Book]:
        pattern = f"%{query.lower()}%"
        result = await db.execute(
            select(Book)
            .where(
                func.lower(Book.title).like(pattern)
                | func.lower(Book.authors).like(pattern)
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_genre(self, db: AsyncSession, genre_id: int, *, limit: int = 20) -> list[Book]:
        result = await db.execute(
            select(Book)
            .join(BookGenre, Book.id == BookGenre.book_id)
            .where(BookGenre.genre_id == genre_id)
            .order_by(Book.average_rating.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_popular(self, db: AsyncSession, *, limit: int = 20) -> list[Book]:
        result = await db.execute(
            select(Book)
            .where(Book.ratings_count > 0)
            .order_by(Book.ratings_count.desc(), Book.average_rating.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert(self, db: AsyncSession, google_id: str, defaults: dict) -> tuple[Book, bool]:
        """Insert or update a book by google_books_id. Returns (book, created)."""
        book = await self.get_by_google_id(db, google_id)
        if book:
            for key, value in defaults.items():
                setattr(book, key, value)
            await db.flush()
            return book, False
        book = Book(google_books_id=google_id, **defaults)
        db.add(book)
        await db.flush()
        await db.refresh(book)
        return book, True

    async def update_rating_stats(self, db: AsyncSession, book_id: int) -> None:
        """Recalculate average_rating and ratings_count from the ratings table."""
        from app.models.rating import Rating
        result = await db.execute(
            select(func.avg(Rating.score), func.count(Rating.id))
            .where(Rating.book_id == book_id)
        )
        avg, count = result.one()
        book = await self.get_by_id(db, book_id)
        if book:
            book.average_rating = round(float(avg or 0), 2)
            book.ratings_count = count or 0
            await db.flush()


book_repository = BookRepository()
