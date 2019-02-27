import os
import warnings

from jinja2 import Template
from pathlib import Path

from tala.ddd.grammar.reader import GrammarReader
from tala.nl.rasa.constants import ACTION_INTENT, QUESTION_INTENT, ANSWER_INTENT, ANSWER_NEGATION_INTENT, \
    NEGATIVE_INTENT
from tala.nl.rasa.generating.examples import Examples
from tala.utils.file_writer import UTF8FileWriter


class RASANotSupportedByGrammarFormatException(Exception):
    pass


class UnexpectedRequiredEntityException(Exception):
    pass


class RASADataNotGeneratedException(Exception):
    pass


class UnexpectedPropositionalEntityEncounteredException(Exception):
    pass


SORTAL_ENTITY_TEMPLATE = Template("[{{ grammar_entry }}](sort:{{ value }})")
PROPOSITIONAL_ENTITY_TEMPLATE = Template("[{{ grammar_entry }}](predicate:{{ value }})")


class RasaGenerator(object):
    def __init__(self, ddd, language_code):
        super(RasaGenerator, self).__init__()
        self._ddd = ddd
        self._language_code = language_code
        self._language_examples = Examples.from_language(language_code)

    def generate(self):
        def add(examples, new_examples):
            for key, values in new_examples.items():
                if key in examples:
                    examples[key].extend(values)
                else:
                    examples[key] = values

        if not GrammarReader.xml_grammar_exists_for_language(self._language_code):
            raise RASANotSupportedByGrammarFormatException(
                "Expected an XML-based grammar at '%s', but it does not exist" %
                os.path.abspath(GrammarReader.path(self._language_code))
            )
        grammar = self._ddd.grammars[self._language_code]

        examples = {}
        add(examples, self._examples_of_requests(grammar))
        add(examples, self._examples_of_questions(grammar))
        add(examples, self._examples_of_sortal_answers_from_individuals(grammar))
        add(examples, self._examples_of_answers(grammar))
        add(examples, self._examples_of_sortal_answer_negations_from_individuals(grammar))
        add(examples, self._examples_of_negative_intent())

        data_template = Template(
            "{% for intent, examples in intent_examples.items() %}"
            "{% if examples %}"
            "## intent:{{ intent }}\n"
            "{% for example in examples %}"
            "- {{ example }}\n"
            "{% endfor %}"
            "\n"
            "{% endif %}"
            "{% endfor %}"
            ""
            "{% for synonym_object in synonym_objects %}"
            "## synonyms:{{ synonym_object.value }}\n"
            "{% for synonym in synonym_object.synonyms %}"
            "- {{ synonym }}\n"
            "{% endfor %}"
            "\n"
            "{% endfor %}"
        )
        rasa_data = data_template.render(intent_examples=examples, synonym_objects=[])

        return rasa_data

    @staticmethod
    def data_file_name():
        return "rasa_data.json"

    def generate_and_write_to_file(self):
        def write(path, text):
            writer = UTF8FileWriter(path)
            writer.create_directories()
            writer.write(text)

        path = Path("build_rasa") / self._language_code / self.data_file_name()
        data = self.generate()
        write(path, data)

    def _examples_of_negative_intent(self):
        return {NEGATIVE_INTENT: list(self._language_examples.negative)}

    def _examples_of_requests(self, grammar):
        examples = {}
        for action in self._ddd.ontology.get_ddd_specific_actions():
            intent = "%s:%s::%s" % (self._ddd.name, ACTION_INTENT, action)
            examples[intent] = self._examples_of_request(grammar, action)
        return examples

    def _examples_of_request(self, grammar, action):
        requests = grammar.requests_of_action(action)
        for request in requests:
            for example in self._examples_of_intent(grammar, request):
                yield example

    def _examples_of_intent(self, grammar, intent):
        head = intent.text_chunks[0]
        texts = intent.text_chunks[1:]
        try:
            examples = self._examples_with_individuals(grammar, texts, intent.required_entities, [head])
        except UnexpectedPropositionalEntityEncounteredException:
            return
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
                all_new_examples.extend(new_examples)
            elif required_entity.is_propositional:
                predicate = self._ddd.ontology.get_predicate(required_entity.name)
                if predicate.getSort().is_string_sort():
                    new_examples = list(
                        self._examples_from_propositional_individual(grammar, required_entity, example, tail)
                    )
                    all_new_examples.extend(new_examples)

                else:
                    message = (
                        "Expected only sortal slots but got a propositional slot for predicate '{}'. "
                        "Skipping this training data example."
                        .format(predicate.get_name(), predicate.getSort())
                    )
                    warnings.warn(message, UserWarning)
                    raise UnexpectedPropositionalEntityEncounteredException(message)
            else:
                raise UnexpectedRequiredEntityException(
                    "Expected either a sortal or propositional required entity but got a %s" %
                    required_entity.__class__.__name__
                )
        return self._examples_with_individuals(grammar, text_chunks[1:], required_entities[1:], all_new_examples)

    def _examples_from_sortal_individual(self, grammar, required_sortal_entity, example_so_far, tail):
        sort = self._ddd.ontology.get_sort(required_sortal_entity.name)
        individuals = self._individual_grammar_entries_samples(grammar, sort)
        return self._examples_from_individuals(
            SORTAL_ENTITY_TEMPLATE, sort.get_name(), individuals, example_so_far, tail
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
        predicate_specific_samples = self._string_examples_of_predicate(grammar, predicate)
        individuals.extend([[predicate_specific_sample] for predicate_specific_sample in predicate_specific_samples])
        return self._examples_from_individuals(
            PROPOSITIONAL_ENTITY_TEMPLATE, predicate_name, individuals, example_so_far, tail
        )

    def _string_examples_of_predicate(self, grammar, predicate):
        return grammar.strings_of_predicate(predicate.get_name())

    def _examples_from_individuals(self, template, identifier, individuals_grammar_entries, example_so_far, tail):
        for grammar_entries in individuals_grammar_entries:
            for grammar_entry in grammar_entries:
                entity = template.render(grammar_entry=grammar_entry, value=identifier)
                example = self._extend_example(entity, example_so_far, tail)
                yield example

    @staticmethod
    def _extend_example(entity, example_so_far, tail=None):
        head = example_so_far
        tail = tail or ""
        return "".join([head, entity, tail])

    def _examples_of_questions(self, grammar):
        def examples(question):
            for example in self._examples_of_question(grammar, question):
                yield example

        result = {}
        for resolve_goal in self._ddd.domain.get_all_resolve_goals():
            question = resolve_goal.get_question()
            predicate = question.get_predicate().get_name()
            intent = "%s:%s::%s" % (self._ddd.name, QUESTION_INTENT, predicate)
            result[intent] = list(examples(question))
        return result

    def _examples_of_question(self, grammar, question):
        predicate = question.get_predicate().get_name()
        questions = grammar.questions_of_predicate(predicate)
        for question in questions:
            for example in self._examples_of_intent(grammar, question):
                yield example

    def _examples_of_answers(self, grammar):
        def examples():
            for answer in grammar.answers():
                for example in self._examples_of_intent(grammar, answer):
                    yield example

        intent = "%s:%s" % (self._ddd.name, ANSWER_INTENT)
        return {intent: list(examples())}

    def _examples_of_sortal_answers_from_individuals(self, grammar):
        def examples():
            for sort in self._ddd.ontology.get_sorts().values():
                examples = self._examples_of_sortal_answers_of_kind(grammar, sort, self._answer_templates)
                for example in examples:
                    yield example

        intent = "%s:%s" % (self._ddd.name, ANSWER_INTENT)
        return {intent: list(examples())}

    def _examples_of_sortal_answers_of_kind(self, grammar, sort, templates):
        for grammar_entries in self._individual_grammar_entries_samples(grammar, sort):
            examples = self._examples_of_individual(grammar_entries, sort.get_name(), templates)
            for example in examples:
                yield example

    def _examples_of_sortal_answer_negations_from_individuals(self, grammar):
        def examples():
            for sort in self._ddd.ontology.get_sorts().values():
                if sort.is_string_sort():
                    continue
                examples = self._examples_of_sortal_answers_of_kind(grammar, sort, self._answer_negation_templates)
                for example in examples:
                    yield example

        intent = "%s:%s" % (self._ddd.name, ANSWER_NEGATION_INTENT)
        return {intent: list(examples())}

    @property
    def _answer_templates(self):
        template = Template('{{ name }}')
        return [template]

    @property
    def _answer_negation_templates(self):
        template = Template('not {{ name }}')
        return [template]

    def _examples_of_individual(self, grammar_entries, identifier, templates):
        for grammar_entry in grammar_entries:
            examples = self._examples_from_templates(grammar_entry, identifier, templates)
            for example in examples:
                yield example

    def _examples_from_templates(self, grammar_entry, identifier, templates):
        for template in templates:
            entity = SORTAL_ENTITY_TEMPLATE.render(grammar_entry=grammar_entry, value=identifier)
            yield template.render(name=entity)
