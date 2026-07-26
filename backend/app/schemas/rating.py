from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class RatingRequest(BaseModel):
    book_id: int
    score: int = Field(ge=1, le=5)
    review: str | None = Field(default=None, max_length=5000)


class RatingOut(BaseModel):
    id: int
    book_id: int
    score: int
    review: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class _ReviewerOut(BaseModel):
    display_name: str | None
    username: str
    model_config = {"from_attributes": True}


class RatingWithUserOut(BaseModel):
    id: int
    score: int
    review: str
    created_at: datetime
    user: _ReviewerOut

    @computed_field
    @property
    def reviewer_name(self) -> str:
        return self.user.display_name or self.user.username

    model_config = {"from_attributes": True}
