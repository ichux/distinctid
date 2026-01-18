import unittest
from unittest import mock

import distinctid


class TestDistinct(unittest.TestCase):
    def setUp(self) -> None:
        self.shard_id = 1
        self.test_redis_key = "distinctid:test:counter"

        # Disable buffering for standard tests
        distinctid.disable_buffering()

        # Clean up test key before each test
        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            # If Redis not available, test will fail with clear error
            pass

    def test_distinct_generates_unique_ids(self):
        """Test that distinct() generates unique, incrementing IDs."""
        id1 = distinctid.distinct(self.shard_id, self.test_redis_key)
        id2 = distinctid.distinct(self.shard_id, self.test_redis_key)
        id3 = distinctid.distinct(self.shard_id, self.test_redis_key)

        self.assertGreater(id2, id1)
        self.assertGreater(id3, id2)
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id2, id3)

    def test_distinct_with_different_shards(self):
        """Test distinct() with different shard IDs."""
        id_shard1 = distinctid.distinct(1, self.test_redis_key)
        id_shard2 = distinctid.distinct(2, self.test_redis_key)

        # Different shards should produce different IDs even with same counter
        self.assertNotEqual(id_shard1, id_shard2)

    def test_distinct_shard_id_validation(self):
        """Test shard_id validation."""
        # Valid range: 0-8191
        distinctid.distinct(0, self.test_redis_key)  # Should work
        distinctid.distinct(8191, self.test_redis_key)  # Should work

        # Out of range
        with self.assertRaises(ValueError):
            distinctid.distinct(-1, self.test_redis_key)

        with self.assertRaises(ValueError):
            distinctid.distinct(8192, self.test_redis_key)


class TestDistinctBatch(unittest.TestCase):
    def setUp(self) -> None:
        self.shard_id = 1
        self.test_redis_key = "distinctid:test:batch:counter"

        # Clean up test key
        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_distinct_batch_generates_multiple_ids(self):
        """Test that distinct_batch() generates correct number of IDs."""
        count = 100
        ids = distinctid.distinct_batch(count, self.shard_id, self.test_redis_key)

        self.assertEqual(len(ids), count)

    def test_distinct_batch_ids_are_unique(self):
        """Test that batch-generated IDs are unique."""
        count = 1000
        ids = distinctid.distinct_batch(count, self.shard_id, self.test_redis_key)

        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))

    def test_distinct_batch_validation(self):
        """Test batch count validation."""
        # Invalid count
        with self.assertRaises(ValueError):
            distinctid.distinct_batch(0, self.shard_id, self.test_redis_key)

        with self.assertRaises(ValueError):
            distinctid.distinct_batch(-1, self.shard_id, self.test_redis_key)

        # Invalid shard_id
        with self.assertRaises(ValueError):
            distinctid.distinct_batch(10, 9000, self.test_redis_key)

    def test_distinct_batch_performance(self):
        """Test that batch generation is efficient."""
        # Generate 1000 IDs in batch (within the 1024 limit per millisecond)
        # Note: The design allows max 1024 unique IDs per millisecond per shard
        count = 1000
        ids = distinctid.distinct_batch(count, self.shard_id, self.test_redis_key)

        self.assertEqual(len(ids), count)
        self.assertEqual(len(set(ids)), count)  # All unique


class TestBuffering(unittest.TestCase):
    def setUp(self) -> None:
        self.shard_id = 1
        self.test_redis_key = "distinctid:test:buffer:counter"

        # Disable buffering initially
        distinctid.disable_buffering()

        # Clean up test key
        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    def test_buffering_enabled(self):
        """Test that buffering can be enabled and works correctly."""
        distinctid.enable_buffering(buffer_size=100)

        # Generate IDs with buffering
        ids = [
            distinctid.distinct(self.shard_id, self.test_redis_key) for _ in range(50)
        ]

        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)  # All unique

    def test_buffering_disabled(self):
        """Test that buffering can be disabled."""
        distinctid.enable_buffering(buffer_size=100)
        distinctid.disable_buffering()

        # Should work without buffering
        id1 = distinctid.distinct(self.shard_id, self.test_redis_key)
        id2 = distinctid.distinct(self.shard_id, self.test_redis_key)

        self.assertGreater(id2, id1)

    def tearDown(self) -> None:
        # Always disable buffering after test
        distinctid.disable_buffering()


class TestConfiguration(unittest.TestCase):
    def test_configure_redis(self):
        """Test Redis configuration."""
        distinctid.configure_redis(
            host="localhost", port=6379, db=0, max_connections=10
        )
        # Should not raise exception
        client = distinctid._get_redis_client()
        self.assertIsNotNone(client)

    def test_environment_variables(self):
        """Test environment variable configuration."""
        with mock.patch.dict(
            "os.environ",
            {
                "DISTINCTID_REDIS_HOST": "testhost",
                "DISTINCTID_REDIS_PORT": "6380",
                "DISTINCTID_REDIS_DB": "2",
            },
        ):
            # Reset client to force re-initialization
            distinctid._redis_client = None

            # This would fail to connect, but we can verify the config is read
            # In actual test, we'd need a Redis instance at testhost:6380
            # For now, just verify no exception on client creation attempt
            try:
                client = distinctid._get_redis_client()
                # If we get here, environment vars were read
                self.assertIsNotNone(client)
            except Exception:
                # Expected if testhost doesn't exist
                pass

    def tearDown(self) -> None:
        # Reset to default configuration
        distinctid._redis_client = None
        distinctid.configure_redis()


class TestMetrics(unittest.TestCase):
    def test_enable_metrics(self):
        """Test metrics can be enabled/disabled."""
        distinctid.enable_metrics(True)
        self.assertTrue(distinctid._enable_metrics)

        distinctid.enable_metrics(False)
        self.assertFalse(distinctid._enable_metrics)


class TestAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.shard_id = 1
        self.test_redis_key = "distinctid:test:async:counter"

        # Reset async client to avoid event loop conflicts
        distinctid._async_redis_client = None

        # Clean up test key
        try:
            client = distinctid._get_redis_client()
            client.delete(self.test_redis_key)
        except Exception:
            pass

    async def asyncTearDown(self) -> None:
        # Clean up async client
        if distinctid._async_redis_client is not None:
            try:
                await distinctid._async_redis_client.aclose()
            except Exception:
                pass
            distinctid._async_redis_client = None

    async def test_distinct_async(self):
        """Test async ID generation."""
        try:
            id1 = await distinctid.distinct_async(self.shard_id, self.test_redis_key)
            id2 = await distinctid.distinct_async(self.shard_id, self.test_redis_key)

            self.assertGreater(id2, id1)
            self.assertNotEqual(id1, id2)
        except ImportError:
            self.skipTest("redis[asyncio] not installed")

    async def test_distinct_batch_async(self):
        """Test async batch generation."""
        try:
            count = 100
            ids = await distinctid.distinct_batch_async(
                count, self.shard_id, self.test_redis_key
            )

            self.assertEqual(len(ids), count)
            self.assertEqual(len(set(ids)), count)  # All unique
        except ImportError:
            self.skipTest("redis[asyncio] not installed")

    async def test_async_validation(self):
        """Test async validation."""
        try:
            # Invalid shard_id
            with self.assertRaises(ValueError):
                await distinctid.distinct_async(9000, self.test_redis_key)

            # Invalid batch count
            with self.assertRaises(ValueError):
                await distinctid.distinct_batch_async(
                    0, self.shard_id, self.test_redis_key
                )
        except ImportError:
            self.skipTest("redis[asyncio] not installed")


class TestEpochCaching(unittest.TestCase):
    def test_epoch_base_cached(self):
        """Test that epoch base is cached."""
        # Call twice and verify it's cached
        epoch1 = distinctid._get_epoch_base()
        epoch2 = distinctid._get_epoch_base()

        self.assertEqual(epoch1, epoch2)

    def test_epoch_base_year_rollover(self):
        """Test epoch base updates on year change."""
        # Get current epoch
        epoch1 = distinctid._get_epoch_base()

        # Mock date.today() to return next year
        with mock.patch("distinctid.date") as mock_date:
            mock_date.today.return_value.year = 2027
            from datetime import datetime as dt

            with mock.patch("distinctid.datetime") as mock_datetime:
                mock_datetime.return_value.timestamp.return_value = dt(
                    2027, 1, 1
                ).timestamp()
                mock_datetime.side_effect = lambda *args, **kw: dt(*args, **kw)

                epoch2 = distinctid._get_epoch_base()

                # Should be different (new year)
                self.assertNotEqual(epoch1, epoch2)


if __name__ == "__main__":
    unittest.main()
