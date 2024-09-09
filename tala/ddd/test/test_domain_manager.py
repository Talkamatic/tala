import unittest

from unittest.mock import Mock

from tala.ddd.domain_manager import DomainManager, UnknownGoalException
from tala.ddd.ddd_manager import DDDManager
from tala.model.domain import Domain
from tala.model.goal import Goal


class DomainManagerTests(unittest.TestCase):
    def setUp(self):
        self.domain_manager = DomainManager(Mock(spec=DDDManager))

    def test_get_without_adding(self):
        self.given_mocked_domain_with_goal()
        self.when_getting_domain_of_goal_then_exception_is_raised()

    def when_getting_domain_of_goal_then_exception_is_raised(self):
        with self.assertRaises(UnknownGoalException):
            self.domain_manager.get_domain_of_goal(self.mock_goal)

    def test_add_and_get(self):
        self.given_mocked_domain_with_goal()
        self.given_domain_has_been_added()
        self.when_getting_domain_of_goal()
        self.then_got_domain()

    def given_mocked_domain_with_goal(self):
        self.mock_goal = Mock(spec=Goal)
        self.mock_goal.is_resolve_goal.return_value = False
        self.mock_domain = Mock(spec=Domain)
        self.mock_domain.goals = [self.mock_goal]

    def given_domain_has_been_added(self):
        self.domain_manager.add(self.mock_domain)

    def when_getting_domain_of_goal(self):
        self.result = self.domain_manager.get_domain_of_goal(self.mock_goal)

    def then_got_domain(self):
        self.assertEqual(self.mock_domain, self.result)

    def test_remove_added_domain(self):
        self.given_mocked_domain_with_goal()
        self.given_domain_has_been_added()
        self.given_removed_domain()
        self.when_getting_domain_of_goal_then_exception_is_raised()

    def given_removed_domain(self):
        self.domain_manager.remove(self.mock_domain)

    def test_removing_unknown_domain(self):
        self.given_mocked_domain_with_goal()
        self.when_removing_domain_then_exception_is_raised()

    def when_removing_domain_then_exception_is_raised(self):
        with self.assertRaises(UnknownGoalException):
            self.domain_manager.remove(self.mock_domain)

    def test_add_and_get_all(self):
        self.given_mocked_domain_with_goal()
        self.given_domain_has_been_added()
        self.when_getting_domains()
        self.then_domain_in_result()

    def when_getting_domains(self):
        self.result = self.domain_manager.domains

    def then_domain_in_result(self):
        self.assertIn(self.mock_domain, self.result)

    def test_remove_added_domain_leaves_no_domains(self):
        self.given_mocked_domain_with_goal()
        self.given_domain_has_been_added()
        self.given_removed_domain()
        self.when_getting_domains()
        self.then_result_is_empty()

    def then_result_is_empty(self):
        self.assertEqual(len(self.result), 0)
