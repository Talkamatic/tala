import json

from mock import patch, Mock, call
import pytest
from requests.exceptions import RequestException

from tala.model.input_hypothesis import InputHypothesis
from tala.model.interpretation import Interpretation
from tala.model.common import Modality
from tala.model.user_move import DDDSpecificUserMove
from tala.utils import tdm_client
from tala.utils.tdm_client import TDMClient, PROTOCOL_VERSION, TDMRuntimeException


class TestTDMClient(object):
    def setup(self):
        self._mocked_requests = None
        self._tdm_client = None
        self._session = None

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_start_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._when_calling_start_session()
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{}}, "request": {{"start_session": {{}}}}}}'.format(
                version=PROTOCOL_VERSION
            ),
            headers={'Content-type': 'application/json'}
        )

    def _given_mocked_requests_module(self, mock_requests):
        self._mocked_requests = mock_requests

    def _given_tdm_client_created_for(self, url):
        self._tdm_client = TDMClient(url)

    def _when_calling_start_session(self, session_data=None):
        self._tdm_client.start_session(session_data)

    def _then_request_was_made_with(self, url, headers, data):
        self._mocked_requests.post.assert_has_calls([call(url, data=data, headers=headers)])

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_start_session_with_data(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._when_calling_start_session(session_data={"key": "value"})
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"key": "value"}}, "request": {{"start_session": {{}}}}}}'.
            format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_say_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_text_input("mock-utterance")
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"session_id": "mock-session-id"}}, '
            '"request": {{"natural_language_input": {{'
            '"modality": "text", "utterance": "mock-utterance"}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _given_session_id(self, session_id):
        self._session = session_id

    def _given_requests_respond_with(self, session_id):
        response = Mock()
        json_response = '''{{
  "version": {version},
  "session": {{
    "session_id": "{session_id}"
  }},
  "output": {{
    "utterance": "mock-system-utterance",
    "expected_passivity": 5.0,
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
}}'''.format(version=PROTOCOL_VERSION, session_id=session_id)
        response.json.return_value = json.loads(json_response)
        self._mocked_requests.post.return_value = response

    def _when_requesting_text_input(self, utterance, session_data=None):
        self._tdm_client.request_text_input(self._session, utterance, session_data)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_say_with_started_session_with_data(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_text_input("mock-utterance", session_data={"key": "value"})
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"key": "value", "session_id": "mock-session-id"}}, '
            '"request": {{"natural_language_input": {{'
            '"modality": "text", "utterance": "mock-utterance"}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_requesting_speech_input_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_speech_input([InputHypothesis("mock-utterance", 0.5)])
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"session_id": "mock-session-id"}}, '
            '"request": {{"natural_language_input": {{'
            '"modality": "speech", '
            '"hypotheses": [{{"utterance": "mock-utterance", "confidence": 0.5}}]'
            '}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _when_requesting_speech_input(self, hypotheses, session_data=None):
        self._tdm_client.request_speech_input(self._session, hypotheses, session_data)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_requesting_speech_input_with_started_session_with_data(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_speech_input([InputHypothesis("mock-utterance", 0.5)], session_data={"key": "value"})
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"key": "value", "session_id": "mock-session-id"}}, '
            '"request": {{"natural_language_input": {{'
            '"modality": "speech", '
            '"hypotheses": [{{"utterance": "mock-utterance", "confidence": 0.5}}]'
            '}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_requesting_semantic_input_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_semantic_input([
            Interpretation(
                [DDDSpecificUserMove(
                    "mock-ddd", "mock-expression", "mock-perception-confidence", "mock-understanding-confidence")],
                modality=Modality.SPEECH,
                utterance="mock-utterance"
            )
        ])  # yapf: disable
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"session_id": "mock-session-id"}}, '
            '"request": {{"semantic_input": {{"interpretations": [{{'
            '"modality": "speech", '
            '"moves": '
            '[{{'
            '"ddd": "mock-ddd", '
            '"perception_confidence": "mock-perception-confidence", '
            '"understanding_confidence": "mock-understanding-confidence", '
            '"semantic_expression": "mock-expression"'
            '}}], '
            '"utterance": "mock-utterance"'
            '}}]}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _when_requesting_semantic_input(self, interpretations, session_data=None):
        self._tdm_client.request_semantic_input(self._session, interpretations, session_data)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_requesting_semantic_input_with_started_session_with_data(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_requesting_semantic_input([
            Interpretation([
                DDDSpecificUserMove(
                    "mock-ddd", "mock-expression", "mock-perception-confidence", "mock-understanding-confidence"
                )
            ],
                           modality=Modality.SPEECH,
                           utterance="mock-utterance")
        ],
                                             session_data={"key": "value"})
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"key": "value", "session_id": "mock-session-id"}}, '
            '"request": {{"semantic_input": {{"interpretations": [{{'
            '"modality": "speech", '
            '"moves": '
            '[{{'
            '"ddd": "mock-ddd", '
            '"perception_confidence": "mock-perception-confidence", '
            '"understanding_confidence": "mock-understanding-confidence", '
            '"semantic_expression": "mock-expression"'
            '}}], '
            '"utterance": "mock-utterance"'
            '}}]}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_passivity_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_calling_passivity()
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"session_id": "mock-session-id"}}, '
            '"request": {{"passivity": {{}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _when_calling_passivity(self, session_data=None):
        self._tdm_client.request_passivity(self._session, session_data)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_passivity_with_started_session_and_data(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session-id")
        self._when_calling_passivity(session_data={"key": "value"})
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": "{version}", "session": {{"key": "value", "session_id": "mock-session-id"}}, '
            '"request": {{"passivity": {{}}}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_start_session_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_requests_error_with("mock-error")
        self._when_starting_session_then_exception_was_raised(TDMRuntimeException, "mock-error")

    def _when_starting_session_then_exception_was_raised(self, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.start_session()

    def _given_requests_error_with(self, description):
        response = Mock()
        json_response = '''{{
  "version": {version},
  "session": {{
    "session_id": "mock-session"
  }},
  "error": {{
    "description": "{description}"
  }}
}}'''.format(version=PROTOCOL_VERSION, description=description)
        response.json.return_value = json.loads(json_response)
        self._mocked_requests.post.return_value = response

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_unexpected_status_code(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_response_status_check_raises(RequestException, "mock-error")
        self._when_starting_session_then_exception_was_raised(RequestException, "mock-error")

    def _given_response_status_check_raises(self, ExceptionClass, message):
        self._mocked_requests.post.return_value.raise_for_status.side_effect = ExceptionClass(message)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_say_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session")
        self._given_requests_error_with("mock-error")
        self._when_requesting_text_input_then_exception_was_raised("mock-utterance", TDMRuntimeException, "mock-error")

    def _when_requesting_text_input_then_exception_was_raised(self, utterance, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_text_input(self._session, utterance)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_request_passivity_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session")
        self._given_requests_error_with("mock-error")
        self._when_requesting_passivity_then_exception_was_raised(TDMRuntimeException, "mock-error")

    def _when_requesting_passivity_then_exception_was_raised(self, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_passivity(self._session)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_request_speech_input_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session")
        self._given_requests_error_with("mock-error")
        self._when_requesting_speech_input_then_exception_was_raised([InputHypothesis("mock-utterance", 0.5)],
                                                                     TDMRuntimeException, "mock-error")

    def _when_requesting_speech_input_then_exception_was_raised(self, hypotheses, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_speech_input(self._session, hypotheses)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_request_semantic_input_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_session_id("mock-session")
        self._given_requests_error_with("mock-error")
        self._when_requesting_semantic_input_then_exception_was_raised([
            Interpretation(
                [DDDSpecificUserMove(
                    "mock-ddd", "mock-expression", "mock-perception-confidence", "mock-understanding-confidence")],
                modality=Modality.SPEECH,
                utterance="mock-utterance"
            )
        ], TDMRuntimeException, "mock-error")  # yapf: disable

    def _when_requesting_semantic_input_then_exception_was_raised(
        self, interpretations, expected_exception, expected_message
    ):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_semantic_input(self._session, interpretations)