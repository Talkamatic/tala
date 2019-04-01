# -*- coding: utf-8 -*-

import os
import re
import shutil
import tempfile
import unittest

from mock import MagicMock, Mock, patch

from tala.model.ddd import DDD
from tala.model.grammar.grammar import GrammarBase
from tala.model.grammar.intent import Request, Question, Answer
from tala.model.grammar.required_entity import RequiredPropositionalEntity, RequiredSortalEntity
from tala.nl.languages import ENGLISH
from tala.model.domain import Domain
from tala.model.goal import ResolveGoal
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.ontology import Ontology
from tala.model.predicate import Predicate
from tala.model.question import WhQuestion
from tala.model.sort import Sort, CustomSort
from tala.nl.rasa.generating import generator
from tala.nl.rasa.generating.generator import RasaGenerator
from tala.nl.rasa.generating.examples import Examples, SortNotSupportedException


class GeneratorTestsBase(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="GeneratorTests")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._mocked_ddd = self._create_mocked_ddd()
        self._generator = None
        self._mocked_grammar = None
        self._grammar_reader_patcher = self._create_grammar_reader_patcher()
        self._result = None
        self._mocked_warnings = None

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)
        self._grammar_reader_patcher.stop()

    def _create_mocked_ddd(self):
        ontology = Mock(spec=Ontology)
        ontology.get_individuals_of_sort.return_value = list()
        ontology.get_ddd_specific_actions.return_value = set()
        ontology.get_sorts.return_value = dict()
        ontology.get_predicates.return_value = dict()
        ontology.get_predicate.side_effect = Exception()
        domain = Mock(spec=Domain)
        domain.get_all_resolve_goals.return_value = []
        ddd = Mock(spec=DDD)
        ddd.ontology = ontology
        ddd.domain = domain
        ddd.grammars = {}
        return ddd

    def _create_grammar_reader_patcher(self):
        patcher = patch("%s.GrammarReader" % generator.__name__, autospec=True)
        MockGrammarReader = patcher.start()
        MockGrammarReader.xml_grammar_exists_for_language.return_value = True
        return patcher

    def given_ddd_name(self, name):
        self._mocked_ddd.name = name

    def given_ontology(
        self,
        sort,
        individuals,
        predicate,
        is_builtin=False,
        is_integer_sort=False,
        is_string_sort=False,
        is_real_sort=False,
        is_datetime_sort=False
    ):
        mocked_sort = Mock(spec=Sort)
        mocked_sort.get_name.return_value = sort
        mocked_sort.is_builtin.return_value = is_builtin
        mocked_sort.is_integer_sort.return_value = is_integer_sort
        mocked_sort.is_string_sort.return_value = is_string_sort
        mocked_sort.is_real_sort.return_value = is_real_sort
        mocked_sort.is_domain_sort.return_value = False
        mocked_sort.is_datetime_sort.return_value = is_datetime_sort
        self._mocked_ddd.ontology.individual_sort.return_value = mocked_sort
        self._mocked_ddd.ontology.get_individuals_of_sort.return_value = individuals
        self._mocked_ddd.ontology.get_sorts.return_value = {sort: mocked_sort}
        self._mocked_ddd.ontology.get_sort.return_value = mocked_sort
        mocked_predicate = Mock(spec=Predicate)
        mocked_predicate.get_name.return_value = predicate
        mocked_predicate.getSort.return_value = mocked_sort
        self._mocked_ddd.ontology.get_predicates.return_value = {predicate: mocked_predicate}
        self._mocked_ddd.ontology.get_predicate.side_effect = None
        self._mocked_ddd.ontology.get_predicate.return_value = mocked_predicate

    def given_actions_in_ontology(self, actions):
        self._mocked_ddd.ontology.get_ddd_specific_actions.return_value = actions

    def given_mocked_grammar(self, requests=None, questions=None, individuals=None, answers=None, strings=None):
        self._mocked_grammar = Mock(spec=GrammarBase)
        self._mocked_grammar.requests_of_action.return_value = requests or []
        self._mocked_grammar.questions_of_predicate.return_value = questions or []
        self._mocked_grammar.answers.return_value = answers or []
        self._mocked_grammar.strings_of_predicate.return_value = strings or []
        individuals = individuals or {}

        def get_individual(name):
            return individuals[name]

        self._mocked_grammar.entries_of_individual.side_effect = get_individual
        self._mocked_ddd.grammars["eng"] = self._mocked_grammar

    def given_generator(self):
        self._generator = RasaGenerator(self._mocked_ddd, ENGLISH)

    def when_generate(self):
        self._result = self._generate()

    def _generate(self):
        return self._generator.generate()

    def when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
        self, expected_exception, expected_pattern
    ):
        try:
            self._generate()
            assert False, "%s not raised" % expected_exception
        except expected_exception as e:
            assert re.match(expected_pattern, str(e))

    def given_expected_plan_questions_in_domain(self, predicates):
        def resolve_goals_of_questions(questions):
            for question in questions:
                mocked_goal = Mock(spec=ResolveGoal)
                mocked_goal.get_question.return_value = question
                yield mocked_goal

        plan_questions = list(self._plan_questions(predicates))
        mocked_resolve_goals = list(resolve_goals_of_questions(plan_questions))
        self._mocked_ddd.domain.get_all_resolve_goals.return_value = mocked_resolve_goals

    def _plan_questions(self, predicates):
        for predicate_name, sort_name in predicates.iteritems():
            predicate = Predicate("mocked_ontology", predicate_name, CustomSort("mocked_ontology", sort_name))
            proposition = LambdaAbstractedPredicateProposition(predicate, "mocked_ontology")
            question = WhQuestion(proposition)
            yield question

    def then_result_matches(self, expected_contents):
        print self._result
        expected_pattern = re.escape(expected_contents)
        assert re.search(expected_pattern, self._result, re.UNICODE) is not None

    def given_mocked_warnings(self, mock_warnings):
        self._mocked_warnings = mock_warnings

    def then_warning_is_issued(self, expected_message):
        self._mocked_warnings.warn.assert_called_once_with(expected_message, UserWarning)


class UnsupportedBuiltinSortGeneratorTestCase(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)

    def test_generate_requests(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="real", predicate="selected_price", individuals=[], is_builtin=True, is_real_sort=True)
        self.given_actions_in_ontology({"purchase"})
        self.given_mocked_grammar(requests=self._requests_of_action("purchase", "selected_price"))
        self.given_generator()
        self.when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
            SortNotSupportedException, "Builtin sort 'real' is not yet supported together with RASA"
        )

    def _requests_of_action(self, action, required_predicate):
        return [
            Request(action, ["take a note that ", ""], [
                RequiredPropositionalEntity(required_predicate),
            ]),
        ]

    def test_generate_questions(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="real", predicate="selected_price", individuals=[], is_builtin=True, is_real_sort=True)
        self.given_expected_plan_questions_in_domain({"selected_price": "real"})
        self.given_mocked_grammar(questions=self._questions_of_predicate("selected_price", "real"))
        self.given_generator()
        self.when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
            SortNotSupportedException, "Builtin sort 'real' is not yet supported together with RASA"
        )

    def _questions_of_predicate(self, question_predicate, sort):
        return [
            Question(
                question_predicate, ["how long time remains of the ", " reminder"], [
                    RequiredSortalEntity(sort),
                ]
            ),
        ]

    def test_generate_answers(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="real", predicate="selected_price", individuals=[], is_builtin=True, is_real_sort=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
            SortNotSupportedException, "Builtin sort 'real' is not yet supported together with RASA"
        )


class CustomSortGeneratorTestCase(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)

    def given_ontology_with_individuals(
        self, sort, predicate, is_integer_sort=False, is_string_sort=False, is_real_sort=False
    ):
        individuals = [
            "contact_john",
            "contact_john_chi",
            "contact_lisa",
            "contact_mary",
            "contact_andy",
            "contact_andy_chi",
        ]
        super(CustomSortGeneratorTestCase,
              self).given_ontology(sort, individuals, predicate, is_integer_sort, is_string_sort, is_real_sort)

    def given_mocked_grammar_with_individuals(self, requests=None, questions=None, answers=None):
        individuals = {
            "contact_john": ["John", "Johnny"],
            "contact_john_chi": [u"约翰"],
            "contact_lisa": ["Lisa", "Elizabeth"],
            "contact_mary": ["Mary"],
            "contact_andy": ["Andy"],
            "contact_andy_chi": [u"安迪"],
        }
        super(CustomSortGeneratorTestCase, self).given_mocked_grammar(requests, questions, individuals, answers)

    def test_generate_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with_individuals(requests=self._requests_of_action(sort="call"))
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:action::call
- make a call
- call [John](sort.contact)
- call [Johnny](sort.contact)
- call [约翰](sort.contact)
- call [Lisa](sort.contact)
- call [Elizabeth](sort.contact)
- call [Mary](sort.contact)
- call [Andy](sort.contact)
- call [安迪](sort.contact)
"""
        )

    def _requests_of_action(self, sort=None, predicate=None):
        yield Request("call", ["make a call"], [])
        if sort is not None:
            yield Request("call", ["call ", ""], [
                RequiredSortalEntity("contact"),
            ])
        if predicate is not None:
            yield Request("call", ["make a call to ", ""], [
                RequiredPropositionalEntity("selected_contact_to_call"),
            ])

    def test_propositional_entities_excluded_from_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with_individuals(
            requests=self._requests_of_action(predicate="selected_contact_to_call")
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(u"""## intent:rasa_test:action::call
- make a call

""")

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_requests_with_propositional_entities_issue_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with_individuals(
            requests=self._requests_of_action(predicate="selected_contact_to_call")
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate "
            "'selected_contact_to_call'. Skipping this training data example."
        )

    def test_generate_requests_with_two_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="caller")
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with_individuals(
            requests=[
                Request(
                    "call", ["call ", " and say hi from ", ""], [
                        RequiredSortalEntity("contact"),
                        RequiredSortalEntity("contact"),
                    ]
                ),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:action::call
- call [John](sort.contact) and say hi from [John](sort.contact)
- call [John](sort.contact) and say hi from [Johnny](sort.contact)
- call [John](sort.contact) and say hi from [约翰](sort.contact)
- call [John](sort.contact) and say hi from [Lisa](sort.contact)
- call [John](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [John](sort.contact) and say hi from [Mary](sort.contact)
- call [John](sort.contact) and say hi from [Andy](sort.contact)
- call [John](sort.contact) and say hi from [安迪](sort.contact)
- call [Johnny](sort.contact) and say hi from [John](sort.contact)
- call [Johnny](sort.contact) and say hi from [Johnny](sort.contact)
- call [Johnny](sort.contact) and say hi from [约翰](sort.contact)
- call [Johnny](sort.contact) and say hi from [Lisa](sort.contact)
- call [Johnny](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [Johnny](sort.contact) and say hi from [Mary](sort.contact)
- call [Johnny](sort.contact) and say hi from [Andy](sort.contact)
- call [Johnny](sort.contact) and say hi from [安迪](sort.contact)
- call [约翰](sort.contact) and say hi from [John](sort.contact)
- call [约翰](sort.contact) and say hi from [Johnny](sort.contact)
- call [约翰](sort.contact) and say hi from [约翰](sort.contact)
- call [约翰](sort.contact) and say hi from [Lisa](sort.contact)
- call [约翰](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [约翰](sort.contact) and say hi from [Mary](sort.contact)
- call [约翰](sort.contact) and say hi from [Andy](sort.contact)
- call [约翰](sort.contact) and say hi from [安迪](sort.contact)
- call [Lisa](sort.contact) and say hi from [John](sort.contact)
- call [Lisa](sort.contact) and say hi from [Johnny](sort.contact)
- call [Lisa](sort.contact) and say hi from [约翰](sort.contact)
- call [Lisa](sort.contact) and say hi from [Lisa](sort.contact)
- call [Lisa](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [Lisa](sort.contact) and say hi from [Mary](sort.contact)
- call [Lisa](sort.contact) and say hi from [Andy](sort.contact)
- call [Lisa](sort.contact) and say hi from [安迪](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [John](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [Johnny](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [约翰](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [Lisa](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [Mary](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [Andy](sort.contact)
- call [Elizabeth](sort.contact) and say hi from [安迪](sort.contact)
- call [Mary](sort.contact) and say hi from [John](sort.contact)
- call [Mary](sort.contact) and say hi from [Johnny](sort.contact)
- call [Mary](sort.contact) and say hi from [约翰](sort.contact)
- call [Mary](sort.contact) and say hi from [Lisa](sort.contact)
- call [Mary](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [Mary](sort.contact) and say hi from [Mary](sort.contact)
- call [Mary](sort.contact) and say hi from [Andy](sort.contact)
- call [Mary](sort.contact) and say hi from [安迪](sort.contact)
- call [Andy](sort.contact) and say hi from [John](sort.contact)
- call [Andy](sort.contact) and say hi from [Johnny](sort.contact)
- call [Andy](sort.contact) and say hi from [约翰](sort.contact)
- call [Andy](sort.contact) and say hi from [Lisa](sort.contact)
- call [Andy](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [Andy](sort.contact) and say hi from [Mary](sort.contact)
- call [Andy](sort.contact) and say hi from [Andy](sort.contact)
- call [Andy](sort.contact) and say hi from [安迪](sort.contact)
- call [安迪](sort.contact) and say hi from [John](sort.contact)
- call [安迪](sort.contact) and say hi from [Johnny](sort.contact)
- call [安迪](sort.contact) and say hi from [约翰](sort.contact)
- call [安迪](sort.contact) and say hi from [Lisa](sort.contact)
- call [安迪](sort.contact) and say hi from [Elizabeth](sort.contact)
- call [安迪](sort.contact) and say hi from [Mary](sort.contact)
- call [安迪](sort.contact) and say hi from [Andy](sort.contact)
- call [安迪](sort.contact) and say hi from [安迪](sort.contact)
"""
        )

    def test_generate_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with_individuals(questions=self._questions_of_predicate(sort="contact"))
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:question::phone_number_of_contact
- tell me a phone number
- what is [John](sort.contact)'s number
- what is [Johnny](sort.contact)'s number
- what is [约翰](sort.contact)'s number
- what is [Lisa](sort.contact)'s number
- what is [Elizabeth](sort.contact)'s number
- what is [Mary](sort.contact)'s number
- what is [Andy](sort.contact)'s number
- what is [安迪](sort.contact)'s number
"""
        )

    def _questions_of_predicate(self, sort=None, predicate=None):
        yield Question("phone_number_of_contact", ["tell me a phone number"], [])
        if sort is not None:
            yield Question("phone_number_of_contact", ["what is ", "'s number"], [
                RequiredSortalEntity(sort),
            ])
        if predicate is not None:
            yield Question(
                "phone_number_of_contact", ["tell me ", "'s number"], [
                    RequiredPropositionalEntity(predicate),
                ]
            )

    def test_propositional_entities_excluded_from_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with_individuals(
            questions=self._questions_of_predicate(predicate="selected_contact_to_call")
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:question::phone_number_of_contact
- tell me a phone number

"""
        )

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_questions_with_propositional_entities_issue_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with_individuals(
            questions=self._questions_of_predicate(predicate="selected_contact_to_call")
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate "
            "'selected_contact_to_call'. Skipping this training data example."
        )

    def test_generate_answer_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_mocked_grammar_with_individuals()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer
- [John](sort.contact)
- [Johnny](sort.contact)
- [约翰](sort.contact)
- [Lisa](sort.contact)
- [Elizabeth](sort.contact)
- [Mary](sort.contact)
- [Andy](sort.contact)
- [安迪](sort.contact)
"""
        )

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_mocked_grammar_with_individuals()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer_negation
- not [John](sort.contact)
- not [Johnny](sort.contact)
- not [约翰](sort.contact)
- not [Lisa](sort.contact)
- not [Elizabeth](sort.contact)
- not [Mary](sort.contact)
- not [Andy](sort.contact)
- not [安迪](sort.contact)
"""
        )

    @property
    def _contact_data(self):
        return ["Andy", "Mary", "Lisa", "Elizabeth", u"安迪", u"约翰", "John", "Johnny"]

    def test_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact")
        self.given_mocked_grammar_with_individuals(answers=list(self._answers(sort="contact")))
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer
- [John](sort.contact)
- [Johnny](sort.contact)
- [约翰](sort.contact)
- [Lisa](sort.contact)
- [Elizabeth](sort.contact)
- [Mary](sort.contact)
- [Andy](sort.contact)
- [安迪](sort.contact)
- my sortal friend [John](sort.contact)
- my sortal friend [Johnny](sort.contact)
- my sortal friend [约翰](sort.contact)
- my sortal friend [Lisa](sort.contact)
- my sortal friend [Elizabeth](sort.contact)
- my sortal friend [Mary](sort.contact)
- my sortal friend [Andy](sort.contact)
- my sortal friend [安迪](sort.contact)
"""
        )

    def test_propositional_entities_excluded_from_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact")
        self.given_mocked_grammar_with_individuals(answers=list(self._answers(predicate="selected_contact")))
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer
- [John](sort.contact)
- [Johnny](sort.contact)
- [约翰](sort.contact)
- [Lisa](sort.contact)
- [Elizabeth](sort.contact)
- [Mary](sort.contact)
- [Andy](sort.contact)
- [安迪](sort.contact)

"""
        )

    def _answers(self, sort=None, predicate=None):
        if sort is not None:
            yield Answer(["my sortal friend ", ""], [
                RequiredSortalEntity(sort),
            ])
        if predicate is not None:
            yield Answer(["my friend ", ""], [
                RequiredPropositionalEntity(predicate),
            ])

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_answers_with_propositional_entities_issues_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact")
        self.given_mocked_grammar_with_individuals(answers=list(self._answers(predicate="selected_contact")))
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate 'selected_contact'."
            " Skipping this training data example."
        )

    def test_synonyms(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact")
        self.given_mocked_grammar_with_individuals(answers=list(self._answers(sort="contact")))
        self.given_generator()
        self.when_generate()
        self.then_result_matches(u"""## synonyms:rasa_test:John
- Johnny

## synonyms:rasa_test:Lisa
- Elizabeth
""")


class BuiltinSortGeneratorTestCase(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)
        self._mock_builtin_sort_examples = ["mock example 1", "mock example 2"]
        self._examples_patcher = self._create_examples_patcher()

    def tearDown(self):
        GeneratorTestsBase.tearDown(self)
        self._examples_patcher.stop()

    def _create_examples_patcher(self):
        def create_mock_examples():
            mock_examples = MagicMock(spec=Examples)
            mock_examples.get_builtin_sort_examples.return_value = self._mock_builtin_sort_examples
            return mock_examples

        patcher = patch("%s.Examples" % generator.__name__)
        mock_examples_patcher = patcher.start()
        mock_examples_patcher.from_language.return_value = create_mock_examples()
        return patcher

    def test_generate_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_actions_in_ontology({"mock_action"})
        self.given_mocked_grammar(
            requests=[
                Request("mock_action", ["mock phrase without entities"], []),
                Request("mock_action", ["mock phrase with sortal entity ", ""], [RequiredSortalEntity("mock_sort")]),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:action::mock_action
- mock phrase without entities
- mock phrase with sortal entity mock example 1
- mock phrase with sortal entity mock example 2
"""
        )

    def test_propositional_entities_excluded_from_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_actions_in_ontology({"mock_action"})
        self.given_mocked_grammar(
            requests=[
                Request("mock_action", ["mock phrase without entities"], []),
                Request(
                    "mock_action", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(u"""## intent:rasa_test:action::mock_action
- mock phrase without entities

""")

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_requests_with_propositional_entities_issues_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_actions_in_ontology({"mock_action"})
        self.given_mocked_grammar(
            requests=[
                Request("mock_action", ["mock phrase without entities"], []),
                Request(
                    "mock_action", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate 'mock_predicate'."
            " Skipping this training data example."
        )

    def test_generate_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_expected_plan_questions_in_domain(predicates={"mock_predicate": "mock_sort"})
        self.given_mocked_grammar(
            questions=[
                Question("mock_predicate", ["mock phrase without entities"], []),
                Question(
                    "mock_predicate", ["mock phrase with sortal entity ", ""], [RequiredSortalEntity("mock_sort")]
                ),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:question::mock_predicate
- mock phrase without entities
- mock phrase with sortal entity mock example 1
- mock phrase with sortal entity mock example 2
"""
        )

    def test_propositional_entities_excluded_from_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_expected_plan_questions_in_domain(predicates={"mock_predicate": "mock_sort"})
        self.given_mocked_grammar(
            questions=[
                Question("mock_predicate", ["mock phrase without entities"], []),
                Question(
                    "mock_predicate", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(u"""## intent:rasa_test:question::mock_predicate
- mock phrase without entities

""")

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_questions_with_propositional_entities_issues_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_expected_plan_questions_in_domain(predicates={"mock_predicate": "mock_sort"})
        self.given_mocked_grammar(
            questions=[
                Question("mock_predicate", ["mock phrase without entities"], []),
                Question(
                    "mock_predicate", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate 'mock_predicate'."
            " Skipping this training data example."
        )

    def test_generate_answer_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer
- mock example 1
- mock example 2
"""
        )

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer_negation
- not mock example 1
- not mock example 2
"""
        )

    def test_propositional_entities_excluded_from_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar(
            answers=[
                Answer(["mock phrase with propositional entity ", ""], [RequiredPropositionalEntity("mock_predicate")])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:answer
- mock example 1
- mock example 2

"""
        )

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_answers_with_propositional_entities_issues_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar(
            answers=[
                Answer(["mock phrase with propositional entity ", ""], [RequiredPropositionalEntity("mock_predicate")])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate 'mock_predicate'."
            " Skipping this training data example."
        )


class StringSortGeneratorTestCase(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)

    def test_examples_extended_with_strings_of_predicate(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(
            sort="string", predicate="mock_predicate", individuals=[], is_builtin=True, is_string_sort=True
        )
        self.given_actions_in_ontology({"mock_action"})
        self.given_mocked_grammar(
            requests=[
                Request("mock_action", ["mock phrase without entities"], []),
                Request("mock_action", ["mock phrase with sortal entity ", ""], [RequiredSortalEntity("string")]),
                Request(
                    "mock_action", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ],
            strings=["mock string of predicate"]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            u"""## intent:rasa_test:action::mock_action
- mock phrase without entities
- mock phrase with sortal entity [single](sort.string)
- mock phrase with sortal entity [double word](sort.string)
- mock phrase with sortal entity [three in one](sort.string)
- mock phrase with sortal entity [hey make it four](sort.string)
- mock phrase with sortal entity [the more the merrier five](sort.string)
- mock phrase with sortal entity [calm down and count to six](sort.string)
- mock phrase with sortal entity [bring them through to the jolly seven](sort.string)
- mock phrase with sortal entity [noone counts toes like an eight toed guy](sort.string)
- mock phrase with sortal entity [it matters to make sense for nine of us](sort.string)
- mock phrase with sortal entity [would you bring ten or none to a desert island](sort.string)
- mock phrase with propositional entity [single](predicate.mock_predicate)
- mock phrase with propositional entity [double word](predicate.mock_predicate)
- mock phrase with propositional entity [three in one](predicate.mock_predicate)
- mock phrase with propositional entity [hey make it four](predicate.mock_predicate)
- mock phrase with propositional entity [the more the merrier five](predicate.mock_predicate)
- mock phrase with propositional entity [calm down and count to six](predicate.mock_predicate)
- mock phrase with propositional entity [bring them through to the jolly seven](predicate.mock_predicate)
- mock phrase with propositional entity [noone counts toes like an eight toed guy](predicate.mock_predicate)
- mock phrase with propositional entity [it matters to make sense for nine of us](predicate.mock_predicate)
- mock phrase with propositional entity [would you bring ten or none to a desert island](predicate.mock_predicate)
- mock phrase with propositional entity [mock string of predicate](predicate.mock_predicate)
"""
        )

    def test_do_not_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(
            sort="string", predicate="selected_message", individuals=[], is_builtin=True, is_string_sort=True
        )
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_does_not_match(u"intent:rasa_test:answer_negation")

    def then_result_does_not_match(self, contents):
        expected_pattern = re.escape(contents)
        assert re.search(expected_pattern, self._result, re.UNICODE) is None


class NegativeIntentGeneratorTestCase(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)

    def test_negative_intent(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:NEGATIVE
- aboard
- about
- above
"""
        )
