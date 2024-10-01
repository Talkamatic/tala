import unittest

from unittest.mock import Mock

from tala.ddd.services.service_interface import ServiceInterface
from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition, LambdaAbstractedGoalProposition
from tala.model.ontology import Ontology
from tala.model.polarity import Polarity
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition
from tala.model.question import WhQuestion
from tala.model.sort import CustomSort, RealSort, IntegerSort, BooleanSort, StringSort
from tala.testing.utils import EqualityAssertionTestCaseMixin


class LibTestCase(unittest.TestCase, EqualityAssertionTestCaseMixin):
    DDD_NAME = "mockup_ddd"

    def setUpLibTestCase(self):
        self.ontology_name = "mockup_ontology"
        self._city_sort = CustomSort(self.ontology_name, "city", dynamic=True)
        self.ontology = self._create_ontology()

        self.empty_ontology = Ontology("empty_ontology", {}, {}, {}, set())

        self.domain_name = "mockup_domain"

        self._create_semantic_objects()
        self.ddd = self._create_and_add_ddd()

    def _create_ontology(self):
        sorts = {
            self._city_sort,
            CustomSort(self.ontology_name, "city_type"),
            CustomSort(self.ontology_name, "ticket_type"),
            CustomSort(self.ontology_name, "passenger_type"),
        }
        predicates = {
            self._create_predicate("dest_city", self._city_sort),
            self._create_predicate(
                "dest_city_type", sort=CustomSort(self.ontology_name, "city_type"), feature_of_name="dest_city"
            ),
            self._create_predicate("dept_city", self._city_sort),
            self._create_predicate("price", RealSort()),
            self._create_predicate("number_of_passengers", IntegerSort()),
            self._create_predicate(
                "passenger_type_to_add", sort=CustomSort(self.ontology_name, "passenger_type"), multiple_instances=True
            ),
            self._create_predicate("available_ticket_type", CustomSort(self.ontology_name, "ticket_type")),
            self._create_predicate("available_city", self._city_sort),
            self._create_predicate("need_visa", BooleanSort()),
            self._create_predicate("comment_message", StringSort()),
        }
        individuals = {
            "paris": self._city_sort,
            "london": self._city_sort,
        }
        actions = {"top", "buy"}
        return Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def _create_predicate(self, *args, **kwargs):
        return Predicate(self.ontology_name, *args, **kwargs)

    def _create_semantic_objects(self):
        self.sort_city = self.ontology.get_sort("city")
        self.sort_city_type = self.ontology.get_sort("city_type")

        self.predicate_dest_city = self.ontology.get_predicate("dest_city")
        self.predicate_dest_city_type = self.ontology.get_predicate("dest_city_type")
        self.predicate_dept_city = self.ontology.get_predicate("dept_city")
        self.predicate_price = self.ontology.get_predicate("price")
        self.predicate_available_ticket_type = self.ontology.get_predicate("available_ticket_type")
        self.predicate_available_city = self.ontology.get_predicate("available_city")
        self.predicate_number_of_passengers = self.ontology.get_predicate("number_of_passengers")
        self.predicate_need_visa = self.ontology.get_predicate("need_visa")

        self.individual_paris = self.ontology.create_individual("paris")
        self.individual_london = self.ontology.create_individual("london")
        self.individual_not_paris = self.ontology.create_negative_individual("paris")

        self.real_individual = self.ontology.create_individual(1234.0)

        self.proposition_dest_city_paris = PredicateProposition(self.predicate_dest_city, self.individual_paris)
        self.proposition_dest_city_london = PredicateProposition(self.predicate_dest_city, self.individual_london)
        self.proposition_dept_city_paris = PredicateProposition(self.predicate_dept_city, self.individual_paris)
        self.proposition_dept_city_london = PredicateProposition(self.predicate_dept_city, self.individual_london)
        self.proposition_not_dest_city_paris = PredicateProposition(
            self.predicate_dest_city, self.individual_paris, Polarity.NEG
        )
        self.price_proposition = PredicateProposition(self.predicate_price, self.real_individual)

        self.lambda_abstracted_price_prop = LambdaAbstractedPredicateProposition(
            self.predicate_price, self.ontology_name
        )
        self.lambda_abstracted_dest_city_prop = LambdaAbstractedPredicateProposition(
            self.predicate_dest_city, self.ontology_name
        )
        self.lambda_abstracted_dept_city_prop = LambdaAbstractedPredicateProposition(
            self.predicate_dept_city, self.ontology_name
        )
        self.lambda_abstracted_ticket_type_prop = LambdaAbstractedPredicateProposition(
            self.predicate_available_ticket_type, self.ontology_name
        )
        self.lambda_abstracted_available_city_prop = LambdaAbstractedPredicateProposition(
            self.predicate_available_city, self.ontology_name
        )
        self.lambda_abstracted_number_of_passengers_prop = LambdaAbstractedPredicateProposition(
            self.predicate_number_of_passengers, self.ontology_name
        )

        self.price_question = WhQuestion(self.lambda_abstracted_price_prop)
        self.dest_city_question = WhQuestion(self.lambda_abstracted_dest_city_prop)
        self.dept_city_question = WhQuestion(self.lambda_abstracted_dept_city_prop)
        self.action_question = WhQuestion(LambdaAbstractedGoalProposition())
        self.available_ticket_type_question = WhQuestion(self.lambda_abstracted_ticket_type_prop)
        self.available_city_question = WhQuestion(self.lambda_abstracted_available_city_prop)
        self.number_of_passengers_question = WhQuestion(self.lambda_abstracted_number_of_passengers_prop)

        self.lambda_abstracted_goal_prop = LambdaAbstractedGoalProposition()

        self.buy_action = self.ontology.create_action("buy")
        self.top_action = self.ontology.create_action("top")

    def _create_and_add_ddd(self):
        return DDD(
            self.DDD_NAME,
            self.ontology,
            Domain(self.DDD_NAME, "mockup_domain", self.ontology),
            service_interface=Mock(spec=ServiceInterface),
        )

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._actual_result)

    def when_call(self, callable_):
        self._actual_result = callable_()

    def when_getting_value(self, result):
        self._actual_result = result
