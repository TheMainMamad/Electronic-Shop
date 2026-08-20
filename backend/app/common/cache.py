import json
from typing import Any

from app.common.redis_client import get_redis

DEFAULT_TTL_SECONDS = 600


async def cache_get_json(key: str) -> Any | None:
    redis = get_redis()
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set_json(key: str, value: Any, *, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    redis = get_redis()
    await redis.set(key, json.dumps(value), ex=ttl)


async def cache_delete(*keys: str) -> None:
    if not keys:
        return
    redis = get_redis()
    await redis.delete(*keys)
