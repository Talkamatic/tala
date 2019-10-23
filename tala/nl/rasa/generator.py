import warnings

from jinja2 import Template

from tala.nl.abstract_generator import AbstractGenerator, UnexpectedPropositionalEntityEncounteredException, \
    UnexpectedRequiredEntityException
from tala.nl.constants import ACTION_INTENT, QUESTION_INTENT
from tala.nl import languages


class RasaGenerator(AbstractGenerator):
    @property
    def _language(self):
        return languages.RASA_LANGUAGE[self._language_code]

    @property
    def _rasa_config_template(self):
        return Template(
            "language: \"{{ language }}\"\n"
            "\n"
            "pipeline: \"spacy_sklearn\"\n"
            "\n"
            "data: |\n"
            "{% for line in data.splitlines() %}"
            "  {{ line }}\n"
            "{% endfor %}"
        )

    def stream(self, file_object):
        stream = self._rasa_config_template.stream(language=self._language, data=self._generate_examples())
        return stream.dump(file_object, encoding="utf-8")

    def generate(self):
        return self._rasa_config_template.render(language=self._language, data=self._generate_examples())

    def _format_action(self, name):
        return "%s::%s" % (ACTION_INTENT, name)

    def _format_question(self, name):
        return "%s::%s" % (QUESTION_INTENT, name)

    @property
    def _builtin_entity_template(self):
        return Template("{{ grammar_entry }}")

    @property
    def _sortal_entity_template(self):
        return Template("[{{ grammar_entry }}](sort.{{ value }})")

    @property
    def _propositional_entity_template(self):
        return Template("[{{ grammar_entry }}](predicate.{{ value }})")

    def _generate_examples(self):
        examples = super(RasaGenerator, self)._generate_examples()

        data_template = Template(
            "{% for generated_intent in ddd_examples %}"
            "{% if generated_intent.samples %}"
            "## intent:{{ ddd }}:{{ generated_intent.name }}\n"
            "{% for sample in generated_intent.samples %}"
            "- {{ sample }}\n"
            "{% endfor %}"
            "\n"
            "{% endif %}"
            "{% endfor %}"
            ""
            "{% for generated_intent in general_examples %}"
            "{% if generated_intent.samples %}"
            "## intent:{{ generated_intent.name }}\n"
            "{% for sample in generated_intent.samples %}"
            "- {{ sample }}\n"
            "{% endfor %}"
            "\n"
            "{% endif %}"
            "{% endfor %}"
            ""
            "{% for synonym_object in synonym_objects %}"
            "## synonyms:{{ ddd }}:{{ synonym_object.value }}\n"
            "{% for synonym in synonym_object.synonyms %}"
            "- {{ synonym }}\n"
            "{% endfor %}"
            "\n"
            "{% endfor %}"
        )
        grammar = self._ddd.grammars[self._language_code]
        synonyms = self._entity_synonyms_from_custom_sorts(grammar)
        rasa_data = data_template.render(
            ddd_examples=examples,
            general_examples=self._examples_of_negative_intent(),
            synonym_objects=synonyms,
            ddd=self._ddd.name
        )

        return rasa_data

    def _entity_synonyms_from_custom_sorts(self, grammar):
        for sort in self._ddd.ontology.get_sorts().values():
            if sort.is_builtin():
                continue
            entities = list(self._all_individual_grammar_entries_of_custom_sort(grammar, sort))
            for individual_entities in entities:
                if len(individual_entities) <= 1:
                    continue
                yield self._create_synonym_object(individual_entities[0], individual_entities[1:])

    @staticmethod
    def _create_synonym_object(value, synonyms):
        return {
            "value": value,
            "synonyms": synonyms,
        }

    def _create_intent_samples(self, grammar, intent):
        head = intent.text_chunks[0]
        texts = intent.text_chunks[1:]
        try:
            samples = self._examples_with_individuals(grammar, texts, intent.required_entities, [head])
            return samples
        except UnexpectedPropositionalEntityEncounteredException:
            return []

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
                        "Skipping this training data example.".format(predicate.get_name(), predicate.getSort())
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
        template = self._entity_template_of(sort)
        return self._examples_from_individuals(template, sort.get_name(), individuals, example_so_far, tail)

    def _individual_grammar_entries_samples(self, grammar, sort):
        if sort.is_builtin():
            return self._sample_individuals_of_builtin_sort(sort)
        return self._all_individual_grammar_entries_of_custom_sort(grammar, sort)

    def _sample_individuals_of_builtin_sort(self, sort):
        examples = self._language_examples.get_builtin_sort_examples(sort)
        return [[entry] for entry in examples]

    def _examples_from_propositional_individual(self, grammar, required_propositional_entity, example_so_far, tail):
        predicate_name = required_propositional_entity.name
        predicate = self._ddd.ontology.get_predicate(predicate_name)
        sort = predicate.getSort()
        individuals = self._individual_grammar_entries_samples(grammar, sort)
        predicate_specific_samples = self._string_examples_of_predicate(grammar, predicate)
        individuals.extend([[predicate_specific_sample] for predicate_specific_sample in predicate_specific_samples])
        return self._examples_from_individuals(
            self._propositional_entity_template, predicate_name, individuals, example_so_far, tail
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

    def _create_sortal_answer_samples(self, grammar, sort, intent_templates):
        for grammar_entries in self._individual_grammar_entries_samples(grammar, sort):
            examples = self._examples_of_individual(
                grammar_entries, sort.get_name(), intent_templates, self._entity_template_of(sort)
            )
            for example in examples:
                yield example

    def _entity_template_of(self, sort):
        sort_should_be_generated_as_entity = sort.is_string_sort() or not sort.is_builtin()
        if sort_should_be_generated_as_entity:
            return self._sortal_entity_template
        return self._builtin_entity_template

    def _examples_of_individual(self, grammar_entries, identifier, intent_templates, entity_template):
        for grammar_entry in grammar_entries:
            examples = self._examples_from_templates(grammar_entry, identifier, intent_templates, entity_template)
            for example in examples:
                yield example

    def _examples_from_templates(self, grammar_entry, identifier, intent_templates, entity_template):
        for intent_template in intent_templates:
            entity = entity_template.render(grammar_entry=grammar_entry, value=identifier)
            yield intent_template.render(name=entity)