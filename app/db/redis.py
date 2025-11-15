"""
Redis connection configuration
"""
from redis import asyncio as aioredis
from typing import Optional
from app.core.config import get_app_settings

settings = get_app_settings()

redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Get Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            f"redis://:{settings.redis_password}@{settings.redis_hostname}:{settings.redis_port}/{settings.redis_db}",
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis_connection():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
