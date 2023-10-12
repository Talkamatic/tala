import unittest
from xml.etree import ElementTree

from tala.ddd.grammar.parser import GrammarParser


class GrammarParserTest(unittest.TestCase):
    def test_parse_returns_etree(self):
        self.when_parse("<mock_root_element/>")
        self.then_result_is_etree_element()

    def when_parse(self, string):
        self._result = GrammarParser.parse(string)

    def then_result_is_etree_element(self):
        self.assertIsInstance(self._result, ElementTree.Element)
