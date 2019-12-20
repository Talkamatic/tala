import difflib
import unittest

from tala.ddd.maker.ddd_py_to_xml import GrammarConverter
from tala.nl.gf.grammar_entry_types import Constants, Node
from tala.nl.gf import rgl_grammar_entry_types as rgl_types


class MockGrammarConverter(GrammarConverter):
    def __init__(self):
        GrammarConverter.__init__(self, "mockup_ddd", "mockup_language")
        self._written_output = ""

    def _write(self, string):
        self._written_output += string

    def get_written_output(self):
        return self._written_output


class GrammarConversionTestCase(unittest.TestCase):
    def test_single_entry(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.ACTION, {"name": "top"},
                     [Node(Constants.ITEM, {}, ["main menu"])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <action name="top">main menu</action>
</grammar>
"""
        )

    def test_multiple_entries(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.ACTION, {"name": "top"},
                     [Node(Constants.ITEM, {}, ["main menu"])]),
                Node(Constants.ACTION, {"name": "buy"},
                     [Node(Constants.ITEM, {}, ["buy"])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <action name="top">main menu</action>

  <action name="buy">buy</action>
</grammar>
"""
        )

    def test_one_of(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.ACTION, {"name": "buy"}, [
                    Node(Constants.ONE_OF, {}, [
                        Node(Constants.ITEM, {}, ["buy"]),
                        Node(Constants.ITEM, {}, ["purchase"])])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <action name="buy">
    <one-of>
      <item>buy</item>
      <item>purchase</item>
    </one-of>
  </action>
</grammar>
"""
        )

    def test_predicate(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.PREDICATE, {"name": "price"},
                     [Node(Constants.ITEM, {}, ["price information"])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <question type="wh_question" speaker="all" predicate="price">price information</question>
</grammar>
"""
        )

    def test_user_question(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.USER_QUESTION, {"predicate": "price"},
                     [Node(Constants.ITEM, {}, ["price for travelling to ",
                                                Node(Constants.SLOT, {"sort": "city"})])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <question type="wh_question" predicate="price" speaker="user">price for travelling to <slot type="individual" predicate="price"/></question>
</grammar>
"""
        )

    def test_answer_combination(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.ANSWER_COMBINATION, {},
                     ["to ", Node(Constants.SLOT, {"sort": "city"})])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <answer speaker="user">to <slot sort="city"/></answer>
</grammar>
"""
        )

    def _given_grammar(self, grammar):
        self._grammar = grammar

    def _when_convert(self):
        self._converter = MockGrammarConverter()
        self._converter._generate_and_write_output(self._grammar)

    def _then_result_is(self, expected_result):
        actual_result = self._converter.get_written_output()
        if expected_result != actual_result:
            differ = difflib.Differ()
            diff = differ.compare(expected_result.split("\n"), actual_result.split("\n"))
            self.fail("\n".join(diff))

    def test_convert_greeting(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.GREETING, {}, [Node(Constants.ITEM, {}, ["Welcome to the Service!"])])
            ]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
<greeting>Welcome to the Service!</greeting></grammar>
"""
        )

    def test_convert_positive_sys_answer(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                     [Node(Constants.ITEM, {},
                           ["you have ", Node(Constants.SLOT, {"predicate": "frequent_flyer_points"}),
                            " frequent flyer points and are qualified for membership"])])
            ]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <answer speaker="system" predicate="qualified_for_membership" polarity="positive">you have <slot type="individual" predicate="frequent_flyer_points"/> frequent flyer points and are qualified for membership</answer>
</grammar>
"""
        )

    def test_convert_negative_sys_answer(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.NEGATIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                     [Node(Constants.ITEM, {}, ["you are not qualified for membership"])])
            ]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <answer speaker="system" predicate="qualified_for_membership" polarity="negative">you are not qualified for membership</answer>
</grammar>
"""
        )

    def test_multi_slot_system_answer(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.SYS_ANSWER, {"predicate": "next_membership_level"},
                     [Node(Constants.ITEM, {},
                           ["you need ", Node(Constants.SLOT, {"predicate": "next_membership_points"}),
                            " to reach ", Node(Constants.SLOT, {}), " level"])])
            ])
        )  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <answer speaker="system" predicate="next_membership_level">you need <slot type="individual" predicate="next_membership_points"/> to reach <slot type="individual" predicate="next_membership_level"/> level</answer>
</grammar>
"""
        )

    def test_utterance(self):
        self._given_grammar(
            Node(Constants.GRAMMAR, {}, [
                Node(Constants.SYS_QUESTION, {"predicate": "dest_city"},
                     [Node(rgl_types.UTTERANCE, {}, ["where do you want to go"])])]))  # yapf: disable
        self._when_convert()
        self._then_result_is(
            """<?xml version="1.0" encoding="utf-8"?>
<grammar>
  <question type="wh_question" predicate="dest_city" speaker="system">
    <utterance>where do you want to go</utterance>
  </question>
</grammar>
"""
        )
