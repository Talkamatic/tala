import unittest

from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction


class ServiceActionOutcomeTests(unittest.TestCase):
    def test_successful_service_action_is_successful(self):
        self.given_created_successful_service_action()
        self.when_is_successful_is_retrieved()
        self.then_result_is(True)

    def given_created_successful_service_action(self):
        self._service_action_outcome = SuccessfulServiceAction()

    def when_is_successful_is_retrieved(self):
        self._actual = self._service_action_outcome.is_successful

    def then_result_is(self, expected):
        self.assertEqual(expected, self._actual)

    def test_failed_service_action_is_not_successful(self):
        self.given_created_failed_service_action()
        self.when_is_successful_is_retrieved()
        self.then_result_is(False)

    def given_created_failed_service_action(self, failure_reason="mock_failure_reason"):
        self._service_action_outcome = FailedServiceAction(failure_reason)

    def test_failure_reason(self):
        self.given_created_failed_service_action(failure_reason="mock_failure_reason")
        self.when_failure_reason_is_retrieved()
        self.then_result_is("mock_failure_reason")

    def when_failure_reason_is_retrieved(self):
        self._actual = self._service_action_outcome.failure_reason

    def test_successful_service_action_equals_successful_service_action(self):
        self.assertEqual(SuccessfulServiceAction(), SuccessfulServiceAction())

    def test_successful_service_action_not_equals_non_service_action_outcome(self):
        self.assertNotEqual(SuccessfulServiceAction(), "non_service_action_outcome")

    def test_failed_service_action_equals_failed_service_action_with_same_failure_reason(self):
        self.assertEqual(FailedServiceAction("mock_failure_reason"), FailedServiceAction("mock_failure_reason"))

    def test_failed_service_action_not_equals_failed_service_action_with_other_failure_reason(self):
        self.assertNotEqual(FailedServiceAction("mock_failure_reason_1"), FailedServiceAction("mock_failure_reason_2"))

    def test_failed_service_action_not_equals_non_service_action_outcome(self):
        self.assertNotEqual(FailedServiceAction("mock_failure_reason"), "non_service_action_outcome")

    def test_successful_service_action_not_equals_failed_service_action(self):
        self.assertNotEqual(SuccessfulServiceAction(), FailedServiceAction("mock_failure_reason"))

    def test_successful_service_action_repr(self):
        self.assertEqual("SuccessfulServiceAction()", repr(SuccessfulServiceAction()))

    def test_successful_service_action_str(self):
        self.assertEqual("SuccessfulServiceAction()", str(SuccessfulServiceAction()))

    def test_failed_service_action_repr(self):
        self.assertEqual("FailedServiceAction('mock_failure_reason')", repr(FailedServiceAction("mock_failure_reason")))

    def test_failed_service_action_str(self):
        self.assertEqual("FailedServiceAction(mock_failure_reason)", str(FailedServiceAction("mock_failure_reason")))
