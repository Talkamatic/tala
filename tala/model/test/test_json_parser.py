import pytest

from tala.ddd.json_parser import NonCheckingJSONParser, JSONParseFailure
from tala.model import plan_item
from tala.testing.lib_test_case import LibTestCase


class TestNonCheckingJsonParser:
    def setup_method(self):
        self._parser = NonCheckingJSONParser()

    def test_parse_log_plan_item_old_format(self):
        self._given_log_plan_item_from_old_json("test message")
        self._when_parsing_item_from_item_as_json()
        self._then_items_are_equal()

    def _given_log_plan_item_from_old_json(self, message):
        plan_item_as_json = {plan_item.TYPE_LOG: message}
        self._plan_item = self._parser.parse_plan_item(plan_item_as_json)

    def _when_parsing_item_from_item_as_json(self):
        self._parse_result = self._parser.parse_plan_item(self._plan_item.as_json())

    def _then_items_are_equal(self):
        assert self._plan_item == self._parse_result

    @pytest.mark.parametrize("log_level", plan_item.Log.LOG_LEVELS)
    def test_log_level_reflected_when_parsing_log_plan_item(self, log_level):
        self._given_plan_item_as_dict({'log': {'message': 'test message', 'level': log_level}})
        self._when_parsing_dict_as_plan_item()
        self._then_item_has_log_level(log_level)

    def _given_plan_item_as_dict(self, item):
        self._dict_to_parse = item

    def _when_parsing_dict_as_plan_item(self):
        self._parse_result = self._parser.parse_plan_item(self._dict_to_parse)

    def _then_item_has_log_level(self, level):
        assert self._parse_result.level == level

    def test_unexpected_log_level_raises_exception(self):
        self._given_plan_item_as_dict({'log': {'message': 'test message', 'level': "kalle_kula"}})
        with pytest.raises(plan_item.UnexpectedLogLevelException):
            self._when_parsing_dict_as_plan_item()

    def test_bind_yes_no_question_preserves_boolean_individual(self):
        lib_case = LibTestCase()
        lib_case.setUpLibTestCase()
        question = lib_case.ontology.create_yes_no_question("need_visa", True)
        item = plan_item.Bind(question)

        parsed = self._parser.parse_plan_item(item.as_json())

        assert parsed.question.content.individual is not None
        assert parsed.question.content.individual.value is True

    def test_bind_rejects_non_question_json(self):
        lib_case = LibTestCase()
        lib_case.setUpLibTestCase()
        proposition = lib_case.proposition_dest_city_paris

        with pytest.raises(JSONParseFailure):
            self._parser.parse_plan_item({plan_item.TYPE_BIND: proposition.as_json()})
