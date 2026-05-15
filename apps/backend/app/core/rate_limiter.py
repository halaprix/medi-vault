"""Redis-backed rate limiter for FastAPI endpoints."""

import time
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded, retry after {retry_after}s")


class RateLimiter:
    """Sliding-window rate limiter using Redis sorted sets."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
        return self.redis

    async def check(
        self,
        key: str,
        max_requests: int = 5,
        window_seconds: int = 60,
    ) -> None:
        """Raise RateLimitExceeded if key exceeds limit."""
        redis = await self._get_redis()
        now = time.monotonic()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 1)
        _, count, _, _ = await pipe.execute()

        if count and int(count) >= max_requests:
            first = await redis.zrange(key, 0, 0, withscores=True)
            retry_after = window_seconds
            if first:
                oldest = first[0][1]
                retry_after = int(oldest + window_seconds - now) + 1
            raise RateLimitExceeded(retry_after=retry_after)


rate_limiter = RateLimiter()
