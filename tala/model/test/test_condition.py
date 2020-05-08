import unittest

from mock import Mock

from tala.model.proposition import PredicateProposition, Proposition, ResolvednessProposition
from tala.model.predicate import Predicate
from tala.model.condition import Condition, HasValue, IsSharedFact
from tala.model.set import Set


class ConditionTestCase(unittest.TestCase):
    def setUp(self):
        self.predicate_a = Mock(spec=Predicate)
        self.predicate_b = Mock(spec=Predicate)
        self.proposition_over_predicate_a = Mock(spec=PredicateProposition)
        self.proposition_over_predicate_a.get_predicate.return_value = self.predicate_a
        self.proposition_b = Mock(spec=PredicateProposition)
        self.other_proposition = Mock(spec=Proposition)
        self.resolvedness_proposition = Mock(spec=ResolvednessProposition)

    def given_condition(self, condition):
        self._condition = condition

    def given_set_of_propositions(self, propositions):
        self._propositions = Set()
        for proposition in propositions:
            self._propositions.add(proposition)

    def when_is_true_given_is_called(self):
        self._result = self._condition.is_true_given(self._propositions)

    def then_result_is(self, value):
        assert self._result is value

    def when_tested_for_equality(self, first_object, second_object):
        self._result = first_object == second_object


class TestConditions(ConditionTestCase):
    def test_get_truth_value_given_empty_facts(self):
        self.given_condition(Condition("some_type"))
        self.given_set_of_propositions([])
        self.when_is_true_given_is_called()
        self.then_result_is(False)

    def test_get_truth_value_given_non_empty_facts(self):
        self.given_condition(Condition("some_type"))
        self.given_set_of_propositions([self.proposition_over_predicate_a])
        self.when_is_true_given_is_called()
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
        self._then_type_is(Condition.HAS_VALUE)

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
        self.when_is_true_given_is_called()
        self.then_result_is(True)

    def test_is_true_given_containing_proposition_with_different_predicate(self):
        self.given_condition(HasValue(self.predicate_a))
        self.given_set_of_propositions([self.proposition_b])
        self.when_is_true_given_is_called()
        self.then_result_is(False)

    def test_get_truth_value_tolerates_any_proposition(self):
        self.given_condition(HasValue(self.proposition_over_predicate_a))
        self.given_set_of_propositions([self.other_proposition])
        self.when_is_true_given_is_called()
        self.then_result_is(False)

    def test_get_truth_value_given_several_propositions(self):
        self.given_condition(HasValue(self.predicate_a))
        self.given_set_of_propositions([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_is_called()
        self.then_result_is(True)


class TestIsSharedFactConditions(ConditionTestCase):
    def test_creation_with_standard_proposition(self):
        IsSharedFact(self.proposition_over_predicate_a)

    def test_get_proposition_for_standard_proposition(self):
        self._given_is_shared_fact_created_for_proposition(self.proposition_over_predicate_a)
        self._when_proposition_is_collected()
        self._then_proposition_is(self.proposition_over_predicate_a)

    def _given_is_shared_fact_created_for_proposition(self, proposition):
        self._condition = IsSharedFact(proposition)

    def _when_proposition_is_collected(self):
        self._result = self._condition.proposition

    def _then_proposition_is(self, proposition):
        self.assertEqual(proposition, self._result)

    def test_string_for_standard_predicate(self):
        self._when_string_is_generated_for_condition_with_proposition(self.proposition_over_predicate_a)
        self._then_string_is(f"IsSharedFact({self.proposition_over_predicate_a})")

    def _when_string_is_generated_for_condition_with_proposition(self, proposition):
        self._string = str(IsSharedFact(proposition))

    def _then_string_is(self, string):
        self.assertEqual(string, self._string)

    def test_type(self):
        self._given_is_shared_fact_condition_created_for_proposition(self.proposition_over_predicate_a)
        self._when_type_is_collected()
        self._then_type_is(Condition.IS_SHARED_FACT)

    def _given_is_shared_fact_condition_created_for_proposition(self, proposition):
        self._is_shared_fact_condition = IsSharedFact(proposition)

    def _when_type_is_collected(self):
        self._type = self._is_shared_fact_condition.condition_type

    def _then_type_is(self, type):
        self.assertEqual(type, self._type)

    def test_equality(self):
        self.when_tested_for_equality(
            IsSharedFact(self.proposition_over_predicate_a), IsSharedFact(self.proposition_over_predicate_a)
        )
        self.then_result_is(True)

    def test_inequality_due_to_proposition(self):
        self.when_tested_for_equality(
            IsSharedFact(self.proposition_over_predicate_a),
            IsSharedFact(self.proposition_b))
        self.then_result_is(False)

    def test_inequality_due_to_type(self):
        self.when_tested_for_equality(
            HasValue(self.predicate_a), IsSharedFact(self.proposition_over_predicate_a))
        self.then_result_is(False)

    def test_inequality_due_to_interface(self):
        self.when_tested_for_equality(IsSharedFact(self.proposition_over_predicate_a), "random_object")
        self.then_result_is(False)

    def test_is_true_given_containing_same_proposition(self):
        self.given_condition(IsSharedFact(self.proposition_over_predicate_a))
        self.given_set_of_propositions([self.proposition_over_predicate_a])
        self.when_is_true_given_is_called()
        self.then_result_is(True)

    def test_is_true_given_containing_different_proposition(self):
        self.given_condition(IsSharedFact(self.proposition_over_predicate_a))
        self.given_set_of_propositions([self.other_proposition])
        self.when_is_true_given_is_called()
        self.then_result_is(False)

    def test_is_true_given_consisting_of_several_propositions(self):
        self.given_condition(IsSharedFact(self.proposition_over_predicate_a))
        self.given_set_of_propositions([self.proposition_over_predicate_a, self.proposition_b])
        self.when_is_true_given_is_called()
        self.then_result_is(True)
