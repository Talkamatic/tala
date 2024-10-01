import unittest

from unittest.mock import Mock

from tala.model.ontology import Ontology
from tala.model.person_name import PersonName

from tala.ddd.services.parameters.retriever import ParameterRetriever, ParameterNotFoundException
from tala.ddd.services.parameters.binding import SingleInstanceParameterBinding, MultiInstanceParameterBinding
from tala.ddd.services.service_interface import ServiceInterface, ServiceActionInterface, DeviceModuleTarget, \
    ServiceParameter, ParameterField
from tala.model.individual import Individual
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.set import Set
from tala.model.polarity import Polarity
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition, ResolvednessProposition
from tala.model.sort import CustomSort, StringSort, IntegerSort, PersonNameSort, BuiltinSort


class ParameterRetrieverTestCase(unittest.TestCase):
    def setUp(self):
        self._mocked_service_interface = None
        self._parameter_retriever = None
        self._ontology = None

    def _given_ontology(self, name="mock_ontology", sorts=None, predicates=None, individuals=None, actions=None):
        if sorts is None:
            sorts = set()
        if predicates is None:
            predicates = set()
        if individuals is None:
            individuals = {}
        if actions is None:
            actions = set()

        self._ontology = Ontology(name, sorts, predicates, individuals, actions)

    def _custom_proposition(self, predicate, individual, sort_name, polarity=Polarity.POS, multiple_instances=False):
        sort = self._sort(sort_name)
        return self._proposition(predicate, individual, sort, polarity=polarity, multiple_instances=multiple_instances)

    def _proposition(self, predicate, individual, sort, polarity=Polarity.POS, multiple_instances=False):
        return PredicateProposition(
            self._predicate(predicate, sort, multiple_instances), self._individual(individual, sort), polarity=polarity
        )

    def _predicate(self, name, sort, multiple_instances=False):
        return Predicate("mocked_ontology", name, sort, multiple_instances=multiple_instances)

    def _individual(self, name, sort):
        return Individual("mocked_ontology", name, sort)

    def _sort(self, name, is_dynamic=False):
        return CustomSort("mocked_ontology", name, is_dynamic)

    def _lambda_abstraction(self, predicate, sort_name):
        sort = self._sort(sort_name)
        return LambdaAbstractedPredicateProposition(self._predicate(predicate, sort), "mocked_ontology")

    def _given_service_interface(self, action):
        self._mocked_service_interface = Mock(spec=ServiceInterface)
        self._mocked_service_interface.get_action.return_value = action

    def _given_created_parameter_retriever(self):
        self._parameter_retriever = ParameterRetriever(self._mocked_service_interface, self._ontology)

    def _then_result_is(self, expected_result):
        self.assertEqual(self._result, expected_result)

    def test_preprocess_arguments_base_case(self):
        self._given_ontology(
            sorts=set([self._sort("city")]), predicates=set([self._predicate("dest_city", self._sort("city"))])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("dest_city")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="MakeReservation", facts=Set([
                self._custom_proposition("dest_city", "paris", "city"),
            ])
        )
        self._then_result_is([
            SingleInstanceParameterBinding(
                ServiceParameter("dest_city"), "paris", self._custom_proposition("dest_city", "paris", "city")
            )
        ])

    def test_non_predicate_proposition_in_facts_is_tolerated(self):
        self._given_ontology(
            sorts=set([self._sort("city")]), predicates=set([self._predicate("dest_city", self._sort("city"))])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("dest_city")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="MakeReservation",
            facts=Set([
                self._custom_proposition("dest_city", "paris", "city"),
                ResolvednessProposition(self._lambda_abstraction("dest_country", "country")),
            ])
        )
        self._then_result_is([
            SingleInstanceParameterBinding(
                ServiceParameter("dest_city"), "paris", self._custom_proposition("dest_city", "paris", "city")
            )
        ])

    def _when_preprocessing_action_arguments(self, name, facts):
        self._result = self._parameter_retriever.preprocess_action_arguments(name, facts, {})

    def _then_result_has_values(self, expected_values):
        actual_values = [binding.value for binding in self._result]
        self.assertEqual(expected_values, actual_values)

    def test_negative_propositions_in_facts_are_ignored(self):
        self._given_ontology(
            sorts=set([self._sort("city")]), predicates=set([self._predicate("dest_city", self._sort("city"))])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("dest_city")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments_then_exception_is_raised(
            name="MakeReservation",
            facts=Set([self._custom_proposition("dest_city", "paris", "city", polarity=Polarity.NEG)]),
            expected_exception=ParameterNotFoundException,
            expected_message="failed to get argument 'dest_city'"
        )

    def test_exception_raised_for_missing_required_parameter(self):
        self._given_ontology(
            sorts=set([self._sort("city")]), predicates=set([self._predicate("dest_city", self._sort("city"))])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("dest_city")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments_then_exception_is_raised(
            name="MakeReservation",
            facts=Set([]),
            expected_exception=ParameterNotFoundException,
            expected_message="failed to get argument 'dest_city'"
        )

    def _when_preprocessing_action_arguments_then_exception_is_raised(
        self, name, facts, expected_exception, expected_message
    ):
        with self.assertRaisesRegex(expected_exception, expected_message):
            self._parameter_retriever.preprocess_action_arguments(name, facts, {})

    def test_multiple_instance_argument_bound_to_all_values_and_propositions(self):
        self._given_ontology(
            sorts=set([self._sort("city")]),
            predicates=set([self._predicate("dest_city", self._sort("city"), multiple_instances=True)])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("dest_city")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="MakeReservation",
            facts=Set([
                self._custom_proposition("dest_city", "paris", "city", multiple_instances=True),
                self._custom_proposition("dest_city", "london", "city", multiple_instances=True),
            ])
        )
        self._then_result_is([
            MultiInstanceParameterBinding(
                ServiceParameter("dest_city", is_optional=False),
                values=["paris", "london"],
                propositions=[
                    self._custom_proposition("dest_city", "paris", "city", multiple_instances=True),
                    self._custom_proposition("dest_city", "london", "city", multiple_instances=True)
                ]
            )
        ])

    def _given_an_individual_of_builtin_sort(self, value):
        self._mock_builtin_sort = Mock(spec=BuiltinSort)
        self._mock_builtin_sort.is_builtin.return_value = True
        self._individual_of_builtin_sort = Mock(spec=Individual)
        self._individual_of_builtin_sort.getSort.return_value = self._mock_builtin_sort
        self._individual_of_builtin_sort.getValue.return_value = value

    def _fact(self, predicate_name, individual, polarity=Polarity.POS, multiple_instances=False):
        sort = individual.getSort()
        return PredicateProposition(
            self._predicate(predicate_name, sort, multiple_instances), individual, polarity=polarity
        )

    def _then_generator_for_individual_of_builtin_sort_is_called_with(
        self, MockGeneratorForIndividualOfBuiltinSort, *args
    ):
        MockGeneratorForIndividualOfBuiltinSort.generate.assert_called_once_with(*args)

    def test_string_parameter(self):
        self._given_ontology(
            sorts=set([self._sort("city")]), predicates=set([self._predicate("dest_city", self._sort("city"))])
        )
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"),
                [ServiceParameter("dest_city", format=ParameterField.VALUE)], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="MakeReservation", facts=Set([
                self._proposition("dest_city", "Paris", StringSort()),
            ])
        )
        self._then_result_has_values(["Paris"])

    def test_integer_parameter(self):
        self._given_ontology(predicates=set([self._predicate("n_stops", IntegerSort())]))
        self._given_service_interface(
            action=ServiceActionInterface(
                "MakeReservation", DeviceModuleTarget(device="MockedDevice"), [ServiceParameter("n_stops")], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="MakeReservation", facts=Set([
                self._proposition("n_stops", 3, IntegerSort()),
            ])
        )
        self._then_result_has_values([3])

    def test_value_of_person_name_parameter(self):
        self._given_ontology(predicates=set([self._predicate("name_of_contact_to_call", PersonNameSort())]))
        self._given_service_interface(
            action=ServiceActionInterface(
                "Call", DeviceModuleTarget(device="MockedDevice"),
                [ServiceParameter("name_of_contact_to_call", ParameterField.VALUE)], []
            )
        )
        self._given_created_parameter_retriever()
        self._when_preprocessing_action_arguments(
            name="Call",
            facts=Set([
                self._proposition("name_of_contact_to_call", PersonName("Anna"), PersonNameSort()),
            ])
        )
        self._then_result_has_values(["Anna"])
