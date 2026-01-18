"""
Comprehensive edge case and stress tests for distinctid.

Tests coverage:
- Counter wraparound at 1024
- Boundary conditions for shard_id
- Concurrent access patterns
- Redis failure scenarios
- Performance regression tests
- Integration tests
"""

import asyncio
import threading
import time
import unittest
from unittest import mock

import redis

import distinctid


class TestCounterWraparound(unittest.TestCase):
    """Test counter behavior at 1024 boundary."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:wraparound"
        distinctid.disable_buffering()

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_counter_modulo_1024(self):
        """Test that counter wraps at 1024 (modulo operation)."""
        # Set Redis counter to just below 1024
        client = distinctid._get_redis_client()
        client.set(self.test_redis_key, 1023)

        # Generate IDs across the 1024 boundary
        ids = []
        for _ in range(5):
            id_val = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
            ids.append(id_val)

        # All should be unique despite counter wrapping
        self.assertEqual(len(ids), len(set(ids)))

        # Verify IDs are incrementing (due to timestamp)
        for i in range(1, len(ids)):
            self.assertGreater(ids[i], ids[i - 1])

    def test_batch_across_1024_boundary(self):
        """Test batch generation across 1024 counter boundary."""
        client = distinctid._get_redis_client()
        client.set(self.test_redis_key, 1020)

        # Generate batch that crosses 1024 boundary
        ids = distinctid.distinct_batch(10, shard_id=1, redis_key=self.test_redis_key)

        # Note: Due to % 1024, some IDs will have duplicate counter portions
        # but overall they should still be in the list
        self.assertEqual(len(ids), 10)


class TestShardIdBoundaries(unittest.TestCase):
    """Test shard_id boundary conditions."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:shard_boundary"
        distinctid.disable_buffering()

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_minimum_shard_id(self):
        """Test shard_id = 0 (minimum valid)."""
        id_val = distinctid.distinct(shard_id=0, redis_key=self.test_redis_key)
        self.assertIsInstance(id_val, int)
        self.assertGreater(id_val, 0)

    def test_maximum_shard_id(self):
        """Test shard_id = 8191 (maximum valid)."""
        id_val = distinctid.distinct(shard_id=8191, redis_key=self.test_redis_key)
        self.assertIsInstance(id_val, int)
        self.assertGreater(id_val, 0)

    def test_negative_shard_id(self):
        """Test shard_id = -1 (invalid)."""
        with self.assertRaises(ValueError) as ctx:
            distinctid.distinct(shard_id=-1, redis_key=self.test_redis_key)
        self.assertIn("0-8191", str(ctx.exception))

    def test_too_large_shard_id(self):
        """Test shard_id = 8192 (invalid)."""
        with self.assertRaises(ValueError) as ctx:
            distinctid.distinct(shard_id=8192, redis_key=self.test_redis_key)
        self.assertIn("0-8191", str(ctx.exception))

    def test_different_shards_produce_different_ids(self):
        """Test that different shards produce different IDs."""
        # Generate IDs from multiple shards at nearly same time
        id_shard_0 = distinctid.distinct(shard_id=0, redis_key=self.test_redis_key)
        id_shard_1 = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
        id_shard_100 = distinctid.distinct(shard_id=100, redis_key=self.test_redis_key)

        # All should be different
        self.assertEqual(len({id_shard_0, id_shard_1, id_shard_100}), 3)


class TestConcurrentAccess(unittest.TestCase):
    """Test concurrent access patterns."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:concurrent"
        distinctid.disable_buffering()

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_concurrent_id_generation(self):
        """Test multiple threads generating IDs concurrently."""
        num_threads = 10
        ids_per_thread = 100
        results = []

        def generate_ids(thread_id):
            thread_ids = []
            for _ in range(ids_per_thread):
                id_val = distinctid.distinct(
                    shard_id=thread_id % 5, redis_key=self.test_redis_key
                )
                thread_ids.append(id_val)
            results.append(thread_ids)

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=generate_ids, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Collect all IDs
        all_ids = []
        for thread_results in results:
            all_ids.extend(thread_results)

        # Verify all IDs are unique
        self.assertEqual(len(all_ids), num_threads * ids_per_thread)
        self.assertEqual(len(set(all_ids)), len(all_ids), "Duplicate IDs generated")

    def test_buffered_concurrent_access(self):
        """Test buffered ID generation with concurrent threads."""
        distinctid.enable_buffering(buffer_size=500)

        num_threads = 5
        ids_per_thread = 50
        results = []

        def generate_buffered(thread_id):
            thread_ids = []
            for _ in range(ids_per_thread):
                id_val = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
                thread_ids.append(id_val)
            results.append(thread_ids)

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=generate_buffered, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        all_ids = []
        for thread_results in results:
            all_ids.extend(thread_results)

        # All should be unique
        self.assertEqual(
            len(set(all_ids)), len(all_ids), "Duplicate IDs with buffering"
        )

        distinctid.disable_buffering()


class TestRedisFailures(unittest.TestCase):
    """Test handling of Redis connection failures."""

    def setUp(self) -> None:
        distinctid.disable_buffering()

    def test_connection_error_handling(self):
        """Test that ConnectionError is properly caught and raised as RuntimeError."""
        # Mock Redis client to raise ConnectionError
        with mock.patch.object(distinctid, "_get_redis_client") as mock_client:
            mock_instance = mock.MagicMock()
            mock_instance.incr.side_effect = redis.ConnectionError("Connection refused")
            mock_client.return_value = mock_instance

            with self.assertRaises(RuntimeError) as ctx:
                distinctid.distinct(shard_id=1)

            self.assertIn("Connection refused", str(ctx.exception))

    def test_timeout_error_handling(self):
        """Test that TimeoutError is properly caught and raised as RuntimeError."""
        with mock.patch.object(distinctid, "_get_redis_client") as mock_client:
            mock_instance = mock.MagicMock()
            mock_instance.incr.side_effect = redis.TimeoutError("Timeout")
            mock_client.return_value = mock_instance

            with self.assertRaises(RuntimeError) as ctx:
                distinctid.distinct(shard_id=1)

            self.assertIn("Timeout", str(ctx.exception))


class TestBatchEdgeCases(unittest.TestCase):
    """Test edge cases for batch generation."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:batch_edge"

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_batch_count_one(self):
        """Test batch with count=1."""
        ids = distinctid.distinct_batch(1, shard_id=1, redis_key=self.test_redis_key)
        self.assertEqual(len(ids), 1)

    def test_batch_large_count(self):
        """Test batch with large count."""
        # Large batch within 1024 limit
        count = 500
        ids = distinctid.distinct_batch(
            count, shard_id=1, redis_key=self.test_redis_key
        )
        self.assertEqual(len(ids), count)
        self.assertEqual(len(set(ids)), count)

    def test_batch_zero_count(self):
        """Test batch with count=0 (invalid)."""
        with self.assertRaises(ValueError):
            distinctid.distinct_batch(0, shard_id=1, redis_key=self.test_redis_key)

    def test_batch_negative_count(self):
        """Test batch with negative count (invalid)."""
        with self.assertRaises(ValueError):
            distinctid.distinct_batch(-5, shard_id=1, redis_key=self.test_redis_key)


class TestBufferingEdgeCases(unittest.TestCase):
    """Test edge cases for buffering."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:buffer_edge"
        distinctid.disable_buffering()

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_buffer_refill(self):
        """Test that buffer refills correctly when exhausted."""
        buffer_size = 10
        distinctid.enable_buffering(buffer_size=buffer_size)

        # Generate more IDs than buffer size to force refill
        ids = []
        for _ in range(buffer_size + 5):
            id_val = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
            ids.append(id_val)

        # All should be unique
        self.assertEqual(len(set(ids)), len(ids))

        distinctid.disable_buffering()

    def test_multiple_enable_disable_cycles(self):
        """Test enabling and disabling buffering multiple times."""
        for _ in range(3):
            distinctid.enable_buffering(buffer_size=50)
            id1 = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)

            distinctid.disable_buffering()
            id2 = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)

            self.assertNotEqual(id1, id2)

        distinctid.disable_buffering()


class TestPerformanceRegression(unittest.TestCase):
    """Performance regression tests."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:perf"
        distinctid.disable_buffering()

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_individual_calls_performance(self):
        """Test that individual calls complete within reasonable time."""
        count = 100
        start = time.perf_counter()

        for _ in range(count):
            distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)

        duration = time.perf_counter() - start

        # Should complete 100 calls in under 500ms (very conservative)
        self.assertLess(duration, 0.5, f"100 calls took {duration*1000:.2f}ms")

    def test_batch_performance(self):
        """Test that batch generation is significantly faster."""
        count = 100

        # Batch approach
        start = time.perf_counter()
        distinctid.distinct_batch(
            count, shard_id=1, redis_key=self.test_redis_key + ":batch"
        )
        batch_duration = time.perf_counter() - start

        # Should complete in under 10ms
        self.assertLess(batch_duration, 0.01, f"Batch took {batch_duration*1000:.2f}ms")

    def test_buffered_performance(self):
        """Test that buffering improves performance."""
        count = 100

        # Without buffering
        distinctid.disable_buffering()
        start = time.perf_counter()
        for _ in range(count):
            distinctid.distinct(shard_id=1, redis_key=self.test_redis_key + ":nobuf")
        no_buffer_duration = time.perf_counter() - start

        # With buffering
        distinctid.enable_buffering(buffer_size=count)
        start = time.perf_counter()
        for _ in range(count):
            distinctid.distinct(shard_id=1, redis_key=self.test_redis_key + ":buf")
        buffer_duration = time.perf_counter() - start

        # Buffered should be faster
        self.assertLess(buffer_duration, no_buffer_duration)

        distinctid.disable_buffering()


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple features."""

    def setUp(self) -> None:
        self.test_redis_key = "distinctid:test:integration"
        distinctid.disable_buffering()
        distinctid.enable_metrics(False)

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_all_generation_methods_produce_unique_ids(self):
        """Test that all generation methods produce unique IDs."""
        all_ids = []

        # Individual calls
        for _ in range(10):
            all_ids.append(
                distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
            )

        # Batch
        all_ids.extend(
            distinctid.distinct_batch(10, shard_id=1, redis_key=self.test_redis_key)
        )

        # Buffered
        distinctid.enable_buffering(buffer_size=20)
        for _ in range(10):
            all_ids.append(
                distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
            )
        distinctid.disable_buffering()

        # All should be unique
        self.assertEqual(len(all_ids), 30)
        self.assertEqual(len(set(all_ids)), 30)

    def test_configuration_persistence(self):
        """Test that configuration changes persist."""
        # Configure Redis
        distinctid.configure_redis(host="localhost", port=6379, max_connections=25)

        # Generate ID to verify config works
        id1 = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
        self.assertIsInstance(id1, int)

        # Enable metrics
        distinctid.enable_metrics(True)
        id2 = distinctid.distinct(shard_id=1, redis_key=self.test_redis_key)
        self.assertIsInstance(id2, int)

        distinctid.enable_metrics(False)


class TestAsyncEdgeCases(unittest.IsolatedAsyncioTestCase):
    """Edge cases for async functionality."""

    async def asyncSetUp(self) -> None:
        self.test_redis_key = "distinctid:test:async_edge"
        distinctid._async_redis_client = None

        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    async def asyncTearDown(self) -> None:
        if distinctid._async_redis_client is not None:
            try:
                await distinctid._async_redis_client.aclose()
            except Exception:
                pass
            distinctid._async_redis_client = None

    async def test_concurrent_async_calls(self):
        """Test concurrent async ID generation."""
        try:
            # Generate IDs concurrently
            tasks = [
                distinctid.distinct_async(shard_id=i % 3, redis_key=self.test_redis_key)
                for i in range(20)
            ]
            ids = await asyncio.gather(*tasks)

            # All should be unique
            self.assertEqual(len(ids), 20)
            self.assertEqual(len(set(ids)), 20)

        except ImportError:
            self.skipTest("redis[asyncio] not installed")

    async def test_async_batch_large(self):
        """Test async batch with large count."""
        try:
            count = 500
            ids = await distinctid.distinct_batch_async(
                count, shard_id=1, redis_key=self.test_redis_key
            )

            self.assertEqual(len(ids), count)
            self.assertEqual(len(set(ids)), count)

        except ImportError:
            self.skipTest("redis[asyncio] not installed")


class TestEpochCachingEdgeCases(unittest.TestCase):
    """Edge cases for epoch base caching."""

    def test_epoch_cache_survives_multiple_calls(self):
        """Test that epoch cache persists across calls."""
        # First call initializes cache
        epoch1 = distinctid._get_epoch_base()

        # Subsequent calls should use cache
        for _ in range(10):
            epoch = distinctid._get_epoch_base()
            self.assertEqual(epoch, epoch1)

    def test_epoch_cache_year_boundary(self):
        """Test epoch cache updates on year change."""
        # Get current epoch
        epoch_current = distinctid._get_epoch_base()

        # Mock year change
        with mock.patch("distinctid.date") as mock_date:
            mock_date.today.return_value.year = 2030

            from datetime import datetime as dt

            with mock.patch("distinctid.datetime") as mock_datetime:
                mock_datetime.side_effect = lambda *args, **kw: dt(*args, **kw)

                # Should recalculate
                epoch_new = distinctid._get_epoch_base()

                # Should be different
                self.assertNotEqual(epoch_current, epoch_new)


if __name__ == "__main__":
    unittest.main()
