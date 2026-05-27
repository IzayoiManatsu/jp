import redis.asyncio as redis
import os
from typing import Optional

class RateLimiter:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        r = await self._get_redis()
        pipe = r.pipeline()
        now = await r.time()
        now_ms = now[0] * 1000 + now[1] // 1000
        window_start = now_ms - window_seconds * 1000

        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.pexpire(key, window_seconds * 1000)

        results = await pipe.execute()
        current = results[1]
        return current < limit

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None