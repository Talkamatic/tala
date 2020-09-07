import json
from typing import Sequence, Mapping  # noqa: F401

import requests

from tala.model.input_hypothesis import InputHypothesis  # noqa: F401
from tala.model.interpretation import Interpretation  # noqa: F401
from tala.model.event_notification import EventNotification  # noqa: F401
from tala.utils.await_endpoint import await_endpoint
from tala.utils.observable import Observable
from copy import copy

PROTOCOL_VERSION = "3.3"


class InvalidResponseError(Exception):
    pass


class TDMRuntimeException(Exception):
    pass


class TDMClient(Observable):
    def __init__(self, url: str) -> None:
        super(TDMClient, self).__init__()
        self._url = url

    def wait_to_start(self, timeout=3):
        url = self._url.replace("/interact", "/health")
        await_endpoint(url, timeout)

    def request_text_input(self, session: str, utterance: str, session_data: Mapping = None) -> Mapping:
        def _create_text_input_request(session, utterance):
            return {
                "version": PROTOCOL_VERSION,
                "session": session,
                "request": {
                    "natural_language_input": {
                        "modality": "text",
                        "utterance": utterance,
                    }
                }
            }

        session_object = self._create_session_object(session_data, session)
        request = _create_text_input_request(session_object, utterance)
        response = self._make_request(request)
        return response

    def request_speech_input(
        self, session: str, hypotheses: Sequence[InputHypothesis], session_data: Mapping = None
    ) -> Mapping:
        def _create_speech_input_request(session, hypotheses):
            return {
                "version": PROTOCOL_VERSION,
                "session": session,
                "request": {
                    "natural_language_input": {
                        "modality": "speech",
                        "hypotheses": [{
                            "utterance": hypothesis.utterance,
                            "confidence": hypothesis.confidence,
                        } for hypothesis in hypotheses],
                    }
                }
            }  # yapf: disable

        session_object = self._create_session_object(session_data, session)
        request = _create_speech_input_request(session_object, hypotheses)
        response = self._make_request(request)
        return response

    def request_semantic_input(
        self, session: str, interpretations: Sequence[Interpretation], session_data: Mapping = None
    ) -> Mapping:
        def _create_semantic_input_request(session, interpretations):
            return {
                "version": PROTOCOL_VERSION,
                "session": session,
                "request": {
                    "semantic_input": {
                        "interpretations": [interpretation.as_dict() for interpretation in interpretations],
                    }
                }
            }  # yapf: disable

        session_object = self._create_session_object(session_data, session)
        request = _create_semantic_input_request(session_object, interpretations)
        response = self._make_request(request)
        return response

    def request_passivity(self, session: str, session_data: Mapping = None) -> Mapping:
        session_object = self._create_session_object(session_data, session)
        request = {"version": PROTOCOL_VERSION, "session": session_object, "request": {"passivity": {}}}
        response = self._make_request(request)
        return response

    def request_event_notification(
        self, session: str, notification: EventNotification, session_data: Mapping = None
    ) -> Mapping:
        def _create_event_notification_request(session, notification):
            return {
                "version": PROTOCOL_VERSION,
                "session": session,
                "request": {
                    "event": {
                        "name": notification.action,
                        "status": notification.status,
                        "parameters": notification.parameters
                    }
                }
            }  # yapf: disable

        session_object = self._create_session_object(session_data, session)
        request = _create_event_notification_request(session_object, notification)
        response = self._make_request(request)
        return response

    def _create_session_object(self, session_data=None, session_id=None):
        session = copy(session_data) if session_data else {}
        if session_id:
            session["session_id"] = session_id
        return session

    def start_session(self, session_data: Mapping = None) -> Mapping:
        session_object = session_data or {}
        request = {"version": PROTOCOL_VERSION, "session": session_object, "request": {"start_session": {}}}
        response = self._make_request(request)
        return response

    def _make_request(self, request_body):
        data_as_json = json.dumps(request_body)
        headers = {'Content-type': 'application/json'}
        response_object = requests.post(self._url, data=data_as_json, headers=headers)
        response_object.raise_for_status()
        try:
            response = response_object.json()
        except ValueError:
            raise InvalidResponseError(f"Expected a valid JSON response but got '{response_object}'.")

        if "error" in response:
            description = response["error"]["description"]
            raise TDMRuntimeException(description)

        return response
