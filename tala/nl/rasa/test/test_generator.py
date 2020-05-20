# -*- coding: utf-8 -*-

import re

from jinja2 import Template
from mock import MagicMock, patch

from tala.model.grammar.intent import Request, Question, Answer
from tala.model.grammar.required_entity import RequiredPropositionalEntity, RequiredSortalEntity
from tala.nl.languages import ENGLISH
from tala.nl import abstract_generator
from tala.nl.rasa import generator
from tala.nl.rasa.generator import RasaGenerator
from tala.nl.examples import Examples, SortNotSupportedException
from tala.nl.test.generator_tests_base import GeneratorTestsMixin


class RasaGeneratorTestMixin(GeneratorTestsMixin):
    def _generator_name(self):
        return generator.__name__

    def _create_generator(self):
        return RasaGenerator(self._mocked_ddd, ENGLISH)

    def then_result_matches(self, expected_contents):
        expected_contents = "\n  ".join(expected_contents.splitlines())
        super(RasaGeneratorTestMixin, self).then_result_matches(expected_contents)


class TestGeneratorWithUnsupportedBuiltinSorts(RasaGeneratorTestMixin):
    def test_generate_requests(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="real", predicate="selected_price", individuals=[], is_builtin=True, is_real_sort=True)
        self.given_actions_in_ontology({"purchase"})
        self.given_mocked_grammar(
            requests=[
                Request("purchase", ["purchase for ", " bucks"], [RequiredPropositionalEntity("selected_price")]),
            ]
        )
        self.given_generator()
        self.when_generating_data_with_mocked_grammar_then_exception_is_raised_matching(
            SortNotSupportedException, "Builtin sort 'real' is not yet supported together with RASA"
        )

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


class TestGeneratorWithCustomSorts(RasaGeneratorTestMixin):
    def test_generate_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            requests=[
                Request("call", ["make a call"], []),
                Request("call", ["call ", ""], [RequiredSortalEntity("contact")])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:action::call
- make a call
- call [John](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact)
"""
        )

    def test_propositional_entities_excluded_from_requests(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            requests=[
                Request("call", ["make a call"], []),
                Request("call", ["take a note that ", ""], [
                    RequiredPropositionalEntity("selected_contact_to_call"),
                ])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches("""## intent:rasa_test:action::call
- make a call

""")

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_requests_with_propositional_entities_issue_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            requests=[
                Request("call", ["make a call"], []),
                Request("call", ["take a note that ", ""], [
                    RequiredPropositionalEntity("selected_contact_to_call"),
                ])
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate "
            "'selected_contact_to_call'. Skipping this training data example."
        )

    def test_generate_requests_with_two_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="caller",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_actions_in_ontology({"call"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
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
            """## intent:rasa_test:action::call
- call [John](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [John](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [Johnny](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [约翰](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [Lisa](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [Elizabeth](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [Mary](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [Andy](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [John](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [Johnny](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [约翰](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [Lisa](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [Elizabeth](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [Mary](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [Andy](rasa_test.sort.contact)
- call [安迪](rasa_test.sort.contact) and say hi from [安迪](rasa_test.sort.contact)
"""
        )

    def test_generate_questions(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            questions=self._questions_of_predicate(sort="contact")
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:question::phone_number_of_contact
- tell me a phone number
- what is [John](rasa_test.sort.contact)'s number
- what is [Johnny](rasa_test.sort.contact)'s number
- what is [约翰](rasa_test.sort.contact)'s number
- what is [Lisa](rasa_test.sort.contact)'s number
- what is [Elizabeth](rasa_test.sort.contact)'s number
- what is [Mary](rasa_test.sort.contact)'s number
- what is [Andy](rasa_test.sort.contact)'s number
- what is [安迪](rasa_test.sort.contact)'s number
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
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            questions=self._questions_of_predicate(predicate="selected_contact_to_call")
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches("""## intent:rasa_test:question::phone_number_of_contact
- tell me a phone number

""")

    @patch("{}.warnings".format(generator.__name__), autospec=True)
    def test_questions_with_propositional_entities_issue_warning(self, mock_warnings):
        self.given_mocked_warnings(mock_warnings)
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_expected_plan_questions_in_domain({"phone_number_of_contact": "contact"})
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
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
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            }
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:answer
- [John](rasa_test.sort.contact)
- [Johnny](rasa_test.sort.contact)
- [约翰](rasa_test.sort.contact)
- [Lisa](rasa_test.sort.contact)
- [Elizabeth](rasa_test.sort.contact)
- [Mary](rasa_test.sort.contact)
- [Andy](rasa_test.sort.contact)
- [安迪](rasa_test.sort.contact)
"""
        )

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact_to_call",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            }
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:answer_negation
- not [John](rasa_test.sort.contact)
- not [Johnny](rasa_test.sort.contact)
- not [约翰](rasa_test.sort.contact)
- not [Lisa](rasa_test.sort.contact)
- not [Elizabeth](rasa_test.sort.contact)
- not [Mary](rasa_test.sort.contact)
- not [Andy](rasa_test.sort.contact)
- not [安迪](rasa_test.sort.contact)
"""
        )

    @property
    def _contact_data(self):
        return ["Andy", "Mary", "Lisa", "Elizabeth", "安迪", "约翰", "John", "Johnny"]

    def test_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            answers=list(self._answers(sort="contact"))
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:answer
- [John](rasa_test.sort.contact)
- [Johnny](rasa_test.sort.contact)
- [约翰](rasa_test.sort.contact)
- [Lisa](rasa_test.sort.contact)
- [Elizabeth](rasa_test.sort.contact)
- [Mary](rasa_test.sort.contact)
- [Andy](rasa_test.sort.contact)
- [安迪](rasa_test.sort.contact)
- my sortal friend [John](rasa_test.sort.contact)
- my sortal friend [Johnny](rasa_test.sort.contact)
- my sortal friend [约翰](rasa_test.sort.contact)
- my sortal friend [Lisa](rasa_test.sort.contact)
- my sortal friend [Elizabeth](rasa_test.sort.contact)
- my sortal friend [Mary](rasa_test.sort.contact)
- my sortal friend [Andy](rasa_test.sort.contact)
- my sortal friend [安迪](rasa_test.sort.contact)
"""
        )

    def test_propositional_entities_excluded_from_answers(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            answers=list(self._answers(predicate="selected_contact"))
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:answer
- [John](rasa_test.sort.contact)
- [Johnny](rasa_test.sort.contact)
- [约翰](rasa_test.sort.contact)
- [Lisa](rasa_test.sort.contact)
- [Elizabeth](rasa_test.sort.contact)
- [Mary](rasa_test.sort.contact)
- [Andy](rasa_test.sort.contact)
- [安迪](rasa_test.sort.contact)

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
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            answers=list(self._answers(predicate="selected_contact"))
        )
        self.given_generator()
        self.when_generate()
        self.then_warning_is_issued(
            "Expected only sortal slots but got a propositional slot for predicate 'selected_contact'."
            " Skipping this training data example."
        )

    def test_synonyms(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology_with(
            sort="contact",
            predicate="selected_contact",
            individuals=[
                "contact_john",
                "contact_john_chi",
                "contact_lisa",
                "contact_mary",
                "contact_andy",
                "contact_andy_chi",
            ]
        )
        self.given_mocked_grammar_with(
            individuals={
                "contact_john": ["John", "Johnny"],
                "contact_john_chi": ["约翰"],
                "contact_lisa": ["Lisa", "Elizabeth"],
                "contact_mary": ["Mary"],
                "contact_andy": ["Andy"],
                "contact_andy_chi": ["安迪"],
            },
            answers=list(self._answers(sort="contact"))
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## synonyms:rasa_test:contact_john
- John
- Johnny

## synonyms:rasa_test:contact_lisa
- Lisa
- Elizabeth
"""
        )


class TestGeneratorWithBuiltinSorts(RasaGeneratorTestMixin):
    def setup(self):
        RasaGeneratorTestMixin.setup(self)
        self._mock_builtin_sort_examples = ["mock example 1", "mock example 2"]
        self._examples_patcher = self._create_examples_patcher()

    def teardown(self):
        RasaGeneratorTestMixin.teardown(self)
        self._examples_patcher.stop()

    def _create_examples_patcher(self):
        def create_mock_examples():
            mock_examples = MagicMock(spec=Examples)
            mock_examples.get_builtin_sort_examples.return_value = self._mock_builtin_sort_examples
            mock_examples.answer_templates = [Template('{{ name }}')]
            mock_examples.answer_negation_templates = [Template('not {{ name }}')]
            return mock_examples

        patcher = patch("%s.Examples" % abstract_generator.__name__)
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
                    "mock_action", ["mock phrase with sortal entity ", " with ending"],
                    [RequiredSortalEntity("mock_sort")]
                ),
            ]
        )
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:rasa_test:action::mock_action
- mock phrase without entities
- mock phrase with sortal entity mock example 1
- mock phrase with sortal entity mock example 2
- mock phrase with sortal entity mock example 1 with ending
- mock phrase with sortal entity mock example 2 with ending
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
        self.then_result_matches("""## intent:rasa_test:action::mock_action
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
            """## intent:rasa_test:question::mock_predicate
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
        self.then_result_matches("""## intent:rasa_test:question::mock_predicate
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
        self.then_result_matches("""## intent:rasa_test:answer
- mock example 1
- mock example 2
""")

    def test_generate_answer_negation_intents(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mock_sort", individuals=[], predicate="mock_predicate", is_builtin=True)
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches("""## intent:rasa_test:answer_negation
- not mock example 1
- not mock example 2
""")

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
        self.then_result_matches("""## intent:rasa_test:answer
- mock example 1
- mock example 2

""")

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


class TestGeneratorWithStringSorts(RasaGeneratorTestMixin):
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
            """## intent:rasa_test:action::mock_action
- mock phrase without entities
- mock phrase with sortal entity [single](rasa_test.sort.string)
- mock phrase with sortal entity [double word](rasa_test.sort.string)
- mock phrase with sortal entity [three in one](rasa_test.sort.string)
- mock phrase with sortal entity [hey make it four](rasa_test.sort.string)
- mock phrase with sortal entity [the more the merrier five](rasa_test.sort.string)
- mock phrase with sortal entity [calm down and count to six](rasa_test.sort.string)
- mock phrase with sortal entity [bring them through to the jolly seven](rasa_test.sort.string)
- mock phrase with sortal entity [noone counts toes like an eight toed guy](rasa_test.sort.string)
- mock phrase with sortal entity [it matters to make sense for nine of us](rasa_test.sort.string)
- mock phrase with sortal entity [would you bring ten or none to a desert island](rasa_test.sort.string)
- mock phrase with propositional entity [single](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [double word](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [three in one](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [hey make it four](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [the more the merrier five](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [calm down and count to six](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [bring them through to the jolly seven](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [noone counts toes like an eight toed guy](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [it matters to make sense for nine of us](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [would you bring ten or none to a desert island](rasa_test.predicate.mock_predicate)
- mock phrase with propositional entity [mock string of predicate](rasa_test.predicate.mock_predicate)
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
        self.then_result_does_not_match("intent:rasa_test:answer_negation")

    def then_result_does_not_match(self, contents):
        expected_pattern = re.escape(contents)
        assert re.search(expected_pattern, self._result, re.UNICODE) is None


class TestGeneratorWithNegativeIntent(RasaGeneratorTestMixin):
    def test_negative_intent(self):
        self.given_ddd_name("mocked_ddd")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches("""## intent:NEGATIVE
- aboard
- about
- above
""")


class TestGeneratorWithBuiltinIntents(RasaGeneratorTestMixin):
    def test_yes(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:yes
- yes
- yeah
- yep
- sure
- ok
- of course
- very well
- fine
- right
- excellent
- okay
- perfect
- I think so
"""
        )

    def test_no(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:no
- no
- nope
- no thanks
- no thank you
- negative
- don't want to
- don't
- do not
- please don't
"""
        )

    def test_top(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches(
            """## intent:top
- forget it
- never mind
- get me out of here
- start over
- beginning
- never mind that
- restart
"""
        )

    def test_up(self):
        self.given_ddd_name("rasa_test")
        self.given_ontology(sort="mocked_sort", predicate="mocked_predicate", individuals=[])
        self.given_mocked_grammar()
        self.given_generator()
        self.when_generate()
        self.then_result_matches("""## intent:up
- go back
- back
- previous
""")
