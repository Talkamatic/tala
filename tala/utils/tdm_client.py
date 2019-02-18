import json

import requests

from tala.utils.observable import Observable

PROTOCOL_VERSION = 2.0


class InvalidResponseError(Exception):
    pass


class SessionNotStartedException(Exception):
    pass


class TDMRuntimeException(Exception):
    pass


class TDMClient(Observable):
    def __init__(self, url):
        super(TDMClient, self).__init__()
        self._url = url
        self._session_id = None

    def say(self, utterance):
        request = self._create_text_input_request(utterance)
        response = self._make_request(request)
        return response

    def request_passivity(self):
        if self._session_id is None:
            raise SessionNotStartedException("Expected the session to be started, but it wasn't")

        request = {
            "version": PROTOCOL_VERSION,
            "session": {
                "session_id": self._session_id
            },
            "request": {
                "type": "passivity"
            }
        }
        response = self._make_request(request)
        return response

    def _create_text_input_request(self, utterance):
        if self._session_id is None:
            raise SessionNotStartedException("Expected the session to be started, but it wasn't")

        return {
            "version": PROTOCOL_VERSION,
            "session": {
                "session_id": self._session_id
            },
            "request": {
                "type": "input"
            },
            "input": {
                "modality": "text",
                "utterance": utterance,
            }
        }

    def start_session(self):
        request = {
            "version": PROTOCOL_VERSION,
            "request": {
                "type": "start_session"
            }
        }
        response = self._make_request(request)
        self._session_id = response["session"]["session_id"]
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

        if "session" in response:
            session_data = response["session"]
            if "session_id" in session_data:
                self._session_id = session_data["session_id"]

        return response
