from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.genre import Genre
from app.repositories.base import BaseRepository


class GenreRepository(BaseRepository[Genre]):
    def __init__(self):
        super().__init__(Genre)

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Genre | None:
        result = await db.execute(select(Genre).where(Genre.slug == slug))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Genre]:
        result = await db.execute(select(Genre).order_by(Genre.name))
        return list(result.scalars().all())

    async def get_by_ids(self, db: AsyncSession, ids: list[int]) -> list[Genre]:
        result = await db.execute(select(Genre).where(Genre.id.in_(ids)))
        return list(result.scalars().all())


genre_repository = GenreRepository()
