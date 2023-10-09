# -*- coding: utf-8 -*-

import json
import pytest
import unittest
from io import StringIO

from mock import patch, ANY, call

from tala.testing.interactions import compiler
from tala.testing.interactions.compiler import InteractionTestCompiler, ParseException

TESTS_FILENAME = "tdm/test/test_interactiontest.txt"


class TestFileParsing:
    def test_is_turn(self):
        assert InteractionTestCompiler._is_turn("U> ")
        assert InteractionTestCompiler._is_turn("U> ''")
        assert InteractionTestCompiler._is_turn("S> ['ask(?X.goal(X)))']")
        assert InteractionTestCompiler._is_turn("U> ['answer(yes)']")
        assert InteractionTestCompiler._is_turn("U> hello there $CHECK")
        assert InteractionTestCompiler._is_turn("S> hello there")
        assert not InteractionTestCompiler._is_turn("")
        assert not InteractionTestCompiler._is_turn("sdflkjsdf")


class TestCompiler():
    def setup_method(self):
        self._compiler = InteractionTestCompiler()

    @patch("%s.InteractionTest" % compiler.__name__)
    def test_name(self, InteractionTest):
        self.when_compile("""\
--- first test
S> system utterance

--- second test
U> user input
""")
        self.then_interaction_tests_created_with(InteractionTest, ["first test", "second test"])

    def then_interaction_tests_created_with(self, InteractionTest, expected_names):
        expected_calls = [call(ANY, name, ANY) for name in expected_names]
        InteractionTest.assert_has_calls(expected_calls, any_order=True)

    def when_compile(self, string):
        file_ = StringIO(string)
        self._result = self._compiler.compile_interaction_tests("mock_test_file.txt", file_)

    def test_user_passivity(self):
        self.when_compile("""\
--- mock name
U>
""")
        self.then_result_has_user_passivity_turn_with_properties(2)

    def then_result_has_user_passivity_turn_with_properties(self, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_user_passivity_turn
        assert expected_line_number == actual_turn.line_number

    def _get_actual_single_turn_from_single_test(self):
        assert 1 == len(self._result)
        actual_test = self._result[0]
        assert 1 == len(actual_test.turns)
        return actual_test.turns[0]

    def test_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_is_user_interpretation()

    def test_moves_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_moves(["request(make_reservation)", "answer(paris)"])

    def test_rich_user_moves(self):
        self.when_compile(
            """\
--- mock name
U> [{"semantic_expression": "request(make_reservation)", "understanding_confidence": 0.12, "perception_confidence": 0.23}, {"semantic_expression": "answer(paris)", "understanding_confidence": 0.45, "perception_confidence": 0.67}]
"""
        )
        self.then_result_has_moves([{
            "semantic_expression": "request(make_reservation)",
            "understanding_confidence": 0.12,
            "perception_confidence": 0.23
        }, {
            "semantic_expression": "answer(paris)",
            "understanding_confidence": 0.45,
            "perception_confidence": 0.67
        }])

    def test_line_number_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_line_number(2)

    def test_utterance_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")

        self.then_result_has_utterance(None)

    def test_modality_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")

        self.then_result_has_modality(None)

    def test_user_interpretation(self):
        self.when_compile(
            """\
--- mock name
U> {"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}
"""
        )
        self.then_result_is_user_interpretation()

    def test_user_interpretations(self):
        self.when_compile(
            """\
--- mock name
U> {"interpretations": [{"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}], "entitites": []}
"""
        )
        self.then_result_is_semantic_input()

    def then_result_is_semantic_input(self):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_user_semantic_input_turn

    @patch(f"{compiler.__name__}.json", autospec=True)
    def test_invalid_json(self, mock_json):
        self.given_json_loads_raises_decode_error(mock_json, "the error", doc="doc", pos=0)
        self.when_compile_then_exception_is_raised(
            string="""\
--- mock name
U> {"moves": []}
""",
            expected_exception_class=ParseException,
            expected_message=r"Expected valid JSON on line 2 of 'mock_test_file.txt' but encountered a decoding error."
            r"\n\n  Line 2: {\"moves\": \[\]}\n\n  Error: 'the error: line 1 column 1 \(char 0\)'"
        )

    def given_json_loads_raises_decode_error(self, mock_json, *args, **kwargs):
        mock_json.decoder.JSONDecodeError = json.decoder.JSONDecodeError
        mock_json.loads.side_effect = json.decoder.JSONDecodeError(*args, **kwargs)

    def when_compile_then_exception_is_raised(self, string, expected_exception_class, expected_message):
        with pytest.raises(expected_exception_class, match=expected_message):
            self.when_compile(string)

    def test_moves_of_user_interpretation(self):
        self.when_compile(
            """\
--- mock name
U> {"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}
"""
        )
        self.then_result_has_moves(["request(make_reservation)", "answer(paris)"])

    def test_line_number_of_user_interpretation(self):
        self.when_compile(
            """\
--- mock name
U> {"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}
"""
        )
        self.then_result_has_line_number(2)

    def test_utterance_of_user_interpretation(self):
        self.when_compile(
            """\
--- mock name
U> {"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}
"""
        )

        self.then_result_has_utterance("an utterance")

    def test_modality_of_user_interpretation(self):
        self.when_compile(
            """\
--- mock name
U> {"moves": ["request(make_reservation)", "answer(paris)"], "utterance": "an utterance", "modality": "speech"}
"""
        )

        self.then_result_has_modality("speech")

    def then_result_is_user_interpretation(self):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_user_interpretation_turn

    def then_result_has_moves(self, expected_moves):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert expected_moves == actual_turn.moves

    def then_result_has_line_number(self, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert expected_line_number == actual_turn.line_number

    def then_result_has_utterance(self, expected):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert expected == actual_turn.utterance

    def then_result_has_modality(self, expected):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert expected == actual_turn.modality

    def test_system_moves(self):
        self.when_compile("""\
--- mock name
S> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_is_system_moves()

    def test_moves_of_system_moves(self):
        self.when_compile("""\
--- mock name
S> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_moves(["request(make_reservation)", "answer(paris)"])

    def test_properties_of_system_moves(self):
        self.when_compile("""\
--- mock name
S> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_line_number(expected_line_number=2)

    def then_result_is_system_moves(self):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_system_moves_turn

    def test_multiple_turns(self):
        self.when_compile(
            """\
--- mock name
S> What do you want to do?
U> ["request(make_reservation)", "answer(paris)"]
"""
        )
        self.then_turns_are_system_utterance_and_user_moves()

    def then_turns_are_system_utterance_and_user_moves(self):
        actual_test = self._result[0]
        assert actual_test.turns[0].is_system_output_turn
        assert actual_test.turns[1].is_user_interpretation_turn

    def test_system_utterance(self):
        self.when_compile("""\
--- mock name
S> Welcome.
""")
        self.then_result_has_system_utterance_turn_with_properties("Welcome.", 2)

    def then_result_has_system_utterance_turn_with_properties(self, expected_utterance, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_system_utterance_turn
        assert expected_utterance == actual_turn.utterance
        assert expected_line_number == actual_turn.line_number

    def test_single_recognition_hypothis(self):
        self.when_compile("""\
--- mock name
U> to paris
""")
        self.then_result_has_recognition_hypotheses_turn_with_properties([("to paris", None)], 2)

    @pytest.mark.parametrize("utterance", ["''", '""'])
    def test_empty_user_utterance(self, utterance):
        self.when_compile(f"""\
--- mock name
U> {utterance}
""")
        self.then_result_has_recognition_hypotheses_turn_with_properties([("", None)], 2)

    def then_result_has_recognition_hypotheses_turn_with_properties(self, expected_hypotheses, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_recognition_hypotheses_turn
        assert expected_hypotheses == actual_turn.hypotheses
        assert expected_line_number == actual_turn.line_number

    def test_recognition_hypothesis_with_confidence_level(self):
        self.when_compile("""\
--- mock name
U> to paris $CHECK
""")
        self.then_result_has_recognition_hypotheses_turn_with_properties([("to paris", "$CHECK")], 2)

    def test_multiple_recognition_hypotheses(self):
        self.when_compile("""\
--- mock name
U> first hypothesis 0.6 | second hypothesis 0.5
""")
        self.then_result_has_recognition_hypotheses_turn_with_properties([("first hypothesis", "0.6"),
                                                                          ("second hypothesis", "0.5")], 2)

    def test_notify_started(self):
        self.when_compile(
            """\
--- mock name
Event> {"name": "AlarmRings", "status": "started", "parameters": {"alarm_hour": 7, "alarm_minute": 30}}
"""
        )
        self.then_result_has_notify_started_turn_with_properties("AlarmRings", {"alarm_hour": 7, "alarm_minute": 30}, 2)

    def then_result_has_notify_started_turn_with_properties(
        self, expected_action, expected_parameters, expected_line_number
    ):
        actual_turn = self._get_actual_single_turn_from_single_test()
        assert actual_turn.is_notify_started_turn
        assert expected_action == actual_turn.action
        assert expected_parameters == actual_turn.parameters
        assert expected_line_number == actual_turn.line_number

    def test_unicode_strings(self):
        self.when_compile("""\
--- mock name
S> Vad vill du göra?
""")
        self.then_result_has_system_utterance_turn_with_properties("Vad vill du göra?", 2)

    def test_empty_system_utterance(self):
        self.when_compile("""\
--- mock name
S>
""")
        self.then_result_has_system_utterance_turn_with_properties("", 2)


class PrettyFormattingTests(unittest.TestCase):
    def setUp(self):
        self._hypotheses = []
        self._system_utterance = None

    def test_pretty_hypotheses(self):
        self._given_hypothesis("first utterance", 0.9)
        self._given_hypothesis("second utterance", 0.8)
        self._when_formatting_hypotheses()
        self._then_the_result_is("U> first utterance 0.9 | second utterance 0.8")

    def _given_hypothesis(self, utterance, confidence):
        self._hypotheses.append((utterance, confidence))

    def _when_formatting_hypotheses(self):
        self._result = InteractionTestCompiler.pretty_hypotheses(self._hypotheses)

    def _then_the_result_is(self, expected_result):
        assert self._result == expected_result

    def test_pretty_passivity(self):
        self._when_formatting_passivity()
        self._then_the_result_is("U>")

    def _when_formatting_passivity(self):
        self._result = InteractionTestCompiler.pretty_passivity()

    def test_pretty_system_utterance(self):
        self._given_system_utterance("an utterance")
        self._when_formatting_system_utterance()
        self._then_the_result_is("S> an utterance")

    def _given_system_utterance(self, utterance):
        self._system_utterance = utterance

    def _when_formatting_system_utterance(self):
        self._result = InteractionTestCompiler.pretty_system_utterance(self._system_utterance)
