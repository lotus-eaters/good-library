import time

from groq import AsyncGroq
from fastapi import HTTPException, status

from app.config import settings
from app.utils.logging import logger

_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set in .env")
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


def _log_llm(fn_name: str, start: float, response=None, error: Exception | None = None) -> None:
    duration_ms = round((time.perf_counter() - start) * 1000)
    extra: dict = {"llm_fn": fn_name, "duration_ms": duration_ms, "model": "llama-3.1-8b-instant"}
    if response:
        usage = getattr(response, "usage", None)
        if usage:
            extra["prompt_tokens"] = usage.prompt_tokens
            extra["completion_tokens"] = usage.completion_tokens
    if error:
        extra["error"] = str(error)
        logger.warning(f"LLM call failed: {fn_name}", extra=extra)
    else:
        logger.info(f"LLM call: {fn_name}", extra=extra)


async def rank_similar_books(
    source_title: str,
    source_description: str,
    candidates: list[dict],  # list of {"id": int, "title": str, "description": str}
    limit: int = 8,
) -> list[int]:
    """Ask Groq to pick the most thematically similar books from candidates. Returns ordered list of book IDs."""
    if not candidates:
        return []

    candidate_lines = "\n".join(
        f"ID {c['id']}: {c['title']} — {(c['description'] or '')[:120]}"
        for c in candidates
    )

    t0 = time.perf_counter()
    try:
        response = await get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=120,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a librarian. Given a source book and a list of candidates, "
                        f"return the IDs of the {limit} most thematically similar books as a "
                        "comma-separated list of integers only. No explanation, no extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Source book: {source_title}\n"
                        f"Source description: {(source_description or '')[:300]}\n\n"
                        f"Candidates:\n{candidate_lines}"
                    ),
                },
            ],
        )
        _log_llm("rank_similar_books", t0, response)
        raw = response.choices[0].message.content.strip()
        return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()][:limit]
    except Exception as exc:
        _log_llm("rank_similar_books", t0, error=exc)
        return [c["id"] for c in candidates[:limit]]


async def generate_reading_insights(
    books_read_this_year: int,
    total_books: int,
    top_rated: list[str],
    top_genres: list[str],
    currently_reading: str | None,
) -> str:
    """Generate 2–3 sentence narrative insight about a user's reading patterns."""
    lines = [
        f"Books read this year: {books_read_this_year}",
        f"Total books in library: {total_books}",
        f"Top rated: {', '.join(top_rated) if top_rated else 'none yet'}",
        f"Favourite genres: {', '.join(top_genres) if top_genres else 'none yet'}",
    ]
    if currently_reading:
        lines.append(f"Currently reading: {currently_reading}")

    t0 = time.perf_counter()
    try:
        response = await get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=150,
            temperature=0.5,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a perceptive literary analyst. Based on a reader's history, "
                        "write 2–3 sentences of genuine insight about their reading patterns and tastes. "
                        "Be specific and personal. Surface something non-obvious. "
                        "Never start with 'Based on' or 'It looks like'."
                    ),
                },
                {
                    "role": "user",
                    "content": "\n".join(lines),
                },
            ],
        )
        _log_llm("generate_reading_insights", t0, response)
        return response.choices[0].message.content.strip()
    except Exception as exc:
        _log_llm("generate_reading_insights", t0, error=exc)
        return "Keep reading — your insights will appear here as your library grows."


async def generate_why_explanation(
    book_title: str,
    book_authors: str,
    top_rated: list[str],      # ["Kafka on the Shore (5★)", "Norwegian Wood (4★)"]
    top_genres: list[str],     # ["literary-fiction", "surrealism"]
) -> str:
    """Generate a 1–2 sentence personalised explanation of why this book was recommended."""
    rated_str = ", ".join(top_rated) if top_rated else "no rated books yet"
    genres_str = ", ".join(top_genres) if top_genres else "no clear genre preference yet"

    t0 = time.perf_counter()
    try:
        response = await get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=100,
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a smart librarian explaining a book recommendation in 1–2 sentences. "
                        "Be specific about the connection to the user's reading history. "
                        "Start with 'Because' or 'Since'. No generic phrases like 'based on your reading'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Recommended book: {book_title} by {book_authors}\n"
                        f"User's top rated books: {rated_str}\n"
                        f"User's favourite genres: {genres_str}\n\n"
                        "Why was this book recommended to this user?"
                    ),
                },
            ],
        )
        _log_llm("generate_why_explanation", t0, response)
        return response.choices[0].message.content.strip()
    except Exception as exc:
        _log_llm("generate_why_explanation", t0, error=exc)
        return "Recommended based on your reading taste."


async def generate_book_summary(title: str, authors: str, description: str) -> str:
    truncated = description[:500].rsplit(" ", 1)[0] if len(description) > 500 else description
    t0 = time.perf_counter()
    try:
        response = await get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=180,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a literary assistant. Given a book's title, author, and description, "
                        "write a 2–3 sentence summary focused on plot, themes, and why a reader would enjoy it. "
                        "No marketing language. No spoilers. No mention of awards, editions, or film adaptations."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\nAuthor: {authors}\nDescription: {truncated}",
                },
            ],
        )
        _log_llm("generate_book_summary", t0, response)
        return response.choices[0].message.content
    except Exception as e:
        _log_llm("generate_book_summary", t0, error=e)
        err = str(e).lower()
        if "authentication" in err or "api key" in err:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service not configured")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
