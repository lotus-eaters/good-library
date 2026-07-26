from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_genre_affinity import UserGenreAffinity
from app.repositories.base import BaseRepository


class UserGenreAffinityRepository(BaseRepository[UserGenreAffinity]):
    def __init__(self):
        super().__init__(UserGenreAffinity)

    async def get_user_affinities(self, db: AsyncSession, user_id: int) -> list[UserGenreAffinity]:
        result = await db.execute(
            select(UserGenreAffinity)
            .where(UserGenreAffinity.user_id == user_id)
            .order_by(UserGenreAffinity.score.desc())
        )
        return list(result.scalars().all())

    async def get_user_genre_affinity(self, db: AsyncSession, user_id: int, genre_id: int) -> UserGenreAffinity | None:
        result = await db.execute(
            select(UserGenreAffinity).where(
                UserGenreAffinity.user_id == user_id,
                UserGenreAffinity.genre_id == genre_id,
            )
        )
        return result.scalar_one_or_none()

    async def increment(self, db: AsyncSession, user_id: int, genre_id: int, delta: float) -> UserGenreAffinity:
        """Add delta to a user's genre score, creating the row if it doesn't exist."""
        affinity = await self.get_user_genre_affinity(db, user_id, genre_id)
        if affinity:
            affinity.score = round(affinity.score + delta, 4)
        else:
            affinity = UserGenreAffinity(user_id=user_id, genre_id=genre_id, score=max(delta, 0.0))
            db.add(affinity)
        await db.flush()
        return affinity

    async def get_top_genre_ids(self, db: AsyncSession, user_id: int, *, limit: int = 5) -> list[int]:
        result = await db.execute(
            select(UserGenreAffinity.genre_id)
            .where(UserGenreAffinity.user_id == user_id)
            .order_by(UserGenreAffinity.score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


user_genre_affinity_repository = UserGenreAffinityRepository()
