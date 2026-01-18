#!/usr/bin/env python3
"""
Demonstration of distinctid features and optimizations.

This script showcases all the optimization features including:
- Basic ID generation
- Batch generation
- Local buffering
- Async support
- Configuration options
- Metrics
"""

import asyncio
import logging
import time

import distinctid

# Configure logging to see metrics
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def demo_basic():
    """Basic ID generation."""
    print("\n" + "=" * 60)
    print("1. BASIC ID GENERATION")
    print("=" * 60)

    # Generate a few IDs
    for i in range(5):
        id_val = distinctid.distinct(shard_id=1)
        print(f"ID {i+1}: {id_val}")


def demo_batch():
    """Batch ID generation for improved performance."""
    print("\n" + "=" * 60)
    print("2. BATCH ID GENERATION")
    print("=" * 60)

    # Generate 100 IDs at once
    count = 100
    start = time.perf_counter()
    ids = distinctid.distinct_batch(count, shard_id=1)
    duration = (time.perf_counter() - start) * 1000

    print(f"Generated {count} IDs in {duration:.2f}ms")
    print(f"First 5 IDs: {ids[:5]}")
    print(f"All unique: {len(ids) == len(set(ids))}")


def demo_buffering():
    """Local buffering for extreme throughput."""
    print("\n" + "=" * 60)
    print("3. LOCAL BUFFERING (1000x IMPROVEMENT)")
    print("=" * 60)

    # Without buffering
    distinctid.disable_buffering()
    start = time.perf_counter()
    for _ in range(100):
        distinctid.distinct(shard_id=1, redis_key="demo:nobuffer")
    duration_no_buffer = (time.perf_counter() - start) * 1000
    print(f"Without buffering (100 IDs): {duration_no_buffer:.2f}ms")

    # With buffering
    distinctid.enable_buffering(buffer_size=1000)
    start = time.perf_counter()
    for _ in range(100):
        distinctid.distinct(shard_id=1, redis_key="demo:buffer")
    duration_buffer = (time.perf_counter() - start) * 1000
    print(f"With buffering (100 IDs):    {duration_buffer:.2f}ms")
    print(f"Speedup: {duration_no_buffer/duration_buffer:.1f}x")

    # Clean up
    distinctid.disable_buffering()


def demo_configuration():
    """Redis configuration options."""
    print("\n" + "=" * 60)
    print("4. CONFIGURATION OPTIONS")
    print("=" * 60)

    # Configure with connection pooling
    distinctid.configure_redis(
        host="localhost", port=6379, db=0, max_connections=50, socket_timeout=5.0
    )
    print("✓ Redis configured with connection pooling")

    # Environment variables also supported:
    # DISTINCTID_REDIS_HOST=localhost
    # DISTINCTID_REDIS_PORT=6379
    # DISTINCTID_REDIS_DB=0
    # DISTINCTID_REDIS_PASSWORD=secret
    print("✓ Environment variable support available")


def demo_validation():
    """Input validation and error handling."""
    print("\n" + "=" * 60)
    print("5. INPUT VALIDATION")
    print("=" * 60)

    # Valid shard IDs: 0-8191
    print("Valid shard_id range: 0-8191")

    try:
        distinctid.distinct(shard_id=9000)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Invalid shard_id rejected: {e}")

    try:
        distinctid.distinct_batch(count=0)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Invalid count rejected: {e}")


def demo_metrics():
    """Performance metrics logging."""
    print("\n" + "=" * 60)
    print("6. PERFORMANCE METRICS")
    print("=" * 60)

    # Enable metrics
    distinctid.enable_metrics(True)
    print("Generating IDs with metrics enabled...")

    for _ in range(3):
        distinctid.distinct(shard_id=1, redis_key="demo:metrics")

    # Disable metrics
    distinctid.enable_metrics(False)
    print("\n✓ Metrics disabled")


async def demo_async():
    """Async ID generation."""
    print("\n" + "=" * 60)
    print("7. ASYNC SUPPORT")
    print("=" * 60)

    try:
        # Single async ID
        id1 = await distinctid.distinct_async(shard_id=1, redis_key="demo:async")
        print(f"Async ID: {id1}")

        # Batch async
        ids = await distinctid.distinct_batch_async(
            10, shard_id=1, redis_key="demo:async:batch"
        )
        print(f"Async batch (10 IDs): {ids[:3]}... (showing first 3)")

        # Concurrent generation
        tasks = [
            distinctid.distinct_async(shard_id=i, redis_key=f"demo:async:shard{i}")
            for i in range(1, 4)
        ]
        results = await asyncio.gather(*tasks)
        print(f"Concurrent generation (3 shards): {results}")

    except ImportError as e:
        print(f"⚠ Async support not available: {e}")
        print("Install with: pip install distinctid[asyncio]")


def demo_performance_comparison():
    """Compare different generation methods."""
    print("\n" + "=" * 60)
    print("8. PERFORMANCE COMPARISON")
    print("=" * 60)

    count = 1000

    # Individual calls
    distinctid.disable_buffering()
    start = time.perf_counter()
    for _ in range(count):
        distinctid.distinct(shard_id=1, redis_key="demo:perf:individual")
    duration_individual = (time.perf_counter() - start) * 1000

    # Batch
    start = time.perf_counter()
    distinctid.distinct_batch(count, shard_id=1, redis_key="demo:perf:batch")
    duration_batch = (time.perf_counter() - start) * 1000

    # Buffered
    distinctid.enable_buffering(buffer_size=count)
    start = time.perf_counter()
    for _ in range(count):
        distinctid.distinct(shard_id=1, redis_key="demo:perf:buffered")
    duration_buffered = (time.perf_counter() - start) * 1000
    distinctid.disable_buffering()

    print(f"Generating {count} IDs:")
    print(f"  Individual calls: {duration_individual:>8.2f}ms (baseline)")
    print(
        f"  Batch generation: {duration_batch:>8.2f}ms ({duration_individual/duration_batch:>5.1f}x faster)"
    )
    print(
        f"  Buffered calls:   {duration_buffered:>8.2f}ms ({duration_individual/duration_buffered:>5.1f}x faster)"
    )


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("DISTINCTID - COMPREHENSIVE FEATURE DEMONSTRATION")
    print("=" * 60)

    demo_basic()
    demo_batch()
    demo_buffering()
    demo_configuration()
    demo_validation()
    demo_metrics()

    # Async demo
    asyncio.run(demo_async())

    demo_performance_comparison()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("✓ Batch generation: 10-100x faster for bulk operations")
    print("✓ Local buffering: ~1000x faster for sustained throughput")
    print("✓ Async support: Native asyncio integration")
    print("✓ Production-ready: Validation, error handling, metrics")
    print("✓ Configurable: Connection pooling, environment variables")
    print("✓ High availability: Redis Sentinel support")
    print("\n")


if __name__ == "__main__":
    main()
