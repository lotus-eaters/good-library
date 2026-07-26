from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.external.anthropic_client import generate_why_explanation, rank_similar_books
from app.models.book import Book
from app.models.rating import Rating
from app.models.user_genre_affinity import UserGenreAffinity
from app.repositories.book_repository import book_repository
from app.repositories.shelf_repository import shelf_repository
from app.repositories.user_genre_affinity_repository import user_genre_affinity_repository
from app.utils.cache import TTL_AI_SUMMARY, cache_get, cache_set


# ── Strategy Pattern ──────────────────────────────────────────────────────────
# Each strategy is a different algorithm for generating recommendations.
# Swap the strategy without changing the service interface.
# Stage 2: add LLMRecommendationStrategy here without touching anything else.

class RecommendationStrategy(ABC):
    @abstractmethod
    async def recommend(self, db: AsyncSession, user_id: int, limit: int) -> list[Book]:
        ...


class GenreAffinityStrategy(RecommendationStrategy):
    """Recommend books in the user's top genres that they haven't shelved yet."""

    async def recommend(self, db: AsyncSession, user_id: int, limit: int) -> list[Book]:
        top_genre_ids = await user_genre_affinity_repository.get_top_genre_ids(db, user_id, limit=5)
        if not top_genre_ids:
            return []

        # Get all book IDs the user has already shelved so we can exclude them
        shelved_ids = await self._get_shelved_book_ids(db, user_id)

        candidates: list[Book] = []
        seen_ids: set[int] = set(shelved_ids)

        for genre_id in top_genre_ids:
            books = await book_repository.get_by_genre(db, genre_id, limit=limit)
            for book in books:
                if book.id not in seen_ids:
                    candidates.append(book)
                    seen_ids.add(book.id)
            if len(candidates) >= limit:
                break

        return candidates[:limit]

    async def _get_shelved_book_ids(self, db: AsyncSession, user_id: int) -> list[int]:
        shelves = await shelf_repository.get_user_shelves(db, user_id)
        shelved_ids = []
        for shelf in shelves:
            full_shelf = await shelf_repository.get_shelf_with_books(db, shelf.id)
            if full_shelf:
                shelved_ids.extend(sb.book_id for sb in full_shelf.shelf_books)
        return shelved_ids


class PopularityStrategy(RecommendationStrategy):
    """Cold-start fallback: return highest-rated books overall."""

    async def recommend(self, db: AsyncSession, user_id: int, limit: int) -> list[Book]:
        return await book_repository.list(db, limit=limit)


# ── Recommendation Service ────────────────────────────────────────────────────

class RecommendationService:
    def __init__(self):
        self._strategy: RecommendationStrategy = GenreAffinityStrategy()
        self._cold_start_strategy: RecommendationStrategy = PopularityStrategy()

    async def get_for_you(self, db: AsyncSession, user_id: int, *, limit: int = 20) -> list[Book]:
        top_genres = await user_genre_affinity_repository.get_top_genre_ids(db, user_id, limit=1)

        # Cold start: new user with no affinity data yet → fall back to popular books
        if not top_genres:
            return await self._cold_start_strategy.recommend(db, user_id, limit)

        return await self._strategy.recommend(db, user_id, limit)

    async def get_similar(self, db: AsyncSession, book_id: int, *, limit: int = 10) -> list[Book]:
        from app.services.book_service import book_service

        # Cache similar books per book — runs once, then served from Redis
        cache_key = f"similar_books:{book_id}:{limit}"
        cached_ids: list[int] | None = await cache_get(cache_key)
        if cached_ids:
            books = [await book_repository.get_by_id(db, bid) for bid in cached_ids]
            return [b for b in books if b]

        book = await book_repository.get_with_genres(db, book_id)
        if not book:
            return []

        seen_ids = {book_id}
        candidates: list[Book] = []

        # 1. Same-author books first — strongest similarity signal
        if book.authors:
            first_author = book.authors.split(",")[0].strip()
            author_books = await book_service.search(db, first_author, limit=limit)
            for b in author_books:
                if b.id not in seen_ids:
                    candidates.append(b)
                    seen_ids.add(b.id)

        # 2. Genre-based pool to fill remaining slots
        for genre in (book.genres or []):
            if len(candidates) >= limit * 3:
                break
            genre_books = await book_repository.get_by_genre(db, genre.id, limit=limit * 2)
            for b in genre_books:
                if b.id not in seen_ids:
                    candidates.append(b)
                    seen_ids.add(b.id)

        if not candidates:
            return []

        # 3. Ask Groq to re-rank candidates by thematic similarity
        ranked_ids = await rank_similar_books(
            source_title=book.title,
            source_description=book.description or "",
            candidates=[
                {"id": b.id, "title": b.title, "description": b.description}
                for b in candidates
            ],
            limit=limit,
        )

        # Preserve Groq's ranking order
        id_to_book = {b.id: b for b in candidates}
        results = [id_to_book[bid] for bid in ranked_ids if bid in id_to_book]

        # Cache for 7 days — similarity doesn't change unless new books are added
        await cache_set(cache_key, [b.id for b in results], 60 * 60 * 24 * 7)
        return results

    async def get_why(self, db: AsyncSession, user_id: int, book_id: int) -> str:
        cache_key = f"why:{user_id}:{book_id}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        # Fetch target book
        book = await book_repository.get_by_id(db, book_id)
        if not book:
            return "Recommended based on your reading taste."

        # Top 5 rated books with titles — no PII, just behaviour
        ratings_result = await db.execute(
            select(Rating)
            .where(Rating.user_id == user_id)
            .options(selectinload(Rating.book))
            .order_by(Rating.score.desc())
            .limit(5)
        )
        top_ratings = ratings_result.scalars().all()
        top_rated = [f"{r.book.title} ({r.score}★)" for r in top_ratings if r.book]

        # Top 5 genre affinities with names
        affinities_result = await db.execute(
            select(UserGenreAffinity)
            .where(UserGenreAffinity.user_id == user_id)
            .options(selectinload(UserGenreAffinity.genre))
            .order_by(UserGenreAffinity.score.desc())
            .limit(5)
        )
        top_affinities = affinities_result.scalars().all()
        top_genres = [a.genre.name for a in top_affinities if a.genre]

        explanation = await generate_why_explanation(
            book_title=book.title,
            book_authors=book.authors or "",
            top_rated=top_rated,
            top_genres=top_genres,
        )

        # Cache for 24h — re-generates as user's taste evolves
        await cache_set(cache_key, explanation, 60 * 60 * 24)
        return explanation


recommendation_service = RecommendationService()
