from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_optional_user
from app.models.user import User
from app.schemas.rating import RatingOut, RatingRequest, RatingWithUserOut
from app.services.rating_service import rating_service

router = APIRouter(prefix="/ratings", tags=["ratings"], redirect_slashes=False)


@router.post("/", response_model=RatingOut, status_code=201)
async def rate_book(
    body: RatingRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await rating_service.rate_book(
        db, user_id=user.id, book_id=body.book_id, score=body.score, review=body.review
    )


@router.get("/{book_id}", response_model=RatingOut | None)
async def get_my_rating(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await rating_service.get_user_rating(db, user_id=user.id, book_id=book_id)


@router.get("/book/{book_id}/reviews", response_model=list[RatingWithUserOut])
async def get_book_reviews(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await rating_service.get_book_reviews(db, book_id=book_id)


@router.delete("/{book_id}", status_code=204)
async def delete_rating(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await rating_service.delete_rating(db, user_id=user.id, book_id=book_id)
