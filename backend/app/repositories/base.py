from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD operations for any SQLAlchemy model.
    Subclasses pass their model type: class UserRepository(BaseRepository[User])
    """

    def __init__(self, model: type[ModelT]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> ModelT | None:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(self, db: AsyncSession, *, offset: int = 0, limit: int = 20) -> list[ModelT]:
        result = await db.execute(select(self.model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj: ModelT) -> ModelT:
        db.add(obj)
        await db.flush()   # write to DB within transaction, get back generated ID
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, obj: ModelT) -> ModelT:
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, obj: ModelT) -> None:
        await db.delete(obj)
        await db.flush()
