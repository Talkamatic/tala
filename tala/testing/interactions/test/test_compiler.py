# -*- coding: utf-8 -*-

import unittest
from io import StringIO

from mock import patch, ANY, call

from tala.testing.interactions import compiler
from tala.testing.interactions.compiler import InteractionTestCompiler

TESTS_FILENAME = "tdm/test/test_interactiontest.txt"


class FileParsingTest(unittest.TestCase):
    def test_is_turn(self):
        self.assertEqual(True, InteractionTestCompiler._is_turn("U> "))
        self.assertEqual(True, InteractionTestCompiler._is_turn("S> ['ask(?X.goal(X)))']"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("U> ['answer(yes)']"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("U> hello there $CHECK"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("S> hello there"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("G> <sdfkjsdf>"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("G> <a>\n<b>\n</a>"))
        self.assertEqual(False, InteractionTestCompiler._is_turn(""))
        self.assertEqual(False, InteractionTestCompiler._is_turn("sdflkjsdf"))
        self.assertEqual(True, InteractionTestCompiler._is_turn("G> "))


class CompilationTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
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
        self.assertTrue(actual_turn.is_user_passivity_turn)
        self.assertEqual(expected_line_number, actual_turn.line_number)

    def _get_actual_single_turn_from_single_test(self):
        self.assertEqual(1, len(self._result))
        actual_test = self._result[0]
        self.assertEqual(1, len(actual_test.turns))
        return actual_test.turns[0]

    def test_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_is_user_moves()

    def test_moves_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_moves(["request(make_reservation)", "answer(paris)"])

    def test_properties_of_user_moves(self):
        self.when_compile("""\
--- mock name
U> ["request(make_reservation)", "answer(paris)"]
""")
        self.then_result_has_properties(expected_line_number=2)

    def then_result_is_user_moves(self):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertTrue(actual_turn.is_user_moves_turn)

    def then_result_has_moves(self, expected_moves):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertEqual(expected_moves, actual_turn.moves)

    def then_result_has_properties(self, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertEqual(expected_line_number, actual_turn.line_number)

    def test_system_moves(self):
        self.when_compile("""\
--- mock name
S> ["request(make_reservation)", 'answer(paris)']
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
        self.then_result_has_properties(expected_line_number=2)

    def then_result_is_system_moves(self):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertTrue(actual_turn.is_system_moves_turn)

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
        self.assertTrue(actual_test.turns[0].is_system_output_turn)
        self.assertTrue(actual_test.turns[1].is_user_moves_turn)

    def test_system_utterance(self):
        self.when_compile("""\
--- mock name
S> Welcome.
""")
        self.then_result_has_system_utterance_turn_with_properties("Welcome.", 2)

    def then_result_has_system_utterance_turn_with_properties(self, expected_utterance, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertTrue(actual_turn.is_system_utterance_turn)
        self.assertEqual(expected_utterance, actual_turn.utterance)
        self.assertEqual(expected_line_number, actual_turn.line_number)

    def test_single_recognition_hypothis(self):
        self.when_compile("""\
--- mock name
U> to paris
""")
        self.then_result_has_recognition_hypotheses_turn_with_properties([("to paris", None)], 2)

    def then_result_has_recognition_hypotheses_turn_with_properties(self, expected_hypotheses, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertTrue(actual_turn.is_recognition_hypotheses_turn)
        self.assertEqual(expected_hypotheses, actual_turn.hypotheses)
        self.assertEqual(expected_line_number, actual_turn.line_number)

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

    def test_gui_output_single_line(self):
        self.when_compile("""\
--- mock name
G> <single_line_xml />
""")
        self.then_result_has_gui_output_turn_with_properties("<single_line_xml />", 2)

    def then_result_has_gui_output_turn_with_properties(self, expected_pattern, expected_line_number):
        actual_turn = self._get_actual_single_turn_from_single_test()
        self.assertTrue(actual_turn.is_gui_output_turn)
        self.assertEqual(expected_pattern, actual_turn.pattern)
        self.assertEqual(expected_line_number, actual_turn.line_number)

    def test_gui_output_multiple_lines(self):
        self.when_compile("""\
--- mock name
G> <multi_line_xml>\\
<some_content />\\
</multi_line_xml>
""")
        self.then_result_has_gui_output_turn_with_properties("<multi_line_xml>\n<some_content />\n</multi_line_xml>", 4)

    def test_gui_output_with_line_comment(self):
        self.when_compile(
            """\
--- mock name
G> <multi_line_xml>\\
#<commented_line />\\
<some_content />\\
</multi_line_xml>
"""
        )
        self.then_result_has_gui_output_turn_with_properties("<multi_line_xml>\n<some_content />\n</multi_line_xml>", 5)

    def test_empty_gui_output(self):
        self.when_compile("""\
--- mock name
G>
""")
        self.then_result_has_gui_output_turn_with_properties("", 2)

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
        self.assertTrue(actual_turn.is_notify_started_turn)
        self.assertEqual(expected_action, actual_turn.action)
        self.assertEqual(expected_parameters, actual_turn.parameters)
        self.assertEqual(expected_line_number, actual_turn.line_number)

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
        self.assertEqual(self._result, expected_result)

    def test_pretty_hypothesis(self):
        self._given_hypothesis("an utterance", 1.0)
        self._when_formatting_hypotheses()
        self._then_the_result_is("U> an utterance")

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
