import json

from mock import patch, Mock, call
import pytest

from tala.utils import tdm_client
from tala.utils.tdm_client import TDMClient, SessionNotStartedException, PROTOCOL_VERSION, TDMRuntimeException


class TestTDMClient(object):
    def setup(self):
        self._mocked_requests = None
        self._tdm_client = None

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_start_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._when_calling_start_session()
        self._then_request_was_made_with(
            "mock-url",
            data='{{"version": {version}, "request": {{"type": "start_session"}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _given_mocked_requests_module(self, mock_requests):
        self._mocked_requests = mock_requests

    def _given_tdm_client_created_for(self, url):
        self._tdm_client = TDMClient(url)

    def _when_calling_start_session(self):
        self._tdm_client.start_session()

    def _then_request_was_made_with(self, url, headers, data):
        self._mocked_requests.post.assert_has_calls([call(url, data=data, headers=headers)])

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_say_without_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._when_calling_say_then_exception_was_raised("mock-utterance",
                                                         SessionNotStartedException,
                                                         "Expected the session to be started, but it wasn't")

    def _when_calling_say_then_exception_was_raised(self, utterance, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.say(utterance)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_say_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_requests_respond_with("mock-session-id")
        self._given_started_session()
        self._when_calling_say("mock-utterance")
        self._then_request_was_made_with(
            "mock-url",
            data='{{"session": {{"session_id": "mock-session-id"}}, '
                 '"input": {{"utterance": "mock-utterance", "modality": "text"}}, '
                 '"version": {version}, "request": {{"type": "input"}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

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

    def _given_started_session(self):
        self._tdm_client.start_session()

    def _when_calling_say(self, utterance):
        self._tdm_client.say(utterance)

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_passivity_without_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._when_calling_passivity_then_exception_was_raised(SessionNotStartedException,
                                                               "Expected the session to be started, but it wasn't")

    def _when_calling_passivity_then_exception_was_raised(self, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_passivity()

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_passivity_with_started_session(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_requests_respond_with("mock-session-id")
        self._given_started_session()
        self._when_calling_passivity()
        self._then_request_was_made_with(
            "mock-url",
            data='{{"session": {{"session_id": "mock-session-id"}}, '
                 '"version": {version}, "request": {{"type": "passivity"}}}}'.format(version=PROTOCOL_VERSION),
            headers={'Content-type': 'application/json'}
        )

    def _when_calling_passivity(self):
        self._tdm_client.request_passivity()

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
    def test_say_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_requests_respond_with("mock-session")
        self._given_started_session()
        self._given_requests_error_with("mock-error")
        self._when_calling_say_then_exception_was_raised("mock-utterance", TDMRuntimeException, "mock-error")

    @patch("{}.requests".format(tdm_client.__name__), autospec=True)
    def test_request_passivity_with_error_response(self, mock_requests):
        self._given_mocked_requests_module(mock_requests)
        self._given_tdm_client_created_for("mock-url")
        self._given_requests_respond_with("mock-session")
        self._given_started_session()
        self._given_requests_error_with("mock-error")
        self._when_requesting_passivity_then_exception_was_raised(TDMRuntimeException, "mock-error")

    def _when_requesting_passivity_then_exception_was_raised(self, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._tdm_client.request_passivity()
