import unittest

from tala.ddd.utils import CacheMethod


class MockClass:
    def __init__(self):
        self.times_called = 0
        self.cache = CacheMethod(self, self.increase)
        self.increment = 1

    def increase(self, x):
        self.times_called += 1
        return x + self.increment

    def set_increment(self, increment):
        self.increment = increment
        self.cache.clear()


class CacheTest(unittest.TestCase):
    def test_preserves_result(self):
        obj = MockClass()
        self.assertEqual(2, obj.increase(1))
        self.assertEqual(5, obj.increase(4))

    def test_uses_cache_when_args_similar(self):
        obj = MockClass()
        self.assertEqual(0, obj.times_called)
        obj.increase(1)
        obj.increase(1)
        self.assertEqual(1, obj.times_called)

    def test_clear_cache(self):
        obj = MockClass()
        self.assertEqual(2, obj.increase(1))
        obj.set_increment(4)
        self.assertEqual(5, obj.increase(1))
