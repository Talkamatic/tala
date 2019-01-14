import os
from copy import copy
import json

from jinja2 import Template
from pathlib import Path

from tala.ddd.grammar.reader import GrammarReader
from tala.nl.rasa.constants import ACTION_INTENT, QUESTION_INTENT, ANSWER_INTENT, ANSWER_NEGATION_INTENT
from tala.nl.rasa.generating.common_example import CommonExample
from tala.nl.rasa.generating.entity_factory import PropositionalEntityFactory, SortalEntityFactory
from tala.nl.rasa.generating.examples import Examples
from tala.utils.file_writer import UTF8FileWriter


class RASANotSupportedByGrammarFormatException(Exception):
    pass


class UnexpectedRequiredEntityException(Exception):
    pass


class RASADataNotGeneratedException(Exception):
    pass


class RasaGenerator(object):
    def __init__(self, ddd, language_code):
        super(RasaGenerator, self).__init__()
        self._ddd = ddd
        self._sortal_entity_factory = SortalEntityFactory()
        self._propositional_entity_factory = PropositionalEntityFactory()
        self._language_code = language_code
        self._language_examples = Examples.from_language(language_code)

    def generate(self):
        if not GrammarReader.xml_grammar_exists_for_language(self._language_code):
            raise RASANotSupportedByGrammarFormatException(
                "Expected an XML-based grammar at '%s', but it does not exist" %
                os.path.abspath(GrammarReader.path(self._language_code))
            )
        grammar = self._ddd.grammars[self._language_code]

        examples = set()
        examples.update(self._examples_of_requests(grammar))
        examples.update(self._examples_of_questions(grammar))
        examples.update(self._examples_of_sortal_answers_from_individuals(grammar))
        examples.update(self._examples_of_sortal_answer_negations_from_individuals(grammar))
        examples.update(self._examples_of_answers(grammar))
        examples.update(self._examples_of_negative_intent())

        rasa_data = {
            "rasa_nlu_data": {
                "regex_features": [],
                "entity_synonyms": [],
                "common_examples": [example.generate() for example in examples]
            }
        }

        return rasa_data

    @staticmethod
    def data_file_name():
        return "rasa_data.json"

    def generate_and_write_to_file(self):
        def write(path, text):
            writer = UTF8FileWriter(path)
            writer.create_directories()
            writer.write(text)

        def as_json(data):
            return json.dumps(data, ensure_ascii=False, indent=4, separators=(',', ': '))

        path = Path("build_rasa") / self._language_code / self.data_file_name()
        data = self.generate()
        write(path, as_json(data))

    def _examples_of_negative_intent(self):
        return self._language_examples.negative

    def _examples_of_requests(self, grammar):
        for action in self._ddd.ontology.get_ddd_specific_actions():
            for example in self._examples_of_request(grammar, action):
                yield example

    def _examples_of_request(self, grammar, action):
        intent = "%s:%s::%s" % (self._ddd.name, ACTION_INTENT, action)
        requests = grammar.requests_of_action(action)
        for request in requests:
            for example in self._examples_of_intent(grammar, intent, request):
                yield example

    def _examples_of_intent(self, grammar, name, intent):
        head = intent.text_chunks[0]
        texts = intent.text_chunks[1:]
        first_example = CommonExample(name, head)
        examples = self._examples_with_individuals(grammar, texts, intent.required_entities, [first_example])
        for example in examples:
            yield example

    def _examples_with_individuals(self, grammar, text_chunks, required_entities, examples_so_far):
        if not text_chunks and not required_entities:
            return examples_so_far
        tail = text_chunks[0]
        required_entity = required_entities[0]
        all_new_examples = []
        for example in examples_so_far:
            if required_entity.is_sortal:
                new_examples = list(self._examples_from_sortal_individual(grammar, required_entity, example, tail))
            elif required_entity.is_propositional:
                new_examples = list(
                    self._examples_from_propositional_individual(grammar, required_entity, example, tail)
                )
            else:
                raise UnexpectedRequiredEntityException(
                    "Expected either a sortal or propositional required entity but got a %s" %
                    required_entity.__class__.__name__
                )
            all_new_examples.extend(new_examples)
        return self._examples_with_individuals(grammar, text_chunks[1:], required_entities[1:], all_new_examples)

    def _examples_from_sortal_individual(self, grammar, required_sortal_entity, example_so_far, tail):
        sort = self._ddd.ontology.get_sort(required_sortal_entity.name)
        individuals = self._individual_grammar_entries_samples(grammar, sort)
        return self._examples_from_individuals(
            self._sortal_entity_factory, sort.get_name(), individuals, example_so_far, tail
        )

    def _sample_individuals_of_builtin_sort(self, sort):
        examples = self._language_examples.get_builtin_sort_examples(sort)
        return [[entry] for entry in examples]

    def _individual_grammar_entries_samples(self, grammar, sort):
        if sort.is_builtin():
            return self._sample_individuals_of_builtin_sort(sort)
        return self._individual_grammar_entries_samples_of_custom_sort(grammar, sort)

    def _individual_grammar_entries_samples_of_custom_sort(self, grammar, sort):
        individuals = self._ddd.ontology.get_individuals_of_sort(sort.get_name())
        grammar_entries = [grammar.entries_of_individual(individual) for individual in individuals]
        return grammar_entries

    def _examples_from_propositional_individual(self, grammar, required_propositional_entity, example_so_far, tail):
        predicate_name = required_propositional_entity.name
        predicate = self._ddd.ontology.get_predicate(predicate_name)
        sort = predicate.getSort()
        individuals = self._individual_grammar_entries_samples(grammar, sort)
        if sort.is_string_sort():
            predicate_specific_samples = self._string_examples_of_predicate(grammar, predicate)
            individuals.extend([[predicate_specific_sample]
                                for predicate_specific_sample in predicate_specific_samples])
        return self._examples_from_individuals(
            self._propositional_entity_factory, predicate_name, individuals, example_so_far, tail
        )

    def _string_examples_of_predicate(self, grammar, predicate):
        return grammar.strings_of_predicate(predicate.get_name())

    def _examples_from_individuals(self, entity_factory, identifier, individuals_grammar_entries, example_so_far, tail):
        for grammar_entries in individuals_grammar_entries:
            for grammar_entry in grammar_entries:
                entity_start = len(example_so_far.text)
                end = entity_start + len(grammar_entry)
                entity = entity_factory.create(identifier, grammar_entry, entity_start, end)
                example = self._extend_example(entity, example_so_far, tail)
                yield example

    @staticmethod
    def _extend_example(entity, example_so_far, tail=None):
        head = example_so_far.text
        tail = tail or ""
        text = "".join([head, entity.text, tail])
        entities = copy(example_so_far.entities)
        entities.append(entity)
        return CommonExample(example_so_far.intent, text, entities)

    def _examples_of_questions(self, grammar):
        for resolve_goal in self._ddd.domain.get_all_resolve_goals():
            question = resolve_goal.get_question()
            for example in self._examples_of_question(grammar, question):
                yield example

    def _examples_of_question(self, grammar, question):
        predicate = question.get_predicate().get_name()
        intent = "%s:%s::%s" % (self._ddd.name, QUESTION_INTENT, predicate)
        questions = grammar.questions_of_predicate(predicate)
        for question in questions:
            for example in self._examples_of_intent(grammar, intent, question):
                yield example

    def _examples_of_answers(self, grammar):
        for answer in grammar.answers():
            intent = "%s:%s" % (self._ddd.name, ANSWER_INTENT)
            for example in self._examples_of_intent(grammar, intent, answer):
                yield example

    def _examples_of_sortal_answers_from_individuals(self, grammar):
        for sort in self._ddd.ontology.get_sorts().values():
            examples = self._examples_of_sortal_answers_of_kind(grammar, sort, ANSWER_INTENT, self._answer_templates)
            for example in examples:
                yield example

    def _examples_of_sortal_answers_of_kind(self, grammar, sort, kind, templates):
        for grammar_entries in self._individual_grammar_entries_samples(grammar, sort):
            examples = self._examples_of_individual(
                kind, self._sortal_entity_factory, grammar_entries, sort.get_name(), templates
            )
            for example in examples:
                yield example

    def _examples_of_sortal_answer_negations_from_individuals(self, grammar):
        for sort in self._ddd.ontology.get_sorts().values():
            if sort.is_string_sort():
                continue
            examples = self._examples_of_sortal_answers_of_kind(
                grammar, sort, ANSWER_NEGATION_INTENT, self._answer_negation_templates
            )
            for example in examples:
                yield example

    @property
    def _answer_templates(self):
        template = Template('{{ name }}')
        return [template]

    @property
    def _answer_negation_templates(self):
        template = Template('not {{ name }}')
        return [template]

    def _examples_of_individual(self, intent_type, entity_factory, grammar_entries, identifier, templates):
        intent = "%s:%s" % (self._ddd.name, intent_type)
        for grammar_entry in grammar_entries:
            examples = self._examples_from_templates(intent, entity_factory, grammar_entry, identifier, templates)
            for example in examples:
                yield example

    def _examples_from_templates(self, intent, entity_factory, grammar_entry, identifier, templates):
        for template in templates:
            text = template.render(name=grammar_entry)
            example = self._create_example_with_only_an_entity(intent, entity_factory, identifier, grammar_entry, text)
            yield example

    @staticmethod
    def _create_example_with_only_an_entity(intent, entity_factory, identifier, grammar_entry, text):
        start = text.find(grammar_entry)
        if start < 0:
            raise RuntimeError(
                "Expected to find individual named '%s' in example '%s' but it was not found." % (grammar_entry, text)
            )
        end = start + len(grammar_entry)
        entity = entity_factory.create(identifier, grammar_entry, start=start, end=end)
        return CommonExample(intent, text, [entity])
