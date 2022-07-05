import unittest

import distinctid


class SimulateDistinctRun(object):
    def __init__(self, process, state, shard_id=None) -> None:
        self.process = process

        if shard_id is None:
            self.result = self.process(state)
        else:
            self.result = self.process(state, shard_id)


class TestDistinct(unittest.TestCase):
    def setUp(self) -> None:
        self.state = 1
        self.shard_id = 1

    def test_distinct_state(self):
        sdr = SimulateDistinctRun(distinctid.distinct, self.state)
        assert sdr.result == distinctid.distinct(self.state)

    def test_distinct_state_and_shard_id(self):
        sdr = SimulateDistinctRun(distinctid.distinct, self.state, self.shard_id)
        assert sdr.result == distinctid.distinct(self.state, self.shard_id)
