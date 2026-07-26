from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating
from app.repositories.book_repository import book_repository
from app.repositories.rating_repository import rating_repository
from app.services.affinity_service import affinity_service
from app.utils.cache import cache_delete


class RatingService:
    async def rate_book(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        book_id: int,
        score: int,
        review: str | None = None,
    ) -> Rating:
        if not 1 <= score <= 5:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Score must be 1–5")

        book = await book_repository.get_by_id(db, book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

        # Capture existing score before upsert so we can calculate affinity delta
        existing = await rating_repository.get_user_book_rating(db, user_id, book_id)
        old_score = existing.score if existing else None

        rating, _ = await rating_repository.upsert(db, user_id, book_id, score, review)

        # Recalculate book's average rating and total count
        await book_repository.update_rating_stats(db, book_id)

        await db.commit()

        # Update genre affinity based on the rating change
        await affinity_service.update_from_rating(
            db, user_id=user_id, book_id=book_id, new_score=score, old_score=old_score
        )
        await db.commit()

        # Invalidate cached insights — taste signals changed
        await cache_delete(f"reading_insights:{user_id}")

        return rating

    async def delete_rating(self, db: AsyncSession, *, user_id: int, book_id: int) -> None:
        rating = await rating_repository.get_user_book_rating(db, user_id, book_id)
        if not rating:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

        await rating_repository.delete(db, rating)
        await book_repository.update_rating_stats(db, book_id)
        await db.commit()

    async def get_user_rating(self, db: AsyncSession, *, user_id: int, book_id: int) -> Rating | None:
        return await rating_repository.get_user_book_rating(db, user_id, book_id)

    async def get_book_reviews(self, db: AsyncSession, *, book_id: int) -> list[Rating]:
        return await rating_repository.get_book_reviews(db, book_id)


rating_service = RatingService()
