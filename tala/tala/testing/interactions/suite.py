import unittest


class TestSuite(unittest.TestSuite):
    def __init__(self, filename):
        super().__init__()
        self._filename = filename

    @property
    def filename(self):
        return self._filename
