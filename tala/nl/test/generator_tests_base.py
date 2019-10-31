# encoding: utf-8

import os
import re
import shutil
import tempfile

from mock import Mock, patch
import pytest

from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.goal import ResolveGoal
from tala.model.grammar.grammar import GrammarBase
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.ontology import Ontology
from tala.model.predicate import Predicate
from tala.model.question import WhQuestion
from tala.model.sort import Sort, CustomSort
from tala.nl import abstract_generator


class GeneratorTestsMixin(object):
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

    def teardown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)
        self._grammar_reader_patcher.stop()

    def _create_mocked_ddd(self):
        ontology = Mock(spec=Ontology)
        ontology.get_individuals_of_sort.return_value = list()
        ontology.get_ddd_specific_actions.return_value = set()
        ontology.get_sorts.return_value = dict()
        ontology.predicate_sorts = set()
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
        patcher = patch("%s.GrammarReader" % abstract_generator.__name__, autospec=True)
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
        name="mocked_ontology",
        is_builtin=False,
        is_integer_sort=False,
        is_string_sort=False,
        is_real_sort=False,
        is_datetime_sort=False,
        is_person_name_sort=False
    ):
        mocked_sort = Mock(spec=Sort)
        mocked_sort.get_name.return_value = sort
        mocked_sort.is_builtin.return_value = is_builtin
        mocked_sort.is_integer_sort.return_value = is_integer_sort
        mocked_sort.is_string_sort.return_value = is_string_sort
        mocked_sort.is_real_sort.return_value = is_real_sort
        mocked_sort.is_domain_sort.return_value = False
        mocked_sort.is_datetime_sort.return_value = is_datetime_sort
        mocked_sort.is_person_name_sort.return_value = is_person_name_sort
        self._mocked_ddd.ontology.name = name
        self._mocked_ddd.ontology.individual_sort.return_value = mocked_sort
        self._mocked_ddd.ontology.get_individuals_of_sort.return_value = individuals
        self._mocked_ddd.ontology.get_sorts.return_value = {sort: mocked_sort}
        self._mocked_ddd.ontology.predicate_sorts = {mocked_sort}
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
        self._generator = self._create_generator()

    def _create_generator(self):
        raise NotImplementedError()

    def when_generate(self):
        self._result = self._generate()

    def _generate(self):
        return self._generator.generate()

    def when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
        self, expected_exception, expected_pattern
    ):
        with pytest.raises(expected_exception, match=expected_pattern):
            self._generate()

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
        expected_pattern = re.escape(expected_contents)
        assert re.search(expected_pattern, self._result, re.UNICODE) is not None, \
            "Expected contents to match {} but got {}".format(expected_pattern, self._result)

    def given_mocked_warnings(self, mock_warnings):
        self._mocked_warnings = mock_warnings

    def then_warning_is_issued(self, expected_message):
        self._mocked_warnings.warn.assert_called_with(expected_message, UserWarning)

    def given_ontology_with(
        self,
        sort,
        predicate,
        individuals,
        is_integer_sort=False,
        is_string_sort=False,
        is_real_sort=False,
        is_builtin=False
    ):
        self.given_ontology(
            sort,
            individuals,
            predicate,
            is_integer_sort=is_integer_sort,
            is_string_sort=is_string_sort,
            is_real_sort=is_real_sort,
            is_builtin=is_builtin
        )

    def given_mocked_grammar_with(self, individuals, requests=None, questions=None, answers=None):
        self.given_mocked_grammar(requests, questions, individuals, answers)
