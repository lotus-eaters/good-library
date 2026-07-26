from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.shelf import AddToShelfRequest, CreateShelfRequest, ShelfDetailOut, ShelfOut
from app.services.shelf_service import shelf_service

router = APIRouter(prefix="/shelves", tags=["shelves"], redirect_slashes=False)


@router.get("/", response_model=list[ShelfDetailOut])
async def get_my_shelves(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await shelf_service.get_user_shelves(db, user.id)


@router.post("/", response_model=ShelfOut, status_code=201)
async def create_shelf(
    body: CreateShelfRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await shelf_service.create_custom_shelf(db, user_id=user.id, name=body.name)


@router.get("/{shelf_id}", response_model=ShelfDetailOut)
async def get_shelf(
    shelf_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await shelf_service.get_shelf_with_books(db, shelf_id, user.id)


@router.post("/{shelf_id}/books", status_code=201)
async def add_book_to_shelf(
    shelf_id: int,
    body: AddToShelfRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await shelf_service.add_to_shelf(db, user_id=user.id, shelf_id=shelf_id, book_id=body.book_id)
    return {"message": "Book added to shelf"}


@router.delete("/{shelf_id}/books/{book_id}", status_code=204)
async def remove_book_from_shelf(
    shelf_id: int,
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await shelf_service.remove_from_shelf(db, user_id=user.id, shelf_id=shelf_id, book_id=book_id)
