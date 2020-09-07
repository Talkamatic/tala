import copy

from tala.model.lambda_abstraction import LambdaAbstractedGoalProposition, LambdaAbstractedPredicateProposition
from tala.testing.lib_test_case import LibTestCase


class LambdaAbstractedGoalPropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.lambda_prop = LambdaAbstractedGoalProposition()

    def test_unicode(self):
        self.assertEqual("X.goal(X)", str(self.lambda_prop))

    def test_equality(self):
        lambda_prop1 = LambdaAbstractedGoalProposition()
        lambda_prop2 = LambdaAbstractedGoalProposition()
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(lambda_prop1, lambda_prop2)

    def test_inequality(self):
        lambda_prop = LambdaAbstractedGoalProposition()
        non_identical_lambda_prop = self.lambda_abstracted_price_prop
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lambda_prop, non_identical_lambda_prop)

    def test_hashing(self):
        {self.lambda_prop}

    def test_is_lambda_abstracted_goal_proposition(self):
        self.assertTrue(self.lambda_abstracted_goal_prop.is_lambda_abstracted_goal_proposition())
        self.assertFalse(self.lambda_abstracted_dest_city_prop.is_lambda_abstracted_goal_proposition())


class LambdaAbstractedPredicatePropositionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.lambda_prop = LambdaAbstractedPredicateProposition(self.predicate_dest_city, self.ontology.get_name())

    def test_unicode(self):
        self.assertEqual("X.dest_city(X)", str(self.lambda_prop))

    def test_equality(self):
        lambda_prop = self.lambda_abstracted_dest_city_prop
        identical_lambda_prop = copy.copy(self.lambda_abstracted_dest_city_prop)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(lambda_prop, identical_lambda_prop)

    def test_inequality(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            self.lambda_abstracted_dest_city_prop, self.lambda_abstracted_price_prop
        )

    def test_not_equals_proposition(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(
            self.proposition_dest_city_paris, self.lambda_prop
        )

    def test_hashing(self):
        {self.lambda_prop}

    def test_is_lambda_abstracted_predicate_proposition(self):
        self.assertTrue(self.lambda_abstracted_dest_city_prop.is_lambda_abstracted_predicate_proposition())
        self.assertFalse(self.lambda_abstracted_goal_prop.is_lambda_abstracted_predicate_proposition())
