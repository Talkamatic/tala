import uuid
import re
import json
import warnings
import requests
import time

import structlog

from tala.model.interpretation import Interpretation
from tala.model.input_hypothesis import InputHypothesis
from tala.model.common import Modality
from tala.model.user_move import UserMove, DDDSpecificUserMove
from tala.utils.tdm_client import TDMClient

from tala.testing.interaction.comparison import StringComparison, MoveComparison
from tala.testing.interaction.stream_listener import StreamListener

from tala.utils.func import configure_stdout_logging, getenv

SPEAKER = "speaker"
USER = "user"
SYSTEM = "system"
TEST_NAME = "name"
MOVE_CONTENT = "move_content"
INTERPRETATIONS = "interpretations"
SPEECH_CONTENT = "speech_content"
OUTPUT = "output"
MOVES = "moves"
SESSION = "session"
EXPECTED_PASSIVITY = "expected_passivity"
UTTERANCE = "utterance"

TDM_PROTOCOL_VERSION = "3.4"

DEFAULT_DEVICE_ID = "interaction-tester"

logger = structlog.get_logger(__name__)
log_level = getenv("LOG_LEVEL", "INFO")
configure_stdout_logging(log_level)


class InteractionTesterException(BaseException):
    pass


class QueryException(BaseException):
    pass


class ZeroDivisionWarning(UserWarning):
    pass


class OutputBuffer:
    def __init__(self):
        self._content_lines = []

    def add(self, new_content):
        self._content_lines.append(new_content)

    def __str__(self):
        output = ""
        for line in self._content_lines:
            output += line + "\n"
        return output


class InteractionTester:
    def __init__(self, port, device_id=DEFAULT_DEVICE_ID, use_streaming=False):
        self._session_id = f"interaction-tester-session-{str(uuid.uuid4())}"
        self._device_id = device_id
        self._port = port
        self._use_streaming = use_streaming

    def start_session(self, session_data=None):
        if session_data:
            self._session_data = session_data
        else:
            self._initialize_session_object()
        self._session_data["neural"] = self._neural
        self._latest_response = self._client.start_session(self._session_data)
        logger.info("starting session", session_id=self._session_id)
        self._session_data = self._latest_response[SESSION]

    def _initialize_session_object(self):
        self._session_data = {"device_id": self._device_id, "session_id": self._session_id}

    def run_testcase(self, case):
        self._initialize_testcase(case)
        self._start_clock()
        self.start_session()
        success = True
        self._previous_entry_type = None
        for entry in case["interaction"]:
            if entry[SPEAKER] == USER:
                success = self._do_user_turn(entry)
            elif entry[SPEAKER] == SYSTEM:
                success = self._do_system_turn(entry)
            if not success:
                self._stop_clock()
                return self._create_response(self._result)
            self._previous_entry_type = entry[SPEAKER]
        self._buffer_output('=== End interaction test ===')
        self._stop_clock()
        self._result = {"success": True}
        return self._create_response(self._result)

    def _initialize_testcase(self, testcase):
        self._output_buffer = OutputBuffer()
        self._ddd_name = testcase["target_ddd"]
        self._neural = testcase.get("neural")
        self._start_date = {time.asctime()}
        url = self._patch_url_with_port(testcase["url"])
        self._client = TDMClient(url)
        self._test_name = testcase["name"]
        self._buffer_output(f'\n=== Begin interaction test "{self._test_name}" ===')
        self._request_times = []
        self._stream_start_times = []
        self._stream_end_times = []

    def _start_stream_listener(self):
        if self._use_streaming:
            self._stream_listener_thread = StreamListener(self._session_id)
            self._stream_listener_thread.start()
            self._stream_listener_thread.stream_started.wait()

    def _start_clock(self):
        self._start_time = time.time()
        self._turn_times = []

    def _patch_url_with_port(self, url):
        if self._port:
            new_url = re.sub(r"^(https?:[^:]*):\d+/(.+)", rf"\1:{self._port}/\2", url)
            return new_url
        return url

    def _buffer_output(self, output):
        logger.info("interaction test output", output=output)
        self._output_buffer.add(output)

    def _print_buffer(self):
        print(str(self._output_buffer))

    def check_for_consecutive_speaker(self, speaker):
        if self._previous_entry_type == speaker:
            raise Exception(f"Two consecutive entries define '{speaker}' input")

    def _do_user_turn(self, user_entry):
        def create_interpretation(moves, utterance_content=""):
            return Interpretation([self._create_user_move(move) for move in moves], Modality.OTHER, utterance_content)

        def create_interpretations_from_dicts(dict_list, utterance):
            interpretations = []
            for entry in dict_list:
                interpretations.append(
                    Interpretation([create_user_move(move) for move in entry["moves"]], entry["modality"], utterance)
                )
            return interpretations

        def create_user_move(move_dict):
            return DDDSpecificUserMove(
                move_dict["ddd"], move_dict["semantic_expression"], move_dict["perception_confidence"],
                move_dict["understanding_confidence"]
            )

        def interpretations_as_json(interpretations):
            return json.dumps([interpretation.as_json() for interpretation in interpretations])

        self.check_for_consecutive_speaker(USER)

        start_time = time.time()

        if MOVE_CONTENT in user_entry:
            moves = user_entry[MOVE_CONTENT]
            self._buffer_output(f"U> {json.dumps(moves)}")
            utterance = user_entry.get("utterance", "")
            interpretation = create_interpretation(moves, utterance)
            self._request_semantic_input([interpretation])
        elif INTERPRETATIONS in user_entry:
            utterance = user_entry.get("utterance", "")
            interpretations = create_interpretations_from_dicts(user_entry[INTERPRETATIONS], utterance)
            entities = user_entry.get("entities", [])
            self._buffer_output(f"U> {utterance if utterance else interpretations_as_json(interpretations)}")
            self._request_semantic_input(interpretations, entities=entities)
        elif EXPECTED_PASSIVITY in user_entry:
            expected_passivity = user_entry[EXPECTED_PASSIVITY]
            self._buffer_output(f"U> {{expected_passivity={expected_passivity}}}")
            if self._passivity_mismatch(user_entry[EXPECTED_PASSIVITY]):
                self._create_passivity_mismatch_description(user_entry[EXPECTED_PASSIVITY])
                return False
            self._request_passivity()
        elif SPEECH_CONTENT in user_entry:
            utterance = user_entry.get(SPEECH_CONTENT)
            self._buffer_output(f"U> {utterance}")
            self._request_speech_input(utterance)
        else:
            raise Exception("Nothing to do in user entry:", user_entry)
        end_time = time.time()
        self._turn_times.append(end_time - start_time)
        return True

    def _request_semantic_input(self, interpretations, entities=None):
        self._start_stream_listener()
        self._request_times.append(time.time())
        self._latest_response = self._client.request_semantic_input(interpretations, self._session_data, entities)
        self._add_streamed_output()
        self._update_session_data()

    def _add_streamed_output(self):
        if self._use_streaming:
            self._latest_response[OUTPUT][UTTERANCE] = self._stream_listener_thread.system_utterance
            self._stream_start_times.append(self._stream_listener_thread.streaming_started)
            self._stream_end_times.append(self._stream_listener_thread.streaming_ended)
            self._stream_listener_thread = None

    def _request_passivity(self):
        self._start_stream_listener()
        self._request_times.append(time.time())
        self._latest_response = self._client.request_passivity(self._session_data)
        self._add_streamed_output()
        self._update_session_data()

    def _request_speech_input(self, utterance):
        hypotheses = [InputHypothesis(utterance, 1.0)]
        self._start_stream_listener()
        self._request_times.append(time.time())
        self._latest_response = self._client.request_speech_input(hypotheses, self._session_data)
        self._add_streamed_output()
        self._update_session_data()

    def _update_session_data(self):
        self._session_data = self._latest_response["session"]

    def _create_user_move(self, move):
        if self._ddd_name:
            return DDDSpecificUserMove(self._ddd_name, move, 1.0, 1.0)
        return UserMove(move, 1.0, 1.0)

    def _do_system_turn(self, system_entry):
        self.check_for_consecutive_speaker(SYSTEM)
        while self._is_request_for_service_invocation():
            self._make_service_request_and_create_tdm_request_with_service_invocation_result()
        else:
            if EXPECTED_PASSIVITY in system_entry and self._passivity_mismatch(system_entry[EXPECTED_PASSIVITY]):
                return self._create_passivity_mismatch_description(system_entry[EXPECTED_PASSIVITY])
            if MOVE_CONTENT in system_entry:
                return self._assert_system_moves_are_matched_by(system_entry[MOVE_CONTENT])
            if SPEECH_CONTENT in system_entry:
                return self._assert_system_utterance_is_matched_by(system_entry[SPEECH_CONTENT])

    def _is_request_for_service_invocation(self):
        if self._is_request_for_service_query_invocation():
            return True
        elif self._is_request_for_service_validation_invocation():
            return True
        elif self._is_request_for_service_action_invocation():
            return True

    def _is_request_for_service_query_invocation(self):
        if "predicate" in self._latest_response:
            return True

    def _is_request_for_service_validation_invocation(self):
        if "validator_name" in self._latest_response:
            return True

    def _is_request_for_service_action_invocation(self):
        if "action_name" in self._latest_response:
            return True

    def _make_service_request_and_create_tdm_request_with_service_invocation_result(self):
        if self._is_request_for_service_query_invocation():
            self._make_service_request_and_create_tdm_request_with_service_query_invocation_result()
        elif self._is_request_for_service_validation_invocation():
            self._make_service_request_and_create_tdm_request_with_service_validator_invocation_result()
        elif self._is_request_for_service_action_invocation():
            self._make_service_request_and_create_tdm_request_with_service_action_invocation_result()

    def _make_service_request_and_create_tdm_request_with_service_query_invocation_result(self):
        predicate = self._latest_response["predicate"]
        url = self._latest_response["url"]
        parameters = self._latest_response["parameters"]
        session = self._latest_response["session"]
        min_results = self._latest_response["min_results"]
        max_results = self._latest_response["max_results"]

        logger.info("invoking service query", predicate=predicate, parameters=parameters)
        query_results = self._make_query_to_http_service(predicate, url, parameters, min_results, max_results, session)
        if query_results["status"] != "success":
            raise QueryException(
                f"HTTP service query failed: url: {url}, parameters:{parameters}, result: {query_results}"
            )

        logger.info("requesting dme with", results=query_results)
        self._make_results_request_for_dme(
            "query_results", {
                "predicate": predicate,
                "url": url,
                "parameters": parameters,
                "ddd_name": self._latest_response["ddd_name"],
                "results": query_results["data"]["result"],
                "earlier_results": self._latest_response["earlier_results"]
            }
        )

    def _make_results_request_for_dme(self, type_, results):
        request = {
            "version": TDM_PROTOCOL_VERSION,
            "request": self._latest_response["original_request"],
            "session": self._latest_response["session"]
        }
        request["request"][type_] = results
        self._latest_response = self._client.make_request(request)

    def _make_query_to_http_service(self, name, url, parameters, min_results, max_results, session):
        data = {
            "session": session,
            "min_results": min_results,
            "max_results": max_results,
            "request": {
                "type": "query",
                "name": name,
                "parameters": parameters,
            }
        }
        logger.info("making query request to http service", url=url, data=data)
        response = requests.post(url, data=json.dumps(data), headers={"Content-type": "application/json"})
        try:
            response_dict = json.loads(response.text)
        except BaseException:
            logger.exception("Exception when loading response from service")
            raise QueryException(
                f"Response to service request is not JSON: request_data='{data}', response='{response.text}'"
            )
        logger.info("query response from http service:", response_dict)
        return response_dict

    def _make_service_request_and_create_tdm_request_with_service_validator_invocation_result(self):
        validator_name = self._latest_response["validator_name"]
        url = self._latest_response["url"]
        parameters = self._latest_response["parameters"]
        session = self._latest_response["session"]

        logger.info("invoking service validator", validator=validator_name, parameters=parameters)
        query_results = self._validate_in_http_service(validator_name, url, parameters, session)
        self._make_results_request_for_dme(
            "validation_results", {
                "validator_name": validator_name,
                "url": url,
                "parameters": parameters,
                "ddd_name": self._latest_response["ddd_name"],
                "result": query_results,
                "earlier_results": self._latest_response["earlier_results"]
            }
        )

    def _validate_in_http_service(self, name, url, parameters, session):
        data = {
            "session": session,
            "request": {
                "type": "validator",
                "name": name,
                "parameters": parameters,
            }
        }
        response = requests.post(url, data=json.dumps(data), headers={"Content-type": "application/json"})
        response_dict = json.loads(response.text)
        return response_dict

    def _make_service_request_and_create_tdm_request_with_service_action_invocation_result(self):
        action_name = self._latest_response["action_name"]
        url = self._latest_response["url"]
        parameters = self._latest_response["parameters"]
        session = self._latest_response["session"]

        logger.info("invoking service request", action=action_name, parameters=parameters)
        action_result = self._perform_action_in_http_service(action_name, url, parameters, session)
        self._make_results_request_for_dme(
            "action_results", {
                "action_name": action_name,
                "url": url,
                "parameters": parameters,
                "ddd_name": self._latest_response["ddd_name"],
                "result": action_result,
                "earlier_results": self._latest_response["earlier_results"]
            }
        )

    def _perform_action_in_http_service(self, name, url, parameters, session):
        data = {
            "session": session,
            "request": {
                "type": "action",
                "name": name,
                "parameters": parameters,
            }
        }
        response = requests.post(url, data=json.dumps(data), headers={"Content-type": "application/json"})
        response_dict = json.loads(response.text)
        return response_dict

    def _passivity_mismatch(self, expected_passivity_value):
        actual_value = self._latest_response[OUTPUT].get(EXPECTED_PASSIVITY)
        if not actual_value and actual_value != 0.0:
            return True
        if expected_passivity_value is True:
            return False
        if expected_passivity_value == actual_value:
            return False
        return True

    def _create_passivity_mismatch_description(self, expected_passivity_value):
        actual_value = self._latest_response[OUTPUT].get(EXPECTED_PASSIVITY, False)
        if actual_value is None:
            if expected_passivity_value is True:
                self._result = {
                    "success": False,
                    "failure_description": "Expected an expected_passivity, but none was set."
                }
            else:
                self._result = {
                    "success": False,
                    "failure_description": f"Expected expected_passivity={expected_passivity_value}, " +
                    "but no expected_passivity was set."
                }
        else:
            self._result = {
                "success": False,
                "failure_description": f"Expected expected_passivity={expected_passivity_value}, " +
                f"but actual expected_passivity was {actual_value}."
            }

    def _assert_system_moves_are_matched_by(self, expected_move_content):
        assert OUTPUT in self._latest_response, f"No {OUTPUT} in {self._latest_response}"
        actual_move_content = self._latest_response[OUTPUT][MOVES]
        comparison = MoveComparison(actual_move_content, expected_move_content)
        if not comparison.match():
            self._result = {"success": False, "failure_description": comparison.mismatch_description()}
            self._buffer_output(comparison.mismatch_description())
            return False
        if self._turn_times:
            self._buffer_output(f"S> {json.dumps(actual_move_content)}: {self._turn_times[-1]:.2f} s")
        else:
            self._buffer_output(f"S> {json.dumps(actual_move_content)}")

        return True

    def _assert_system_utterance_is_matched_by(self, expected_speech_content):
        assert OUTPUT in self._latest_response, f"No {OUTPUT} in {self._latest_response}"
        actual_utterance_content = self._latest_response[OUTPUT][UTTERANCE]

        comparison = StringComparison(actual_utterance_content, expected_speech_content)
        if not comparison.match():
            self._result = {"success": False, "failure_description": comparison.mismatch_description()}
            self._buffer_output(comparison.mismatch_description())
            return False
        if self._turn_times:
            self._buffer_output(f"S> {actual_utterance_content}: {self._turn_times[-1]:.2f} s")
        else:
            self._buffer_output(f"S> {actual_utterance_content}")
        return True

    def _create_response(self, response):
        def get_stream_onset_times():
            onsets = []
            for request_sent, first_token in zip(self._request_times, self._stream_start_times):
                try:
                    onsets.append(first_token - request_sent)
                except TypeError:
                    pass
            return onsets

        def get_streaming_times():
            streaming_times = []
            for first_token, end_stream in zip(self._stream_start_times, self._stream_end_times):
                try:
                    streaming_times.append(end_stream - first_token)
                except TypeError:
                    pass
            return streaming_times

        onset_times = get_stream_onset_times()
        streaming_times = get_streaming_times()

        response["name"] = self._test_name
        response["session_id"] = self._session_id

        response["transcript"] = str(self._output_buffer)

        response["start_time"] = self._start_time
        response["running_time"] = self._end_time - self._start_time

        if self._use_streaming:
            try:
                response["avg_stream_start"] = sum(onset_times) / len(onset_times)
            except ZeroDivisionError:
                response["avg_stream_start"] = -1
                warnings.warn(
                    "Attempted division by zero when calculating average stream start.\n"
                    "\tresponse[\"avg_stream_start\"] = sum(onset_times) / len(onset_times)\n"
                    f"\tonset_times = {onset_times}"
                    f"\trequest_times = {self._request_times}"
                    f"\tstream_start_times = {self._stream_start_times}", ZeroDivisionWarning
                )

            response["max_stream_start"] = max(onset_times)

            try:
                response["avg_streaming_time"] = sum(streaming_times) / len(streaming_times)
            except ZeroDivisionError:
                response["avg_streaming_time"] = -1
                warnings.warn(
                    "Attempted division by zero when calculating average stream time.\n"
                    "\tresponse[\"avg_streaming_time\"] = sum(streaming_times) / len(streaming_times)\n"
                    f"\tstreaming_times = {streaming_times}"
                    f"\tstream_start_times = {self._stream_start_times}"
                    f"\tstream_end_times = {self._stream_end_times}", ZeroDivisionWarning
                )
            response["max_streaming_time"] = max(streaming_times)

        response["avg_turn_time"] = sum(self._turn_times) / len(self._turn_times) if self._turn_times else 0
        response["max_turn_time"] = max(self._turn_times) if self._turn_times else 0

        return response

    def _stop_clock(self):
        self._end_time = time.time()
