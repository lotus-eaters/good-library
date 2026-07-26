import httpx

from app.config import settings

GOOGLE_BOOKS_BASE_URL = "https://www.googleapis.com/books/v1"
MAX_RESULTS = 40  # Google Books API maximum per request


class GoogleBooksClient:
    """
    Thin async wrapper around the Google Books API.
    Handles HTTP, pagination, and normalising their response shape
    into a flat dict that maps 1:1 to our Book model columns.
    """

    def __init__(self):
        self._base_params = {}
        if settings.google_books_api_key and settings.google_books_api_key != "your-google-books-api-key-here":
            self._base_params["key"] = settings.google_books_api_key

    async def search(self, query: str, *, limit: int = 20) -> list[dict]:
        """Search volumes by title, author, or keyword."""
        params = {
            **self._base_params,
            "q": query,
            "maxResults": min(limit, MAX_RESULTS),
            "printType": "books",
            "projection": "full",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GOOGLE_BOOKS_BASE_URL}/volumes", params=params)
            response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        return [self._parse_volume(item) for item in items if self._parse_volume(item)]

    async def get_by_id(self, google_id: str) -> dict | None:
        """Fetch a single book by its Google Books volume ID."""
        params = {**self._base_params}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GOOGLE_BOOKS_BASE_URL}/volumes/{google_id}", params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()

        return self._parse_volume(response.json())

    async def get_new_releases(self, genre_query: str = "fiction", *, limit: int = 20) -> list[dict]:
        """Fetch recently published books for a genre."""
        params = {
            **self._base_params,
            "q": f"subject:{genre_query}+after:2022",
            "maxResults": min(limit, MAX_RESULTS),
            "orderBy": "newest",
            "printType": "books",
            "projection": "full",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GOOGLE_BOOKS_BASE_URL}/volumes", params=params)
            response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        return [parsed for item in items if (parsed := self._parse_volume(item))]

    def _parse_volume(self, volume: dict) -> dict | None:
        """
        Normalise a Google Books volume object into a flat dict
        matching our Book model columns. Returns None for invalid entries.
        """
        google_id = volume.get("id")
        info = volume.get("volumeInfo", {})

        title = info.get("title", "").strip()
        if not google_id or not title:
            return None

        authors = info.get("authors", [])
        image_links = info.get("imageLinks", {})

        # Prefer larger thumbnail; replace http → https to avoid mixed-content browser warnings
        cover_url = (
            image_links.get("thumbnail") or image_links.get("smallThumbnail")
        )
        if cover_url:
            cover_url = cover_url.replace("http://", "https://")

        isbn_13 = None
        for identifier in info.get("industryIdentifiers", []):
            if identifier.get("type") == "ISBN_13":
                isbn_13 = identifier.get("identifier")
                break

        return {
            "google_books_id": google_id,
            "title": title,
            "authors": ", ".join(authors) if authors else "Unknown",
            "description": info.get("description"),
            "cover_url": cover_url,
            "published_date": info.get("publishedDate"),
            "publisher": info.get("publisher"),
            "page_count": info.get("pageCount"),
            "language": info.get("language", "en"),
            "isbn_13": isbn_13,
            "categories": info.get("categories", []),  # used for genre matching, not stored directly
        }


google_books_client = GoogleBooksClient()
