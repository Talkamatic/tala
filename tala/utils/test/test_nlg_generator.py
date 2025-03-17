import json
import os

from jinja2 import Environment
import structlog

from tala.utils import nlg
from tala.utils.func import configure_stdout_logging

environment = Environment()

DEFAULT_CONTEXT = {"facts": {}, "facts_being_grounded": {}, "entities_under_discussion": {}}


class TestGenerator():
    def setup_method(self):
        self.logger = structlog.get_logger(__name__)
        configure_stdout_logging("DEBUG")
        self.load_default_model()
        self.given_context(DEFAULT_CONTEXT)

    def load_default_model(self):
        self._path_of_this_script = os.path.dirname(os.path.realpath(__file__))
        self._load_model(f"{self._path_of_this_script}/nlg_data.json")

    def _load_model(self, path):
        with open(path) as nlg_data:
            self._data = json.load(nlg_data)

    def given_context(self, data):
        self._context = data

    def given_facts(self, facts):
        self._context["facts"] = facts

    def given_moves(self, data):
        self._moves = data

    def when_generate_is_called(self):
        session = {"nlg": self._data}
        self._result = nlg.generate(self._moves, self._context, session, self.logger)

    def then_result_contains(self, expected):
        for key in expected:
            assert expected[key] == self._result[key]

    def then_result_contains_one_of(self, possible_results):
        def entry_lists_match(expected, actual):
            for i in range(0, len(expected)):
                if not entries_match(expected[i], actual):
                    print("no match:", expected[i], actual)
                    return False
            return True

        def entries_match(expected, actual):
            return expected.get("uttrance", None) == actual.get("uttrance", None) \
                and expected.get("persona", None) == actual.get("persona", None)

        assert any([entry_lists_match(expected, self._result) for expected in possible_results])

    def test_basic_request(self):
        self.given_moves(["greet"])
        self.when_generate_is_called()
        self.then_result_contains_one_of([[{
            "utterance": "Hello!",
            "persona": None,
            "voice": None
        }], [{
            "utterance": "Hi!",
            "persona": None,
            "voice": None
        }]])

    def test_two_moves(self):
        self.given_moves(["icm:acc*pos", "ask(?X.city_mock_uuid_1(X))"])
        self.when_generate_is_called()
        self.then_result_contains({'persona': 'tutor', 'utterance': 'Ok. What city do you want the temperature for?'})

    def test_get_utterance_of_two_moves(self):
        self.given_moves(["icm:acc*pos", "ask(?X.city_mock_uuid_1(X))"])
        self.when_generate_utterance_is_called()
        self.then_result_is('Ok. What city do you want the temperature for?')

    def when_generate_utterance_is_called(self):
        session = {"nlg": self._data}
        self._result = nlg.generate_utterance(self._moves, {}, session, self.logger)

    def then_result_is(self, result):
        assert result == self._result

    def test_generalized_slots_for_grammar_entries_in_db(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "20_mock_uuid_5",
            },
            "city_mock_uuid_1": {
                "sort": "other_sort",
                "value": "gothenburg_mock_uuid_2",
            }
        })
        self.given_moves(["answer(temperature_mock_uuid_0(20_mock_uuid_5))"])
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': 'The temperature in Gothenburg is 20 degrees centigrade.'
        })

    def test_generalized_slots_for_grammar_entries_in_db_dont_care_about_individual(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "20_mock_uuid_5",
            },
            "city_mock_uuid_1": {
                "sort": "other_sort",
                "value": "gothenburg_mock_uuid_2",
            }
        })
        self.given_moves(["answer(temperature_mock_uuid_0(some_random_string))"])
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': 'The temperature in Gothenburg is 20 degrees centigrade.'
        })

    def test_generalized_slots_from_facts(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "id_24333u4u",
                "grammar_entry": "30"
            },
            "city_mock_uuid_1": {
                "sort": "other_sort",
                "value": "id_24333u4u",
                "grammar_entry": "Paris"
            }
        })
        self.given_moves(["answer(temperature_mock_uuid_0(30_mock_uuid_5))"])
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': 'The temperature in Paris is 30 degrees centigrade.'
        })

    def test_grammar_entry_overrides_other_data(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "3000_mock_uuid_10",
            },
            "city_mock_uuid_1": {
                "sort": "other_sort",
                "value": "hell",
            }
        })
        self.given_moves(["answer(temperature_mock_uuid_0(3000_mock_uuid_10))"])
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': "The temperature in hell can't be measured in centigrades."
        })
