import copy
import unittest

from unittest.mock import Mock

from tala.model.error import OntologyError
from tala.model.goal import PerformGoal
from tala.model import speaker
from tala.model.ontology import Ontology
from tala.model.polarity import Polarity
from tala.model.question import YesNoQuestion
from tala.model.proposition import PreconfirmationProposition, ResolvednessProposition, PrereportProposition, ServiceActionTerminatedProposition, RejectedPropositions, PropositionSet, ServiceResultProposition, Proposition, QuitProposition, MuteProposition, UnderstandingProposition, UnmuteProposition, PredicateProposition, GoalProposition, KnowledgePreconditionProposition
from tala.model.sort import StringSort, ImageSort
from tala.testing.lib_test_case import LibTestCase
from tala.model.image import Image
from tala.model.set import Set
from tala.utils.json_api import IncludedObject


class TestPropositionAsCondition(unittest.TestCase):
    def setUp(self):
        pass

    def test_proposition_truth_value_given_empty_facts(self):
        self.given_a_proposition(Proposition("some_type"))
        self.given_a_set_of_facts([])
        self.when_proposition_evaluated_with_facts()
        self.then_result_is(False)

    def given_a_proposition(self, proposition):
        self.proposition = proposition

    def given_a_set_of_facts(self, facts):
        self.facts = Set()
        for fact in facts:
            self.facts.add(fact)

    def when_proposition_evaluated_with_facts(self):
        self.result = self.proposition.is_true_given_proposition_set(self.facts)

    def then_result_is(self, truth_value):
        self.assertEqual(truth_value, self.result)

    def test_proposition_truth_value_false_given_non_empty_facts(self):
        self.given_a_proposition(Proposition("some_type"))
        self.given_a_set_of_facts([Proposition("other_type")])
        self.when_proposition_evaluated_with_facts()
        self.then_result_is(False)

    def test_proposition_truth_value_true_given_non_empty_facts_with_same_proposition(self):
        self.given_a_proposition(Proposition("some_type"))
        self.given_a_set_of_facts([Proposition("other_type"), Proposition("some_type")])
        self.when_proposition_evaluated_with_facts()
        self.then_result_is(True)


class PropositionTests(LibTestCase, unittest.TestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_quit_proposition_string(self):
        quit_prop = QuitProposition()
        self.assertEqual("QUIT", str(quit_prop))

    def test_quit_proposition_type(self):
        quit_prop = QuitProposition()
        self.assertEqual("QUIT", quit_prop.type_)

    def test_mute_proposition_string(self):
        mute_prop = MuteProposition()
        self.assertEqual("MUTE", str(mute_prop))

    def test_unmute_proposition_string(self):
        unmute_prop = UnmuteProposition()
        self.assertEqual("UNMUTE", str(unmute_prop))

    def test_quit_proposition_equality(self):
        quit_proposition_1 = QuitProposition()
        quit_proposition_2 = QuitProposition()
        self.assertEqual(quit_proposition_1, quit_proposition_2)

    def test_understanding_proposition_getters(self):
        proposition = self.proposition_dest_city_paris
        und = UnderstandingProposition(speaker.USR, proposition)
        self.assertEqual(speaker.USR, und.get_speaker())
        self.assertEqual(proposition, und.get_content())

    def test_understanding_proposition_to_string(self):
        proposition = self.proposition_dest_city_paris
        und = UnderstandingProposition(speaker.USR, proposition)
        self.assertEqual("und(USR, dest_city(paris))", str(und))


class ServiceResultPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.action = "mockup_action"
        self.arguments = ["mockup_arguments"]
        self.proposition = ServiceResultProposition(
            self.ontology_name, self.action, self.arguments, "mock_perform_result"
        )

    def test_is_service_result_proposition(self):
        self.assertTrue(self.proposition.is_service_result_proposition())

    def test_getters(self):
        self.assertEqual(self.action, self.proposition.get_service_action())
        self.assertEqual(self.arguments, self.proposition.get_arguments())
        self.assertEqual("mock_perform_result", self.proposition.get_result())

    def test_equality(self):
        identical_proposition = ServiceResultProposition(
            self.ontology_name, self.action, self.arguments, "mock_perform_result"
        )
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.proposition, identical_proposition)

    def test_inequality_due_to_result(self):
        non_identical_proposition = ServiceResultProposition(
            self.ontology_name, self.action, self.arguments, "other_perform_result"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.proposition, non_identical_proposition)

    def test_inequality_due_to_action(self):
        other_action = "other_service_action"
        non_identical_proposition = ServiceResultProposition(
            self.ontology_name, other_action, self.arguments, True, None
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.proposition, non_identical_proposition)

    def test_unicode(self):
        self.assertEqual(
            "ServiceResultProposition(mockup_action, ['mockup_arguments'], mock_perform_result)", str(self.proposition)
        )

    def test_hashable(self):
        assert {self.proposition}


class PropositionSetTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.emtpy_prop_set = PropositionSet([])
        self.positive_prop_set = PropositionSet([self.proposition_dest_city_london, self.proposition_dest_city_paris])
        self.negative_prop_set = PropositionSet([self.proposition_dest_city_london, self.proposition_dest_city_paris],
                                                polarity=Polarity.NEG)

    def test_equality(self):
        identical_prop_set = PropositionSet([self.proposition_dest_city_london, self.proposition_dest_city_paris])
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.positive_prop_set, identical_prop_set)

    def test_inequality_due_to_propositions(self):
        non_identical_prop_set = PropositionSet([self.proposition_dest_city_london])
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.positive_prop_set, non_identical_prop_set)

    def test_inequality_due_to_polarity(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.negative_prop_set, self.positive_prop_set)

    def test_inequality_due_to_element_order(self):
        non_identical_prop_set = PropositionSet([self.proposition_dest_city_paris, self.proposition_dest_city_london])
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.positive_prop_set, non_identical_prop_set)

    def test_is_positive(self):
        self.assertTrue(self.positive_prop_set.is_positive())
        self.assertFalse(self.negative_prop_set.is_positive())

    def test_get_polarity(self):
        self.assertEqual(Polarity.POS, self.positive_prop_set.get_polarity())
        self.assertEqual(Polarity.NEG, self.negative_prop_set.get_polarity())

    def test_positive_propositionset_unicode(self):
        self.assertEqual("set([dest_city(london), dest_city(paris)])", str(self.positive_prop_set))

    def test_negative_propositionset_unicode(self):
        self.assertEqual("~set([dest_city(london), dest_city(paris)])", str(self.negative_prop_set))

    def test_is_understanding_proposition_false(self):
        self.assertFalse(self.positive_prop_set.is_understanding_proposition())

    def test_is_proposition_set(self):
        self.assertTrue(self.positive_prop_set.is_proposition_set())
        self.assertFalse(self.buy_action.is_proposition_set())

    def test_get_predicate(self):
        self.assertEqual(self.predicate_dest_city, self.positive_prop_set.predicate)

    def test_repr(self):
        self.assertEqual(
            "PropositionSet([PredicateProposition("
            "Predicate('dest_city', CustomSort('city', True), None, False), "
            "Individual('london', CustomSort('city', True)), "
            "'POS', False), "
            "PredicateProposition("
            "Predicate('dest_city', CustomSort('city', True), None, False), "
            "Individual('paris', CustomSort('city', True)"
            "), 'POS', False)], 'POS')", repr(self.positive_prop_set)
        )

    def test_is_ontology_specific_with_some_ontology_specific_propositions(self):
        self.given_proposition_set_with([
            self._create_mocked_ontology_specific_proposition("an ontology"),
            self._create_mocked_proposition(),
        ])
        self.when_retrieving_is_ontology_specific()
        self.then_result_is(False)

    def _create_mocked_ontology_specific_proposition(self, ontology_name):
        mock = Mock(spec=PreconfirmationProposition)
        mock.is_ontology_specific.return_value = True
        mock.ontology_name = ontology_name
        return mock

    def _create_mocked_proposition(self):
        mock = Mock(spec=Proposition)
        mock.is_ontology_specific.return_value = False
        return mock

    def given_proposition_set_with(self, propositions):
        self._proposition_set = PropositionSet(propositions)

    def when_retrieving_is_ontology_specific(self):
        self._actual_result = self._proposition_set.is_ontology_specific()

    def test_is_ontology_specific_with_only_ontology_specific_propositions_of_different_ontologies(self):
        self.given_proposition_set_with([
            self._create_mocked_ontology_specific_proposition("an ontology"),
            self._create_mocked_ontology_specific_proposition("another ontology"),
        ])
        self.when_retrieving_is_ontology_specific()
        self.then_result_is(False)

    def test_is_ontology_specific_with_only_ontology_specific_propositions_of_same_ontologies(self):
        self.given_proposition_set_with([
            self._create_mocked_ontology_specific_proposition("an ontology"),
            self._create_mocked_ontology_specific_proposition("an ontology"),
        ])
        self.when_retrieving_is_ontology_specific()
        self.then_result_is(True)

    def test_is_ontology_specific_with_no_ontology_specific_propositions(self):
        self.given_proposition_set_with([
            self._create_mocked_proposition(),
            self._create_mocked_proposition(),
        ])
        self.when_retrieving_is_ontology_specific()
        self.then_result_is(False)

    def test_is_ontology_specific_without_propositions(self):
        self.given_proposition_set_with([])
        self.when_retrieving_is_ontology_specific()
        self.then_result_is(False)

    def test_proposition_set_as_json_api(self):
        self.given_proposition_set(self.positive_prop_set)
        self.when_proposition_set_as_json_api()
        self.then_json_api_is()

    def given_proposition_set(self, propositions):
        self._proposition_set = propositions

    def when_proposition_set_as_json_api(self):
        self._set_as_json_api = self._proposition_set.as_json_api_dict()

    def then_json_api_is(self):
        type_ = 'tala.model.proposition.PropositionSet'
        version = "2"
        attributes = {'polarity': 'POS', 'type_': 'PROPOSITION_SET'}
        relationships = {
            'propositions_data': {
                'data': [{
                    'id': 'mockup_ontology:dest_city:london:POS:False',
                    'type': 'tala.model.proposition.PredicateProposition'
                }, {
                    'id': 'mockup_ontology:dest_city:paris:POS:False',
                    'type': 'tala.model.proposition.PredicateProposition'
                }]
            }
        }
        included = [{
            'attributes': {
                'dynamic': True,
                'name': 'city',
                'ontology_name': 'mockup_ontology'
            },
            'id': 'mockup_ontology:city',
            'relationships': {},
            'type': 'tala.model.sort.CustomSort',
            'version:id': '2'
        }, {
            'attributes': {
                '_multiple_instances': False,
                'feature_of_name': None,
                'name': 'dest_city',
                'ontology_name': 'mockup_ontology'
            },
            'id': 'mockup_ontology:dest_city',
            'relationships': {
                'sort': {
                    'data': {
                        'id': 'mockup_ontology:city',
                        'type': 'tala.model.sort.CustomSort'
                    }
                }
            },
            'type': 'tala.model.predicate.Predicate',
            'version:id': '2'
        }, {
            'attributes': {
                'ontology_name': 'mockup_ontology',
                'value': 'london'
            },
            'id': 'mockup_ontology:london',
            'relationships': {
                'sort': {
                    'data': {
                        'id': 'mockup_ontology:city',
                        'type': 'tala.model.sort.CustomSort'
                    }
                }
            },
            'type': 'tala.model.individual.Individual',
            'version:id': '2'
        }, {
            'attributes': {
                'ontology_name': 'mockup_ontology',
                'value': 'paris'
            },
            'id': 'mockup_ontology:paris',
            'relationships': {
                'sort': {
                    'data': {
                        'id': 'mockup_ontology:city',
                        'type': 'tala.model.sort.CustomSort'
                    }
                }
            },
            'type': 'tala.model.individual.Individual',
            'version:id': '2'
        }, {
            'attributes': {
                '_predicted': False,
                'ontology_name': 'mockup_ontology',
                'polarity': 'POS'
            },
            'id': 'mockup_ontology:dest_city:london:POS:False',
            'relationships': {
                'individual': {
                    'data': {
                        'id': 'mockup_ontology:london',
                        'type': 'tala.model.individual.Individual'
                    }
                },
                'predicate': {
                    'data': {
                        'id': 'mockup_ontology:dest_city',
                        'type': 'tala.model.predicate.Predicate'
                    }
                }
            },
            'type': 'tala.model.proposition.PredicateProposition',
            'version:id': '2'
        }, {
            'attributes': {
                '_predicted': False,
                'ontology_name': 'mockup_ontology',
                'polarity': 'POS'
            },
            'id': 'mockup_ontology:dest_city:paris:POS:False',
            'relationships': {
                'individual': {
                    'data': {
                        'id': 'mockup_ontology:paris',
                        'type': 'tala.model.individual.Individual'
                    }
                },
                'predicate': {
                    'data': {
                        'id': 'mockup_ontology:dest_city',
                        'type': 'tala.model.predicate.Predicate'
                    }
                }
            },
            'type': 'tala.model.proposition.PredicateProposition',
            'version:id': '2'
        }]

        self.assertEqual(type_, self._set_as_json_api["data"]["type"])
        self.assertEqual(version, self._set_as_json_api["data"]["version:id"])
        self.assertEqual(attributes, self._set_as_json_api["data"]["attributes"])
        self.assertEqual(relationships, self._set_as_json_api["data"]["relationships"])
        self.assertEqual(included, self._set_as_json_api["included"])
        self.assertIn("id", self._set_as_json_api["data"])

    def test_recreated_proposition_set_from_json_api_is_equal(self):
        self.given_proposition_set(self.positive_prop_set)
        self.given_proposition_set_as_json_api()
        self.when_proposition_set_created_from_json_api()
        self.then_sets_are_equal(self._recreated_proposition_set, self._proposition_set)

    def given_proposition_set_as_json_api(self):
        self.when_proposition_set_as_json_api()

    def when_proposition_set_created_from_json_api(self):
        self._recreated_proposition_set = PropositionSet.create_from_json_api_data(
            self._set_as_json_api["data"], IncludedObject(self._set_as_json_api["included"])
        )

    def then_sets_are_equal(self, set_1, set_2):
        self.assertEqual(set_1, set_2)

    def test_recreated_empty_proposition_set_from_json_api_is_equal(self):
        self.given_proposition_set(self.emtpy_prop_set)
        self.given_proposition_set_as_json_api()
        self.when_proposition_set_created_from_json_api()
        self.then_sets_are_equal(self._recreated_proposition_set, self._proposition_set)


class ServiceActionTerminatedTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.service_action = "MakeReservation"
        self.done = ServiceActionTerminatedProposition(self.ontology_name, self.service_action)

    def test_done_proposition_is_done_prop(self):
        self.assertTrue(self.done.is_service_action_terminated_proposition())

    def test_done_proposition_contains_action(self):
        self.assertEqual(self.service_action, self.done.get_service_action())

    def test_done_proposition_equality(self):
        identical_done_prop = ServiceActionTerminatedProposition(self.ontology_name, self.service_action)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_done_prop, self.done)

    def test_done_proposition_inequality(self):
        inequal_done_prop = ServiceActionTerminatedProposition(self.ontology_name, "hskjhs")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(inequal_done_prop, self.done)

    def test_done_proposition_unicode(self):
        expected_str = "service_action_terminated(MakeReservation)"
        self.assertEqual(expected_str, str(self.done))

    def test_hashing(self):
        {self.done}

    def test_repr(self):
        self.assertEqual(
            "ServiceActionTerminatedProposition('mockup_ontology', 'MakeReservation', 'POS')", repr(self.done)
        )


class RejectionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.rejected_combination = PropositionSet([self.proposition_dest_city_paris])
        self.rejected = RejectedPropositions(self.rejected_combination)

    def test_rejected_proposition_is_rejected_prop(self):
        self.assertTrue(self.rejected.is_rejected_proposition())

    def test_creation_with_reason(self):
        reason = "ssdlfkjslkf"
        rejected = RejectedPropositions(self.rejected_combination, reason=reason)
        self.assertEqual(self.rejected_combination, rejected.get_rejected_combination())
        self.assertEqual(reason, rejected.get_reason())

    def test_rejected_with_reason_unicode(self):
        reason = "ssdlfkjslkf"
        rejected = RejectedPropositions(self.rejected_combination, reason=reason)
        string = "rejected(%s, %s)" % (self.rejected_combination, reason)
        self.assertEqual(string, str(rejected))

    def test_get_rejected_combination(self):
        self.assertEqual(self.rejected_combination, self.rejected.get_rejected_combination())

    def test_rejected_proposition_unicode(self):
        rejected_as_string = "rejected(%s)" % self.rejected_combination
        self.assertEqual(rejected_as_string, str(self.rejected))

    def test_equality(self):
        identical_rejected_prop = RejectedPropositions(PropositionSet([self.proposition_dest_city_paris]))
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_rejected_prop, self.rejected)

    def test_inequality_due_to_rejected_combination(self):
        other_combination = "hskjhs"
        inequal_rejected_prop = RejectedPropositions(PropositionSet(other_combination))
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(inequal_rejected_prop, self.rejected)

    def test_inequality_due_to_reason(self):
        inequal_rejected_prop = RejectedPropositions(self.rejected_combination, reason="some_reason")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(inequal_rejected_prop, self.rejected)

    def test_hashable(self):
        prop_set = {self.rejected}
        self.assertTrue(self.rejected in prop_set)


class PrereportPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.service_action = "MakeReservation"
        self.empty_arguments = []
        self.prereport = self._create_with_empty_param_list()

    def _create_with_empty_param_list(self):
        confirmation_proposition = PrereportProposition(self.ontology_name, self.service_action, self.empty_arguments)
        return confirmation_proposition

    def test_type(self):
        self.assertTrue(self.prereport.is_prereport_proposition())

    def test_get_service_action(self):
        self.assertEqual(self.service_action, self.prereport.get_service_action())

    def test_get_arguments(self):
        self.assertEqual(self.empty_arguments, self.prereport.get_arguments())

    def test_proposition_unicode(self):
        self.assertEqual("prereported(MakeReservation, [])", str(self.prereport))

    def test_equality(self):
        identical_prereport = PrereportProposition(self.ontology_name, self.service_action, self.empty_arguments)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.prereport, identical_prereport)

    def test_inequality_due_to_action(self):
        other_action = "CacelTransaction"
        non_identical_proposition = PrereportProposition(self.ontology_name, other_action, self.empty_arguments)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.prereport, non_identical_proposition)


class PreconfirmationTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.service_action = "MakeReservation"
        self.arguments = [self.proposition_dest_city_paris, self.proposition_dept_city_london]
        self.preconfirmation = PreconfirmationProposition(self.ontology_name, self.service_action, self.arguments)

    def test_type(self):
        self.assertTrue(self.preconfirmation.is_preconfirmation_proposition())

    def test_get_service_action(self):
        self.assertEqual(self.service_action, self.preconfirmation.get_service_action())

    def test_get_arguments(self):
        self.assertEqual(self.arguments, self.preconfirmation.get_arguments())

    def test_positive_proposition_unicode(self):
        self.assertEqual(
            "preconfirmed(MakeReservation, [dest_city(paris), dept_city(london)])", str(self.preconfirmation)
        )

    def test_negative_proposition_unicode(self):
        negative_preconfirmation = self.preconfirmation.negate()
        self.assertEqual(
            "~preconfirmed(MakeReservation, [dest_city(paris), dept_city(london)])", str(negative_preconfirmation)
        )

    def test_equality(self):
        identical_preconfirmation = PreconfirmationProposition(self.ontology_name, self.service_action, self.arguments)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.preconfirmation, identical_preconfirmation)

    def test_inequality_due_to_other_class(self):
        object_of_other_class = ServiceActionTerminatedProposition(self.ontology_name, self.service_action)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.preconfirmation, object_of_other_class)

    def test_inequality_due_to_action(self):
        other_action = "CancelTransaction"
        non_identical_proposition = PreconfirmationProposition(self.ontology_name, other_action, self.arguments)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.preconfirmation, non_identical_proposition)

    def test_inequality_due_to_polarity(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            self.preconfirmation, self.preconfirmation.negate()
        )

    def test_inequality_due_to_arguments_in_other_order(self):
        other_arguments = [self.proposition_dept_city_london, self.proposition_dest_city_paris]
        other_preconfirmation = PreconfirmationProposition(self.ontology_name, self.service_action, other_arguments)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.preconfirmation, other_preconfirmation)

    def test_default_polarity_is_positive(self):
        self.assertTrue(self.preconfirmation.is_positive())

    def test_is_positive_false_for_negative_proposition(self):
        self.assertFalse(self.preconfirmation.negate().is_positive())

    def test_hashable(self):
        {self.preconfirmation}


class ResolvednessPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.issue = self.price_question
        self.proposition = ResolvednessProposition(self.issue)

    def test_get_issue(self):
        self.assertEqual(self.issue, self.proposition.get_issue())

    def test_unicode(self):
        self.assertEqual("resolved(?X.price(X))", str(self.proposition))

    def test_equality(self):
        identical_proposition = ResolvednessProposition(self.issue)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.proposition, identical_proposition)

    def test_inequality_due_to_issue(self):
        other_issue = self.dest_city_question
        non_identical_proposition = ResolvednessProposition(other_issue)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.proposition, non_identical_proposition)

    def test_hashable(self):
        {self.proposition}


class QuestionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_preconfirmation_question_true_for_yes_no_questions_about_confirmation(self):
        preconfirmation_question = YesNoQuestion(
            PreconfirmationProposition(self.ontology_name, "mockup_service_action", [])
        )
        self.assertTrue(preconfirmation_question.is_preconfirmation_question())

    def test_is_preconfirmation_question_false_for_yes_no_questions_about_non_preconfirmations(self):
        non_preconfirmation_question = YesNoQuestion(self.proposition_dest_city_paris)
        self.assertFalse(non_preconfirmation_question.is_preconfirmation_question())

    def test_is_preconfirmation_question_false_for_non_yes_no_questions(self):
        self.assertFalse(self.dest_city_question.is_preconfirmation_question())


class PredicatePropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_getters(self):
        self.assertEqual(self.predicate_dest_city, self.proposition_dest_city_paris.predicate)
        self.assertEqual(self.individual_paris, self.proposition_dest_city_paris.individual)

    def test_positive_unicode(self):
        self.assertEqual("dest_city(paris)", str(self.proposition_dest_city_paris))

    def test_negative_unicode(self):
        self.assertEqual("~dest_city(paris)", str(self.proposition_not_dest_city_paris))

    def test_equality(self):
        proposition = self.proposition_dest_city_paris
        identical_proposition = copy.copy(self.proposition_dest_city_paris)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(proposition, identical_proposition)

    def test_inequality_due_to_individual(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            self.proposition_dest_city_paris, self.proposition_dest_city_london
        )

    def test_inequality_due_to_polarity(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            self.proposition_dest_city_paris, self.proposition_not_dest_city_paris
        )

    def test_default_polarity_is_positive(self):
        proposition = PredicateProposition(self.predicate_dest_city, self.individual_paris)
        self.assertTrue(proposition.is_positive())

    def test_default_polarity_is_positive_with_help_method(self):
        proposition = PredicateProposition(self.predicate_dest_city, self.individual_paris)
        self.assertTrue(proposition.is_positive())

    def test_negative_proposition(self):
        proposition = PredicateProposition(self.predicate_dest_city, self.individual_paris, Polarity.NEG)
        self.assertFalse(proposition.is_positive())

    def test_create_illegal_proposition(self):
        with self.assertRaises(OntologyError):
            predicate = self.ontology.get_predicate("destination")
            individual = self.ontology.create_individual("car")
            PredicateProposition(predicate, individual)

    def test_predicate(self):
        self.assertEqual("dest_city", self.proposition_dest_city_paris.predicate.get_name())

    def test_value(self):
        self.assertEqual("paris", self.proposition_dest_city_paris.individual.value)

    def test_hashable(self):
        {self.proposition_dest_city_paris}

    def test_nullary(self):
        proposition = PredicateProposition(self.predicate_need_visa)
        self.assertEqual(None, proposition.individual)
        self.assertEqual("need_visa", str(proposition))

    def test_is_predicate_proposition_true(self):
        self.assertTrue(self.proposition_dest_city_paris.is_predicate_proposition())

    def test_is_predicate_proposition_false(self):
        self.assertFalse(self.individual_paris.is_predicate_proposition())

    def test_predicate_proposition_with_sortal_mismatch_yields_exception(self):
        individual_of_wrong_type = self.ontology.create_individual("paris")
        with self.assertRaises(OntologyError):
            PredicateProposition(self.predicate_price, individual_of_wrong_type)


class GoalPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.proposition = GoalProposition(PerformGoal(self.buy_action))
        self.negative_proposition = GoalProposition(PerformGoal(self.buy_action), polarity=Polarity.NEG)

    def test_equality(self):
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(
            GoalProposition(PerformGoal(self.buy_action)), GoalProposition(PerformGoal(self.buy_action))
        )

    def test_inequality_due_to_goal(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            GoalProposition(PerformGoal(self.buy_action)), GoalProposition(PerformGoal(self.top_action))
        )

    def test_inequality_due_to_polarity(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            GoalProposition(PerformGoal(self.buy_action), polarity=Polarity.POS),
            GoalProposition(PerformGoal(self.buy_action), polarity=Polarity.NEG)
        )

    def test_hashable(self):
        {self.proposition}

    def test_positive_proposition_unicode(self):
        self.assertEqual("goal(perform(buy))", str(self.proposition))

    def test_negative_proposition_unicode(self):
        self.assertEqual("~goal(perform(buy))", str(self.negative_proposition))


class StringPropositionTests(LibTestCase):
    def setUp(self):
        self._create_ontology()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("number_to_call", StringSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_str_with_string_argument(self):
        predicate_number_to_call = self.ontology.get_predicate("number_to_call")
        individual = self.ontology.create_individual('"123"')
        string_proposition = PredicateProposition(predicate_number_to_call, individual)
        self.assertEqual('number_to_call("123")', str(string_proposition))


class ImagePropositionTests(LibTestCase):
    def setUp(self):
        self._create_ontology()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("map_to_show", ImageSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_str_with_string_argument(self):
        map_to_show = self.ontology.get_predicate("map_to_show")
        individual = self.ontology.create_individual(Image("http://mymap.com/map.png"))
        image_proposition = PredicateProposition(map_to_show, individual)
        self.assertEqual('map_to_show(image("http://mymap.com/map.png"))', str(image_proposition))


class KnowledgePreconditionPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_equality(self):
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(
            KnowledgePreconditionProposition("mock_question", Polarity.POS),
            KnowledgePreconditionProposition("mock_question", Polarity.POS)
        )

    def test_inequality_due_to_question(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            KnowledgePreconditionProposition("mock_question_1", Polarity.POS),
            KnowledgePreconditionProposition("mock_question_2", Polarity.POS)
        )

    def test_inequality_due_to_polarity(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            KnowledgePreconditionProposition("mock_question", Polarity.POS),
            KnowledgePreconditionProposition("mock_question", Polarity.NEG)
        )
