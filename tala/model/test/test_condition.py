import unittest

from unittest.mock import Mock

from tala.model.proposition import PredicateProposition, Proposition, ResolvednessProposition
from tala.model.predicate import Predicate
from tala.model import condition
from tala.model.condition import (
    Condition,
    HasPrivateValue,
    HasSharedValue,
    HasValue,
    AndCondition,
    InBeliefsOrCommitments,
    InPrivateBeliefs,
    InSharedCommitments,
    NotCondition,
    OrCondition,
)
from tala.model.set import Set


class TIS:
    def __init__(self):
        self.shared = Shared()
        self.private = Private()


class Shared:
    def __init__(self):
        self.com = {}


class Private:
    def __init__(self):
        self.bel = {}


class ConditionTestCase(unittest.TestCase):
    def setUp(self):
        self.predicate_a = Mock(spec=Predicate)
        self.predicate_b = Mock(spec=Predicate)
        self.proposition_over_predicate_a = Mock(spec=PredicateProposition)
        self.proposition_over_predicate_a.predicate = self.predicate_a
        self.proposition_b = Mock(spec=PredicateProposition)
        self.other_proposition = Mock(spec=Proposition)
        self.resolvedness_proposition = Mock(spec=ResolvednessProposition)

    def given_condition(self, condition):
        self._condition = condition

    def given_set_of_propositions(self, propositions):
        self._propositions = Set()
        for proposition in propositions:
            self._propositions.add(proposition)

    def when_is_true_given_proposition_set_is_called(self):
        self._result = self._condition.is_true_given_proposition_set(self._propositions)

    def then_result_is(self, value):
        assert self._result is value

    def when_tested_for_equality(self, first_object, second_object):
        self._result = first_object == second_object


class TestConditions(ConditionTestCase):
    def test_get_truth_value_given_empty_facts(self):
        self.given_condition(Condition("some_type"))
        self.given_set_of_propositions([])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_get_truth_value_given_non_empty_facts(self):
        self.given_condition(Condition("some_type"))
        self.given_set_of_propositions([self.proposition_over_predicate_a])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_equality(self):
        self.when_tested_for_equality(Condition("some_type"), Condition("some_type"))
        self.then_result_is(True)

    def test_inequality_due_to_type(self):
        self.when_tested_for_equality(Condition("some_type"), Condition("other_type"))
        self.then_result_is(False)

    def test_inequality_due_to_interface(self):
        self.when_tested_for_equality(Condition("some_type"), "random object")
        self.then_result_is(False)

    def test_inequality_due_to_none(self):
        self.when_tested_for_equality(Condition("some_type"), None)
        self.then_result_is(False)


class TestHasValueCondition(ConditionTestCase):
    def test_creation_with_standard_predicate(self):
        HasValue(self.predicate_a)

    def test_get_predicate_for_standard_predicate(self):
        self._given_hasvalue_condition_created_for_predicate(self.predicate_a)
        self._when_predicate_is_collected()
        self._then_predicate_is(self.predicate_a)

    def _given_hasvalue_condition_created_for_predicate(self, predicate):
        self._has_value_condition = HasValue(predicate)

    def _when_predicate_is_collected(self):
        self._result = self._has_value_condition.predicate

    def _then_predicate_is(self, predicate):
        self.assertEqual(predicate, self._result)

    def test_string_for_standard_predicate(self):
        self._when_string_is_generated_for_has_value_with_predicate(self.predicate_a)
        self._then_string_is(f"HasValue({self.predicate_a})")

    def _when_string_is_generated_for_has_value_with_predicate(self, predicate):
        self._string = str(HasValue(predicate))

    def _then_string_is(self, string):
        self.assertEqual(string, self._string)

    def test_type(self):
        self._given_hasvalue_condition_created_for_predicate(self.predicate_a)
        self._when_type_is_collected()
        self._then_type_is(condition.HAS_VALUE)

    def _when_type_is_collected(self):
        self._type = self._has_value_condition.condition_type

    def _then_type_is(self, type):
        self.assertEqual(type, self._type)

    def test_equality(self):
        self.when_tested_for_equality(HasValue(self.predicate_a), HasValue(self.predicate_a))
        self.then_result_is(True)

    def test_inequality_due_to_predicate(self):
        self.when_tested_for_equality(HasValue(self.predicate_a), HasValue(self.predicate_b))
        self.then_result_is(False)

    def test_is_true_given_containing_proposition_with_same_predicate(self):
        self.given_condition(HasValue(self.predicate_a))
        self.given_set_of_propositions([self.proposition_over_predicate_a])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(True)

    def test_is_true_given_containing_proposition_with_different_predicate(self):
        self.given_condition(HasValue(self.predicate_a))
        self.given_set_of_propositions([self.proposition_b])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_get_truth_value_tolerates_any_proposition(self):
        self.given_condition(HasValue(self.proposition_over_predicate_a))
        self.given_set_of_propositions([self.other_proposition])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_get_truth_value_given_several_propositions(self):
        self.given_condition(HasValue(self.predicate_a))
        self.given_set_of_propositions([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(True)


class TestInBeliefsOrCommitmentsConditions(ConditionTestCase):
    def test_creation_with_standard_proposition(self):
        InBeliefsOrCommitments(self.proposition_over_predicate_a)

    def test_get_proposition_for_standard_proposition(self):
        self._given_in_beliefs_or_commitments_created_for_proposition(self.proposition_over_predicate_a)
        self._when_proposition_is_collected()
        self._then_proposition_is(self.proposition_over_predicate_a)

    def _given_in_beliefs_or_commitments_created_for_proposition(self, proposition):
        self._condition = InBeliefsOrCommitments(proposition)

    def _when_proposition_is_collected(self):
        self._result = self._condition.proposition

    def _then_proposition_is(self, proposition):
        self.assertEqual(proposition, self._result)

    def test_string_for_standard_predicate(self):
        self._when_string_is_generated_for_condition_with_proposition(self.proposition_over_predicate_a)
        self._then_string_is(f"InBeliefsOrCommitments({self.proposition_over_predicate_a})")

    def _when_string_is_generated_for_condition_with_proposition(self, proposition):
        self._string = str(InBeliefsOrCommitments(proposition))

    def _then_string_is(self, string):
        self.assertEqual(string, self._string)

    def test_type(self):
        self._given_in_beliefs_or_commitments_created_for_proposition(self.proposition_over_predicate_a)
        self._when_type_is_collected()
        self._then_type_is(condition.IN_BELIEFS_OR_COMMITMENTS)

    def _when_type_is_collected(self):
        self._type = self._condition.condition_type

    def _then_type_is(self, type):
        self.assertEqual(type, self._type)

    def test_equality(self):
        self.when_tested_for_equality(
            InBeliefsOrCommitments(self.proposition_over_predicate_a),
            InBeliefsOrCommitments(self.proposition_over_predicate_a),
        )
        self.then_result_is(True)

    def test_inequality_due_to_proposition(self):
        self.when_tested_for_equality(
            InBeliefsOrCommitments(self.proposition_over_predicate_a),
            InBeliefsOrCommitments(self.proposition_b),
        )
        self.then_result_is(False)

    def test_inequality_due_to_type(self):
        self.when_tested_for_equality(HasValue(self.predicate_a), InBeliefsOrCommitments(self.proposition_over_predicate_a))
        self.then_result_is(False)

    def test_inequality_due_to_interface(self):
        self.when_tested_for_equality(InBeliefsOrCommitments(self.proposition_over_predicate_a), "random_object")
        self.then_result_is(False)

    def test_is_true_given_containing_same_proposition(self):
        self.given_condition(InBeliefsOrCommitments(self.proposition_over_predicate_a))
        self.given_tis_with_commitments([self.proposition_over_predicate_a])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(True)

    def test_is_true_given_containing_different_proposition(self):
        self.given_condition(InBeliefsOrCommitments(self.proposition_over_predicate_a))
        self.given_tis_with_commitments([self.other_proposition])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(False)

    def test_is_true_given_consisting_of_several_propositions(self):
        self.given_condition(InBeliefsOrCommitments(self.proposition_over_predicate_a))
        self.given_tis_with_beliefs([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(True)

    def when_is_true_given_tis_is_called(self):
        self._result = self._condition.is_true_given_tis(self.tis)

    def given_tis_with_commitments(self, commitments):
        self.tis = TIS()
        self.tis.shared.com = commitments

    def given_tis_with_beliefs(self, beliefs):
        self.tis = TIS()
        self.tis.private.bel = beliefs


class TestHasSharedValueCondition(ConditionTestCase):
    def test_creation_with_standard_predicate(self):
        HasSharedValue(self.predicate_a)

    def test_string_for_standard_predicate(self):
        self._when_string_is_generated_for_has_value_with_predicate(self.predicate_a)
        self._then_string_is(f"HasSharedValue({self.predicate_a})")

    def _when_string_is_generated_for_has_value_with_predicate(self, predicate):
        self._string = str(HasSharedValue(predicate))

    def _then_string_is(self, string):
        self.assertEqual(string, self._string)

    def test_type(self):
        self._given_has_shared_value_condition_created_for_predicate(self.predicate_a)
        self._when_type_is_collected()
        self._then_type_is(condition.HAS_SHARED_VALUE)

    def _given_has_shared_value_condition_created_for_predicate(self, predicate):
        self._has_value_condition = HasSharedValue(predicate)

    def _when_type_is_collected(self):
        self._type = self._has_value_condition.condition_type

    def _then_type_is(self, type):
        self.assertEqual(type, self._type)

    def test_is_true_given_containing_proposition_with_same_predicate(self):
        self.given_condition(HasSharedValue(self.predicate_a))
        self.given_tis_with_commitments([self.proposition_over_predicate_a])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(True)

    def given_tis_with_commitments(self, commitments):
        self.tis = TIS()
        self.tis.shared.com = commitments

    def when_is_true_given_proposition_set_is_called(self):
        self._result = self._condition.is_true_given_tis(self.tis)

    def test_equality(self):
        self.when_tested_for_equality(HasSharedValue(self.predicate_a), HasSharedValue(self.predicate_a))
        self.then_result_is(True)

    def test_inequality_due_to_predicate(self):
        self.when_tested_for_equality(HasSharedValue(self.predicate_a), HasSharedValue(self.predicate_b))
        self.then_result_is(False)

    def test_is_true_given_containing_proposition_with_different_predicate(self):
        self.given_condition(HasSharedValue(self.predicate_a))
        self.given_tis_with_commitments([self.proposition_b])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_get_truth_value_tolerates_any_proposition(self):
        self.given_condition(HasSharedValue(self.proposition_over_predicate_a))
        self.given_tis_with_commitments([self.other_proposition])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def test_get_truth_value_given_several_propositions_in_com(self):
        self.given_condition(HasSharedValue(self.predicate_a))
        self.given_tis_with_commitments([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(True)

    def test_get_truth_value_given_several_propositions_in_bel(self):
        self.given_condition(HasSharedValue(self.predicate_a))
        self.given_tis_with_beliefs([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_proposition_set_is_called()
        self.then_result_is(False)

    def given_tis_with_beliefs(self, beliefs):
        self.tis = TIS()
        self.tis.private.bel = beliefs


class TestInSharedCommitmentsCondition(ConditionTestCase):
    def test_is_true_given_shared_commitment(self):
        self.given_condition(InSharedCommitments(self.proposition_over_predicate_a))
        self.given_tis_with_commitments([self.proposition_over_predicate_a])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(True)

    def test_is_false_given_private_belief(self):
        self.given_condition(InSharedCommitments(self.proposition_over_predicate_a))
        self.given_tis_with_beliefs([self.proposition_over_predicate_a])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(False)

    def when_is_true_given_tis_is_called(self):
        self._result = self._condition.is_true_given_tis(self.tis)

    def given_tis_with_commitments(self, commitments):
        self.tis = TIS()
        self.tis.shared.com = commitments

    def given_tis_with_beliefs(self, beliefs):
        self.tis = TIS()
        self.tis.private.bel = beliefs


class TestInPrivateBeliefsCondition(ConditionTestCase):
    def test_is_true_given_private_belief(self):
        self.given_condition(InPrivateBeliefs(self.proposition_over_predicate_a))
        self.given_tis_with_beliefs([self.proposition_over_predicate_a])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(True)

    def test_is_false_given_shared_commitment(self):
        self.given_condition(InPrivateBeliefs(self.proposition_over_predicate_a))
        self.given_tis_with_commitments([self.proposition_over_predicate_a])
        self.when_is_true_given_tis_is_called()
        self.then_result_is(False)

    def when_is_true_given_tis_is_called(self):
        self._result = self._condition.is_true_given_tis(self.tis)

    def given_tis_with_commitments(self, commitments):
        self.tis = TIS()
        self.tis.shared.com = commitments

    def given_tis_with_beliefs(self, beliefs):
        self.tis = TIS()
        self.tis.private.bel = beliefs


class TestBooleanConditions(ConditionTestCase):
    def test_and_condition_true_when_all_true(self):
        self._given_true_and_false_conditions()
        condition = AndCondition([self._true_condition, self._true_condition])
        self._when_condition_tested(condition)
        self._then_condition_result_is(True)

    def test_and_condition_false_when_any_false(self):
        self._given_true_and_false_conditions()
        condition = AndCondition([self._true_condition, self._false_condition])
        self._when_condition_tested(condition)
        self._then_condition_result_is(False)

    def test_or_condition_true_when_any_true(self):
        self._given_true_and_false_conditions()
        condition = OrCondition([self._false_condition, self._true_condition])
        self._when_condition_tested(condition)
        self._then_condition_result_is(True)

    def test_or_condition_false_when_all_false(self):
        self._given_true_and_false_conditions()
        condition = OrCondition([self._false_condition, self._false_condition])
        self._when_condition_tested(condition)
        self._then_condition_result_is(False)

    def test_not_condition_inverts_value(self):
        self._given_true_and_false_conditions()
        condition = NotCondition(self._false_condition)
        self._when_condition_tested(condition)
        self._then_condition_result_is(True)

    def _given_true_and_false_conditions(self):
        predicate = self.predicate_a
        true_proposition = self.proposition_over_predicate_a
        self.tis = TIS()
        self.tis.shared.com = [true_proposition]
        self.tis.private.bel = []
        self._true_condition = HasSharedValue(predicate)
        self._false_condition = HasPrivateValue(predicate)

    def _when_condition_tested(self, condition):
        self._result = condition.is_true_given_tis(self.tis)

    def _then_condition_result_is(self, value):
        assert self._result is value
