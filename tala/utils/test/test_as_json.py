import pytest
from mock import patch

import tala.utils.as_json
from tala.utils.as_json import JSONLoggable, convert_to_json


class TestConvertToJson(object):
    def test_none_is_returned_as_is(self):
        self.when_convert_to_json(None)
        self.then_result_is(None)

    def when_convert_to_json(self, object_):
        self._result = convert_to_json(object_)

    def then_result_is(self, expected):
        assert expected == self._result

    @pytest.mark.parametrize("value", [True, False])
    def test_boolean_is_returned_as_is(self, value):
        self.when_convert_to_json(value)
        self.then_result_is(value)

    @patch("{}.JSONLoggable.as_json".format(format(tala.utils.as_json.__name__)))
    def test_json_loggable_is_processed_with_its_as_json_method(self, mock_as_json):
        self.given_mock_as_json(mock_as_json)
        self.given_a_json_loggable()
        self.when_convert_to_json(self._object)
        self.then_result_is(mock_as_json(self._object))

    def given_mock_as_json(self, mock_as_json):
        def mock_convert(object_):
            return "mock_conversion:%s" % object_
            mock_as_json.side_effect = mock_convert

    def given_a_json_loggable(self):
        class JSONLoggableSubClass(JSONLoggable):
            def __init__(self):
                super(JSONLoggableSubClass, self).__init__()
                self.an_attribute = "a_value"
        self._object = JSONLoggableSubClass()

    @patch("{}.JSONLoggable.as_json".format(format(tala.utils.as_json.__name__)))
    def test_list_is_processed_recursively_and_returned_as_list(self, mock_as_json):
        self.given_mock_as_json(mock_as_json)
        self.given_a_json_loggable()
        self.when_convert_to_json([self._object])
        self.then_result_is([mock_as_json(self._object)])

    @patch("{}.JSONLoggable.as_json".format(format(tala.utils.as_json.__name__)))
    def test_set_is_processed_recursively_and_returned_as_dict(self, mock_as_json):
        self.given_mock_as_json(mock_as_json)
        self.given_a_json_loggable()
        self.when_convert_to_json(set([self._object]))
        self.then_result_is({"set": [mock_as_json(self._object)]})

    @patch("{}.JSONLoggable.as_json".format(format(tala.utils.as_json.__name__)))
    def test_dict_is_processed_recursively_and_returned_as_dict(self, mock_as_json):
        self.given_mock_as_json(mock_as_json)
        self.given_a_json_loggable()
        self.when_convert_to_json({"mock_key": self._object})
        self.then_result_is({"mock_key": mock_as_json(self._object)})

    def test_unicode_of_object_is_returned_as_fallback(self):
        self.given_an_object_that_should_be_treated_with_a_fallback_strategy()
        self.when_convert_to_json(self._object)
        self.then_result_is(unicode(self._object))

    def given_an_object_that_should_be_treated_with_a_fallback_strategy(self):
        class MockCustomClass(object):
            def __unicode__(self):
                return u"mock_unicode_return_value"
        self._object = MockCustomClass()


class TestJSONLoggable(object):
    @patch("{}.convert_to_json".format(tala.utils.as_json.__name__))
    def test_as_json_returns_dict_with_values_converted_json(self, mock_convert_to_json):
        self.given_mock_convert_to_json(mock_convert_to_json)
        self.given_json_loggable_has_attribute("mock_attribute_name", "mock_attribute_value")
        self.when_call_as_json()
        self.then_result_is({"mock_attribute_name": mock_convert_to_json("mock_attribute_value")})

    def given_mock_convert_to_json(self, mock_convert_to_json):
        def mock_convert(object_):
            return "mock_conversion:%s" % object_
        mock_convert_to_json.side_effect = mock_convert

    def given_json_loggable_has_attribute(self, attribute_name, attribute_value):
        self._json_loggable = JSONLoggable()
        setattr(self._json_loggable, attribute_name, attribute_value)

    def when_call_as_json(self):
        self._result = self._json_loggable.as_json()

    def then_result_is(self, expected):
        assert expected == self._result
