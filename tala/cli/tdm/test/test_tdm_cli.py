import json

from unittest.mock import patch, ANY

from tala.cli.tdm import tdm_cli
from tala.cli.tdm.passivity_timer import PASSIVE
from tala.cli.tdm.tdm_cli import TDMCLI
from tala.utils.tdm_client import PROTOCOL_VERSION


class TestTDMCLI(object):
    def setup_method(self):
        self._mocked_tdm_client = None
        self._MockPromptSession = None
        self._mocked_prompt_session = None
        self._tdm_cli = None
        self._system_turns = None
        self._system_turn = None
        self._MockFileHistory = None
        self._mocked_file_history = None
        self._mocked_passivity_timer = None
        self._mocked_application = None
        self._capsys = None

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    def test_first_system_turn_starts_session(self, MockTDMClient, MockPromptSession):
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._when_getting_system_turn()
        self._then_session_is_started()

    def _given_mocked_tdm_client(self, MockTDMClient):
        self._mocked_tdm_client = MockTDMClient.return_value
        self._mocked_tdm_client.start_session.return_value = self._create_tdm_client_response()
        self._mocked_tdm_client.request_text_input.return_value = self._create_tdm_client_response()
        self._mocked_tdm_client.request_passivity.return_value = self._create_tdm_client_response()

    def _create_tdm_client_response(self, system_utterance="mock-system-utterance", expected_passivity="null"):
        return json.loads(
            '''{{
  "version": {version},
  "session": {{
    "session_id": "mock-session-id"
  }},
  "output": {{
    "utterance": "{system_utterance}",
    "expected_passivity": {expected_passivity},
    "actions": []
  }},
  "nlu_result": {{
    "selected_utterance": "call John",
    "confidence": 0.88
  }},
  "context": {{
    "active_ddd": "my_ddd",
    "facts": {{}},
    "language": "eng"
  }}
}}'''.format(version=PROTOCOL_VERSION, system_utterance=system_utterance, expected_passivity=expected_passivity)
        )

    def _given_mocked_prompt_session(self, MockPromptSession):
        self._MockPromptSession = MockPromptSession
        self._mocked_prompt_session = MockPromptSession.return_value

    def _given_created_tdm_cli(self):
        self._tdm_cli = self._create_tdm_cli()

    def _create_tdm_cli(self, url="mocked-url"):
        return TDMCLI(url, None)

    def _given_initiated_system_turns(self):
        self._system_turns = self._tdm_cli.system_turns()

    def _when_getting_system_turn(self):
        self._system_turn = next(self._system_turns)

    def _then_session_is_started(self):
        self._mocked_tdm_client.start_session.assert_called_once()

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    def test_prompt_started_after_session_is_started(self, MockTDMClient, MockPromptSession):
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._given_session_is_started()
        self._when_getting_system_turn()
        self._then_prompt_is_started_with("U> ")

    def _given_session_is_started(self):
        next(self._system_turns)
        self._mocked_tdm_client.start_session.assert_called_once()

    def _then_prompt_is_started_with(self, expected_message):
        self._mocked_prompt_session.prompt.assert_called_once_with(expected_message)

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.FileHistory".format(tdm_cli.__name__), autospec=True)
    def test_file_history_is_used(self, MockFileHistory, MockTDMClient, MockPromptSession):
        self._given_mocked_file_history(MockFileHistory)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._when_creating_tdm_cli()
        self._then_file_history_is_used()

    def _given_mocked_file_history(self, MockFileHistory):
        self._MockFileHistory = MockFileHistory
        self._mocked_file_history = self._MockFileHistory.return_value

    def _when_creating_tdm_cli(self):
        self._create_tdm_cli()

    def _then_file_history_is_used(self):
        self._MockPromptSession.assert_called_once_with(
            history=self._mocked_file_history, mouse_support=True, validator=ANY
        )

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.FileHistory".format(tdm_cli.__name__), autospec=True)
    def test_file_history_is_stored_in_local_tala_folder(self, MockFileHistory, MockTDMClient, MockPromptSession):
        self._given_mocked_file_history(MockFileHistory)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._when_creating_tdm_cli()
        self._then_file_history_is_stored_in(".tala/history")

    def _then_file_history_is_stored_in(self, expected_path):
        self._MockFileHistory.assert_called_once_with(expected_path)

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    def test_system_utterance_from_tdm_client_is_used_as_system_turn(self, MockTDMClient, MockPromptSession):
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_tdm_client_returns_utterance_on_start_session("system-utterance")
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._when_getting_system_turn()
        self._then_system_turn_is("S> system-utterance")

    def _given_mocked_tdm_client_returns_utterance_on_start_session(self, utterance):
        self._mocked_tdm_client.start_session.return_value = \
            self._create_tdm_client_response(system_utterance=utterance)

    def _then_system_turn_is(self, turn):
        assert self._system_turn == turn

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.PassivityTimer".format(tdm_cli.__name__), autospec=True)
    def test_passivity_timer_is_started(self, MockPassivityTimer, MockTDMClient, MockPromptSession):
        self._given_mocked_passivity_timer(MockPassivityTimer)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_tdm_client_expects_passivity_when_session_is_started(expected_passivity=5.0)
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._when_getting_system_turn()
        self._then_passivity_timer_is_started_with(5.0)

    def _given_mocked_passivity_timer(self, MockPassivityTimer):
        self._mocked_passivity_timer = MockPassivityTimer.return_value

    def _given_mocked_tdm_client_expects_passivity_when_session_is_started(self, expected_passivity):
        self._mocked_tdm_client.start_session.return_value = \
            self._create_tdm_client_response(expected_passivity=expected_passivity)

    def _then_passivity_timer_is_started_with(self, expected_duration):
        self._mocked_passivity_timer.start.assert_called_once_with(expected_duration)

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.PassivityTimer".format(tdm_cli.__name__), autospec=True)
    def test_passivity_timer_triggers_call_to_tdm_client(self, MockPassivityTimer, MockTDMClient, MockPromptSession):
        self._given_mocked_passivity_timer(MockPassivityTimer)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._when_passivity_timer_triggers()
        self._then_passivity_is_called_in_tdm_client()

    def _when_passivity_timer_triggers(self):
        args, kwargs = self._mocked_passivity_timer.add_observer.call_args
        observer, = args
        observer.update(PASSIVE)

    def _then_passivity_is_called_in_tdm_client(self):
        self._mocked_tdm_client.request_passivity.assert_called_once()

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.prompt_toolkit.application".format(tdm_cli.__name__), autospec=True)
    @patch("{}.PassivityTimer".format(tdm_cli.__name__), autospec=True)
    def test_system_utterance_from_passivity_call_to_tdm_client_is_used_as_system_utterance(
        self, MockPassivityTimer, mock_application, MockTDMClient, MockPromptSession, capsys
    ):
        self._given_mocked_passivity_timer(MockPassivityTimer)
        self._given_mocked_application(mock_application)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_tdm_client_returns_utterance_on_passivity("system-utterance")
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_stdout_is_being_captured(capsys)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._given_session_is_started()
        self._when_passivity_timer_triggers()
        self._then_prompt_toolkit_is_instructed_to_print("U>\nS> system-utterance\n")

    def _given_mocked_application(self, mock_application):
        self._mocked_application = mock_application

    def _given_mocked_tdm_client_returns_utterance_on_passivity(self, utterance):
        self._mocked_tdm_client.request_passivity.return_value = \
            self._create_tdm_client_response(system_utterance=utterance)

    def _given_stdout_is_being_captured(self, capsys):
        self._capsys = capsys

    def _then_prompt_toolkit_is_instructed_to_print(self, expected_string):
        def get_print_callable_from_prompt_toolkit():
            self._mocked_application.run_in_terminal.assert_called_once()
            args, kwargs = self._mocked_application.run_in_terminal.call_args
            print_callable, = args
            return print_callable

        def actual_stdout():
            captured = self._capsys.readouterr()
            return captured.out

        printer = get_print_callable_from_prompt_toolkit()
        printer()
        assert actual_stdout() == expected_string

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    @patch("{}.Validator".format(tdm_cli.__name__), autospec=True)
    @patch("{}.PassivityTimer".format(tdm_cli.__name__), autospec=True)
    def test_passivity_timer_stopped_when_user_becomes_active(
        self, MockPassivityTimer, MockValidator, MockTDMClient, MockPromptSession
    ):
        self._given_mocked_passivity_timer(MockPassivityTimer)
        self._given_mocked_user_activity_detector(MockValidator)
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._when_user_activity_is_detected()
        self._then_passivity_timer_is_stopped()

    def _given_mocked_user_activity_detector(self, MockValidator):
        self._mocked_activity_detector = MockValidator.from_callable

    def _when_user_activity_is_detected(self):
        def get_detector_callable():
            args, kwargs = self._mocked_activity_detector.call_args
            activity_detector_callable, = args
            return activity_detector_callable

        detector = get_detector_callable()
        detector("mock-input")

    def _then_passivity_timer_is_stopped(self):
        self._mocked_passivity_timer.stop.assert_called_once()

    @patch("{}.PromptSession".format(tdm_cli.__name__), autospec=True)
    @patch("{}.TDMClient".format(tdm_cli.__name__), autospec=True)
    def test_endurance(self, MockTDMClient, MockPromptSession):
        self._given_mocked_tdm_client(MockTDMClient)
        self._given_mocked_tdm_client_returns_utterance_on_request_text_input("system-utterance")
        self._given_mocked_prompt_session(MockPromptSession)
        self._given_created_tdm_cli()
        self._given_initiated_system_turns()
        self._given_session_is_started()
        self._when_user_and_system_are_taking_turns_for_a_long_while()
        self._then_system_turn_is("S> system-utterance")

    def _given_mocked_tdm_client_returns_utterance_on_request_text_input(self, utterance):
        self._mocked_tdm_client.request_text_input.return_value = self._create_tdm_client_response(
            system_utterance=utterance
        )

    def _when_user_and_system_are_taking_turns_for_a_long_while(self):
        for i in range(100):
            next(self._system_turns)
        self._system_turn = next(self._system_turns)
