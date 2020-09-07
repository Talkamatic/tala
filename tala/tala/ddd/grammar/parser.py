from xml.etree import ElementTree


class GrammarParser(object):
    @classmethod
    def parse(cls, grammar_string):
        return ElementTree.fromstring(grammar_string)
