import unittest

from mock import Mock

from tala.model.predicate import Predicate
from tala.model.sort import Sort
from tala.model.individual import Individual
from tala.model.proposition import Proposition, PredicateProposition
from tala.model.polarity import Polarity
from tala.ddd.ddd_component_manager import DDDComponentManager

from tala.http_formatting import HttpFormatter
from tala.ddd.ddd_specific_components import DDDSpecificComponents


class HttpFormattingTest(unittest.TestCase):
    def setUp(self):
        self._mock_ddd = self._create_mock_ddd_components()
        self._mock_ddd_manager = self._create_mock_ddd_component_manager()

    def _create_mock_ddd_components(self):
        mock_components = Mock(spec=DDDSpecificComponents)
        return mock_components

    def _create_mock_ddd_component_manager(self):
        mock_component_manager = Mock(spec=DDDComponentManager)
        mock_component_manager.get_ddd_specific_components_of_ontology_name.return_value = self._mock_ddd
        return mock_component_manager

    def test_fact_to_json_object_for_value_with_grammar_entry(self):
        self.given_created_http_formatter()
        self.when_call_fact_to_json_object(
            self.mock_predicate_proposition(
                predicate_name="mock_predicate",
                sort_name="mock_sort",
                value="mock_individual_value",
                value_as_json_object={"value": "mock_value"}
            ), {
                "session_id": "blah",
                "entities": [{
                    "sort": "mock_sort",
                    "natural_language_form": "mock_grammar_entry",
                    "name": "mock_individual_value"
                }]
            }
        )
        self.then_result_is({
            "sort": "mock_sort",
            "value": "mock_value",
            "grammar_entry": "mock_grammar_entry",
            'perception_confidence': None,
            'understanding_confidence': None,
            'weighted_confidence': None,
            'weighted_understanding_confidence': None
        })

    def given_created_http_formatter(self):
        self._http_formatter = HttpFormatter(self._mock_ddd_manager)

    def when_call_fact_to_json_object(self, fact, session):
        self._actual_result = self._http_formatter.fact_to_json_object(fact, session)

    def mock_predicate_proposition(
        self,
        predicate_name="mock_predicate",
        sort_name="mock_sort",
        value="mock_value",
        perception_confidence=None,
        understanding_confidence=None,
        weighted_confidence=None,
        weighted_understanding_confidence=None,
        value_as_json_object=None,
        polarity=Polarity.POS
    ):
        value_as_json_object = value_as_json_object or {"value": "mock_value"}
        sort = self._mock_sort(sort_name)
        predicate = self._mock_predicate(predicate_name, sort)
        individual = self._mock_individual(value, value_as_json_object, sort)
        mock_proposition = Mock(spec=PredicateProposition)
        mock_proposition.is_predicate_proposition.return_value = True
        mock_proposition.predicate = predicate
        mock_proposition.individual = individual
        mock_proposition.sort = sort
        mock_proposition.get_polarity.return_value = polarity
        mock_proposition.confidence_estimates.perception_confidence = perception_confidence
        mock_proposition.confidence_estimates.understanding_confidence = understanding_confidence
        mock_proposition.confidence_estimates.weighted_confidence = weighted_confidence
        mock_proposition.confidence_estimates.weighted_understanding_confidence = weighted_understanding_confidence
        return mock_proposition

    def _mock_predicate(self, name, sort):
        mock_predicate = Mock(spec=Predicate)
        mock_predicate.get_name.return_value = name
        mock_predicate.sort = sort
        return mock_predicate

    def _mock_sort(self, name):
        mock_sort = Mock(spec=Sort)
        mock_sort.get_name.return_value = name
        return mock_sort

    def _mock_individual(self, value, value_as_json_object, sort):
        mock_individual = Mock(spec=Individual)
        mock_individual.sort = sort
        mock_individual.value = value
        mock_individual.value_as_json_object.return_value = value_as_json_object
        return mock_individual

    def then_result_is(self, expected):
        self.assertEqual(expected, self._actual_result)

    def test_fact_to_json_object_for_value_without_grammar_entry(self):
        self.given_created_http_formatter()
        self.when_call_fact_to_json_object(
            self.mock_predicate_proposition(
                predicate_name="mock_predicate",
                sort_name="mock_sort",
                value="mock_value",
                value_as_json_object={"value": "mock_value"}
            ), {}
        )
        self.then_result_is({
            "sort": "mock_sort",
            "value": "mock_value",
            "grammar_entry": None,
            'perception_confidence': None,
            'understanding_confidence': None,
            'weighted_confidence': None,
            'weighted_understanding_confidence': None
        })

    def test_fact_to_json_object_for_none(self):
        self.given_created_http_formatter()
        self.when_call_fact_to_json_object(None, {})
        self.then_result_is(None)

    def test_facts_to_json_object_base_case(self):
        self.given_created_http_formatter()
        self.when_call_facts_to_json_object([
            self.mock_predicate_proposition(
                predicate_name="mock_predicate",
                sort_name="mock_sort",
                value="mock_value",
                value_as_json_object={"value": "mock_value"}
            )
        ], {
            "session_id": "blah",
            "entities": [{
                "sort": "mock_sort",
                "natural_language_form": "mock_grammar_entry",
                "name": "mock_value"
            }]
        })
        self.then_result_is({
            "mock_predicate": {
                "sort": "mock_sort",
                "value": "mock_value",
                "grammar_entry": "mock_grammar_entry",
                'perception_confidence': None,
                'understanding_confidence': None,
                'weighted_confidence': None,
                'weighted_understanding_confidence': None
            }
        })

    def when_call_facts_to_json_object(self, facts, session):
        self._actual_result = self._http_formatter.facts_to_json_object(facts, session)

    def test_facts_to_json_object_excludes_negative_predicate_propositions(self):
        self.given_created_http_formatter()
        self.when_call_facts_to_json_object([self.mock_predicate_proposition(polarity=Polarity.NEG)], {})
        self.then_result_is({})

    def test_facts_to_json_object_excludes_non_predicate_propositions(self):
        self.given_created_http_formatter()
        self.when_call_facts_to_json_object([self.mock_non_predicate_proposition()], {})
        self.then_result_is({})

    def test_facts_to_json_object_excludes_nullary_predicate_propositions(self):
        self.given_created_http_formatter()
        self.when_call_facts_to_json_object([self.mock_nullary_predicate_proposition()], {})
        self.then_result_is({})

    def mock_non_predicate_proposition(self, polarity=Polarity.POS):
        mock_proposition = Mock(spec=Proposition)
        mock_proposition.is_predicate_proposition.return_value = False
        mock_proposition.get_polarity.return_value = polarity
        return mock_proposition

    def mock_nullary_predicate_proposition(self, predicate_name="mock_yn_predicate", sort_name="boolean"):
        sort = self._mock_sort(sort_name)
        predicate = self._mock_predicate(predicate_name, sort)
        mock_proposition = Mock(spec=PredicateProposition)
        mock_proposition.predicate = predicate
        mock_proposition.value = None
        return mock_proposition
