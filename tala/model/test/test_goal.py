from tala.model.goal import Goal, ResolveGoal, PerformGoal
from tala.model.speaker import Speaker
from tala.testing.lib_test_case import LibTestCase


class GoalTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_equality(self):
        goal = Goal("type 1", Speaker.SYS)
        identical_goal = Goal("type 1", Speaker.SYS)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_goal, goal)

    def test_is_goal_false_by_default(self):
        non_goal_object = self.top_action
        self.assertFalse(non_goal_object.is_goal())


class ResolveGoalTest(LibTestCase):
    def test_equality(self):
        goal = ResolveGoal(self.price_question, Speaker.SYS)
        identical_goal = ResolveGoal(self.price_question, Speaker.SYS)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_goal, goal)

    def test_inequality_due_to_question(self):
        goal1 = ResolveGoal(self.dest_city_question, Speaker.SYS)
        goal2 = ResolveGoal(self.price_question, Speaker.SYS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(goal1, goal2)

    def test_inequality_due_to_target(self):
        goal1 = ResolveGoal(self.dest_city_question, Speaker.USR)
        goal2 = ResolveGoal(self.dest_city_question, Speaker.SYS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(goal1, goal2)

    def test_hashable(self):
        goal = ResolveGoal(self.price_question, Speaker.SYS)
        set([goal])

    def test_is_goal(self):
        goal = ResolveGoal(self.price_question, Speaker.SYS)
        self.assertTrue(goal.is_goal())

    def test_str_with_target_sys(self):
        goal = ResolveGoal(self.price_question, Speaker.SYS)
        self.assertEquals("resolve(?X.price(X))", unicode(goal))

    def test_str_with_target_user(self):
        goal = ResolveGoal(self.price_question, Speaker.USR)
        self.assertEquals("resolve_user(?X.price(X))", unicode(goal))

    def test_str_with_background(self):
        goal = ResolveGoal(self.price_question, Speaker.SYS)
        goal.set_background(self.predicate_dest_city)
        self.assertEquals("resolve(?X.price(X), dest_city)", unicode(goal))

    def setUp(self):
        self.setUpLibTestCase()


class PerformGoalTest(LibTestCase):
    def test_equality(self):
        goal = PerformGoal(self.top_action)
        identical_goal = PerformGoal(self.top_action)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_goal, goal)

    def test_inequality_due_to_action(self):
        goal1 = PerformGoal(self.buy_action)
        goal2 = PerformGoal(self.top_action)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(goal1, goal2)

    def test_hashable(self):
        goal = PerformGoal(self.top_action)
        set([goal])

    def test_is_goal(self):
        goal = PerformGoal(self.top_action)
        self.assertTrue(goal.is_goal())

    def setUp(self):
        self.setUpLibTestCase()
