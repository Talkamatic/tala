# -*- coding: utf-8 -*-

import copy
import os
import re
import shutil
import tempfile
import unittest

from mock import MagicMock, Mock, patch
from pathlib import Path

import tala.utils
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
from tala.nl.rasa.generating.examples import Examples, EnglishExamples, SortNotSupportedException


class GeneratorTestsBase(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="GeneratorTests")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._mocked_ddd = self._create_mocked_ddd()
        self._generator = None
        self._mocked_grammar = None
        self._expected_data = None
        self._grammar_reader_patcher = self._create_grammar_reader_patcher()
        self._result = None

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

    def given_changed_to_temp_folder(self):
        temp_dir = tempfile.mkdtemp(prefix="RasaGeneratorTestCase")
        return tala.float_comparison.chdir(temp_dir)

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

    def _action_example(self, action, text, entities=None):
        identifier = "rasa_test:action::%s" % action
        return self._intent_example(identifier, text, entities)

    def _question_example(self, predicate, text, entities=None):
        identifier = "rasa_test:question::%s" % predicate
        return self._intent_example(identifier, text, entities)

    def _intent_example(self, identifier, text, entities=None):
        entities = entities or []
        return {
            "text": text,
            "intent": identifier,
            "entities": entities,
        }

    def _action_examples_with_sortal_entities(self, action, texts, sort, entity_names):
        identifier = "sort:%s" % sort
        return self._action_examples_with_entities(action, texts, identifier, entity_names)

    def _question_examples_with_sortal_entities(self, predicate_in_question, texts, sort, entity_names):
        identifier = "sort:%s" % sort
        return self._question_examples_with_entities(predicate_in_question, texts, identifier, entity_names)

    def _action_examples_with_entities(self, action, texts, entity_identifier, entity_names):
        intent_identifier = "rasa_test:action::%s" % action
        return self._intent_examples_with_entities(intent_identifier, texts, entity_identifier, entity_names)

    def _question_examples_with_entities(self, predicate, texts, entity_identifier, entity_names):
        intent_identifier = "rasa_test:question::%s" % predicate
        return self._intent_examples_with_entities(intent_identifier, texts, entity_identifier, entity_names)

    def _answer_examples_with_sortal_entities(self, sort, entity_names):
        intent_identifier = "rasa_test:answer"
        entity_identifier = "sort:%s" % sort
        return self._intent_examples_with_entities(intent_identifier, [""], entity_identifier, entity_names)

    def _answer_examples_with_propositional_entities(self, predicate, texts, entity_names):
        intent_identifier = "rasa_test:answer"
        entity_identifier = "predicate:%s" % predicate
        return self._intent_examples_with_entities(intent_identifier, texts, entity_identifier, entity_names)

    def _answer_negation_examples_with_sortal_entities(self, sort, entity_names):
        intent_identifier = "rasa_test:answer_negation"
        entity_identifier = "sort:%s" % sort
        return self._intent_examples_with_entities(intent_identifier, ["not "], entity_identifier, entity_names)

    def _answer_negation_examples_with_propositional_entities(self, predicate, texts, entity_names):
        intent_identifier = "rasa_test:answer_negation"
        entity_identifier = "predicate:%s" % predicate
        return self._intent_examples_with_entities(intent_identifier, texts, entity_identifier, entity_names)

    def _intent_examples_with_entities(self, intent_identifier, original_texts, entity_identifier, entity_names):
        start = len(original_texts[0])
        for entity_name in entity_names:
            entities = list(self._entity_examples(entity_identifier, [entity_name], start))
            texts = copy.deepcopy(original_texts)
            texts.insert(1, entity_name)
            text = "".join(texts)
            yield self._intent_example(intent_identifier, text, entities)

    def _entity_examples(self, entity_identifier, entity_names, start):
        for name in entity_names:
            yield {"start": start, "end": start + len(name), "value": name, "entity": entity_identifier}

    def _action_examples_with_propositional_entities(self, action, texts, predicate, entity_names):
        identifier = "predicate:%s" % predicate
        return self._action_examples_with_entities(action, texts, identifier, entity_names)

    def _question_examples_with_propositional_entities(self, question_predicate, texts, answer_predicate, entity_names):
        entity_identifier = "predicate:%s" % answer_predicate
        return self._question_examples_with_entities(question_predicate, texts, entity_identifier, entity_names)

    def _assert_common_examples_in_generated_data_is(self, expected_common_examples):
        actual_common_examples = self._result["rasa_nlu_data"]["common_examples"]
        for expected_common_example in expected_common_examples:
            assert expected_common_example in actual_common_examples, "Expected to find %s in %s but didn't" % (
                expected_common_example, actual_common_examples
            )

    def then_common_examples_have_been_generated(self, expected_common_examples):
        self._assert_common_examples_in_generated_data_is(expected_common_examples)

    def then_no_common_examples_have_been_generated_for_answer_negation(self):
        actual_common_examples = self._result["rasa_nlu_data"]["common_examples"]
        actual_negation_examples = [
            example for example in actual_common_examples if example["intent"] == "rasa_test:answer_negation"
        ]
        assert len(actual_negation_examples) == 0, "Expected no answer negations but got %s" % actual_negation_examples


class GenerateAndWriteTests(GeneratorTestsBase, unittest.TestCase):
    def setUp(self):
        GeneratorTestsBase.setup(self)
        self._MockUTF8FileWriter = None
        self._mocked_file_writer = None

    @patch("{}.UTF8FileWriter".format(generator.__name__), autospec=True)
    def test_written_data_when_calling_generate_and_write_to_file(self, MockUTF8FileWriter):
        self.given_mocked_file_writer(MockUTF8FileWriter)
        self.given_generator()
        self.given_generate_returns({"data": "mock"})
        self.when_calling_generate_and_write_to_file()
        self.then_written_data_was('{\n    "data": "mock"\n}')

    def given_mocked_file_writer(self, MockUTF8FileWriter):
        self._MockUTF8FileWriter = MockUTF8FileWriter
        self._mocked_file_writer = MockUTF8FileWriter.return_value

    def given_generate_returns(self, data):
        self._generator.generate = Mock()
        self._generator.generate.return_value = data

    def when_calling_generate_and_write_to_file(self):
        self._generator.generate_and_write_to_file()

    def then_written_data_was(self, expected_data):
        self._mocked_file_writer.write.assert_called_once_with(expected_data)

    @patch("{}.UTF8FileWriter".format(generator.__name__), autospec=True)
    def test_path_when_calling_generate_and_write_to_file(self, MockUTF8FileWriter):
        self.given_mocked_file_writer(MockUTF8FileWriter)
        self.given_generator()
        self.given_generate_returns({"data": "mock"})
        self.when_calling_generate_and_write_to_file()
        self.then_path_was(Path("build_rasa") / "eng" / "rasa_data.json")

    def then_path_was(self, expected_path):
        self._MockUTF8FileWriter.assert_called_once_with(expected_path)

    @patch("{}.UTF8FileWriter".format(generator.__name__), autospec=True)
    def test_directories_created_when_calling_generate_and_write_to_file(self, MockUTF8FileWriter):
        self.given_mocked_file_writer(MockUTF8FileWriter)
        self.given_generator()
        self.given_generate_returns({"data": "mock"})
        self.when_calling_generate_and_write_to_file()
        self.then_directories_was_created()

    def then_directories_was_created(self):
        self._mocked_file_writer.create_directories.assert_called_once_with()


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
        self.given_mocked_grammar_with_individuals(requests=self._requests_of_action)
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated_for_action("call", "contact", "selected_contact_to_call")

    @property
    def _requests_of_action(self):
        return [
            Request("call", ["make a call"], []),
            Request("call", ["call ", ""], [
                RequiredSortalEntity("contact"),
            ]),
            Request("call", ["make a call to ", ""], [
                RequiredPropositionalEntity("selected_contact_to_call"),
            ]),
        ]

    def then_common_examples_have_been_generated_for_action(self, action, sort, predicate_of_propositional_answer):
        def examples():
            yield self._action_example(action, "make a call")
            for example in self._action_examples_with_sortal_entities(action, ["call "], sort, self._contact_data):
                yield example
            for example in self._action_examples_with_propositional_entities(
                action, ["make a call to "], predicate_of_propositional_answer, self._contact_data
            ):
                yield example

        self._assert_common_examples_in_generated_data_is(examples())

    def test_generate_requests_with_two_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="caller")
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with_individuals(
            requests=[
                Request(
                    "call", ["call ", " and say hi from ", ""], [
                        RequiredSortalEntity("contact"),
                        RequiredPropositionalEntity("caller"),
                    ]
                ),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated([
            {
                "text":
                "call John and say hi from Lisa",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 9,
                    "value": "John",
                    "entity": "sort:contact"
                }, {
                    "start": 26,
                    "end": 30,
                    "value": "Lisa",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Johnny and say hi from Lisa",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 11,
                    "value": "Johnny",
                    "entity": "sort:contact"
                }, {
                    "start": 28,
                    "end": 32,
                    "value": "Lisa",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call John and say hi from Elizabeth",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 9,
                    "value": "John",
                    "entity": "sort:contact"
                }, {
                    "start": 26,
                    "end": 35,
                    "value": "Elizabeth",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Johnny and say hi from Elizabeth",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 11,
                    "value": "Johnny",
                    "entity": "sort:contact"
                }, {
                    "start": 28,
                    "end": 37,
                    "value": "Elizabeth",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Lisa and say hi from John",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 9,
                    "value": "Lisa",
                    "entity": "sort:contact"
                }, {
                    "start": 26,
                    "end": 30,
                    "value": "John",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Lisa and say hi from Johnny",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 9,
                    "value": "Lisa",
                    "entity": "sort:contact"
                }, {
                    "start": 26,
                    "end": 32,
                    "value": "Johnny",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Elizabeth and say hi from John",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 14,
                    "value": "Elizabeth",
                    "entity": "sort:contact"
                }, {
                    "start": 31,
                    "end": 35,
                    "value": "John",
                    "entity": "predicate:caller"
                }]
            },
            {
                "text":
                "call Elizabeth and say hi from Johnny",
                "intent":
                "rasa_test:action::call",
                "entities": [{
                    "start": 5,
                    "end": 14,
                    "value": "Elizabeth",
                    "entity": "sort:contact"
                }, {
                    "start": 31,
                    "end": 37,
                    "value": "Johnny",
                    "entity": "predicate:caller"
                }]
            },
        ])

    def test_generate_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with_individuals(questions=self._questions_of_predicate)
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated_for_question(
            "phone_number_of_contact", "contact", "selected_contact_of_phone_number"
        )

    @property
    def _questions_of_predicate(self):
        return [
            Question("phone_number_of_contact", ["tell me a phone number"], []),
            Question("phone_number_of_contact", ["what is ", "'s number"], [
                RequiredSortalEntity("contact"),
            ]),
            Question(
                "phone_number_of_contact", ["tell me ", "'s number"], [
                    RequiredPropositionalEntity("selected_contact_of_phone_number"),
                ]
            ),
        ]

    def then_common_examples_have_been_generated_for_question(
        self, predicate_in_question, sort, predicate_of_propositional_answer
    ):
        def examples():
            yield self._question_example(predicate_in_question, "tell me a phone number")
            for example in self._question_examples_with_sortal_entities(
                predicate_in_question, ["what is ", "'s number"], sort, self._contact_data
            ):
                yield example
            for example in self._question_examples_with_propositional_entities(
                predicate_in_question, ["tell me ", "'s number"], predicate_of_propositional_answer, self._contact_data
            ):
                yield example

        self._assert_common_examples_in_generated_data_is(examples())

    def then_common_examples_have_been_generated_for_questions_and_exected_data(self):
        self.then_common_examples_have_been_generated_for_questions(self._expected_data)

    def test_generate_answer_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_mocked_grammar_with_individuals()
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated_for_answer("contact")

    def then_common_examples_have_been_generated_for_answer(self, sort):
        def examples():
            for example in self._answer_examples_with_sortal_entities(sort, self._contact_data):
                yield example

        self._assert_common_examples_in_generated_data_is(examples())

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact_to_call")
        self.given_mocked_grammar_with_individuals()
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated_for_answer_negation("contact")

    def then_common_examples_have_been_generated_for_answer_negation(self, sort):
        def examples():
            for example in self._answer_negation_examples_with_sortal_entities(sort, self._contact_data):
                yield example

        self._assert_common_examples_in_generated_data_is(examples())

    @property
    def _contact_data(self):
        return ["Andy", "Mary", "Lisa", "Elizabeth", u"安迪", u"约翰", "John", "Johnny"]

    def test_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with_individuals(sort="contact", predicate="selected_contact")
        self.given_mocked_grammar_with_individuals(answers=self._answers("selected_contact"))
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated_for_propositional_answer("selected_contact")

    def _answers(self, answer_predicate):
        return [
            Answer(["my friend ", ""], [
                RequiredPropositionalEntity(answer_predicate),
            ]),
        ]

    def then_common_examples_have_been_generated_for_propositional_answer(self, predicate):
        def examples():
            for example in self._answer_examples_with_propositional_entities(
                predicate, ["my friend ", ""], self._contact_data
            ):
                yield example

        self._assert_common_examples_in_generated_data_is(examples())


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
                Request(
                    "mock_action", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated(
            [self._action_example("mock_action", "mock phrase without entities")] + list(
                self._action_examples_with_sortal_entities(
                    "mock_action", ["mock phrase with sortal entity "], "mock_sort", self._mock_builtin_sort_examples
                )
            ) + list(
                self._action_examples_with_propositional_entities(
                    "mock_action", ["mock phrase with propositional entity "], "mock_predicate", self.
                    _mock_builtin_sort_examples
                )
            )
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
                Question(
                    "mock_predicate", ["mock phrase with propositional entity ", ""],
                    [RequiredPropositionalEntity("mock_predicate")]
                )
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated(
            [self._question_example("mock_predicate", "mock phrase without entities")] + list(
                self._question_examples_with_sortal_entities(
                    "mock_predicate", ["mock phrase with sortal entity "], "mock_sort", self._mock_builtin_sort_examples
                )
            ) + list(
                self._question_examples_with_propositional_entities(
                    "mock_predicate", ["mock phrase with propositional entity "], "mock_predicate", self.
                    _mock_builtin_sort_examples
                )
            )
        )

    def test_generate_answer_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated(
            self._answer_examples_with_sortal_entities("mock_sort", self._mock_builtin_sort_examples)
        )

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated(
            self._answer_negation_examples_with_sortal_entities("mock_sort", self._mock_builtin_sort_examples)
        )

    def test_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar(
            answers=[
                Answer(["mock phrase with propositional entity ", ""], [RequiredPropositionalEntity("mock_predicate")])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_common_examples_have_been_generated(
            self._answer_examples_with_propositional_entities(
                "mock_predicate", ["mock phrase with propositional entity ", ""], self._mock_builtin_sort_examples
            )
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
        self.then_common_examples_have_been_generated(
            [self._action_example("mock_action", "mock phrase without entities")] + list(
                self._action_examples_with_string_entities(
                    "mock_action", ["mock phrase with sortal entity "],
                    EnglishExamples().string
                )
            ) + list(
                self._action_examples_with_propositional_entities(
                    "mock_action", ["mock phrase with propositional entity "], "mock_predicate",
                    EnglishExamples().string + ["mock string of predicate"]
                )
            )
        )

    def _action_examples_with_string_entities(self, action, texts, entity_names):
        return self._action_examples_with_entities(action, texts, "string", entity_names)

    def test_do_not_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(
            sort="string", predicate="selected_message", individuals=[], is_builtin=True, is_string_sort=True
        )
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_no_common_examples_have_been_generated_for_answer_negation()
