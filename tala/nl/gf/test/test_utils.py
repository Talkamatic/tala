# -*- coding: utf-8 -*-

import pytest
import unittest

from tala.nl.gf import utils

NL_PLACEHOLDER = utils.nl_user_answer_placeholder_of_sort("mock_sort", 5)
NL_PLACEHOLDER_2 = utils.nl_user_answer_placeholder_of_sort("mocksort2", 99)

SEM_PLACEHOLDER = utils.semantic_user_answer_placeholder_of_sort("mock_sort", 5)
SEM_PLACEHOLDER_2 = utils.semantic_user_answer_placeholder_of_sort("mocksort2", 99)


@pytest.mark.parametrize(
    "unformatted_string, placeholder, empty_string", [
        ["zldknfb %s", NL_PLACEHOLDER, ""],
        ["zldknfb %s lsdgfnkj", NL_PLACEHOLDER, ""],
        ["zldknfb %s %s lsdgfnkj", (NL_PLACEHOLDER, NL_PLACEHOLDER_2), ("", "")],
    ])
def test_remove_nl_placeholder_from_string(unformatted_string, placeholder, empty_string):
    original = unformatted_string % placeholder
    expected = unformatted_string % empty_string
    actual = utils.remove_nl_placeholders_from_string(original)
    assert expected.split() == actual.split()


@pytest.mark.parametrize(
    "unformatted_string, placeholder, empty_string", [
        ["zldknfb %s", SEM_PLACEHOLDER, ""],
        ["zldknfb %s lsdgfnkj", SEM_PLACEHOLDER, ""],
        ["zldknfb %s %s lsdgfnkj", (SEM_PLACEHOLDER, SEM_PLACEHOLDER_2), ("", "")],
    ])
def test_remove_sem_placeholder_from_string(unformatted_string, placeholder, empty_string):
    original = unformatted_string % placeholder
    expected = unformatted_string % empty_string
    actual = utils.remove_sem_placeholders_from_string(original)
    assert expected.split() == actual.split()


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


class PlaceholderPreprocessingTestCase(unittest.TestCase):
    def test_preprocess_strings_double_quotes(self):
        self.when_preprocess_placeholders(
            'answer(comment("a comment"))')
        self.then_expect(
            preprocessed_string="answer(comment(_placeholder_0_))",
            table={"_placeholder_0_": "a comment"})

    def when_preprocess_placeholders(self, string):
        self._string_to_preprocess = string
        self._actual_table = {}
        self._actual_preprocessed_string = utils.preprocess_placeholders(string, self._actual_table)

    def then_expect(self, preprocessed_string, table):
        self.assertEquals(preprocessed_string, self._actual_preprocessed_string)
        self.assertEquals(table, self._actual_table)

    def test_preprocess_strings_single_quotes(self):
        self.when_preprocess_placeholders(
            "answer(comment('a comment'))")
        self.then_expect(
            preprocessed_string="answer(comment(_placeholder_0_))",
            table={"_placeholder_0_": "a comment"})

    def test_preprocess_strings_mixed_quotes_no_action(self):
        self.when_preprocess_placeholders(
            "answer(comment('10:05\"))")
        self.then_expect_unchanged_string()

    def then_expect_unchanged_string(self):
        self.assertEquals(self._string_to_preprocess, self._actual_preprocessed_string)

    def test_preprocess_datetime(self):
        self.when_preprocess_placeholders(
            'report(ServiceResultProposition(BookFlight, [desired_time(datetime(2018-04-11T22:00:00.000Z))], '
            'SuccessfulServiceAction()))')
        self.then_expect(
            preprocessed_string='report(ServiceResultProposition(BookFlight, [desired_time(_placeholder_0_)], '
                                'SuccessfulServiceAction()))',
            table={"_placeholder_0_": "04/11/2018 10:00 PM"})

    def test_preprocess_integers_doesnt_touch_plain_digits(self):
        self.when_preprocess_placeholders("222")
        self.then_expect_unchanged_string()

    def test_preprocess_integers_processes_more_than_2_digits_in_parens(self):
        self.when_preprocess_placeholders("(222)")
        self.then_expect(preprocessed_string="(_placeholder_0_)", table={"_placeholder_0_": "222"})

    def test_preprocess_integers_skips_2_or_less_digits_in_parens(self):
        self.when_preprocess_placeholders("(22)")
        self.then_expect(preprocessed_string="(22)", table={})

    def test_preprocess_multiple_sorts_in_mixed_order(self):
        self.when_preprocess_placeholders(
            'mock_move('
            'integer_predicate_1(123),'
            'datetime_predicate_1(datetime(2001-01-01T01:01:00.000Z)),'
            'string_predicate_1("string 1"),'
            'integer_predicate_2(456),'
            'datetime_predicate_2(datetime(2002-02-02T02:02:00.000Z)),'
            'string_predicate_2("string 2")'
            ')')
        self.then_expect(
            preprocessed_string='mock_move('
                                'integer_predicate_1(_placeholder_2_),'
                                'datetime_predicate_1(_placeholder_4_),'
                                'string_predicate_1(_placeholder_0_),'
                                'integer_predicate_2(_placeholder_3_),'
                                'datetime_predicate_2(_placeholder_5_),'
                                'string_predicate_2(_placeholder_1_)'
                                ')',
            table={"_placeholder_2_": "123",
                   "_placeholder_4_": "01/01/2001 01:01 AM",
                   "_placeholder_0_": "string 1",
                   "_placeholder_3_": "456",
                   "_placeholder_5_": "02/02/2002 02:02 AM",
                   "_placeholder_1_": "string 2"})


class GenericPlaceholderReplacementTestCase(unittest.TestCase):
    def test_base_case(self):
        self._when_replace_placeholders_is_invoked(
            "the comment has _placeholder_0_ likes", {"_placeholder_0_": "222"})
        self._then_result_is("the comment has 222 likes")

    def _when_replace_placeholders_is_invoked(self, string, table):
        self._result = utils.replace_placeholders(string, table)

    def _then_result_is(self, expected_result):
        self.assertEquals(expected_result, self._result)

    def test_placeholder_not_as_its_own_token(self):
        self._when_replace_placeholders_is_invoked(
            "_placeholder_0_: this is not a valid temperature",
            {"_placeholder_0_": "222"})
        self._then_result_is("222: this is not a valid temperature")


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
