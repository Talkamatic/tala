import json
from typing import Text  # noqa: F401

import requests

from tala.model.input_hypothesis import InputHypothesis  # noqa: F401
from tala.model.interpretation import Interpretation  # noqa: F401
from tala.utils.observable import Observable
from copy import copy

PROTOCOL_VERSION = "3.1"


class InvalidResponseError(Exception):
    pass


class TDMRuntimeException(Exception):
    pass


class TDMClient(Observable):
    def __init__(self, url):
        # type: (Text) -> None
        super(TDMClient, self).__init__()
        self._url = url

    def request_text_input(self, session, utterance, session_data=None):
        # type: (str, unicode, dict) -> dict
        session_object = self._create_session_object(session_data, session)
        request = self._create_text_input_request(session_object, utterance)
        response = self._make_request(request)
        return response

    def request_speech_input(self, session, hypotheses, session_data=None):
        # type: (str, [InputHypothesis], dict) -> dict
        session_object = self._create_session_object(session_data, session)
        request = self._create_speech_input_request(session_object, hypotheses)
        response = self._make_request(request)
        return response

    def request_semantic_input(self, session, interpretations, session_data=None):
        # type: (str, [Interpretation], dict) -> dict
        session_object = self._create_session_object(session_data, session)
        request = self._create_semantic_input_request(session_object, interpretations)
        response = self._make_request(request)
        return response

    def request_passivity(self, session, session_data=None):
        # type: (str, dict) -> dict
        session_object = self._create_session_object(session_data, session)
        request = {"version": PROTOCOL_VERSION, "session": session_object, "request": {"passivity": {}}}
        response = self._make_request(request)
        return response

    def _create_session_object(self, session_data=None, session_id=None):
        session = copy(session_data) if session_data else {}
        if session_id:
            session["session_id"] = session_id
        return session

    def _create_text_input_request(self, session, utterance):
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

    def _create_speech_input_request(self, session, hypotheses):
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

    def _create_semantic_input_request(self, session, interpretations):
        return {
            "version": PROTOCOL_VERSION,
            "session": session,
            "request": {
                "semantic_input": {
                    "interpretations": [{
                        "modality": interpretation.modality,
                        "moves": [{
                            "ddd": move.ddd,
                            "perception_confidence": move.perception_confidence,
                            "understanding_confidence": move.understanding_confidence,
                            "semantic_expression": move.semantic_expression,
                        } for move in interpretation.moves],
                        "utterance": interpretation.utterance,
                    } for interpretation in interpretations],
                }
            }
        }  # yapf: disable

    def start_session(self, session_data=None):
        # type: (dict) -> dict
        session_object = session_data or {}
        request = {"version": PROTOCOL_VERSION, "session": session_object, "request": {"start_session": {}}}
        response = self._make_request(request)
        return response

    def _make_request(self, request_body):
        data_as_json = json.dumps(request_body)
        headers = {'Content-type': 'application/json'}
        json_encoded_response = requests.post(self._url, data=data_as_json, headers=headers)
        try:
            response = json_encoded_response.json()
        except ValueError:
            raise InvalidResponseError("Expected a valid JSON response but got %s." % json_encoded_response)

        if "error" in response:
            description = response["error"]["description"]
            raise TDMRuntimeException(description)

        return response
