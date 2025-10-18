import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

import redis as sync_redis
import redis.asyncio as redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from .config import settings

logger = logging.getLogger(__name__)

# Connection pool configuration
POOL_MAX_CONNECTIONS = 50
POOL_TIMEOUT = 20  # seconds
SOCKET_TIMEOUT = 5  # seconds
SOCKET_CONNECT_TIMEOUT = 5  # seconds
SOCKET_KEEPALIVE = True
HEALTH_CHECK_INTERVAL = 30  # seconds

# Async Redis connection pool
async_redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=POOL_MAX_CONNECTIONS,
    socket_timeout=SOCKET_TIMEOUT,
    socket_connect_timeout=SOCKET_CONNECT_TIMEOUT,
    socket_keepalive=SOCKET_KEEPALIVE,
    health_check_interval=HEALTH_CHECK_INTERVAL,
    retry_on_timeout=True,
)

# Sync Redis connection pool
sync_redis_pool = sync_redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=POOL_MAX_CONNECTIONS,
    socket_timeout=SOCKET_TIMEOUT,
    socket_connect_timeout=SOCKET_CONNECT_TIMEOUT,
    socket_keepalive=SOCKET_KEEPALIVE,
    health_check_interval=HEALTH_CHECK_INTERVAL,
    retry_on_timeout=True,
)


@contextmanager
def sync_get_redis_client() -> Generator[sync_redis.Redis, None, None]:
    """
    Context manager for synchronous Redis client.

    Provides a Redis client from the connection pool with proper cleanup.
    Handles connection errors gracefully and ensures resources are released.

    Yields:
        sync_redis.Redis: A synchronous Redis client instance.

    Raises:
        ConnectionError: If unable to connect to Redis.
        RedisError: For other Redis-related errors.

    Example:
        with sync_get_redis_client() as client:
            client.set("key", "value")
    """
    client = None
    try:
        client = sync_redis.Redis(connection_pool=sync_redis_pool)
        # Test connection
        client.ping()
        yield client
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise
    except TimeoutError as e:
        logger.error(f"Redis timeout error: {e}")
        raise
    except RedisError as e:
        logger.error(f"Redis error: {e}")
        raise
    finally:
        if client:
            try:
                client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Async context manager for Redis client (FastAPI dependency compatible).

    Provides an async Redis client from the connection pool with proper cleanup.
    Handles connection errors gracefully and ensures resources are released.

    Yields:
        redis.Redis: An async Redis client instance.

    Raises:
        ConnectionError: If unable to connect to Redis.
        RedisError: For other Redis-related errors.

    Example:
        async with get_redis_client() as client:
            await client.set("key", "value")

        # Or as FastAPI dependency:
        @app.get("/")
        async def endpoint(redis: redis.Redis = Depends(get_redis_client)):
            await redis.set("key", "value")
    """
    client = None
    try:
        client = redis.Redis(connection_pool=async_redis_pool)
        # Test connection
        await client.ping()
        yield client
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise
    except TimeoutError as e:
        logger.error(f"Redis timeout error: {e}")
        raise
    except RedisError as e:
        logger.error(f"Redis error: {e}")
        raise
    finally:
        if client:
            try:
                await client.aclose()
            except Exception as e:
                logger.warning(f"Error closing async Redis client: {e}")


async def check_redis_health() -> bool:
    """
    Check Redis connection health.

    Returns:
        bool: True if Redis is healthy, False otherwise.
    """
    try:
        async with get_redis_client() as client:
            await client.ping()
            return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def check_redis_health_sync() -> bool:
    """
    Check Redis connection health (synchronous).

    Returns:
        bool: True if Redis is healthy, False otherwise.
    """
    try:
        with sync_get_redis_client() as client:
            client.ping()
            return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def close_redis_pools() -> None:
    """
    Close all Redis connection pools.

    Should be called during application shutdown to ensure
    all connections are properly closed.
    """
    try:
        await async_redis_pool.aclose()
        sync_redis_pool.disconnect()
        logger.info("Redis connection pools closed successfully")
    except Exception as e:
        logger.error(f"Error closing Redis pools: {e}")
