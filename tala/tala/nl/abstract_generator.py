import os

from tala.ddd.grammar.reader import GrammarReader
from tala.model.grammar.intent import Answer, AnswerNegation
from tala.model.grammar.required_entity import RequiredSortalEntity
from tala.nl.examples import Examples
from tala.nl.generated_intent import GeneratedIntent
from tala.nl.constants import ANSWER_INTENT, ANSWER_NEGATION_INTENT


class GrammarFormatNotSupportedException(Exception):
    pass


class UnexpectedPropositionalEntityEncounteredException(Exception):
    pass


class UnexpectedRequiredEntityException(Exception):
    pass


class AbstractGenerator(object):
    def __init__(self, ddd, language_code):
        self._ddd = ddd
        self._language_code = language_code
        self._language_examples = Examples.from_language(language_code)

    def stream(self, file_object):
        raise NotImplementedError()

    def generate(self):
        raise NotImplementedError()

    def _create_intent_samples(self, grammar, ddd, intent):
        raise NotImplementedError()

    def _create_sortal_answer_samples(self, grammar, ddd, sort, intent_templates):
        raise NotImplementedError()

    def _format_action(self, name):
        raise NotImplementedError()

    def _format_question(self, name):
        raise NotImplementedError()

    def _generate_examples(self):
        if not GrammarReader.xml_grammar_exists_for_language(self._language_code):
            raise GrammarFormatNotSupportedException(
                "Expected an XML-based grammar at '%s', but it does not exist" %
                os.path.abspath(GrammarReader.path(self._language_code))
            )

        grammar = self._ddd.grammars[self._language_code]
        ddd = self._ddd.name

        intent_generators = [
            self._examples_of_actions(grammar, ddd),
            self._examples_of_questions(grammar, ddd),
            self._examples_of_answers(grammar, ddd),
            self._examples_of_answer_negations(grammar, ddd),
        ]

        for generated_intents in intent_generators:
            for generated_intent in generated_intents:
                yield generated_intent

    def _examples_of_actions(self, grammar, ddd):
        for action in self._ddd.ontology.get_ddd_specific_actions():
            yield self._generated_action_intent_for(grammar, ddd, action)

    def _generated_action_intent_for(self, grammar, ddd, action):
        def samples(requests):
            for request in requests:
                for sample in self._create_intent_samples(grammar, ddd, request):
                    yield sample

        intent = self._format_action(action)
        requests = list(grammar.requests_of_action(action))
        return GeneratedIntent(intent, requests, list(samples(requests)))

    def _examples_of_questions(self, grammar, ddd):
        for resolve_goal in self._ddd.domain.get_all_resolve_goals():
            question = resolve_goal.get_question()
            yield self._generated_question_intent_for(grammar, ddd, question)

    def _generated_question_intent_for(self, grammar, ddd, question):
        def samples(questions):
            for question in questions:
                for sample in self._create_intent_samples(grammar, ddd, question):
                    yield sample

        predicate = question.get_predicate().get_name()
        intent = self._format_question(predicate)
        questions = list(grammar.questions_of_predicate(predicate))
        return GeneratedIntent(intent, questions, list(samples(questions)))

    def _examples_of_answers(self, grammar, ddd):
        def samples_from_sorts(sorts):
            for sort in sorts:
                templates = list(self._language_examples.answer_templates)
                for sample in self._create_sortal_answer_samples(grammar, ddd, sort, templates):
                    yield sample

        def samples_from_explicit_answers(answers):
            for answer in answers:
                for sample in self._create_intent_samples(grammar, ddd, answer):
                    yield sample

        def answers_from_sorts(sorts):
            for sort in sorts:
                yield Answer(["", ""], [RequiredSortalEntity(sort.get_name())])

        sorts = self._ddd.ontology.predicate_sorts
        explicit_answers = list(grammar.answers())
        answers = list(answers_from_sorts(sorts)) + explicit_answers
        samples = list(samples_from_sorts(sorts)) + list(samples_from_explicit_answers(explicit_answers))
        yield GeneratedIntent(ANSWER_INTENT, answers, samples)

    def _examples_of_answer_negations(self, grammar, ddd):
        def generate_samples(sorts):
            for sort in sorts:
                templates = list(self._language_examples.answer_negation_templates)
                for sample in self._create_sortal_answer_samples(grammar, ddd, sort, templates):
                    yield sample

        def answers_from_sorts(sorts):
            for sort in sorts:
                yield AnswerNegation(["", ""], [RequiredSortalEntity(sort.get_name())])

        sorts = [sort for sort in self._ddd.ontology.predicate_sorts if not sort.is_string_sort()]
        answers = list(answers_from_sorts(sorts))
        samples = list(generate_samples(sorts))
        yield GeneratedIntent(ANSWER_NEGATION_INTENT, answers, samples)

    def _all_individual_grammar_entries_of_custom_sort(self, grammar, sort):
        individuals = self._ddd.ontology.get_individuals_of_sort(sort.get_name())
        for individual in individuals:
            yield grammar.entries_of_individual(individual)

    def _all_individuals_of_custom_sort(self, grammar, sort):
        individuals = self._ddd.ontology.get_individuals_of_sort(sort.get_name())
        for individual in individuals:
            yield individual, grammar.entries_of_individual(individual)
