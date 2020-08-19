from mock import patch
import unittest

import tala.testing.endurance.named_test
from tala.testing.endurance.named_test import EnduranceInteractionTest, MissingTurnsException
from tala.testing.interactions.named_test import InteractionTest
from tala.testing.interactions.turn import RecognitionHypothesesTurn, SystemUtteranceTurn


class EnduranceInteractionTestTests(unittest.TestCase):
    def setUp(self):
        self._interaction_tests = []
        self._duration = None
        self._endurance_test = None
        self._actual_turn = None
        self._turns_iterator = None
        self._mock_time = None
        self._mock_random = None

    def test_first_turn_is_of_type_system(self):
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                SystemUtteranceTurn("mock system utterance", 1),
                RecognitionHypothesesTurn(["mock user utterance"], 2)
            ])])
        self._given_duration(0)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._when_fetching_the_next_turn()
        self._then_it_is_recognition_hypotheses_turn()

    @staticmethod
    def _create_interaction_test_with_turns(turns):
        mocked_test = InteractionTest("mock_file", "mock_name", turns)
        return mocked_test

    def _given_mocked_tests(self, tests):
        self._interaction_tests = tests

    def _given_duration(self, duration):
        self._duration = duration

    def _given_created_endurance_test(self):
        self._endurance_test = EnduranceInteractionTest(self._interaction_tests, self._duration)

    def _given_fetched_turns_iterator(self):
        self._turns_iterator = self._endurance_test.turns

    def _when_fetching_the_next_turn(self):
        self._actual_turn = next(self._turns_iterator)

    def _then_it_is_recognition_hypotheses_turn(self):
        self.assertTrue(self._actual_turn.is_recognition_hypotheses_turn)

    def test_only_turn_is_of_type_system(self):
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                SystemUtteranceTurn("mock system utterance", 1)
            ])])
        self._given_duration(0)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._when_fetching_the_next_turn_then_exception_is_raised_matching(
            MissingTurnsException, "Expected turns but found none in test 'mock_name' of 'mock_file'")

    def _when_fetching_the_next_turn_then_exception_is_raised_matching(self, ExceptionClass, message_regex):
        with self.assertRaisesRegex(ExceptionClass, message_regex):
            next(self._turns_iterator)

    def _given_fetched_the_next_turn(self):
        next(self._turns_iterator)

    @patch("%s.time" % tala.testing.endurance.named_test.__name__)
    def test_turns_with_positive_duration(self, mock_time):
        self._given_mock_time(mock_time)
        self._given_mock_time_is(0)
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                RecognitionHypothesesTurn(["mock user utterance"], 1)
            ])])
        self._given_duration(1)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._given_fetched_the_next_turn()
        self._given_mock_time_is(2)
        self._when_fetching_the_next_turn_then_stop_iteration_is_raised()

    def _when_fetching_the_next_turn_then_stop_iteration_is_raised(self):
        with self.assertRaises(StopIteration):
            next(self._turns_iterator)

    def _given_mock_time(self, mock_time):
        self._mock_time = mock_time

    def _given_mock_time_is(self, time_now):
        self._mock_time.time.return_value = time_now

    def test_stop(self):
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                RecognitionHypothesesTurn(["mock user utterance"], 1)
            ])])
        self._given_duration(0)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._given_fetched_the_next_turn()
        self._given_called_stop()
        self._when_fetching_the_next_turn_then_stop_iteration_is_raised()

    def _given_called_stop(self):
        self._endurance_test.stop()

    def test_turns_are_generated_over_and_over_again(self):
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                RecognitionHypothesesTurn(["mock user utterance"], 1)
            ])])
        self._given_duration(0)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._given_fetched_the_next_turn()  # U>
        self._given_fetched_the_next_turn()  # PASSIVITY
        self._given_fetched_the_next_turn()  # S> *
        self._when_fetching_the_next_turn()  # U> again
        self._then_it_is_recognition_hypotheses_turn()

    @patch("%s.random" % tala.testing.endurance.named_test.__name__)
    def test_turns_are_generated_randomly(self, mock_random):
        self._given_mock_random(mock_random)
        self._given_mock_random_choice_returns(
            self._create_interaction_test_with_turns([
                RecognitionHypothesesTurn(["mock user utterance"], 1)
            ]))
        self._given_mocked_tests([
            self._create_interaction_test_with_turns([
                RecognitionHypothesesTurn(["mock user utterance"], 1)
            ])])
        self._given_duration(0)
        self._given_created_endurance_test()
        self._given_fetched_turns_iterator()
        self._when_fetching_the_next_turn()
        self._then_next_interaction_test_was_randomly_selected()

    def _given_mock_random(self, mock_random):
        self._mock_random = mock_random

    def _given_mock_random_choice_returns(self, test):
        self._mock_random.choice.return_value = test

    def _then_next_interaction_test_was_randomly_selected(self):
        self.assertIs(self._actual_turn, self._mock_random.choice.return_value.turns[0])
