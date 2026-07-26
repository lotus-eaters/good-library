from app.models.book import Book
from app.models.book_genre import BookGenre
from app.models.genre import Genre
from app.models.rating import Rating
from app.models.shelf import Shelf
from app.models.shelf_book import ShelfBook
from app.models.user import User
from app.models.user_genre_affinity import UserGenreAffinity

__all__ = [
    "Book", "BookGenre", "Genre", "Rating",
    "Shelf", "ShelfBook", "User", "UserGenreAffinity",
]
