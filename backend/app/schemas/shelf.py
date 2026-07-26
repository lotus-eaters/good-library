from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.schemas.book import BookOut


class ShelfOut(BaseModel):
    id: int
    name: str
    shelf_type: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ShelfBookOut(BaseModel):
    book: BookOut
    added_at: datetime

    model_config = {"from_attributes": True}


class ShelfDetailOut(ShelfOut):
    shelf_books: list[ShelfBookOut] = []

    @computed_field
    @property
    def books(self) -> list[BookOut]:
        return [sb.book for sb in self.shelf_books]


class AddToShelfRequest(BaseModel):
    book_id: int


class CreateShelfRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
