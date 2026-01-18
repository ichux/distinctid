import logging
import os
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime
from typing import Optional

import redis
from redis.sentinel import Sentinel

__author__ = "Chukwudi Nwachukwu"
version = "1.0.5"

URL = "https://github.com/ichux/distinctid"

# Configure logging
logger = logging.getLogger(__name__)

# Redis connection singletons
_redis_client: Optional[redis.Redis] = None
_async_redis_client = None  # Lazy import for async

# Epoch base cache: (year, epoch_ms)
_epoch_base_cache: Optional[tuple[int, int]] = None

# Performance monitoring flag
_enable_metrics: bool = False


class IDBuffer:
    """Thread-safe local buffer for pre-allocated IDs."""

    def __init__(self, buffer_size: int = 10000):
        """
        Initialize ID buffer.

        Args:
            buffer_size: Number of IDs to pre-allocate per Redis call
        """
        self.buffer_size = buffer_size
        self.current = 0
        self.max = 0
        self.lock = threading.Lock()

    def get_next_id(self, redis_client: redis.Redis, redis_key: str) -> int:
        """
        Get next ID from buffer, refilling from Redis if needed.

        Args:
            redis_client: Redis client instance
            redis_key: Redis key for counter storage

        Returns:
            Next counter value
        """
        with self.lock:
            if self.current >= self.max:
                # Refill buffer with single atomic Redis call
                self.max = redis_client.incrby(redis_key, self.buffer_size)
                self.current = self.max - self.buffer_size + 1

            new_id = self.current
            self.current += 1

        return new_id


# Global buffer instance
_id_buffer: Optional[IDBuffer] = None


def _get_epoch_base() -> int:
    """
    Calculate epoch base (milliseconds since Jan 1 of current year).

    Cached with automatic year rollover handling.

    Returns:
        Epoch milliseconds for Jan 1 of current year
    """
    global _epoch_base_cache
    current_year = date.today().year

    if _epoch_base_cache is None or _epoch_base_cache[0] != current_year:
        # Efficient datetime construction - no string parsing
        epoch = int(datetime(current_year, 1, 1).timestamp() * 1000)
        _epoch_base_cache = (current_year, epoch)
        logger.debug(f"Epoch base cached for year {current_year}: {epoch}")

    return _epoch_base_cache[1]


def _get_redis_client() -> redis.Redis:
    """
    Get or create Redis client singleton with environment variable support.

    Environment variables:
        DISTINCTID_REDIS_HOST: Redis host (default: localhost)
        DISTINCTID_REDIS_PORT: Redis port (default: 6379)
        DISTINCTID_REDIS_DB: Redis database number (default: 0)
        DISTINCTID_REDIS_PASSWORD: Redis password (optional)

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("DISTINCTID_REDIS_HOST", "localhost"),
            port=int(os.getenv("DISTINCTID_REDIS_PORT", "6379")),
            db=int(os.getenv("DISTINCTID_REDIS_DB", "0")),
            password=os.getenv("DISTINCTID_REDIS_PASSWORD"),
            decode_responses=False,
        )
        logger.debug("Redis client initialized from environment variables")
    return _redis_client


def _get_async_redis_client():
    """
    Get or create async Redis client singleton.

    Returns:
        Async Redis client instance
    """
    global _async_redis_client
    if _async_redis_client is None:
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError(
                "Async support requires redis[asyncio]. "
                "Install with: pip install redis[asyncio]"
            )

        _async_redis_client = aioredis.Redis(
            host=os.getenv("DISTINCTID_REDIS_HOST", "localhost"),
            port=int(os.getenv("DISTINCTID_REDIS_PORT", "6379")),
            db=int(os.getenv("DISTINCTID_REDIS_DB", "0")),
            password=os.getenv("DISTINCTID_REDIS_PASSWORD"),
            decode_responses=False,
        )
        logger.debug("Async Redis client initialized")
    return _async_redis_client


@contextmanager
def _track_redis_call(operation: str = "redis_call"):
    """
    Context manager to track Redis operation duration.

    Args:
        operation: Operation name for logging
    """
    if not _enable_metrics:
        yield
        return

    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.debug(f"{operation} took {duration_ms:.2f}ms")


def enable_metrics(enabled: bool = True) -> None:
    """
    Enable or disable performance metrics logging.

    Args:
        enabled: True to enable metrics, False to disable
    """
    global _enable_metrics
    _enable_metrics = enabled
    logger.info(f"Metrics {'enabled' if enabled else 'disabled'}")


def configure_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    max_connections: int = 50,
    socket_timeout: float = 5.0,
    socket_connect_timeout: float = 5.0,
    retry_on_timeout: bool = True,
    **kwargs,
) -> None:
    """
    Configure Redis connection with connection pooling.

    Args:
        host: Redis host (default: localhost)
        port: Redis port (default: 6379)
        db: Redis database number (default: 0)
        password: Redis password (optional)
        max_connections: Maximum connections in pool (default: 50)
        socket_timeout: Socket timeout in seconds (default: 5.0)
        socket_connect_timeout: Socket connect timeout in seconds (default: 5.0)
        retry_on_timeout: Retry on timeout (default: True)
        **kwargs: Additional redis.ConnectionPool() parameters
    """
    global _redis_client

    pool = redis.ConnectionPool(
        host=host,
        port=port,
        db=db,
        password=password,
        max_connections=max_connections,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
        retry_on_timeout=retry_on_timeout,
        **kwargs,
    )

    _redis_client = redis.Redis(connection_pool=pool, decode_responses=False)
    logger.info(f"Redis configured: {host}:{port} (max_connections={max_connections})")


def configure_redis_sentinel(
    sentinels: list[tuple[str, int]],
    service_name: str,
    password: Optional[str] = None,
    sentinel_kwargs: Optional[dict] = None,
    **kwargs,
) -> None:
    """
    Configure Redis connection using Sentinel for high availability.

    Args:
        sentinels: List of (host, port) tuples for sentinel servers
        service_name: Name of the master service
        password: Redis password (optional)
        sentinel_kwargs: Additional Sentinel() parameters
        **kwargs: Additional parameters for master connection
    """
    global _redis_client

    sentinel_kwargs = sentinel_kwargs or {}
    sentinel = Sentinel(sentinels, **sentinel_kwargs)

    _redis_client = sentinel.master_for(
        service_name,
        socket_timeout=kwargs.get("socket_timeout", 0.1),
        password=password,
        decode_responses=False,
        **kwargs,
    )
    logger.info(f"Redis Sentinel configured for service: {service_name}")


def enable_buffering(buffer_size: int = 10000) -> None:
    """
    Enable local ID buffering for extreme throughput.

    Pre-allocates IDs in batches, reducing Redis calls by ~1000x.

    Args:
        buffer_size: Number of IDs to pre-allocate (default: 10000)
    """
    global _id_buffer
    _id_buffer = IDBuffer(buffer_size=buffer_size)
    logger.info(f"ID buffering enabled with buffer_size={buffer_size}")


def disable_buffering() -> None:
    """Disable local ID buffering."""
    global _id_buffer
    _id_buffer = None
    logger.info("ID buffering disabled")


def _validate_shard_id(shard_id: int) -> None:
    """
    Validate shard_id is within acceptable range.

    Args:
        shard_id: Shard identifier to validate

    Raises:
        ValueError: If shard_id is out of range
    """
    # 13 bits for shard_id (23 bits timestamp + 13 bits shard = 36 bits, leaving 28 bits)
    # Actually looking at the bit layout: timestamp << 23, shard_id << 10
    # So shard_id has room for 13 bits (8192 values: 0-8191)
    if not 0 <= shard_id < 8192:
        raise ValueError(f"shard_id must be 0-8191, got {shard_id}")


def distinct(shard_id: int = 1, redis_key: str = "distinctid:counter") -> int:
    """
    Generate a unique, sortable 64-bit integer ID.

    Uses Redis atomic INCR for lock-free counter increments.
    Supports local buffering for extreme throughput.

    Args:
        shard_id: Shard identifier (0-8191, default: 1)
        redis_key: Redis key for counter storage (default: 'distinctid:counter')

    Returns:
        Unique 64-bit integer composed of:
        - Timestamp (milliseconds since Jan 1 of current year) << 23 bits
        - Shard ID << 10 bits
        - Counter % 1024

    Raises:
        ValueError: If shard_id is out of range
        RuntimeError: If Redis connection fails
    """
    _validate_shard_id(shard_id)

    try:
        client = _get_redis_client()

        # Use buffered or direct approach
        if _id_buffer is not None:
            new_id = _id_buffer.get_next_id(client, redis_key)
        else:
            with _track_redis_call("incr"):
                new_id = client.incr(redis_key)

    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}") from e
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout: {e}")
        raise RuntimeError(f"Redis timeout: {e}") from e

    # Calculate timestamp portion
    epoch = int(time.time() * 1000)
    epoch_base = _get_epoch_base()
    result = (epoch - epoch_base) << 23

    # Combine: timestamp | shard_id | counter
    did = (result | (shard_id << 10)) | (new_id % 1024)

    return did


def distinct_batch(
    count: int, shard_id: int = 1, redis_key: str = "distinctid:counter"
) -> list[int]:
    """
    Generate multiple unique IDs efficiently using single Redis operation.

    Args:
        count: Number of IDs to generate
        shard_id: Shard identifier (0-8191, default: 1)
        redis_key: Redis key for counter storage (default: 'distinctid:counter')

    Returns:
        List of unique 64-bit integers

    Raises:
        ValueError: If count <= 0 or shard_id is out of range
        RuntimeError: If Redis connection fails
    """
    if count <= 0:
        raise ValueError(f"count must be > 0, got {count}")

    _validate_shard_id(shard_id)

    try:
        client = _get_redis_client()

        # Single atomic operation to reserve ID range
        with _track_redis_call(f"incrby({count})"):
            max_id = client.incrby(redis_key, count)

    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}") from e
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout: {e}")
        raise RuntimeError(f"Redis timeout: {e}") from e

    # Calculate starting ID
    start_id = max_id - count + 1

    # Generate all IDs locally (no more Redis calls)
    epoch = int(time.time() * 1000)
    epoch_base = _get_epoch_base()
    result = (epoch - epoch_base) << 23

    return [(result | (shard_id << 10)) | ((start_id + i) % 1024) for i in range(count)]


async def distinct_async(
    shard_id: int = 1, redis_key: str = "distinctid:counter"
) -> int:
    """
    Generate a unique ID asynchronously for asyncio applications.

    Args:
        shard_id: Shard identifier (0-8191, default: 1)
        redis_key: Redis key for counter storage (default: 'distinctid:counter')

    Returns:
        Unique 64-bit integer

    Raises:
        ValueError: If shard_id is out of range
        RuntimeError: If Redis connection fails
        ImportError: If redis[asyncio] not installed
    """
    _validate_shard_id(shard_id)

    try:
        client = _get_async_redis_client()
        new_id = await client.incr(redis_key)

    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}") from e
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout: {e}")
        raise RuntimeError(f"Redis timeout: {e}") from e

    # Calculate timestamp portion
    epoch = int(time.time() * 1000)
    epoch_base = _get_epoch_base()
    result = (epoch - epoch_base) << 23

    # Combine: timestamp | shard_id | counter
    did = (result | (shard_id << 10)) | (new_id % 1024)

    return did


async def distinct_batch_async(
    count: int, shard_id: int = 1, redis_key: str = "distinctid:counter"
) -> list[int]:
    """
    Generate multiple unique IDs asynchronously.

    Args:
        count: Number of IDs to generate
        shard_id: Shard identifier (0-8191, default: 1)
        redis_key: Redis key for counter storage (default: 'distinctid:counter')

    Returns:
        List of unique 64-bit integers

    Raises:
        ValueError: If count <= 0 or shard_id is out of range
        RuntimeError: If Redis connection fails
        ImportError: If redis[asyncio] not installed
    """
    if count <= 0:
        raise ValueError(f"count must be > 0, got {count}")

    _validate_shard_id(shard_id)

    try:
        client = _get_async_redis_client()
        max_id = await client.incrby(redis_key, count)

    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}") from e
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout: {e}")
        raise RuntimeError(f"Redis timeout: {e}") from e

    # Calculate starting ID
    start_id = max_id - count + 1

    # Generate all IDs locally
    epoch = int(time.time() * 1000)
    epoch_base = _get_epoch_base()
    result = (epoch - epoch_base) << 23

    return [(result | (shard_id << 10)) | ((start_id + i) % 1024) for i in range(count)]
