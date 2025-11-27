from config import settings

import redis


redis_pool = redis.ConnectionPool(
    host=settings.CACHE_HOST,
    port=settings.CACHE_PORT,
    db=settings.CACHE_DB,
    max_connections=settings.CACHE_MAX_CONNECTIONS,
)

redis_client = redis.Redis(connection_pool=redis_pool)


# Constants
MINUTE_SECONDS = 60
HOUR_SECONDS = MINUTE_SECONDS ** 2
DAY_SECONDS = HOUR_SECONDS * 24


def setCacheValue(key: str, value: str, expire: int = MINUTE_SECONDS*10) -> None:
    redis_client.set(key, value, ex=expire)
    
def getCacheValue(key: str) -> str | None:
    value: bytes | None = redis_client.get(key)
    if value:
        return value.decode('utf-8')

def deleteCacheKey(key: str) -> None:
    redis_client.delete(key)

def getCacheKeyTTL(key: str) -> int | None:
    ttl = redis_client.ttl(key)
    if ttl not in [-2, -1]:
        return ttl
