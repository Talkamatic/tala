import unittest

import pytest

from tala.model.semantic_logic import SemanticLogic


@pytest.mark.usefixtures("ddd_manager", "loaded_mockup_travel")
class SemanticsTester(unittest.TestCase):
    def setUp(self):
        self._semantic_logic = SemanticLogic(self.ddd_manager)
        self.ddd = self.ddd_manager.get_ddd("mockup_travel")
        self.parser = self.ddd.parser
        self.valid_combinations = []
        self.valid_relevances = []
        self.valid_resolves = []
        self.valid_incompatibles = []
        self.answers = set()
        self.questions = set()
        self.failures = []

    def tearDown(self):
        if len(self.failures) > 0:
            self.fail("Failures:\n" + "\n".join(self.failures))
        self.ddd_manager.reset_ddd(self.ddd.name)

    def declare_combinable_and_relevant(self, declarations):
        for declaration in declarations:
            (question_as_string, answer_as_string, result_as_string) = \
                declaration
            question = self.create_object(question_as_string)
            answer = self.create_object(answer_as_string)
            result = self.create_object(result_as_string)
            self.valid_combinations.append((question, answer, result))
            self.valid_relevances.append((question, answer))
            self.answers.add(answer)
            self.questions.add(question)

    def declare_relevant_not_resolving(self, declarations):
        for declaration in declarations:
            (question_as_string, answer_as_string) = declaration
            question = self.create_object(question_as_string)
            answer = self.create_object(answer_as_string)
            self.valid_relevances.append((question, answer))
            self.answers.add(answer)
            self.questions.add(question)

    def declare_resolving(self, declarations):
        for declaration in declarations:
            (question_as_string, answer_as_string) = declaration
            question = self.create_object(question_as_string)
            answer = self.create_object(answer_as_string)
            self.valid_resolves.append((question, answer))
            self.answers.add(answer)
            self.questions.add(question)

    def declare_answer(self, answer_as_string):
        answer = self.create_object(answer_as_string)
        self.answers.add(answer)

    def declare_incompatible(self, declarations):
        for declaration in declarations:
            (answer_1_as_string, answer_2_as_string) = declaration
            answer_1 = self.create_object(answer_1_as_string)
            answer_2 = self.create_object(answer_2_as_string)
            self.answers.add(answer_1)
            self.answers.add(answer_2)
            self.valid_incompatibles.append((answer_1, answer_2))

    def semantics_test_valid_combines(self):
        for combination in self.valid_combinations:
            (question, answer, result) = combination
            self._assert_combination(question, answer, result)

    def semantics_test_invalid_combines(self):
        for question in self.questions:
            for answer in self.answers:
                if self._is_invalid_combination(question, answer):
                    self._assert_not_combinable(question, answer)

    def semantics_test_relevance(self):
        for relevance in self.valid_relevances:
            (question, answer) = relevance
            self._assert_relevant(question, answer)

    def semantics_test_irrelevance(self):
        for question in self.questions:
            for answer in self.answers:
                if self._is_irrelevant(question, answer):
                    self._assert_not_relevant(question, answer)

    def semantics_test_resolves(self):
        for resolve in self.valid_resolves:
            (question, answer) = resolve
            self._assert_resolving(question, answer)

    def semantics_test_non_resolves(self):
        for question in self.questions:
            for answer in self.answers:
                if self._is_not_resolving(question, answer):
                    self._assert_not_resolving(question, answer)

    def semantics_test_valid_incompatibles(self):
        for (answer_1, answer_2) in self.valid_incompatibles:
            self._assert_incompatible(answer_1, answer_2)
            self._assert_incompatible(answer_2, answer_1)

    def semantics_test_invalid_incompatibles(self):
        for answer_1 in self._get_propostional_answers():
            for answer_2 in self._get_propostional_answers():
                if not (answer_1, answer_2) in self.valid_incompatibles and \
                        not (answer_2, answer_1) in self.valid_incompatibles:
                    self._assert_compatible(answer_1, answer_2)
                    self._assert_compatible(answer_2, answer_1)

    def _is_invalid_combination(self, question, answer):
        for combination in self.valid_combinations:
            (combinable_question, combinable_answer, result) = combination
            if combinable_question == question and combinable_answer == answer:
                return False
        return True

    def _is_irrelevant(self, question, answer):
        return not (question, answer) in self.valid_relevances

    def _is_not_resolving(self, question, answer):
        return not (question, answer) in self.valid_resolves

    def _assert_combination(self, question, answer, expected_result):
        if not self._semantic_logic.are_combinable(question, answer):
            self._report_failure(
                "SemanticLogic.are_combinable(%s, %s) should be True but was False" % (question, answer)
            )
        actual_result = self._semantic_logic.combine(question, answer)
        if expected_result != actual_result:
            self._report_failure(
                "SemanticLogic.combine(%s, %s) should return %s but returned %s" %
                (question, answer, expected_result, actual_result)
            )

    def _assert_not_combinable(self, question, answer):
        if self._semantic_logic.are_combinable(question, answer):
            self._report_failure(
                "SemanticLogic.are_combinable(%s, %s) should be False but was True" % (question, answer)
            )

    def _assert_resolving(self, question, answer):
        if not self._semantic_logic.resolves(question, answer):
            self._report_failure("SemanticLogic.resolves(%s, %s) should be True but was False" % (question, answer))

    def _assert_not_resolving(self, question, answer):
        if self._semantic_logic.resolves(question, answer):
            self._report_failure(
                "SemanticLogic.resolves(%s, %s) has not been explicitly declared but was True" % (question, answer)
            )

    def _assert_relevant(self, question, answer):
        if not self._semantic_logic.is_relevant(question, answer):
            self._report_failure("relevant(%s, %s) should be True but was False" % (question, answer))

    def _assert_not_relevant(self, question, answer):
        if self._semantic_logic.is_relevant(question, answer):
            self._report_failure("relevant(%s, %s) has not been explicitly declared but was True" % (question, answer))

    def _report_failure(self, failure):
        self.failures.append(failure)

    def _get_propostional_answers(self):
        return list(filter(self._is_proposition, self.answers))

    @staticmethod
    def _is_proposition(answer):
        try:
            return answer.is_proposition()
        except AttributeError:
            return False

    def _assert_incompatible(self, proposition_1, proposition_2):
        if not proposition_1.is_incompatible_with(proposition_2):
            self._report_failure("%s should be incompatible with %s" % (proposition_1, proposition_2))

    def _assert_compatible(self, proposition_1, proposition_2):
        if proposition_1.is_incompatible_with(proposition_2):
            self._report_failure("%s should be compatible with %s" % (proposition_1, proposition_2))

    def create_object(self, string):
        return self.parser.parse(string)
