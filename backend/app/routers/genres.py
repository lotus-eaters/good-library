from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.repositories.genre_repository import genre_repository
from app.schemas.genre import GenreOut

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("/", response_model=list[GenreOut])
async def list_genres(db: AsyncSession = Depends(get_db)):
    return await genre_repository.get_all(db)
