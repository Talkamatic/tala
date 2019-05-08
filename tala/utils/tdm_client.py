import json

import requests

from tala.utils.observable import Observable

PROTOCOL_VERSION = 2.0


class InvalidResponseError(Exception):
    pass


class TDMRuntimeException(Exception):
    pass


class TDMClient(Observable):
    def __init__(self, url):
        super(TDMClient, self).__init__()
        self._url = url

    def request_text_input(self, session, utterance):
        request = self._create_text_input_request(session, utterance)
        response = self._make_request(request)
        return response

    def request_speech_input(self, session, hypotheses):
        request = self._create_speech_input_request(session, hypotheses)
        response = self._make_request(request)
        return response

    def request_passivity(self, session):
        request = {"version": PROTOCOL_VERSION, "session": {"session_id": session}, "request": {"type": "passivity"}}
        response = self._make_request(request)
        return response

    def _create_text_input_request(self, session, utterance):
        return {
            "version": PROTOCOL_VERSION,
            "session": {
                "session_id": session
            },
            "request": {
                "type": "input"
            },
            "input": {
                "modality": "text",
                "utterance": utterance,
            }
        }

    def _create_speech_input_request(self, session, hypotheses):
        return {
            "version": PROTOCOL_VERSION,
            "session": {
                "session_id": session
            },
            "request": {
                "type": "input"
            },
            "input": {
                "modality":
                "speech",
                "hypotheses": [{
                    "utterance": hypothesis.utterance,
                    "confidence": hypothesis.confidence,
                } for hypothesis in hypotheses],
            }
        }

    def start_session(self):
        request = {"version": PROTOCOL_VERSION, "request": {"type": "start_session"}}
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
