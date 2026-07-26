from pydantic import BaseModel


class GenreOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    icon: str | None

    model_config = {"from_attributes": True}
