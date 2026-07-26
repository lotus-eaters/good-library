from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rating import Rating
from app.repositories.base import BaseRepository


class RatingRepository(BaseRepository[Rating]):
    def __init__(self):
        super().__init__(Rating)

    async def get_user_book_rating(self, db: AsyncSession, user_id: int, book_id: int) -> Rating | None:
        result = await db.execute(
            select(Rating).where(Rating.user_id == user_id, Rating.book_id == book_id)
        )
        return result.scalar_one_or_none()

    async def get_book_ratings(self, db: AsyncSession, book_id: int, *, limit: int = 20) -> list[Rating]:
        result = await db.execute(
            select(Rating)
            .where(Rating.book_id == book_id)
            .order_by(Rating.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_book_reviews(self, db: AsyncSession, book_id: int, *, limit: int = 20) -> list[Rating]:
        result = await db.execute(
            select(Rating)
            .where(Rating.book_id == book_id, Rating.review.isnot(None), Rating.review != '')
            .options(selectinload(Rating.user))
            .order_by(Rating.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert(self, db: AsyncSession, user_id: int, book_id: int, score: int, review: str | None) -> tuple[Rating, bool]:
        """Insert or update a rating. Returns (rating, created)."""
        rating = await self.get_user_book_rating(db, user_id, book_id)
        if rating:
            rating.score = score
            rating.review = review
            await db.flush()
            return rating, False
        rating = Rating(user_id=user_id, book_id=book_id, score=score, review=review)
        db.add(rating)
        await db.flush()
        await db.refresh(rating)
        return rating, True


rating_repository = RatingRepository()
