import unittest

from tala.model.individual import Yes, No


class YesTestCase(unittest.TestCase):
    def test_is_yes(self):
        self.when_created_yes()
        self.then_is_yes_is_true()

    def when_created_yes(self):
        self._yes = Yes()

    def then_is_yes_is_true(self):
        self.assertTrue(self._yes.is_yes())

    def test_hashing_of_yes(self):
        _set = set()
        _set.add(Yes())

    def test_yes_is_positive(self):
        self.assertTrue(Yes().is_positive())


class NoTestCase(unittest.TestCase):
    def test_is_no(self):
        self.when_created_no()
        self.then_is_no_is_true()

    def when_created_no(self):
        self._no = No()

    def then_is_no_is_true(self):
        self.assertTrue(self._no.is_no())

    def test_hashing_of_no(self):
        _set = set()
        _set.add(No())

    def test_no_is_not_positive(self):
        self.assertFalse(No().is_positive())
