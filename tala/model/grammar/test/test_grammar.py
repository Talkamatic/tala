# -*- coding: utf-8 -*-

from contextlib import contextmanager
import os
import warnings

from mock import Mock, patch
import pytest

from tala.model.ddd import DDD
from tala.model.grammar import grammar
from tala.model.grammar.grammar import Grammar, GrammarForRGL, UnexpectedAnswerFormatException
from tala.ddd.grammar.parser import GrammarParser
from tala.model.grammar.intent import Question, Request, Answer
from tala.model.grammar.required_entity import RequiredPropositionalEntity, RequiredSortalEntity
from tala.model.ontology import Ontology
from tala.model.sort import Sort


class TestGrammar(object):
    def setup_method(self):
        self._mocked_ddd = self._create_mocked_ddd()
        self._grammar = None
        self._grammar_path = None
        self._result = None

    def _create_mocked_ddd(self):
        ontology = Mock(spec=Ontology)
        ontology.get_individuals_of_sort.return_value = []
        ddd = Mock(spec=DDD)
        ddd.ontology = ontology
        return ddd

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [(GrammarForRGL, "tala/model/grammar/test/grammar_for_rgl_example.xml"),
                                 (Grammar, "tala/model/grammar/test/grammar_example.xml")]
    )
    def test_requests_of_action(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_individuals_in_ontology(
            sort="contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_requests_of_action("call")
        self.then_result_is([
            Request("call", ["make a call"], []),
            Request("call", ["call ", ""], [
                RequiredSortalEntity("contact"),
            ]),
            Request("call", ["make a call to ", ""], [
                RequiredPropositionalEntity("selected_contact_to_call"),
            ]),
        ])

    def given_ddd_name(self, name):
        self._mocked_ddd.name = name

    def given_individuals_in_ontology(self, sort, individuals):
        mocked_sort = Mock(spec=Sort)
        mocked_sort.get_name.return_value = sort
        self._mocked_ddd.ontology.individual_sort.return_value = mocked_sort
        self._mocked_ddd.ontology.get_individuals_of_sort.return_value = individuals

    def given_grammar_file(self, path):
        absolute_path = os.path.abspath(path)
        self._grammar_path = absolute_path

    def given_grammar_from_class(self, GrammarClass):
        with open(self._grammar_path, 'r') as grammar_file:
            grammar_string = grammar_file.read()
        grammar_root = GrammarParser.parse(grammar_string)
        self._grammar = GrammarClass(grammar_root, self._grammar_path)

    def when_fetching_requests_of_action(self, action):
        self._result = list(self._grammar.requests_of_action(action))

    def then_result_is(self, expected_result):
        assert expected_result == self._result

    @contextmanager
    def expect_warnings(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            yield

    def when_fetching_questions_of_predicate_then_warns(self, predicate, expected_warning):
        with patch("%s.warnings" % grammar.__name__) as mocked_warnings:
            self.when_fetching_questions_of_predicate(predicate)
            mocked_warnings.warn.assert_called_once_with(expected_warning)

    def when_fetching_requests_of_action_then_warns(self, action, expected_warning):
        with patch("%s.warnings" % grammar.__name__) as mocked_warnings:
            self.when_fetching_requests_of_action(action)
            mocked_warnings.warn.assert_called_once_with(expected_warning)

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [(GrammarForRGL, "tala/model/grammar/test/grammar_for_rgl_example.xml"),
                                 (Grammar, "tala/model/grammar/test/grammar_example.xml")]
    )
    def test_questions_of_predicate(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_individuals_in_ontology(
            sort="contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_questions_of_predicate("phone_number_of_contact")
        self.then_result_is([
            Question("phone_number_of_contact", ["tell me a phone number"], []),
            Question("phone_number_of_contact", ["what is ", "'s number"], [
                RequiredSortalEntity("contact"),
            ]),
            Question(
                "phone_number_of_contact", ["tell me ", "'s number"], [
                    RequiredPropositionalEntity("selected_contact_of_phone_number"),
                ]
            ),
        ])

    def when_fetching_questions_of_predicate(self, predicate):
        self._result = list(self._grammar.questions_of_predicate(predicate))

    @pytest.mark.parametrize(
        "GrammarClass,grammar,results", [
            (
                    GrammarForRGL,
                    "tala/model/grammar/test/grammar_for_rgl_example.xml",
                    [["John"],
                     [u"约翰"],
                     ["Lisa"],
                     ["Mary"],
                     ["Andy"],
                     [u"安迪"]]
            ),
            (
                    Grammar,
                    "tala/model/grammar/test/grammar_example.xml",
                    [["John", "Johnny"],
                     [u"约翰"],
                     ["Lisa"],
                     ["Mary"],
                     ["Andy"],
                     [u"安迪"]]
            )
        ])  # yapf: disable
    def test_entries_of_individual(self, GrammarClass, grammar, results):
        self.given_ddd_name("rasa_test")
        self.given_individuals_in_ontology(
            sort="contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_entries_of_individuals([
            "contact_john",
            "contact_john_chi",
            "contact_lisa",
            "contact_mary",
            "contact_andy",
            "contact_andy_chi",
        ])
        self.then_result_is(results)

    def when_fetching_entries_of_individuals(self, individuals):
        self._result = [self._grammar.entries_of_individual(individual) for individual in individuals]

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_with_single_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_single_entries.xml"),
        ]
    )
    def test_single_question_entry(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_questions_of_predicate("phone_number_of_contact")
        self.then_result_is([
            Question("phone_number_of_contact", ["tell me a phone number"], []),
        ])

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_with_single_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_single_entries.xml"),
        ]
    )
    def test_single_action_entry(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        with self.expect_warnings():
            self.when_fetching_requests_of_action("top")
        self.then_result_is([
            Request("top", ["never mind"], []),
        ])

    def test_action_without_plain_text_entries_warns(self):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file("tala/model/grammar/test/grammar_example_without_plain_text_entries.xml")
        self.given_grammar_from_class(Grammar)
        self.when_fetching_requests_of_action_then_warns(
            "call",
            "Grammar ignores element 'action' with attributes {'name': 'call'} since there are no plain text items"
        )

    def test_request_in_rgl_without_plain_text_entries_warns(self):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file("tala/model/grammar/test/grammar_example_for_rgl_without_plain_text_entries.xml")
        self.given_grammar_from_class(GrammarForRGL)
        self.when_fetching_requests_of_action_then_warns(
            "call",
            "GrammarForRGL ignores element 'request' with attributes {'action': 'call'} since it has no <utterance>"
        )

    def test_question_without_plain_text_entries_warns(self):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file("tala/model/grammar/test/grammar_example_without_plain_text_entries.xml")
        self.given_grammar_from_class(Grammar)
        self.when_fetching_questions_of_predicate_then_warns(
            "phone_number_of_contact", "Grammar ignores element 'question' with attributes "
            "{'predicate': 'phone_number_of_contact', 'speaker': 'user'} since there are no plain text items"
        )

    def test_question_in_rgl_without_plain_text_entries_warns(self):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file("tala/model/grammar/test/grammar_example_for_rgl_without_plain_text_entries.xml")
        self.given_grammar_from_class(GrammarForRGL)
        self.when_fetching_questions_of_predicate_then_warns(
            "phone_number_of_contact", "GrammarForRGL ignores element 'question' with attributes "
            "{'predicate': 'phone_number_of_contact', 'speaker': 'user'} since it has no <utterance>"
        )

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_with_answer_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_with_answer_entries.xml"),
        ]
    )
    def test_answers(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_user_answers()
        self.then_result_is([
            Answer(["in ", " hours ", " minutes"], [
                RequiredPropositionalEntity("hours"),
                RequiredPropositionalEntity("minutes"),
            ]),
            Answer(["", " hours"], [
                RequiredPropositionalEntity("hours"),
            ]),
            Answer(["in ", " minutes"], [
                RequiredPropositionalEntity("minutes"),
            ]),
            Answer(["", " minutes"], [
                RequiredPropositionalEntity("minutes"),
            ]),
            Answer(["in ", ""], [
                RequiredPropositionalEntity("minutes"),
            ]),
        ])

    def when_fetching_user_answers(self):
        self._result = list(self._grammar.answers())

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_with_answer_entry_without_predicate.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_with_answer_entry_without_predicate.xml"),
        ]
    )
    def test_answer_entry_without_propositional_fails_fast(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_user_answers_then_exception_is_raised_matching(
            UnexpectedAnswerFormatException, "Expected at least one <[\w]+ .../> in every item in "
            "<answer speaker=\"user\"> but found some without"
        )

    def when_fetching_user_answers_then_exception_is_raised_matching(self, expected_exception, expected_pattern):
        with pytest.raises(expected_exception, match=expected_pattern):
            self.when_fetching_user_answers()

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_with_string_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_with_string_entries.xml"),
        ]
    )
    def test_string_entries(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_strings_of_predicate("comment")
        self.then_result_is([
            "i like movies",
            "i hate movies",
        ])

    def when_fetching_strings_of_predicate(self, predicate):
        with self.expect_warnings():
            self._result = list(self._get_strings_of_predicate(predicate))

    def _get_strings_of_predicate(self, predicate):
        return self._grammar.strings_of_predicate(predicate)

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_without_string_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_without_string_entries.xml"),
        ]
    )
    def test_no_string_entries(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_strings_of_predicate("comment")
        self.then_result_is([])

    @pytest.mark.parametrize(
        "GrammarClass,grammar", [
            (GrammarForRGL, "tala/model/grammar/test/grammar_example_for_rgl_without_string_entries.xml"),
            (Grammar, "tala/model/grammar/test/grammar_example_without_string_entries.xml"),
        ]
    )
    def test_warnings_with_no_string_entries(self, GrammarClass, grammar):
        self.given_ddd_name("rasa_test")
        self.given_grammar_file(grammar)
        self.given_grammar_from_class(GrammarClass)
        self.when_fetching_strings_of_predicate_then_warning_is_issued_matching(
            "comment",
            """Expected training examples for predicate 'comment' of sort 'string' but found none. Add them with:

<string predicate="comment">
  <one-of>
    <item>an example</item>
    <item>another example</item>
  </one-of>
</string>"""
        )

    def when_fetching_strings_of_predicate_then_warning_is_issued_matching(self, predicate, expected_warning):
        with patch("%s.warnings" % grammar.__name__) as mocked_warnings:
            self.when_fetching_strings_of_predicate(predicate)
            mocked_warnings.warn.assert_called_once_with(expected_warning)
