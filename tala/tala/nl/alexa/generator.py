# encoding: utf-8

import json
import warnings

from tala.nl.abstract_generator import AbstractGenerator, UnexpectedRequiredEntityException
from tala.nl.constants import ACTION_INTENT, QUESTION_INTENT
from tala.nl.examples import SortNotSupportedException


class AlexaGenerator(AbstractGenerator):
    def stream(self, file_object):
        json.dump(self._generate_data(), file_object, sort_keys=True, indent=4, separators=(',', ': '))

    def generate(self):
        return json.dumps(self._generate_data(), sort_keys=True, indent=4, separators=(',', ': '))

    def _format_action(self, name):
        return "%s_%s" % (ACTION_INTENT, name)

    def _format_question(self, name):
        return "%s_%s" % (QUESTION_INTENT, name)

    def _sortal_entity_name(self, sort):
        return "{ddd}_sort_{sort}".format(ddd=self._ddd.name, sort=sort)

    def _generate_data(self):
        def used_sorts(examples):
            encountered_entities = set()
            for generated_intent in examples:
                for entity in generated_intent.required_entities:
                    if entity.is_sortal and entity.name not in encountered_entities:
                        sort = self._ddd.ontology.get_sort(entity.name)
                        if is_enumerated(entity.name) and not has_individuals(sort):
                            continue
                        encountered_entities.add(entity.name)
                        yield entity.name

        def has_individuals(sort):
            return any(self._all_individual_grammar_entries_of_custom_sort(grammar, sort))

        def is_applicable_for_slot(required_entity):
            sort_name = self._sort_of_entity(required_entity)
            sort = self._ddd.ontology.get_sort(sort_name)
            if sort.is_integer_sort():
                return True
            if sort.is_builtin():
                message = "Builtin sort '{}' is not yet supported together with Alexa. Skipping this sort." \
                    .format(sort.get_name())
                warnings.warn(message, UserWarning)
            return has_individuals(sort)

        def is_enumerated(sort_name):
            sort = self._ddd.ontology.get_sort(sort_name)
            if sort.is_builtin():
                return False
            return has_individuals(sort)

        grammar = self._ddd.grammars[self._language_code]
        ddd_examples = list(self._generate_examples())

        data = {
            "interactionModel": {
                "languageModel": {
                    "invocationName":
                    self._ddd.name,
                    "intents": [{
                        "name": "{}_{}".format(self._ddd.name, generated_intent.name),
                        "slots": [{
                            "name": self._name_of_entity(entity),
                            "type": self._type_of_entity(entity),
                        } for entity in generated_intent.required_entities if is_applicable_for_slot(entity)],
                        "samples": generated_intent.samples
                    } for generated_intent in ddd_examples] + [
                        {
                            "name": "AMAZON.YesIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.NoIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.CancelIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.StopIntent",
                            "samples": []
                        },
                    ],
                    "types": [{
                        "name": self._sortal_entity_name(sort),
                        "values": [{
                            "id": individual,
                            "name": {
                                "value": grammar.entries_of_individual(individual)[0],
                                "synonyms": grammar.entries_of_individual(individual)[1:]
                            }
                        } for individual in self._ddd.ontology.get_individuals_of_sort(sort)]
                    } for sort in used_sorts(ddd_examples) if is_enumerated(sort)],
                }
            }
        }  # yapf: disable
        return data

    def _name_of_entity(self, required_entity):
        if required_entity.is_sortal:
            sort = self._ddd.ontology.get_sort(required_entity.name)
            return self._sortal_entity_name(sort.get_name())
        if required_entity.is_propositional:
            predicate = self._ddd.ontology.get_predicate(required_entity.name)
            return "{ddd}_predicate_{predicate}".format(ddd=self._ddd.name, predicate=predicate.get_name())
        raise UnexpectedRequiredEntityException(
            "Expected either a sortal or propositional required entity but got a %s" %
            required_entity.__class__.__name__
        )

    def _sort_of_entity(self, required_entity):
        if required_entity.is_sortal:
            sort = self._ddd.ontology.get_sort(required_entity.name)
            return sort.get_name()
        if required_entity.is_propositional:
            predicate = self._ddd.ontology.get_predicate(required_entity.name)
            return predicate.getSort().get_name()
        raise UnexpectedRequiredEntityException(
            "Expected either a sortal or propositional required entity but got a %s" %
            required_entity.__class__.__name__
        )

    def _type_of_entity(self, required_entity):
        sort_name = self._sort_of_entity(required_entity)
        sort = self._ddd.ontology.get_sort(sort_name)
        if sort.is_integer_sort():
            return "AMAZON.NUMBER"
        if sort.is_builtin():
            message = "Builtin sort '{}' is not yet supported together with Alexa".format(sort.get_name())
            raise SortNotSupportedException(message)
        return self._sortal_entity_name(sort_name)

    def _create_intent_samples(self, grammar, ddd, intent):
        head = intent.text_chunks[0]
        texts = intent.text_chunks[1:]
        return self._examples_with_individuals(grammar, texts, intent.required_entities, [head])

    def _examples_with_individuals(self, grammar, text_chunks, required_entities, examples_so_far):
        def new_example(head, identifier, tail):
            return "{}{{{}}}{}".format(head, identifier, tail)

        if not text_chunks and not required_entities:
            return examples_so_far

        for entity in required_entities:
            sort_name = self._sort_of_entity(entity)
            sort = self._ddd.ontology.get_sort(sort_name)
            if not sort.is_builtin():
                grammar_entries = self._all_individual_grammar_entries_of_custom_sort(grammar, sort)
                if not any(grammar_entries):
                    return []

        tail = text_chunks[0]
        required_entity = required_entities[0]
        identifier = self._name_of_entity(required_entity)
        new_examples = [new_example(example, identifier, tail) for example in examples_so_far]
        return self._examples_with_individuals(grammar, text_chunks[1:], required_entities[1:], new_examples)

    def _create_sortal_answer_samples(self, grammar, ddd, sort, intent_templates):
        for template in intent_templates:
            entity = self._sortal_entity_name(sort.get_name())
            if sort.is_builtin():
                if not sort.is_integer_sort():
                    continue
            if not sort.is_builtin():
                if not any(self._all_individual_grammar_entries_of_custom_sort(grammar, sort)):
                    continue
            alexa_name = "{{{}}}".format(entity)
            answer = template.render(name=alexa_name)
            yield answer
