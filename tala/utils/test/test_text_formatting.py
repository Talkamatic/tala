import unittest

from tala.utils import text_formatting


class TextFormattingTests(unittest.TestCase):
    def setUp(self):
        self._elements = None
        self._result = None

    def test_readable_list_with_no_elements(self):
        self.given_list([])
        self.when_creating_readable_list()
        self.then_result_was("")

    def given_list(self, elements):
        self._elements = elements

    def when_creating_readable_list(self):
        self._result = text_formatting.readable_list(self._elements)

    def then_result_was(self, expected):
        self.assertEqual(expected, self._result)

    def test_readable_list_with_one_element(self):
        self.given_list(["element"])
        self.when_creating_readable_list()
        self.then_result_was("element")

    def test_readable_list_with_two_elements(self):
        self.given_list(["first element", "second element"])
        self.when_creating_readable_list()
        self.then_result_was("first element and second element")

    def test_readable_list_with_three_elements(self):
        self.given_list(["first element", "second element", "third element"])
        self.when_creating_readable_list()
        self.then_result_was("first element, second element and third element")
