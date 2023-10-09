import pytest

from unittest.mock import call, Mock, patch, ANY

from tala.model.common import Modality
from tala.model.event_notification import EventNotification
from tala.model.input_hypothesis import InputHypothesis
from tala.model.interpretation import Interpretation, InterpretationWithoutUtterance
from tala.model.user_move import UserMove
from tala.testing.interactions import testcase
from tala.testing.interactions.named_test import InteractionTest
from tala.testing.interactions.testcase import InteractionTestingTestCase
from tala.testing.interactions.turn import RecognitionHypothesesTurn, UserInterpretationTurn, \
    SystemUtteranceTurn, UserPassivityTurn, NotifyStartedTurn, SystemMovesTurn
from tala.utils.tdm_client import TDMRuntimeException


class TestInteractionTestingTestCase:
    def setup_method(self):
        self._mock_tdm_client = None
        self._responses = []
        self._response_iterator = None

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_request_initial_system_output_if_test_has_initial_system_utterance(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterance("utterance")
        self.given_tdm_client_response(utterance="utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_starts_session()

    def given_mock_tdm_client(self, MockTDMClient):
        def side_effect(*args, **kwargs):
            if len(self._responses) > 1:
                if self._response_iterator is None:
                    self._response_iterator = iter(self._responses)
                return next(self._response_iterator)
            if len(self._responses) > 0:
                return self._responses[0]
            return self._create_tdm_client_response()

        self._mock_tdm_client = MockTDMClient.return_value
        self._mock_tdm_client.request_text_input.side_effect = side_effect
        self._mock_tdm_client.request_speech_input.side_effect = side_effect
        self._mock_tdm_client.request_semantic_input.side_effect = side_effect
        self._mock_tdm_client.request_passivity.side_effect = side_effect
        self._mock_tdm_client.request_event_notification.side_effect = side_effect
        self._mock_tdm_client.start_session.side_effect = side_effect

    def then_starts_session(self):
        self._mock_tdm_client.start_session.assert_called_with(session_data={"device_id": "tala"})

    def given_tdm_client_response(self, *args, **kwargs):
        self._responses.append(self._create_tdm_client_response(*args, **kwargs))  # yapf: disable

    def _create_tdm_client_response(
        self,
        utterance="mock_system_utterance",
        moves=None,
        expected_passivity=None,
        actions=None,
        nlu_result="mock_nlu_result",
        context="mock_context",
        selected_interpretation="mock_selected_interpretation",
        expected_input="mock_expected_input"
    ):
        return {
            "version": "3.4",
            "session": {
                "session_id": "mock-session-id"
            },
            "output": {
                "moves": moves or [],
                "utterance": utterance,
                "expected_passivity": expected_passivity,
                "actions": actions or []
            },
            "nlu_result": nlu_result,
            "context": context,
            "selected_interpretation": selected_interpretation,
            "expected_input": expected_input
        }

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_request_initial_system_output_if_test_has_initial_user_utterance(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_utterance("mockup_utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_starts_session()

    def then_request_is_not_enqueued(self, request):
        unexpected_call = call(request)
        actual_calls = self._mock_tdm_client.enqueue_request.call_args_list
        if unexpected_call in actual_calls:
            raise AssertionError(
                "Expected the request '%s' not to be enqueued but found it in the list %s" % (request, actual_calls)
            )

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_user_utterance_with_explicit_score(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_utterance("mockup_utterance", "1.0")
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_speech_input([InputHypothesis("mockup_utterance", 1.0)])

    def then_requests_speech_input(self, expected_hypotheses):
        self._mock_tdm_client.request_speech_input.assert_called_with(expected_hypotheses, ANY)

    def given_mock_backends_return_frontend_simulator(self):
        self._mock_tdm_client = self.mock_backend_factory.create.return_value
        self._mock_tdm_client._get_module_instance.return_value = self.mock_frontend_simulator

    def given_test_with_user_utterance(self, utterance, score_or_confidence_level="1.0", line_number=1):
        turn = RecognitionHypothesesTurn([(utterance, score_or_confidence_level)], line_number)
        self.test = self._create_mock_test([turn])

    def given_testcase(self):
        mock_domain_orchestration = Mock()
        self.testcase = InteractionTestingTestCase(self.test, mock_domain_orchestration)

    def when_performing_test(self):
        self.testcase.setUp()
        self.testcase.perform()
        self.testcase.tearDown()

    def _create_mock_test(self, turns):
        test = Mock(spec=InteractionTest)
        test.turns = turns
        test.name = "mock_test_name"
        test.filename = "mock_file_name"
        return test

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_user_utterance_with_confidence_level(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_utterance("mockup_utterance", "$ACKNOWLEDGE")
        self.given_testcase()
        self.when_performing_test_then_exception_is_raised(
            NotImplementedError, match="Explicit names of confidence levels are not supported in this version."
        )

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_utterance_that_matches(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterance("mockup_utterance")
        self.given_tdm_client_response(utterance="mockup_utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_test_is_successful()

    def then_test_is_successful(self):
        pass

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_utterance_not_matching_output(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterance("utterance")
        self.given_tdm_client_response(utterance="another")
        self.given_testcase()
        self.when_performing_test_then_it_fails_with_message(
            """On line 1 of mock_file_name,

expected:
  S> utterance

but got:
  S> another"""
        )

    def when_performing_test_then_it_fails_with_message(self, expected_message):
        with pytest.raises(AssertionError, match=expected_message):
            self.when_performing_test()

    def given_test_with_system_utterance(self, utterance, line_number=1):
        turn = SystemUtteranceTurn(utterance, line_number)
        self.test = self._create_mock_test([turn])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_moves_that_matches(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_moves(["mock_move"])
        self.given_tdm_client_response(moves=["mock_move"])
        self.given_testcase()
        self.when_performing_test()
        self.then_test_is_successful()

    def given_test_with_system_moves(self, moves, line_number=1):
        turn = SystemMovesTurn(moves, line_number)
        self.test = self._create_mock_test([turn])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_moves_not_matching_output(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_moves(["a_move"])
        self.given_tdm_client_response(moves=["another_move"])
        self.given_testcase()
        self.when_performing_test_then_it_fails_with_message(
            r"""On line 1 of mock_file_name,

expected:
  S> \["a_move"\]

but got:
  S> \["another_move"\]"""
        )

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_passivity_after_system_utterance(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterances_and_passivity(
            utterance_before_passivity="utterance before passivity",
            utterance_after_passivity="utterance after passivity"
        )
        self.given_tdm_client_response(utterance="utterance before passivity", expected_passivity=5.0)
        self.given_tdm_client_response(utterance="utterance after passivity")
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_passivity()

    def then_requests_passivity(self):
        self._mock_tdm_client.request_passivity.assert_called_with(ANY)

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_user_moves(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_interpretation(["semantic_expression_1", "semantic_expression_2"])
        self.given_tdm_client_response(utterance="an utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_semantic_input([
            Interpretation([UserMove("semantic_expression_1", 1.0, 1.0),
                            UserMove("semantic_expression_2", 1.0, 1.0)], Modality.OTHER)
        ])

    def then_requests_semantic_input(self, expected_interpretations):
        self._mock_tdm_client.request_semantic_input.assert_called_with(expected_interpretations, ANY)

    def given_test_with_user_interpretation(self, moves, line_number=1, utterance=None, modality=None):
        turn = UserInterpretationTurn(moves, line_number, modality, utterance)
        self.test = self._create_mock_test([turn])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_json_user_moves(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_interpretation([{
            "semantic_expression": "semantic_expression_1",
            "understanding_confidence": 0.12,
            "perception_confidence": 0.11,
        }, {
            "semantic_expression": "semantic_expression_2",
            "perception_confidence": 0.21,
            "understanding_confidence": 0.22
        }])
        self.given_tdm_client_response(utterance="an utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_semantic_input([
            InterpretationWithoutUtterance(
                moves=[UserMove("semantic_expression_1", 0.11, 0.12),
                       UserMove("semantic_expression_2", 0.21, 0.22)],
                modality=Modality.OTHER,
            )
        ])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_json_user_interpretation(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_user_interpretation(
            moves=[{
                "semantic_expression": "semantic_expression_1",
                "understanding_confidence": 0.12,
                "perception_confidence": 0.11,
            }, {
                "semantic_expression": "semantic_expression_2",
                "perception_confidence": 0.21,
                "understanding_confidence": 0.22
            }],
            utterance="mock utterance",
            modality="speech"
        )
        self.given_tdm_client_response(utterance="an utterance")
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_semantic_input([
            Interpretation(
                moves=[UserMove("semantic_expression_1", 0.11, 0.12),
                       UserMove("semantic_expression_2", 0.21, 0.22)],
                modality=Modality.SPEECH,
                utterance="mock utterance",
            )
        ])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_notify_started(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_notify_started("mock_action", {})
        self.given_testcase()
        self.when_performing_test()
        self.then_requests_event_notification(EventNotification("mock_action", EventNotification.STARTED, {}))

    def then_requests_event_notification(self, expected_event_notifications):
        self._mock_tdm_client.request_event_notification.assert_called_with(expected_event_notifications, ANY)

    def given_test_with_notify_started(self, action, parameters, line_number=1):
        turn = NotifyStartedTurn(action, parameters, line_number)
        self.test = self._create_mock_test([turn])

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_failure_when_no_response_to_user_passivity(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterances_and_passivity(
            utterance_before_passivity="utterance before passivity",
            line_number_of_passivity=2,
            utterance_after_passivity="utterance after passivity",
            line_number_of_utterance_after_passivity=3
        )
        self.given_tdm_client_response(utterance="utterance before passivity", expected_passivity=None)
        self.given_testcase()
        self.when_performing_test_then_it_fails_with_message(
            """

On line 3 of mock_file_name,
expected:
  S> utterance after passivity

in response to
  U>
on line 2

but the system didn't expect user passivity."""
        )

    def when_performing_test_then_exception_is_raised(self, *args, **kwargs):
        with pytest.raises(*args, **kwargs):
            self.when_performing_test()

    def given_test_with_system_utterances_and_passivity(
        self,
        utterance_before_passivity="utterance before passivity",
        line_number_of_utterance_before_passivity=1,
        line_number_of_passivity=2,
        utterance_after_passivity="utterance after passivity",
        line_number_of_utterance_after_passivity=3
    ):
        turns = [
            SystemUtteranceTurn(utterance_before_passivity, line_number_of_utterance_before_passivity),
            UserPassivityTurn(line_number_of_passivity),
            SystemUtteranceTurn(utterance_after_passivity, line_number_of_utterance_after_passivity)
        ]
        self.test = self._create_mock_test(turns)

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_returns_nothing_when_expecting_system_utterance(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterance("utterance")
        self.given_error("Error message.")
        self.given_testcase()
        self.when_performing_test_then_exception_is_raised(TDMRuntimeException, match="Error message.")

    def given_error(self, message):
        side_effect = TDMRuntimeException(message)
        self._mock_tdm_client.request_text_input.side_effect = side_effect
        self._mock_tdm_client.request_speech_input.side_effect = side_effect
        self._mock_tdm_client.request_semantic_input.side_effect = side_effect
        self._mock_tdm_client.request_passivity.side_effect = side_effect
        self._mock_tdm_client.request_event_notification.side_effect = side_effect
        self._mock_tdm_client.start_session.side_effect = side_effect

    @patch(f"{testcase.__name__}.TDMClient", autospec=True)
    def test_system_errors_when_expecting_system_utterance(self, MockTDMClient):
        self.given_mock_tdm_client(MockTDMClient)
        self.given_test_with_system_utterance("utterance")
        self.given_error("an error")
        self.given_testcase()
        self.when_performing_test_then_exception_is_raised(TDMRuntimeException, match="an error")
