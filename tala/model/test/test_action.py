import copy

from tala.model.action import Action
from tala.testing.lib_test_case import LibTestCase


class ActionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_create(self):
        self.assertTrue(self.buy_action.is_action())
        self.assertEqual("buy", self.buy_action.value)

    def test_unicode(self):
        self.assertEqual("buy", str(self.buy_action))

    def test_equality(self):
        action = self.buy_action
        identical_action = copy.copy(self.buy_action)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(action, identical_action)

    def test_inequal_when_only_ontology_name_differs(self):
        action_name = "action_name"
        action = Action(action_name, "an_ontology")
        other = Action(action_name, "other_ontology")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(action, other)

    def test_inequality(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.buy_action, self.top_action)

    def test_is_action(self):
        action = self.buy_action
        non_action = self.proposition_dest_city_paris
        self.assertTrue(action.is_action())
        self.assertFalse(non_action.is_action())

    def test_actions_are_hashable(self):
        {self.buy_action}
