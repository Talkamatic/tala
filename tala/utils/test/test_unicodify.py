import unittest

from tala.utils import unicodify


class TestSelectionTests(unittest.TestCase):
    def setUp(self):
        self.unicodify = unicodify

    def test_sequence_string(self):
        self.when_sequence_string(["item one", "item two"])
        self.then_unicode_str_is("['item one', 'item two']")

    def when_sequence_string(self, sequence):
        self.unicode_str = self.unicodify._sequence_string(sequence)

    def then_unicode_str_is(self, expected_str):
        self.assertEqual(self.unicode_str, expected_str)

    def test_sequence_string_nested(self):
        self.when_sequence_string(["item one", ["sub item one", "sub item two"]])
        self.then_unicode_str_is("['item one', ['sub item one', 'sub item two']]")

    def test_dict_string(self):
        self.when_dict_string({"value one": "key one", "value two": "key two"})
        self.then_unicode_str_is("{'value one': 'key one', 'value two': 'key two'}")

    def test_dict_string_nested(self):
        self.when_dict_string({
            "value one": {
                "sub value one": "sub key two",
                "sub value two": "sub key two"
            },
            "value two": "key two"
        })
        self.then_unicode_str_is(
            "{'value one': {'sub value one': 'sub key two', 'sub value two': 'sub key two'}, 'value two': 'key two'}"
        )

    def when_dict_string(self, _dict):
        self.unicode_str = self.unicodify._dict_string(_dict)

    def test_tuple_string(self):
        self.when_tuple_string(("item one", "item two"))
        self.then_unicode_str_is("('item one', 'item two')")

    def when_tuple_string(self, _tuple):
        self.unicode_str = self.unicodify._tuple_string(_tuple)

    def test_tuple_string_nested(self):
        self.when_tuple_string(("item one", ("sub item one", "item two")))
        self.then_unicode_str_is("('item one', ('sub item one', 'item two'))")
