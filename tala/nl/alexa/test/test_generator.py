# encoding: utf-8

import json
import re

from mock import patch
import pytest

from tala.model.grammar.intent import Request, Question, Answer
from tala.model.grammar.required_entity import RequiredPropositionalEntity, RequiredSortalEntity
from tala.nl.alexa import generator
from tala.nl.alexa.generator import AlexaGenerator
from tala.nl.languages import ENGLISH
from tala.nl.test.generator_tests_base import GeneratorTestsMixin


class TestAlexaGenerator(GeneratorTestsMixin):
    def _create_generator(self):
        return AlexaGenerator(self._mocked_ddd, ENGLISH)

    def then_result_matches(self, expected_contents):
        expected_contents = json.dumps(expected_contents)
        super(TestAlexaGenerator, self).then_result_matches(expected_contents)

    def test_generate_requests(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=["mocked_individual"])
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            individuals={"mocked_individual": ["mock individual"]},
            requests=[
                Request("mocked_action", ["mocked action"], []),
                Request("mocked_action", ["mocked action ", ""], [RequiredSortalEntity("mocked_sort")])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_action_mocked_action",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": ["mocked action", "mocked action {mock_ddd_sort_mocked_sort}"]
        })  # yapf: disable

    def then_result_has_intent(self, expected_intent):
        actual_content = json.loads(self._result)
        actual_intents = actual_content["interactionModel"]["languageModel"]["intents"]
        assert expected_intent in actual_intents, \
            "Expected to find {!r} in {!r} but didn't".format(expected_intent, actual_intents)

    def test_individuals_added_as_types(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_type({
            "name": "mock_ddd_sort_mocked_sort",
            "values": [{
                "id": "contact_john",
                "name": {
                    "value": "John",
                    "synonyms": ["Johnny"]
                }
            }, {
                "id": "contact_john_chi",
                "name": {
                    "value": u"约翰",
                    "synonyms": []
                }
            }, {
                "id": "contact_lisa",
                "name": {
                    "value": "Lisa",
                    "synonyms": ["Elizabeth"]
                }
            }, {
                "id": "contact_mary",
                "name": {
                    "value": "Mary",
                    "synonyms": []
                }
            }, {
                "id": "contact_andy",
                "name": {
                    "value": "Andy",
                    "synonyms": []
                }
            }, {
                "id": "contact_andy_chi",
                "name": {
                    "value": u"安迪",
                    "synonyms": []
                }
            }]
        })  # yapf: disable

    def test_propositional_entities_in_requests(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request(
                    "mocked_action", ["make a mocked_action to ", ""], [
                        RequiredPropositionalEntity("mocked_predicate"),
                    ]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_action_mocked_action",
            "slots": [{
                "name": "mock_ddd_predicate_mocked_predicate",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": [
                "make a mocked_action",
                "make a mocked_action to {mock_ddd_predicate_mocked_predicate}"
            ]
        })  # yapf: disable

    def then_result_has_type(self, expected_type):
        actual_content = json.loads(self._result)
        assert expected_type in actual_content["interactionModel"]["languageModel"]["types"]

    def test_generate_requests_with_two_sortal_entities(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            requests=[
                Request(
                    "mocked_action", ["first ", " then ", ""], [
                        RequiredSortalEntity("mocked_sort"),
                        RequiredSortalEntity("mocked_sort"),
                    ]
                ),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_action_mocked_action",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": ["first {mock_ddd_sort_mocked_sort} then {mock_ddd_sort_mocked_sort}"]
        })  # yapf: disable

    def test_generate_questions(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_expected_plan_questions_in_domain({"mocked_question": "mocked_sort"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            questions=[
                Question("mocked_question", ["tell me a phone number"], []),
                Question("mocked_question", ["what is ", "'s number"], [
                    RequiredSortalEntity("mocked_sort"),
                ])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_question_mocked_question",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": [
                "tell me a phone number",
                "what is {mock_ddd_sort_mocked_sort}'s number"
            ]
        })  # yapf: disable

    def test_propositional_entities_in_questions(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_expected_plan_questions_in_domain({"mocked_question": "mocked_sort"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            questions=[
                Question("mocked_question", ["tell me a phone number"], []),
                Question(
                    "mocked_question", ["tell me ", "'s number"], [
                        RequiredPropositionalEntity("mocked_predicate"),
                    ]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_question_mocked_question",
            "slots": [{
                "name": "mock_ddd_predicate_mocked_predicate",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": [
                "tell me a phone number",
                "tell me {mock_ddd_predicate_mocked_predicate}'s number"
            ]
        })  # yapf: disable

    def test_generate_answer_intents(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            }
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_answer",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": ["{mock_ddd_sort_mocked_sort}"]
        })  # yapf: disable

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            }
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_answer_negation",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": ["not {mock_ddd_sort_mocked_sort}"]
        })  # yapf: disable

    @property
    def _contact_data(self):
        return ["Andy", "Mary", "Lisa", "Elizabeth", u"安迪", u"约翰", "John", "Johnny"]

    def test_sortal_entities_in_answers(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            answers=[Answer(["my sortal friend ", ""], [
                RequiredSortalEntity("mocked_sort"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_answer",
            "slots": [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort",
            }],
            "samples": [
                "{mock_ddd_sort_mocked_sort}",
                "my sortal friend {mock_ddd_sort_mocked_sort}",
            ]
        })  # yapf: disable

    def test_propositional_entities_in_answers(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": [u"约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": [u"安迪"],
            },
            answers=[Answer(["my friend ", ""], [
                RequiredPropositionalEntity("mocked_predicate"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({
            "name": "mock_ddd_answer",
            "slots": [
                {
                    "name": "mock_ddd_sort_mocked_sort",
                    "type": "mock_ddd_sort_mocked_sort",
                },
                {
                    "name": "mock_ddd_predicate_mocked_predicate",
                    "type": "mock_ddd_sort_mocked_sort",
                },
            ],
            "samples": [
                "{mock_ddd_sort_mocked_sort}",
                "my friend {mock_ddd_predicate_mocked_predicate}",
            ]
        })  # yapf: disable

    @pytest.mark.parametrize(
        "expected_intent", ["AMAZON.YesIntent", "AMAZON.NoIntent", "AMAZON.CancelIntent", "AMAZON.StopIntent"]
    )
    def test_builtin_intents(self, expected_intent):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(individuals={})
        self.given_generator()
        self.when_generate()
        self.then_result_has_intent({"name": expected_intent, "samples": []})

    def test_negative_intent_excluded(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(individuals={})
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_intent_named("NEGATIVE")

    def then_result_does_not_contain_intent_named(self, expected_name):
        actual_content = json.loads(self._result)
        actual_intents = actual_content["interactionModel"]["languageModel"]["intents"]
        actual_names = [intent["name"] for intent in actual_intents]
        assert expected_name not in actual_names, \
            "Expected no intent '{}' among {} but found one".format(expected_name, actual_names)

    def test_sorts_with_no_individuals_are_not_generated_as_types(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(individuals={})
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_type_named("mock_ddd_sort_mocked_sort")

    def then_result_does_not_contain_type_named(self, expected_name):
        actual_content = json.loads(self._result)
        actual_types = actual_content["interactionModel"]["languageModel"]["types"]
        actual_names = [type_["name"] for type_ in actual_types]
        assert expected_name not in actual_names, \
            "Expected no type '{}' among {} but found one".format(expected_name, actual_names)

    def test_types_are_unique(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=["mocked_individual"])
        self.given_mocked_grammar_with(individuals={"mocked_individual": ["mocked individual"]})
        self.given_generator()
        self.when_generate()
        self.then_result_contains_only_one_type_named("mock_ddd_sort_mocked_sort")

    def then_result_contains_only_one_type_named(self, expected_name):
        actual_content = json.loads(self._result)
        actual_types = actual_content["interactionModel"]["languageModel"]["types"]
        matching_types = [type_ for type_ in actual_types if type_["name"] == expected_name]
        n_matches = len(matching_types)
        assert n_matches == 1, \
            "Expected exactly 1 type '{}' among {} but found {}".format(expected_name, actual_types, n_matches)

    def test_sorts_with_no_individuals_are_not_generated_as_answer_slots(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(
            individuals={},
            answers=[Answer(["mocked answer with ", " entity"], [
                RequiredSortalEntity("mocked_sort"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_slots_for("mock_ddd_answer")

    def then_result_does_not_contain_slots_for(self, expected_intent):
        content = json.loads(self._result)
        intents = content["interactionModel"]["languageModel"]["intents"]
        intent = [intent for intent in intents if intent["name"] == expected_intent][0]
        actual_slots = intent["slots"]
        assert not any(actual_slots), \
            "Expected no slots but found {}".format(actual_slots)

    def test_predicates_with_explicit_answer_is_generated_as_answer_slot(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=["mocked_individual"])
        self.given_mocked_grammar_with(
            individuals={"mocked_individual": ["mocked individual"]},
            answers=[Answer(["mocked answer with ", " entity"], [
                RequiredPropositionalEntity("mocked_predicate"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_contains_slots_for(
            "mock_ddd_answer", [{
                "name": "mock_ddd_sort_mocked_sort",
                "type": "mock_ddd_sort_mocked_sort"
            }, {
                "name": "mock_ddd_predicate_mocked_predicate",
                "type": "mock_ddd_sort_mocked_sort"
            }]
        )

    def then_result_contains_slots_for(self, expected_intent, expected_slots):
        content = json.loads(self._result)
        intents = content["interactionModel"]["languageModel"]["intents"]
        intent = [intent for intent in intents if intent["name"] == expected_intent][0]
        actual_slots = intent["slots"]
        assert actual_slots == expected_slots

    def test_sorts_with_no_individuals_are_not_generated_as_answer_samples(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(
            individuals={},
            answers=[Answer(["mocked answer with ", " entity"], [
                RequiredPropositionalEntity("mocked_predicate"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_samples_for("mock_ddd_answer")

    def then_result_does_not_contain_samples_for(self, expected_intent):
        content = json.loads(self._result)
        intents = content["interactionModel"]["languageModel"]["intents"]
        intent = [intent for intent in intents if intent["name"] == expected_intent][0]
        actual_samples = intent["samples"]
        assert not any(actual_samples), \
            "Expected no samples but found {}".format(actual_samples)

    def test_sorts_with_no_individuals_are_not_generated_as_answer_negation_slots(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(
            individuals={},
            answers=[Answer(["mocked answer with ", " entity"], [
                RequiredPropositionalEntity("mocked_predicate"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_slots_for("mock_ddd_answer_negation")

    def test_sorts_with_no_individuals_are_not_generated_as_answer_negation_samples(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar_with(
            individuals={},
            answers=[Answer(["mocked answer with ", " entity"], [
                RequiredPropositionalEntity("mocked_predicate"),
            ])]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_samples_for("mock_ddd_answer_negation")

    def test_slot_is_generated_for_propositional_entity_of_integer_sort(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=["mocked_individual"],
            is_integer_sort=True,
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request(
                    "mocked_action", ["make a mocked_action to ", ""], [
                        RequiredPropositionalEntity("mocked_predicate"),
                    ]
                )
            ],
            individuals={"mocked_individual": ["mocked individual"]}
        )
        self.given_generator()
        self.when_generate()
        self.then_slot_exists_for(
            expected_intent="mock_ddd_action_mocked_action",
            expected_slot={
                "name": "mock_ddd_predicate_mocked_predicate",
                "type": "AMAZON.NUMBER"
            }
        )

    def then_slot_exists_for(self, expected_intent, expected_slot):
        content = json.loads(self._result)
        intents = content["interactionModel"]["languageModel"]["intents"]
        intent = [intent for intent in intents if intent["name"] == expected_intent][0]
        actual_slots = intent["slots"]
        assert expected_slot in actual_slots, \
            "Expected slot {} among {} but didn't find it".format(expected_slot, actual_slots)

    def test_slot_is_generated_for_sortal_entity_of_integer_sort(self):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=["mocked_individual"],
            is_integer_sort=True,
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request("mocked_action", ["make a mocked_action to ", ""], [
                    RequiredSortalEntity("mocked_sort"),
                ])
            ],
            individuals={"mocked_individual": ["mocked individual"]}
        )
        self.given_generator()
        self.when_generate()
        self.then_slot_exists_for(
            expected_intent="mock_ddd_action_mocked_action",
            expected_slot={
                "name": "mock_ddd_sort_mocked_sort",
                "type": "AMAZON.NUMBER"
            }
        )

    @pytest.mark.parametrize("type_name", ["mock_ddd_sort_integer", "AMAZON.NUMBER"])
    def test_types_are_not_included_for_integer_sort(self, type_name):
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=["mocked_individual"],
            is_integer_sort=True,
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request("mocked_action", ["make a mocked_action to ", ""], [
                    RequiredSortalEntity("mocked_sort"),
                ])
            ],
            individuals={"mocked_individual": ["mocked individual"]}
        )
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_contain_type_named(type_name)

    @patch("{}.warnings".format(generator.__name__, autospec=True))
    def test_unsupported_builtin_sort_for_propositional_entity_raises_exception(self, mocked_warnings):
        self.given_mocked_warnings(mocked_warnings)
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[],
            is_builtin=True,
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request(
                    "mocked_action", ["make a mocked_action to ", ""], [
                        RequiredPropositionalEntity("mocked_predicate"),
                    ]
                )
            ],
            individuals={}
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Builtin sort 'mocked_sort' is not yet supported together with Alexa. "
            "Skipping this sort."
        )

    def when_generate_then_an_exception_is_raised_matching(self, expected_exception, expected_pattern):
        try:
            self.when_generate()
            assert False, "%s not raised" % expected_exception
        except expected_exception as e:
            assert re.match(expected_pattern, str(e))

    @patch("{}.warnings".format(generator.__name__, autospec=True))
    def test_unsupported_builtin_sort_for_sortal_entity_warns(self, mocked_warnings):
        self.given_mocked_warnings(mocked_warnings)
        self.given_ddd_name("mock_ddd")
        self.given_ontology_with(
            sort="mocked_sort",
            predicate="mocked_predicate",
            individuals=[],
            is_builtin=True,
        )
        self.given_actions_in_ontology({"mocked_action"})
        self.given_mocked_grammar_with(
            requests=[
                Request("mocked_action", ["make a mocked_action"], []),
                Request("mocked_action", ["make a mocked_action to ", ""], [
                    RequiredSortalEntity("mocked_sort"),
                ])
            ],
            individuals={}
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Builtin sort 'mocked_sort' is not yet supported together with Alexa. "
            "Skipping this sort."
        )
