import fnmatch
import json
import re
import unittest

import structlog

from tala.model.input_hypothesis import InputHypothesis
from tala.model.event_notification import EventNotification
from tala.utils.tdm_client import TDMClient, TDMRuntimeException
from tala.model.user_move import UserMove  # noqa: F401
from tala.model.interpretation import InterpretationWithoutUtterance, Interpretation  # noqa: F401
from tala.model.common import Modality


class EventNotReceivedException(Exception):
    pass


class InvalidConfidenceException(Exception):
    pass


class UnsupportedTurn(Exception):
    pass


class UnexpectedMoveFormatException(Exception):
    pass


class InteractionTestingTestCase(unittest.TestCase):
    def __init__(self, test, environment_or_url):
        self._test = test
        self._logger = structlog.get_logger(__name__)
        self._tdm_client = TDMClient(environment_or_url)

        method_name = self._ensure_name_can_be_used_as_python_method(test.name)
        self._create_test_method(method_name)
        unittest.TestCase.__init__(self, method_name)

        self._last_system_output_response = None
        self._detected_unexpected_passivity = False

    @property
    def name(self):
        return self._test.name

    @property
    def session_id(self):
        return self._last_system_output_response["session"]["session_id"]

    @staticmethod
    def _ensure_name_can_be_used_as_python_method(name):
        return re.sub(r"\W", "_", name)

    def _create_test_method(self, name):
        setattr(self, name, self.perform)

    def perform(self):
        self._logger.debug(f"Running interaction test '{self._test.name}' from file '{self._test.filename}'")
        self._start_session()
        for turn in self._test.turns:
            try:
                self._perform(turn)
            except TDMRuntimeException as exception:
                self._raise_and_log_assertion_error(
                    f"On line {turn.line_number} of {self._test.filename},\n\nencountered an error:\n  {exception}"
                )

    def _perform(self, turn):
        if turn.is_system_output_turn:
            self._handle_system_output_turn(turn)
        elif turn.is_user_input_turn:
            self._simulate_user_input(turn)
        elif turn.is_user_passivity_turn:
            self._simulate_user_passivity(turn)
        elif turn.is_event_turn:
            self._handle_event_notification(turn)
        else:
            raise UnsupportedTurn("Expected one of the supported turns but got '%s'." % turn)

    def _start_session(self):
        self._last_system_output_response = self._tdm_client.start_session()

    def _handle_system_output_turn(self, turn):
        if turn.is_system_utterance_turn:
            self._expect_system_utterance(turn)
        elif turn.is_system_moves_turn:
            self._expect_system_moves(turn)
        else:
            raise UnsupportedTurn("Expected one of the supported system output turns but got '%s'." % turn)

    def _simulate_user_input(self, turn):
        self._logger.debug("Simulating user input")
        if turn.is_recognition_hypotheses_turn:
            self._handle_recognition_hypotheses(turn)
        elif turn.is_user_interpretation_turn:
            self._handle_user_moves(turn)
        else:
            raise UnsupportedTurn("Expected one of the supported user input turns but got '%s'." % turn)

    def _handle_recognition_hypotheses(self, turn):
        self._last_system_output_response = self._send_natural_language_input_request(turn.hypotheses)

    def _handle_user_moves(self, turn):
        def interpretation(moves, utterance, modality):
            if utterance:
                modality = modality or Modality.SPEECH
                return Interpretation(moves, modality, utterance=utterance)
            modality = modality or Modality.OTHER
            return InterpretationWithoutUtterance(moves, modality)

        moves = [self._create_move(move_as_string) for move_as_string in turn.moves]
        interpretations = [interpretation(moves, turn.utterance, turn.modality)]
        self._last_system_output_response = self._tdm_client.request_semantic_input(self.session_id, interpretations)

    def _create_move(self, move):
        def is_semantic_expression(move):
            return isinstance(move, str)

        def is_move_object(move):
            return isinstance(move, dict)

        if is_move_object(move):
            return self._move_from_dict(move)
        if is_semantic_expression(move):
            return UserMove(move, perception_confidence=1.0, understanding_confidence=1.0)
        raise UnexpectedMoveFormatException(f"Expected either a semantic expression or a JSON object, but got {move}")

    def _move_from_dict(self, move):
        perception_confidence = move.get("perception_confidence", 1.0)
        understanding_confidence = move.get("understanding_confidence", 1.0)
        semantic_expression = move["semantic_expression"]
        return UserMove(
            semantic_expression,
            perception_confidence=perception_confidence,
            understanding_confidence=understanding_confidence
        )

    def _simulate_user_passivity(self, turn):
        self._logger.debug("Simulating user passivity")
        if self._last_system_output_response and \
           self._last_system_output_response["output"]["expected_passivity"] is not None:
            self._last_system_output_response = self._tdm_client.request_passivity(self.session_id)
        else:
            self._detected_unexpected_passivity = True
            self._line_number_of_unexpected_passivity = turn.line_number

    def _expect_system_utterance(self, system_utterance_turn):
        self._logger.debug("%s._expect_system_utterance(%s)" % (self.__class__.__name__, str(system_utterance_turn)))
        if self._detected_unexpected_passivity:
            self._raise_assertion_error_for_unexpected_passivity(system_utterance_turn)
        self._has_system_output_turn_been_processed = True
        actual_utterance = self._get_system_utterance()
        self._assert_system_utterance_matches(
            system_utterance_turn.utterance, actual_utterance, system_utterance_turn.line_number
        )

    def _expect_system_moves(self, system_moves_turn):
        self._logger.debug("%s._expect_system_moves(%s)" % (self.__class__.__name__, str(system_moves_turn)))
        if self._detected_unexpected_passivity:
            self._raise_assertion_error_for_unexpected_passivity(system_moves_turn)
        self._has_system_output_turn_been_processed = True
        actual_moves = self._get_system_moves()
        self._assert_system_moves_equals(system_moves_turn.moves, actual_moves, system_moves_turn.line_number)

    def _format_output(self, output):
        if isinstance(output, list):
            return json.dumps(output)
        return output

    def _raise_assertion_error_for_unexpected_passivity(self, system_turn):
        raise AssertionError(
            "\n\nOn line %d of %s,\n" % (system_turn.line_number, self._test.filename) +
            "expected:\n  S> %s\n\n" % self._format_output(system_turn.output) +
            "in response to\n  U>\non line %d\n\n" % self._line_number_of_unexpected_passivity +
            "but the system didn't expect user passivity."
        )

    def _raise_and_log_assertion_error(self, error_string):
        self._logger.debug("Assertion error: %s" % error_string)
        raise AssertionError(error_string)

    def _get_system_utterance(self):
        actual_utterance = self._last_system_output_response["output"]["utterance"]
        self._logger.debug("Got system utterance %r" % actual_utterance)
        self._last_system_output_response = self._last_system_output_response
        return actual_utterance

    def _get_system_moves(self):
        actual_moves = self._last_system_output_response["output"]["moves"]
        self._logger.debug(f"Got system moves {actual_moves!r}")
        return actual_moves

    def _assert_system_utterance_matches(self, pattern, utterance, line_number):
        if not fnmatch.fnmatch(utterance, pattern):
            self._fail_with_mismatch(line_number, pattern, utterance)

    def _assert_system_moves_equals(self, expected_moves, actual_moves, line_number):
        if not expected_moves == actual_moves:
            self._fail_with_mismatch(line_number, expected_moves, actual_moves)

    def _fail_with_mismatch(self, line_number, expected, actual):
        self._raise_and_log_assertion_error(
            "On line %d of %s,\n\nexpected:\n  S> %s\n\nbut got:\n  S> %s" %
            (line_number, self._test.filename, self._format_output(expected), self._format_output(actual))
        )

    def _send_natural_language_input_request(self, hypotheses_tuples):
        hypotheses = [
            InputHypothesis(utterance, self._parse_score(score_as_string))
            for utterance, score_as_string in hypotheses_tuples
        ]
        return self._tdm_client.request_speech_input(self.session_id, hypotheses)

    def _parse_score(self, score):
        if score is None:
            return 1.0
        utterance_string_and_confidence_matcher = r"^\$(?P<level>\w+)|(?P<explicit>\d*\.\d+)?$"
        m = re.search(utterance_string_and_confidence_matcher, score)
        confidence_level_name = m.group("level")
        if confidence_level_name:
            raise NotImplementedError("Explicit names of confidence levels are not supported in this version.")
        explicit_score = m.group("explicit")
        if explicit_score:
            return float(explicit_score)
        raise InvalidConfidenceException("Invalid formatting of confidence: %s" % score)

    def _handle_event_notification(self, event_turn):
        if event_turn.is_notify_started_turn:
            self._last_system_output_response = self._tdm_client.request_event_notification(
                self.session_id, EventNotification(event_turn.action, EventNotification.STARTED, event_turn.parameters)
            )
        else:
            raise UnsupportedTurn("Expected one of the supported event turns but got '%s'." % event_turn)


class StringComparison(object):
    def __init__(self, string, pattern):
        self._string = string
        self._pattern = pattern
        self._match = self._string_matches_pattern(string, pattern)

    def match(self):
        return self._match

    def _string_matches_pattern(self, string, pattern):
        content = re.escape(pattern).replace(r'\*', '.*')
        re_pattern = f"^{content}$"
        return re.search(re_pattern, string, re.MULTILINE | re.DOTALL)

    def mismatch_description(self):
        return "expected:\n---\n%s\n---\nbut got:\n---\n%s" % (
            self._mismatch_position_description_for_pattern(), self._mismatch_position_description_for_string()
        )

    def _mismatch_position_description_for_pattern(self):
        position = self._get_mismatch_position()
        if position > 0:
            pattern_prefix = self._pattern[0:position]
            pattern_suffix = self._pattern[position:]
            return "%s======== HERE ========%s" % (pattern_prefix, pattern_suffix)
        else:
            return self._pattern

    def _mismatch_position_description_for_string(self):
        position = self._get_mismatch_position()
        length = len(self._string)
        while length > 0:
            if self._string_matches_pattern(self._string[0:length], self._pattern[0:position]):
                string_prefix = self._string[0:length]
                string_suffix = self._string[length:]
                return "%s======== HERE? ========%s" % (string_prefix, string_suffix)
            length = length - 1
        return self._string

    def _get_mismatch_position(self):
        length = len(self._pattern) - 1
        while length > 0:
            if self._string_matches_pattern(self._string, self._pattern[0:length] + "*"):
                return length
            length = length - 1
        return 0
