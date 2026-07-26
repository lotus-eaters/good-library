from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.book import BookOut
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/for-you", response_model=list[BookOut])
async def get_for_you(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await recommendation_service.get_for_you(db, user.id, limit=limit)


@router.get("/similar/{book_id}", response_model=list[BookOut])
async def get_similar(
    book_id: int,
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await recommendation_service.get_similar(db, book_id, limit=limit)


@router.get("/why/{book_id}")
async def get_why(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    explanation = await recommendation_service.get_why(db, user.id, book_id)
    return {"explanation": explanation}
