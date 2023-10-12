import unittest

from tala.log.serialization import serialize, unserialize


class CustomClass(object):
    def __eq__(self, other):
        return isinstance(other, CustomClass)

    def __ne__(self, other):
        return not (other == self)


class SerializationTestCase(unittest.TestCase):
    def test_round_trip_for_instance_of_builtin_class(self):
        self.given_serialized("a string")
        self.when_unserializing_serialized_result()
        self.then_result_is("a string")

    def given_serialized(self, obj):
        self._serialized_result = serialize(obj)

    def when_unserializing_serialized_result(self):
        self._result = unserialize(self._serialized_result)

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._result)

    def test_round_trip_for_instance_of_custom_class(self):
        self.given_serialized(CustomClass())
        self.when_unserializing_serialized_result()
        self.then_result_is(CustomClass())

    def test_serialized_string_spans_single_line(self):
        self.when_serialize_string_containing_newline()
        self.then_result_contains_no_newline()

    def when_serialize_string_containing_newline(self):
        self._result = serialize("line1\nline2")

    def then_result_contains_no_newline(self):
        self.assertNotIn(b"\n", self._result)
