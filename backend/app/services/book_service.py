from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.external.google_books import google_books_client
from app.models.book import Book
from app.models.book_genre import BookGenre
from app.repositories.book_repository import book_repository
from app.repositories.genre_repository import genre_repository
from app.external.anthropic_client import generate_book_summary
from app.utils.cache import TTL_AI_SUMMARY, TTL_NEW_RELEASES, TTL_SEARCH, cache_get, cache_set

# Maps common Google Books category strings → our genre slugs
CATEGORY_TO_SLUG: dict[str, str] = {
    "fiction": "fiction",
    "science fiction": "science-fiction",
    "fantasy": "fantasy",
    "mystery": "mystery",
    "thriller": "mystery",
    "romance": "romance",
    "horror": "horror",
    "historical fiction": "historical-fiction",
    "biography": "biography",
    "self-help": "self-help",
    "self help": "self-help",
    "science": "science",
    "philosophy": "philosophy",
    "poetry": "poetry",
    "comics": "graphic-novel",
    "juvenile fiction": "young-adult",
    "young adult": "young-adult",
    "business": "business",
    "history": "history",
    "travel": "travel",
    "cooking": "cooking",
    "art": "art",
}


class BookService:
    async def search(self, db: AsyncSession, query: str, *, limit: int = 20) -> list[Book]:
        if not query.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query cannot be empty")

        # 1. Check local DB first
        local_results = await book_repository.search(db, query.strip(), limit=limit)
        if len(local_results) >= limit:
            return local_results

        # 2. Check Redis cache before hitting Google Books API
        cache_key = f"google_search:{query.lower().strip()}:{limit}"
        cached = await cache_get(cache_key)
        google_results: list[dict] = cached or []

        if not cached:
            try:
                google_results = await google_books_client.search(query, limit=limit)
                await cache_set(cache_key, google_results, TTL_SEARCH)
            except Exception:
                return local_results

        # 3. Upsert each result and collect
        seen_ids = {b.google_books_id for b in local_results}
        for raw in google_results:
            if raw["google_books_id"] not in seen_ids:
                book, _ = await self._upsert_from_raw(db, dict(raw))
                local_results.append(book)
                seen_ids.add(raw["google_books_id"])

        await db.commit()
        return local_results[:limit]

    async def semantic_search(self, db: AsyncSession, query: str, *, limit: int = 10) -> list[Book]:
        from sqlalchemy import select
        from app.external.embedding_client import embed

        query_vector = await embed(query)
        # cosine distance operator <=> — lower is more similar
        result = await db.execute(
            select(Book)
            .where(Book.embedding.is_not(None))
            .order_by(Book.embedding.cosine_distance(query_vector))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_summary(self, db: AsyncSession, book_id: int) -> str:
        book = await book_repository.get_by_id(db, book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

        cache_key = f"ai_summary:{book_id}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        if not book.description:
            return "No description available to summarise."

        summary = await generate_book_summary(book.title, book.authors or "", book.description)
        await cache_set(cache_key, summary, TTL_AI_SUMMARY)
        return summary

    async def get_popular(self, db: AsyncSession, *, limit: int = 20) -> list[Book]:
        return await book_repository.get_popular(db, limit=limit)

    async def get_by_id(self, db: AsyncSession, book_id: int) -> Book:
        book = await book_repository.get_with_genres(db, book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        return book

    async def get_by_genre(self, db: AsyncSession, genre_slug: str, *, limit: int = 20) -> list[Book]:
        genre = await genre_repository.get_by_slug(db, genre_slug)
        if not genre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")

        local_results = await book_repository.get_by_genre(db, genre.id, limit=limit)
        if len(local_results) >= limit:
            return local_results

        # Fetch from Google Books and cache
        try:
            google_results = await google_books_client.get_new_releases(genre_slug.replace("-", " "), limit=limit)
            seen_ids = {b.google_books_id for b in local_results}
            for raw in google_results:
                if raw["google_books_id"] not in seen_ids:
                    book, _ = await self._upsert_from_raw(db, raw)
                    local_results.append(book)
                    seen_ids.add(raw["google_books_id"])
            await db.commit()
        except Exception:
            pass

        return local_results[:limit]

    async def get_new_releases(self, db: AsyncSession, genre: str = "fiction", *, limit: int = 20) -> list[Book]:
        cache_key = f"new_releases:{genre.lower()}:{limit}"
        cached = await cache_get(cache_key)
        google_results: list[dict] = cached or []

        if not cached:
            try:
                google_results = await google_books_client.get_new_releases(genre, limit=limit)
                if google_results:
                    await cache_set(cache_key, google_results, TTL_NEW_RELEASES)
            except Exception:
                pass

        if not google_results:
            return await book_repository.get_popular(db, limit=limit)

        books: list[Book] = []
        for raw in google_results:
            book, _ = await self._upsert_from_raw(db, dict(raw))
            books.append(book)

        await db.commit()
        books.sort(key=lambda b: self._parse_year(b.published_date), reverse=True)
        return books[:limit]

    @staticmethod
    def _parse_year(date_str: str | None) -> int:
        if not date_str:
            return 0
        try:
            return int(date_str[:4])
        except (ValueError, IndexError):
            return 0

    async def import_from_google(self, db: AsyncSession, google_id: str) -> Book:
        existing = await book_repository.get_by_google_id(db, google_id)
        if existing:
            return await book_repository.get_with_genres(db, existing.id)

        raw = await google_books_client.get_by_id(google_id)
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found on Google Books")

        book, _ = await self._upsert_from_raw(db, raw)
        await db.commit()
        return await book_repository.get_with_genres(db, book.id)

    async def _upsert_from_raw(self, db: AsyncSession, raw: dict) -> tuple[Book, bool]:
        """Save a parsed Google Books result to the DB and link its genres."""
        categories = raw.pop("categories", [])
        google_id = raw["google_books_id"]
        defaults = {k: v for k, v in raw.items() if k != "google_books_id"}

        book, created = await book_repository.upsert(db, google_id, defaults)

        if created:
            await self._link_genres(db, book, categories)
            await self._embed_book(book)

        return book, created

    @staticmethod
    async def _embed_book(book: Book) -> None:
        """Fire-and-forget: generate embedding in background so import stays fast."""
        if book.embedding is not None:
            return
        try:
            from app.external.embedding_client import embed
            text = f"{book.title} {book.authors} {(book.description or '')[:400]}"
            book.embedding = await embed(text)
        except Exception:
            pass  # embedding is optional — search falls back gracefully

    async def _link_genres(self, db: AsyncSession, book: Book, categories: list[str]) -> None:
        """Match Google's category strings to our genre slugs and create book_genre rows."""
        matched_genre_ids: set[int] = set()
        for category in categories:
            for key, slug in CATEGORY_TO_SLUG.items():
                if key in category.lower():
                    genre = await genre_repository.get_by_slug(db, slug)
                    if genre and genre.id not in matched_genre_ids:
                        db.add(BookGenre(book_id=book.id, genre_id=genre.id))
                        matched_genre_ids.add(genre.id)
                        break
        if matched_genre_ids:
            await db.flush()


book_service = BookService()
