# encoding: utf-8

import pytest
from unittest.mock import patch, Mock

import tala.utils.as_json
from tala.utils.as_json import AsJSONMixin, convert_to_json
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class TestConvertToJson(object):
    def test_none_is_returned_as_is(self):
        self.given_object(None)
        self.when_convert_to_json()
        self.then_result_is(None)

    def given_object(self, object_):
        self._object = object_

    def when_convert_to_json(self, verbose=True):
        self._result = convert_to_json(self._object, verbose=verbose)

    def then_result_is(self, expected):
        assert expected == self._result

    @pytest.mark.parametrize("value", [True, False])
    def test_boolean_is_returned_as_is(self, value):
        self.given_object(value)
        self.when_convert_to_json()
        self.then_result_is(value)

    def test_as_json_mixin_is_processed_with_its_as_dict_method(self):
        self.given_a_mocked_as_json_mixin(as_dict_return_value={"key": "value"})
        self.when_convert_to_json()
        self.then_result_is({"key": "value"})

    def given_a_mocked_as_json_mixin(self, *args, **kwargs):
        self._object = self._create_mocked_as_json_mixin(*args, **kwargs)

    def _create_mocked_as_json_mixin(self, as_dict_return_value=None):
        mock = Mock(spec=AsJSONMixin)
        mock.as_dict.return_value = as_dict_return_value or {}
        return mock

    def test_list_is_processed_recursively_and_returned_as_list(self):
        self.given_a_mocked_as_json_mixin_as_a_list(as_dict_return_value={"key": "value"})
        self.when_convert_to_json()
        self.then_result_is([{"key": "value"}])

    def given_a_mocked_as_json_mixin_as_a_list(self, *args, **kwargs):
        self._object = [self._create_mocked_as_json_mixin(*args, **kwargs)]

    def test_set_is_processed_recursively_and_returned_as_dict(self):
        self.given_a_mocked_as_json_mixin_as_a_set(as_dict_return_value={"key": "value"})
        self.when_convert_to_json()
        self.then_result_is({"set": [{"key": "value"}]})

    def given_a_mocked_as_json_mixin_as_a_set(self, *args, **kwargs):
        self._object = {self._create_mocked_as_json_mixin(*args, **kwargs)}

    def test_dict_is_processed_recursively_and_returned_as_dict(self):
        self.given_object({"key": self._create_mocked_as_json_mixin(as_dict_return_value={"inner_key": "inner_value"})})
        self.when_convert_to_json()
        self.then_result_is({"key": {"inner_key": "inner_value"}})

    def test_that_non_verbose_call_with_as_json_is_processed_with_its_as_dict_method(self):
        self.given_a_mocked_as_json_mixin(as_dict_return_value={"key": "value"})
        self.when_convert_to_json(verbose=False)
        self.then_result_is({"key": "value"})

    def test_non_verbose_call_with_as_semantic_expression_mixin(self):
        self.given_a_mocked_as_semantic_expression_mixin(as_semantic_expression_return_value="expression")
        self.when_convert_to_json(verbose=False)
        self.then_result_is({"semantic_expression": "expression"})

    def given_a_mocked_as_semantic_expression_mixin(self, as_semantic_expression_return_value):
        mock = Mock(spec=AsSemanticExpressionMixin)
        mock.as_semantic_expression.return_value = as_semantic_expression_return_value
        self._object = mock

    def test_non_verbose_call_with_object_mixed_in_with_json_and_semantic_expression(self):
        self.given_a_mocked_object_mixed_in_with_both_json_and_semantic_expression(
            as_semantic_expression_return_value="expression", as_dict_return_value={"key": "value"}
        )
        self.when_convert_to_json(verbose=False)
        self.then_result_is({
            "semantic_expression": "expression",
        })

    def given_a_mocked_object_mixed_in_with_both_json_and_semantic_expression(
        self, as_semantic_expression_return_value, as_dict_return_value
    ):
        class JSONAndSemanticExpressionMixin(AsJSONMixin, AsSemanticExpressionMixin):
            pass

        mock = Mock(spec=JSONAndSemanticExpressionMixin)
        mock.as_semantic_expression.return_value = as_semantic_expression_return_value
        mock.as_dict.return_value = as_dict_return_value
        self._object = mock

    def test_verbose_call_with_object_mixed_in_with_json_and_semantic_expression(self):
        self.given_a_mocked_object_mixed_in_with_both_json_and_semantic_expression(
            as_semantic_expression_return_value="expression", as_dict_return_value={"key": "value"}
        )
        self.when_convert_to_json(verbose=True)
        self.then_result_is({
            "key": "value",
            "semantic_expression": "expression",
        })

    def test_unicode_of_object_is_returned_as_fallback(self):
        self.given_an_object_that_should_be_treated_with_a_fallback_strategy(unicode_return_value="åäö unicode_string")
        self.when_convert_to_json()
        self.then_result_is("åäö unicode_string")

    def given_an_object_that_should_be_treated_with_a_fallback_strategy(self, unicode_return_value):
        class MockCustomClass(object):
            def __str__(self):
                return unicode_return_value

        self._object = MockCustomClass()


class TestAsJSONMixin(object):
    def setup_method(self):
        self._mock_convert_to_json = None
        self._as_json_mixin = None
        self._result = None

    @patch("{}.convert_to_json".format(tala.utils.as_json.__name__), autospec=True)
    def test_as_json_returns_convert_to_json_result(self, mock_convert_to_json):
        self.given_mock_convert_to_json(mock_convert_to_json)
        self.given_as_json_mixin()
        self.when_call_as_json()
        self.then_result_is_from_mocked_convert_to_json()

    def given_mock_convert_to_json(self, mock_convert_to_json):
        self._mock_convert_to_json = mock_convert_to_json

    def given_as_json_mixin(self):
        self._as_json_mixin = AsJSONMixin()

    def when_call_as_json(self):
        self._result = self._as_json_mixin.as_json()

    def then_result_is_from_mocked_convert_to_json(self):
        assert self._result == self._mock_convert_to_json.return_value

    @patch("{}.convert_to_json".format(tala.utils.as_json.__name__), autospec=True)
    def test_as_json_calls_convert_to_json_with_verbose(self, mock_convert_to_json):
        self.given_mock_convert_to_json(mock_convert_to_json)
        self.given_as_json_mixin()
        self.when_call_as_json()
        self.then_convert_to_json_is_called_with_as_json_mixin_object(verbose=True)

    def then_convert_to_json_is_called_with_as_json_mixin_object(self, verbose):
        self._mock_convert_to_json.assert_called_once_with(self._as_json_mixin, verbose=verbose)

    @patch("{}.convert_to_json".format(tala.utils.as_json.__name__), autospec=True)
    def test_as_compact_json_returns_dict_with_values_converted_to_json(self, mock_convert_to_json):
        self.given_mock_convert_to_json(mock_convert_to_json)
        self.given_as_json_mixin()
        self.when_call_as_compact_json()
        self.then_result_is_from_mocked_convert_to_json()

    def when_call_as_compact_json(self):
        self._result = self._as_json_mixin.as_compact_json()

    @patch("{}.convert_to_json".format(tala.utils.as_json.__name__), autospec=True)
    def test_as_compact_json_calls_convert_to_json_without_verbose(self, mock_convert_to_json):
        self.given_mock_convert_to_json(mock_convert_to_json)
        self.given_as_json_mixin()
        self.when_call_as_compact_json()
        self.then_convert_to_json_is_called_with_as_json_mixin_object(verbose=False)
