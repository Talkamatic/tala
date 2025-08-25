import json
import os

from jinja2 import Environment
import structlog

from tala.nlg import nlg
from tala.utils.func import configure_stdout_logging

environment = Environment()

DEFAULT_CONTEXT = {"facts": {}, "facts_being_grounded": {}, "entities_under_discussion": {}}


class TestGenerator():
    def setup_method(self):
        self.logger = structlog.get_logger(__name__)
        configure_stdout_logging("DEBUG")
        self._load_default_model()
        self._load_context(DEFAULT_CONTEXT)

    def _load_default_model(self):
        self._path_of_this_script = os.path.dirname(os.path.realpath(__file__))
        self._load_model(f"{self._path_of_this_script}/nlg_data.json")

    def _load_model(self, path):
        with open(path) as nlg_data:
            self._data = json.load(nlg_data)

    def _load_context(self, data):
        self._context = data

    def then_result_contains(self, expected):
        for key in expected:
            assert expected[key] == self._nlg.result[key]

    def test_basic_request(self):
        self.given_moves(["greet"])
        self.given_nlg()
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

    def given_moves(self, data):
        self._moves = data

    def given_nlg(self):
        session = {"nlg": self._data}
        self._nlg = nlg.NLG(self._moves, self._context, session, self.logger)

    def when_generate_is_called(self):
        self._nlg.generate()

    def then_result_contains_one_of(self, possible_results):
        def entry_lists_match(expected, actual):
            for i in range(0, len(expected)):
                if not entries_match(expected[i], actual):
                    return False
            return True

        def entries_match(expected, actual):
            return expected.get("uttrance", None) == actual.get("uttrance", None) \
                and expected.get("persona", None) == actual.get("persona", None)

        assert any([entry_lists_match(expected, self._nlg.result) for expected in possible_results])

    def test_two_moves(self):
        self.given_moves(["icm:acc*pos", "ask(?X.city_mock_uuid_1(X))"])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({'persona': 'tutor', 'utterance': 'Ok. What city do you want the temperature for?'})

    def test_get_utterance_of_two_moves(self):
        self.given_moves(["icm:acc*pos", "ask(?X.city_mock_uuid_1(X))"])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_utterance_is('Ok. What city do you want the temperature for?')

    def then_utterance_is(self, expected_utterance):
        assert expected_utterance == self._nlg.utterance

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
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': 'The temperature in Gothenburg is 20 degrees centigrade.'
        })

    def given_facts(self, facts):
        self._context["facts"] = facts

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
        self.given_nlg()
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
        self.given_nlg()
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
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': "The temperature in hell can't be measured in centigrades."
        })

    def test_generalized_slots_for_string_individuals(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "20_mock_uuid_5",
            },
            "city_mock_uuid_1": {
                "sort": "string",
                "value": "Barcelona"
            }
        })
        self.given_moves(["answer(temperature_mock_uuid_0(20_mock_uuid_5))"])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': 'The temperature in Barcelona is 20 degrees centigrade.'
        })

    def test_generalized_slots_for_string_individuals_all_answers(self):
        self.given_facts({
            "temperature_mock_uuid_0": {
                "sort": "some_sort",
                "value": "20_mock_uuid_5",
            },
            "city_mock_uuid_1": {
                "sort": "string",
                "value": "Barcelona"
            }
        })
        self.given_moves(["answer(temperature_alternatives(20_mock_uuid_5))"])
        self.given_nlg()
        self.when_generate_all_utterances_is_called()
        self.then_result_is({
            'persona': 'tutor',
            'status': 'success',
            'utterances': [
                'The temperature in Barcelona is 20 degrees centigrade.',
                "It's 20 degrees centigrade in Barcelona.",
            ],
            'voice': None,
        })

    def test_naturalistic_string_slot_handling_for_single_move_utterance(self):
        self.given_facts({
            "user_name": {
                "grammar_entry": None,
                "perception_confidence": None,
                "sort": "string",
                "understanding_confidence": None,
                "value": "Fred",
                "weighted_confidence": None,
                "weighted_understanding_confidence": None
            }
        })
        self.given_moves(["answer(end_segment_information_predicate(end_segment_information))"])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({'persona': "tutor", 'utterance': "Keep up the good work, Fred!"})

    def test_naturalistic_string_slot_handling_for_multi_move_utterance(self):
        self.given_facts({
            "user_name": {
                "grammar_entry": None,
                "perception_confidence": None,
                "sort": "string",
                "understanding_confidence": None,
                "value": "Fred",
                "weighted_confidence": None,
                "weighted_understanding_confidence": None
            }
        })
        self.given_moves(['icm:acc*pos', 'ask(?X.goal(X))'])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({'persona': "tutor", 'utterance': "Yes, how can I help you, Fred?"})

    def test_string_slot_handling_in_string_proposition(self):
        self.given_facts({
            "user_name": {
                "grammar_entry": None,
                "perception_confidence": None,
                "sort": "string",
                "understanding_confidence": None,
                "value": "Fred",
                "weighted_confidence": None,
                "weighted_understanding_confidence": None
            }
        })
        self.given_moves(["answer(user_name(\"Fred\"))"])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({'utterance': "I'll call you Fred."})

    def test_move_subsequence(self):
        self.given_moves(['icm:per*pos:"wolla bolla kolla"', 'icm:sem*neg', 'icm:reraise', 'ask(?X.goal(X))'])
        self.given_nlg()
        self.when_generate_is_called()
        self.then_result_contains({
            'persona': "tutor",
            'utterance': "Sorry, I didn't catch that. Say \"coach\" if you want to talk to me again."
        })

    def test_generate_all_utterances_for_move(self):
        self.given_moves(['greet'])
        self.given_nlg()
        self.when_generate_all_utterances_is_called()
        self.then_result_is({"status": "success", "persona": None, "utterances": ["Hello!", "Hi!"], "voice": None})

    def test_generate_all_utterances_for_failing_move(self):
        self.given_moves(['greetings'])
        self.given_nlg()
        self.when_generate_all_utterances_is_called()
        self.then_result_is({"status": "fail", "message": "Could not generate utterances for ['greetings']"})

    def when_generate_all_utterances_is_called(self):
        self._nlg.generate_all_utterances()

    def then_result_is(self, expected_result):
        assert self._nlg.result == expected_result
