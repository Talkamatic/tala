# -*- coding: utf-8 -*-

import unittest

from tala.nl.gf import utils


class BindTokensTestCase(unittest.TestCase):
    def test_base_case(self):
        self._when_bind_tokens(["what", utils.BIND, "'s", "the", "time"])
        self._then_result_is(["what's", "the", "time"])

    def test_no_bind(self):
        self._when_bind_tokens(["what", "is", "the", "time"])
        self._then_result_is(["what", "is", "the", "time"])

    def test_multiple_binds(self):
        self._when_bind_tokens(["what", utils.BIND, "'s", "john", utils.BIND, "'s", "number"])
        self._then_result_is(["what's", "john's", "number"])

    def _when_bind_tokens(self, tokens):
        self._result = utils.bind_tokens(tokens)

    def _then_result_is(self, expected_result):
        self.assertEquals(expected_result, self._result)


class str_phrase_test_case(unittest.TestCase):
    def test_base_case(self):
        self.assert_phrase_to_string(
            ["calling", "alex", "berman"],
            "calling alex berman")

    def test_closing_punctuation(self):
        self.assert_phrase_to_string(
            ["okay", "."],
            "okay.")
        self.assert_phrase_to_string(
            ["okay", "?"],
            "okay?")
        self.assert_phrase_to_string(
            ["okay", "!"],
            "okay!")

    def test_comma(self):
        self.assert_phrase_to_string(
            ["okay", ",", "so"],
            "okay, so")

    def test_bind_genitive(self):
        self.assert_phrase_to_string(
            ["berman", utils.BIND, "'", utils.BIND, "s"],
            "berman's")

    def test_bind_between_word_and_comma(self):
        self.assert_phrase_to_string(
            ["berman", utils.BIND, ",", "alex"],
            "berman, alex")

    def assert_phrase_to_string(self, tokens, expected_string):
        self.assertEquals(expected_string, utils.str_phrase(tokens))


class GFTests(unittest.TestCase):
    def test_tokenise(self):
        self.assertEquals(['pred', '(', 'arg', ')'],
                          utils.tokenise('pred(arg)'))

    def test_tokenise_with_string_constant(self):
        self.assertEquals(['you', 'said', '_placeholder_0_', '.'],
                          utils.tokenise('you said _placeholder_0_.'))

    def test_tokenise_genitive(self):
        self.assertEquals(["Alex's"],
                          utils.tokenise("Alex's"))

    def test_tokenise_contraction(self):
        self.assertEquals(["don't"],
                          utils.tokenise("don't"))

    def test_tokenise_time_expressions(self):
        self.assertEquals(["1:30", "10:30"],
                          utils.tokenise("1:30 10:30"))

    def test_tokenise_time_expressions_negative(self):
        self.assertEquals(
            [":", "30", "10:30", "3", "101", ":", "30", "19", ":", "1"],
            utils.tokenise(":30 10:303 101:30 19:1"))

    def test_tokenise_with_magic_wording(self):
        self.assertEquals(["a", "message"],
                          utils.tokenise("a message"))

    def test_tokenise_am_pm(self):
        self.assertEquals(["p.m.", "2:10", "a.m."],
                          utils.tokenise("p.m. 2:10 a.m."))

    def test_tokenise_am_pm_and_magic_wordings(self):
        self.assertEquals(["send", "a", "message", "at", "2", "p.m."],
                          utils.tokenise("send a message at 2 p.m."))

    def test_tokenisation_doesnt_split_at_hyphen(self):
        self.assertEquals(["Berlin-Tegel"], utils.tokenise("Berlin-Tegel"))

    def test_dont_split_7bit_encoded_tokens(self):
        string = u"ställa klockan"
        expected_tokens = [u"ställa", "klockan"]
        self.assertEquals(expected_tokens, utils.tokenise(string))
