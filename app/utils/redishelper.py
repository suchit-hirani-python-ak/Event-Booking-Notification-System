import json
from typing import Any, Optional
from redis.asyncio import Redis

class RedisHelper:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_cache(self, key: str) -> Optional[Any]:
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None

    async def set_cache(self, key: str, data: Any, ttl: int = 60):
        # Use default=str to handle ObjectIds and datetimes automatically
        await self.redis.set(key, json.dumps(data, default=str), ex=ttl)

    async def delete_cache(self, *keys: str):
        if keys:
            await self.redis.delete(*keys)
