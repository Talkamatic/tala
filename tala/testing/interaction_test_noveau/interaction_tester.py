import uuid
import re
import json

from tala.model.interpretation import Interpretation
from tala.model.input_hypothesis import InputHypothesis
from tala.model.common import Modality
from tala.model.user_move import UserMove, DDDSpecificUserMove
from tala.utils.tdm_client import TDMClient

from tala.testing.interaction_test_noveau.comparison import StringComparison, MoveComparison

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


class InteractionTester():
    def __init__(self, port):
        self._session_id = f"interaction-tester-session-{str(uuid.uuid4())}"
        self._initialize_session_object()
        self._port = port

    def _initialize_session_object(self):
        self._session_data = {"session_id": self._session_id}

    def start_session(self, session_data=None):
        if session_data:
            self._session_data = session_data
        self._latest_response = self._client.start_session(self._session_data)
        self._session_data = self._latest_response[SESSION]

    def run_testcase(self, case):
        self._initialize_testcase(case)
        self.start_session()
        self.line_number = 0
        success = True
        for entry in case["interaction"]:
            self.line_number += 1
            if entry[SPEAKER] == USER:
                success = self._do_user_turn(entry)
            elif entry[SPEAKER] == SYSTEM:
                success = self._do_system_turn(entry)
            if not success:
                return self._create_response(self._result)
        self._buffer_output('=== End interaction test ===')
        self._result = {"success": True}
        return self._create_response(self._result)

    def _initialize_testcase(self, testcase):
        self._output_buffer = OutputBuffer()
        self._ddd_name = testcase["target_ddd"]
        url = self._patch_url_with_port(testcase["url"])
        self._client = TDMClient(url)
        self._test_name = testcase["name"]
        self._buffer_output(f'\n=== Begin interaction test "{self._test_name}" ===')

    def _patch_url_with_port(self, url):
        if self._port:
            new_url = re.sub(r"^(https?:[^:]*):\d+/(.+)", rf"\1:{self._port}/\2", url)
            return new_url
        return url

    def _buffer_output(self, output):
        self._output_buffer.add(output)

    def _print_buffer(self):
        print(str(self._output_buffer))

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
            self._buffer_output(f"U> {utterance if utterance else json.dumps(interpretations)}")
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
        return True

    def _request_semantic_input(self, interpretations, entities=None):
        self._latest_response = self._client.request_semantic_input(interpretations, self._session_data, entities)
        self._update_session_data()

    def _request_passivity(self):
        self._latest_response = self._client.request_passivity(self._session_data)
        self._update_session_data()

    def _request_speech_input(self, utterance):
        hypotheses = [InputHypothesis(utterance, 1.0)]
        self._latest_response = self._client.request_speech_input(hypotheses, self._session_data)
        self._update_session_data()

    def _update_session_data(self):
        self._session_data = self._latest_response["session"]

    def _create_user_move(self, move):
        if self._ddd_name:
            return DDDSpecificUserMove(self._ddd_name, move, 1.0, 1.0)
        return UserMove(move, 1.0, 1.0)

    def _do_system_turn(self, system_entry):
        if EXPECTED_PASSIVITY in system_entry and self._passivity_mismatch(system_entry[EXPECTED_PASSIVITY]):
            return self._create_passivity_mismatch_description(system_entry[EXPECTED_PASSIVITY])
        if MOVE_CONTENT in system_entry:
            return self._assert_system_moves_are_matched_by(system_entry[MOVE_CONTENT])
        if SPEECH_CONTENT in system_entry:
            return self._assert_system_utterance_is_matched_by(system_entry[SPEECH_CONTENT])

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
        actual_move_content = self._latest_response[OUTPUT][MOVES]
        comparison = MoveComparison(actual_move_content, expected_move_content)
        if not comparison.match():
            self._result = {"success": False, "failure_description": comparison.mismatch_description()}
            self._buffer_output(comparison.mismatch_description())
            return False
        self._buffer_output(f"S> {json.dumps(actual_move_content)}")
        return True

    def _assert_system_utterance_is_matched_by(self, expected_speech_content):
        actual_utterance_content = self._latest_response[OUTPUT][UTTERANCE]
        comparison = StringComparison(actual_utterance_content, expected_speech_content)
        if not comparison.match():
            self._result = {"success": False, "failure_description": comparison.mismatch_description()}
            self._buffer_output(comparison.mismatch_description())
            return False
        self._buffer_output(f"S> {actual_utterance_content}")
        return True

    def _create_response(self, response):
        response["transcript"] = str(self._output_buffer)
        return response
