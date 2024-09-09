import unittest

from tala.ddd.ddd_manager import DDDManager
from tala.model.semantic_logic import SemanticLogic
from tala.model.test.semanticstester import SemanticsTester
from tala.model.ontology import Ontology
from tala.model.polarity import Polarity
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition, PropositionSet
from tala.model.sort import CustomSort


class SemanticLogicTests(SemanticsTester):
    def setUp(self):
        SemanticsTester.setUp(self)
        self.declare_valid_relations()
        self.declare_provoker_objects()

    def declare_valid_relations(self):
        self.declare_combinable_and_relevant([
            # WH questions
            ("?X.dest_city(X)", "dest_city(paris)", "dest_city(paris)"),
            ("?X.dest_city(X)", "dest_city(london)", "dest_city(london)"),
            ("?X.dest_city(X)", "~dest_city(paris)", "~dest_city(paris)"),
            ("?X.dest_city(X)", "~dest_city(london)", "~dest_city(london)"),
            ("?X.dest_city(X)", "paris", "dest_city(paris)"),
            ("?X.dest_city(X)", "london", "dest_city(london)"),
            ("?X.dest_city(X)", "~paris", "~dest_city(paris)"),
            ("?X.dest_city(X)", "~london", "~dest_city(london)"),
            (
                "?X.dest_city(X)", "~set([dest_city(paris), dest_city(london)])",
                "~set([dest_city(paris), dest_city(london)])"
            ),
            ("?X.goal(X)", "goal(perform(make_reservation))", "goal(perform(make_reservation))"),
            ("?X.goal(X)", "goal(perform(make_domestic_reservation))", "goal(perform(make_domestic_reservation))"),
            ("?X.goal(X)", "goal(resolve(?X.price(X)))", "goal(resolve(?X.price(X)))"),

            # Yes-no questions
            ("?dest_city(paris)", "yes", "dest_city(paris)"),
            ("?dest_city(paris)", "no", "~dest_city(paris)"),
            ("?dest_city(paris)", "~dest_city(paris)", "~dest_city(paris)"),
            ("?dest_city(paris)", "paris", "dest_city(paris)"),
            ("?dest_city(paris)", "~paris", "~dest_city(paris)"),
            ("?dest_city(paris)", "dest_city(paris)", "dest_city(paris)"),
            ("?goal(perform(make_reservation))", "yes", "goal(perform(make_reservation))"),
            ("?goal(perform(make_reservation))", "no", "~goal(perform(make_reservation))"),
            ("?goal(perform(make_reservation))", "goal(perform(make_reservation))", "goal(perform(make_reservation))"),

            # understanding questions
            ("?und(USR, dest_city(paris))", "yes", "und(USR, dest_city(paris))"),
            ("?und(USR, dest_city(paris))", "no", "~und(USR, dest_city(paris))"),
            ("?und(USR, goal(perform(make_reservation)))", "yes", "und(USR, goal(perform(make_reservation)))"),
            ("?und(USR, goal(perform(make_reservation)))", "no", "~und(USR, goal(perform(make_reservation)))"),

            # multi-alt questions
            ("?set([dest_city(paris), dest_city(london)])", "dest_city(paris)", "dest_city(paris)"),
            ("?set([dest_city(paris), dest_city(london)])", "dest_city(london)", "dest_city(london)"),
            ("?set([dest_city(paris), dest_city(london)])", "~dest_city(paris)", "~dest_city(paris)"),
            ("?set([dest_city(paris), dest_city(london)])", "~dest_city(london)", "~dest_city(london)"),
            ("?set([dest_city(paris), dest_city(london)])", "paris", "dest_city(paris)"),
            ("?set([dest_city(paris), dest_city(london)])", "london", "dest_city(london)"),
            ("?set([dest_city(paris), dest_city(london)])", "~paris", "~dest_city(paris)"),
            ("?set([dest_city(paris), dest_city(london)])", "~london", "~dest_city(london)"),
            ("?set([dest_city(paris), dest_city(london)])", "no", "~set([dest_city(paris), dest_city(london)])"),
            (
                "?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])",
                "goal(perform(make_reservation))", "goal(perform(make_reservation))"
            ),
            (
                "?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "goal(resolve(?X.price(X)))",
                "goal(resolve(?X.price(X)))"
            ),
            (
                "?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "no",
                "~set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])"
            ),

            # single-alt questions
            ("?set([dest_city(paris)])", "dest_city(paris)", "dest_city(paris)"),
            ("?set([dest_city(paris)])", "~dest_city(paris)", "~dest_city(paris)"),
            ("?set([dest_city(paris)])", "paris", "dest_city(paris)"),
            ("?set([dest_city(paris)])", "~paris", "~dest_city(paris)"),
            ("?set([dest_city(paris)])", "yes", "dest_city(paris)"),
            ("?set([dest_city(paris)])", "no", "~dest_city(paris)"),
            (
                "?set([goal(perform(make_reservation))])", "goal(perform(make_reservation))",
                "goal(perform(make_reservation))"
            ),
            ("?set([goal(perform(make_reservation))])", "yes", "goal(perform(make_reservation))"),
            ("?set([goal(perform(make_reservation))])", "no", "~goal(perform(make_reservation))"),

            # preconfirmation question
            ("?preconfirmed(MakeReservation, [])", "yes", "preconfirmed(MakeReservation, [])"),
            ("?preconfirmed(MakeReservation, [])", "no", "~preconfirmed(MakeReservation, [])"),
            # features
            ("?X.dest_city(X)", "resort", "dest_city_type(resort)"),
            ("?X.dest_city(X)", "dest_city_type(resort)", "dest_city_type(resort)"),
            ("?X.dest_city(X)", "~resort", "~dest_city_type(resort)"),
            ("?X.dest_city(X)", "~dest_city_type(resort)", "~dest_city_type(resort)"),

            # knowledge precondition question
            ("?know_answer(?X.dest_city_type(X))", "yes", "know_answer(?X.dest_city_type(X))"),
            ("?know_answer(?X.dest_city_type(X))", "no", "~know_answer(?X.dest_city_type(X))"),
            ("?know_answer(?X.dest_city_type(X))", "dest_city_type(resort)", "dest_city_type(resort)"),
            ("?know_answer(?X.dest_city_type(X))", "resort", "dest_city_type(resort)"),
            ("?know_answer(?X.dest_city_type(X))", "~dest_city_type(resort)", "~dest_city_type(resort)"),
            ("?know_answer(?X.dest_city_type(X))", "~resort", "~dest_city_type(resort)"),

            # consequent question
            (
                "?X.implies(dest_city(paris), price(X))", "implies(dest_city(paris), price(123.0))",
                "implies(dest_city(paris), price(123.0))"
            ),
        ])

        self.declare_relevant_not_resolving([
            # WH questions
            ("?X.dest_city(X)", "~set([dest_city(paris), dest_city(london)])"),

            # alt questions
            ("?set([dest_city(paris), dest_city(london)])", "no"),
            ("?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "no"),

            # features
            ("?X.dest_city(X)", "~dest_city_type(resort)"),
            ("?X.dest_city(X)", "~resort"),
            ("?dest_city(paris)", "resort"),
            ("?dest_city(paris)", "~resort"),
            ("?dest_city(paris)", "~dest_city_type(resort)"),
            ("?set([dest_city(paris), dest_city(london)])", "resort"),
            ("?set([dest_city(paris)])", "resort"),
            ("?set([dest_city(paris)])", "~resort"),
            ("?set([dest_city(paris)])", "~dest_city_type(resort)"),
            ("?dest_city(paris)", "dest_city_type(resort)"),
            ("?set([dest_city(paris), dest_city(london)])", "dest_city_type(resort)"),
            ("?set([dest_city(paris), dest_city(london)])", "~dest_city_type(resort)"),
            ("?set([dest_city(paris), dest_city(london)])", "~resort"),
            ("?set([dest_city(paris)])", "dest_city_type(resort)"),

            # knowledge precondition question
            ("?know_answer(?X.dest_city_type(X))", "~dest_city_type(resort)"),
            ("?know_answer(?X.dest_city_type(X))", "~resort"),
        ])

        self.declare_resolving([
            # WH questions
            ("?X.dest_city(X)", "dest_city(paris)"),
            ("?X.dest_city(X)", "dest_city(london)"),
            ("?X.dest_city(X)", "paris"),
            ("?X.dest_city(X)", "london"),
            ("?X.goal(X)", "goal(perform(make_reservation))"),
            ("?X.goal(X)", "goal(perform(make_domestic_reservation))"),
            ("?X.goal(X)", "goal(resolve(?X.price(X)))"),

            # Yes-no questions
            ("?dest_city(paris)", "dest_city(paris)"),
            ("?dest_city(paris)", "~dest_city(paris)"),
            ("?dest_city(paris)", "paris"),
            ("?dest_city(paris)", "~paris"),
            ("?dest_city(paris)", "yes"),
            ("?dest_city(paris)", "no"),
            ("?goal(perform(make_reservation))", "goal(perform(make_reservation))"),
            ("?goal(perform(make_reservation))", "yes"),
            ("?goal(perform(make_reservation))", "no"),

            # Understanding questions
            ("?und(USR, dest_city(paris))", "yes"),
            ("?und(USR, dest_city(paris))", "no"),
            ("?und(USR, goal(perform(make_reservation)))", "yes"),
            ("?und(USR, goal(perform(make_reservation)))", "no"),

            # Multi-alt questions
            ("?set([dest_city(paris), dest_city(london)])", "dest_city(paris)"),
            ("?set([dest_city(paris), dest_city(london)])", "dest_city(london)"),
            ("?set([dest_city(paris), dest_city(london)])", "paris"),
            ("?set([dest_city(paris), dest_city(london)])", "london"),
            ("?set([dest_city(paris), dest_city(london)])", "no"),
            ("?set([dest_city(paris), dest_city(london)])", "~set([dest_city(paris), dest_city(london)])"),
            ("?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "goal(perform(make_reservation))"),
            ("?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "goal(resolve(?X.price(X)))"),
            ("?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])", "no"),
            (
                "?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])",
                "~set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])"
            ),

            # single-alt questions
            ("?set([dest_city(paris)])", "dest_city(paris)"),
            ("?set([dest_city(paris)])", "~dest_city(paris)"),
            ("?set([dest_city(paris)])", "paris"),
            ("?set([dest_city(paris)])", "~paris"),
            ("?set([dest_city(paris)])", "yes"),
            ("?set([dest_city(paris)])", "no"),
            ("?set([goal(perform(make_reservation))])", "goal(perform(make_reservation))"),
            ("?set([goal(perform(make_reservation))])", "yes"),
            ("?set([goal(perform(make_reservation))])", "no"),

            # preconfirmation question
            ("?preconfirmed(MakeReservation, [])", "yes"),
            ("?preconfirmed(MakeReservation, [])", "no"),

            # special case: issues-alt-question, issue answer not in alts
            # NOTE: does not seem to be needed.
            # ("?set([goal(resolve(?X.dest_city(X))), goal(resolve(?X.dept_city(X)))])",
            #  "goal(resolve(?X.price(X)))"),
            # ("?set([goal(resolve(?X.dest_city(X))), goal(resolve(?X.dept_city(X)))])",
            #  "no"),

            # special case: answer action is dominated by action in alts
            ("?set([goal(perform(make_reservation))])", "goal(perform(make_domestic_reservation))"),
            ("?set([goal(perform(make_reservation))])", "goal(resolve(?X.price(X)))"),
            (
                "?set([goal(perform(make_reservation)), goal(resolve(?X.price(X)))])",
                "goal(perform(make_domestic_reservation))"
            ),

            # knowledge precondition question
            ("?know_answer(?X.dest_city_type(X))", "dest_city_type(resort)"),
            ("?know_answer(?X.dest_city_type(X))", "resort"),
            ("?know_answer(?X.dest_city_type(X))", "yes"),
            ("?know_answer(?X.dest_city_type(X))", "no"),
            ("?know_answer(?X.dest_city_type(X))", "~resort"),  # disputable
            ("?know_answer(?X.dest_city_type(X))", "~dest_city_type(resort)"),  # disputable

            # consequent question
            ("?X.implies(dest_city(paris), price(X))", "implies(dest_city(paris), price(123.0))"),
        ])

        self.declare_incompatible([
            ("dest_city(paris)", "dest_city(london)"),
            ("dest_city(paris)", "~dest_city(paris)"),
            ("dest_city(london)", "~dest_city(london)"),
            ("means_of_transport(plane)", "~means_of_transport(plane)"),

            # features
            ("dest_city_type(resort)", "~dest_city(london)"),
            ("dest_city_type(resort)", "~dest_city(paris)"),
            ("~dest_city(london)", "~dest_city_type(resort)"),
            ("~dest_city(paris)", "~dest_city_type(resort)"),
            ("~dest_city_type(resort)", "dest_city_type(resort)"),
        ])

    def declare_provoker_objects(self):
        self.declare_answer("means_of_transport(plane)")
        self.declare_answer("~means_of_transport(plane)")
        self.declare_answer("plane")
        self.declare_answer("~plane")
        self.add_answers_that_are_compatible_due_to_multiple_instance_predicate()
        self.declare_answer("implies(dept_city(paris), price(123.0))")
        self.declare_answer("implies(dest_city(paris), dest_city_type(resort))")

    def add_answers_that_are_compatible_due_to_multiple_instance_predicate(self):
        self.declare_answer("passenger_type_to_add(adult)")
        self.declare_answer("passenger_type_to_add(child)")

    def test_valid_combines(self):
        self.semantics_test_valid_combines()

    def test_invalid_combines(self):
        self.semantics_test_invalid_combines()

    def test_relevance(self):
        self.semantics_test_relevance()

    def test_irrelevance(self):
        self.semantics_test_irrelevance()

    def test_resolves(self):
        self.semantics_test_resolves()

    def test_non_resolves(self):
        self.semantics_test_non_resolves()

    def test_valid_incompatibles(self):
        self.semantics_test_valid_incompatibles()

    def test_invalid_incompatibles(self):
        self.semantics_test_invalid_incompatibles()


class TestSemanticLogicWithPropositions(unittest.TestCase):
    def setUp(self):
        self._ddd_manager = DDDManager()
        self._create_ontology()
        self.ontology = self._ddd_manager.get_ontology(self.ontology_name)
        self._create_semantic_objects()
        self._language_code = "mocked_language"

        self.positive_prop_set = PropositionSet([self.proposition_dest_city_london, self.proposition_dest_city_paris])

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        self._city_sort = CustomSort(self.ontology_name, "city", dynamic=True)
        sorts = {
            self._city_sort,
            CustomSort(self.ontology_name, "city_type"),
            CustomSort(self.ontology_name, "ticket_type"),
            CustomSort(self.ontology_name, "passenger_type"),
        }
        predicates = {
            self._create_predicate("dest_city", self._city_sort),
            self._create_predicate("dept_city", self._city_sort),
        }
        individuals = {"paris": self._city_sort, "london": self._city_sort}
        actions = {"top", "buy"}
        ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)
        self._ddd_manager.add_ontology(ontology)

        self.empty_ontology = Ontology("empty_ontology", {}, {}, {}, set([]))
        self._ddd_manager.add_ontology(self.empty_ontology)

    def _create_predicate(self, *args, **kwargs):
        return Predicate(self.ontology_name, *args, **kwargs)

    def _create_semantic_objects(self):
        self.sort_city = self.ontology.get_sort("city")
        self.sort_city_type = self.ontology.get_sort("city_type")

        self.predicate_dest_city = self.ontology.get_predicate("dest_city")
        self.predicate_dept_city = self.ontology.get_predicate("dept_city")

        self.individual_paris = self.ontology.create_individual("paris")
        self.individual_london = self.ontology.create_individual("london")
        self.individual_not_paris = self.ontology.create_negative_individual("paris")

        self.proposition_dest_city_paris = \
            PredicateProposition(self.predicate_dest_city,
                                 self.individual_paris)
        self.proposition_dest_city_london = \
            PredicateProposition(self.predicate_dest_city,
                                 self.individual_london)
        self.proposition_dept_city_paris = \
            PredicateProposition(self.predicate_dept_city,
                                 self.individual_paris)
        self.proposition_dept_city_london = \
            PredicateProposition(self.predicate_dept_city,
                                 self.individual_london)
        self.proposition_not_dest_city_paris = \
            PredicateProposition(self.predicate_dest_city,
                                 self.individual_paris,
                                 Polarity.NEG)

    def test_combine_with_proposition_in_set_returns_proposition(self):
        self.assertEqual(
            self.proposition_dest_city_paris,
            SemanticLogic(self._ddd_manager).combine(self.positive_prop_set, self.proposition_dest_city_paris)
        )

    def test_combine_with_individual_in_set_returns_proposition(self):
        self.assertEqual(
            self.proposition_dest_city_paris,
            SemanticLogic(self._ddd_manager).combine(self.positive_prop_set, self.individual_paris)
        )

    def test_combine_with_negated_proposition_in_set_returns_negated_proposition(self):
        self.assertEqual(
            self.proposition_not_dest_city_paris,
            SemanticLogic(self._ddd_manager).combine(self.positive_prop_set, self.proposition_not_dest_city_paris)
        )

    def test_combine_with_negated_individual_in_set_returns_negated_proposition(self):
        self.assertEqual(
            self.proposition_not_dest_city_paris,
            SemanticLogic(self._ddd_manager).combine(self.positive_prop_set, self.individual_not_paris)
        )
