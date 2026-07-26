import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

# TTLs in seconds
TTL_SEARCH = 60 * 30          # 30 min — search results
TTL_NEW_RELEASES = 60 * 60 * 6  # 6 hours — new releases change slowly
TTL_GENRES = 60 * 60 * 24     # 24 hours — genres never change
TTL_AI_SUMMARY = 60 * 60 * 24 * 30  # 30 days — summaries never go stale

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Any | None:
    try:
        value = await get_redis().get(key)
        return json.loads(value) if value else None
    except Exception:
        return None  # Redis down → degrade gracefully, never crash


async def cache_set(key: str, value: Any, ttl: int) -> None:
    try:
        await get_redis().setex(key, ttl, json.dumps(value))
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    try:
        await get_redis().delete(key)
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern. Use sparingly — scans the keyspace."""
    try:
        r = get_redis()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception:
        pass
