import unittest

import distinctid


class SimulateDistinctRun(object):
    def __init__(self, process, shard_id=None) -> None:
        self.result = process(shard_id)


class TestDistinct(unittest.TestCase):
    def setUp(self) -> None:
        self.shard_id = 1

    def test_distinct_and_shard_id(self):
        sdr = SimulateDistinctRun(distinctid.distinct, self.shard_id)
        assert distinctid.distinct(self.shard_id) > sdr.result
