# -*- coding: utf-8 -*-
# flake8: noqa

import os
import re
import shutil
import tempfile
import unittest

from mock import Mock

import tala.nl.gf.resource
import tala.ddd.schemas
from tala.model.ddd import DDD
from tala.ddd.ddd_py_compiler import DddPyCompiler
from tala.ddd.ddd_xml_compiler import DddXmlCompiler, ViolatesSchemaException
from tala.ddd.services.constants import UNDEFINED_SERVICE_ACTION_FAILURE
from tala.ddd.parser import Parser
from tala.ddd.services.service_interface import ServiceInterface, ServiceActionInterface, DeviceModuleTarget, ServiceParameter, ActionFailureReason, ServiceValidatorInterface
from tala.model.device import DeviceAction
from tala.model.domain import Domain
from tala.model.ontology import Ontology
from tala.model.plan import Plan
from tala.nl.gf.auto_generator import AutoGenerator, UnexpectedParameter, InvalidSortOfBackgroundPredicateException
from tala.nl.gf.grammar_entry_types import Node, Constants

UNKNOWN_CATEGORY = "Unknown;\n"
UNKNOWN_FUNCTION = "unknown_string : Unknown -> Sort_string;\n"
MK_UNKNOWN_FUNCTION = "mkUnknown : String -> Unknown;\n"

UNKNOWN_LINCAT = "Unknown = SS"
UNKNOWN_LINERARIZATION = """unknown_string unknown = ss ("\\"" ++ unknown.s ++ "\\"");\n"""
MK_UNKNOWN_LINEARIZATION = "mkUnknown string = ss string.s;\n"

UNKNOWN_NL_LINEARIZATION = """unknown_string unknown = unknown;\n"""
MK_UNKNOWN_NL_LINEARIZATION = """mkUnknown string = string;\n"""


class AutoGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        class MockupDevice:
            actions = {}
            validities = []

        self._device_class = MockupDevice
        self._grammar = Node(Constants.GRAMMAR)
        self._grammar_compiler = DddPyCompiler()
        self._ontology = None
        self._domain = None
        self._ddd_name = "mockup_ddd"

        self._service_actions = []
        self._service_validators = []
        self.mock_service_target = self._create_mock_service_target()

    def given_ontology(self, *args, **kwargs):
        self._create_ontology(*args, **kwargs)

    def _create_ontology(self, sorts=None, predicates=None, actions=None, individuals=None):
        if sorts is None:
            sorts = {
                "city": {},
                "passenger_type": {},
                "keyword": {
                    "dynamic": True
                },
                "membership": {},
            }

        if predicates is None:
            predicates = {
                "dest_city": "city",
                "dest_city_type": {
                    "sort": "city",
                    "feature_of": "dest_city"
                },
                "dept_city": "city",
                "distance": "integer",
                "price": "integer",
                "day_to_set": "integer",
                "hour_to_set": "integer",
                "minute_to_set": "integer",
                "passenger_type_to_add": "passenger_type",
                "passenger_quantity_to_add": "integer",
                "qualified_for_membership": "boolean",
                "frequent_flyer_points": "integer",
                "location": "string",
                "next_membership_level": "membership",
                "next_membership_points": "integer",
                "comment": "string",
                "attraction_information": "string",
                "attraction": "string",
                "flight_departure": "datetime",
            }

        if actions is None:
            actions = set([
                "top",
                "make_reservation",
                "settings",
                "set_time",
            ])

        if individuals is None:
            individuals = {
                "new_york": "city",
            }

        class MockupOntology:
            pass

        MockupOntology.sorts = sorts
        MockupOntology.predicates = predicates
        MockupOntology.actions = actions
        MockupOntology.individuals = individuals
        self._ontology_class = MockupOntology

        ontology_args = DddPyCompiler().compile_ontology(self._ontology_class)
        self._ontology = Ontology(**ontology_args)
        self._parser = Parser(self._ddd_name, self._ontology)

    def _create_mock_service_target(self):
        mock_target = Mock(spec=DeviceModuleTarget)
        mock_target.is_frontend = False
        return mock_target

    def given_compulsory_grammar_for_app(self, exclude=None):
        entries = [
            (Constants.ACTION, {
                "name": "top"
            }, [Node(Constants.ITEM, {}, ["start view"])]),
            (Constants.ACTION, {
                "name": "up"
            }, [Node(Constants.ITEM, {}, ["go back"])]),
            (Constants.ACTION, {
                "name": "make_reservation"
            }, [Node(Constants.ITEM, {}, ["make a reservation"])]),
            (Constants.ACTION, {
                "name": "settings"
            }, [Node(Constants.ITEM, {}, ["settings"])]),
            (Constants.ACTION, {
                "name": "set_time"
            }, [Node(Constants.ITEM, {}, ["set the time"])]),
            (Constants.INDIVIDUAL, {
                "name": "new_york"
            }, [Node(Constants.ITEM, {}, ["New York"])]),
        ]
        for node_type, parameters, children in entries:
            if exclude != (node_type, parameters):
                self._grammar.add_child(Node(node_type, parameters, children))

    def given_grammar(self, added_nodes):
        for node in added_nodes:
            self._grammar.add_child(node)

    def given_form(self, form):
        self._form = form

    def given_generator(self, language_code="eng"):
        self._create_generator(language_code)

    def when_generating(self, language_code="eng"):
        self._create_generator(language_code)
        self.generator.generate(language_code)

    def _then_no_exception_is_raised(self):
        pass

    def _create_generator(self, language_code):
        self._create_mock_ddd()

        def get_grammar(language_code):
            return self._grammar

        self.generator = MockAutoGenerator(self._ddd)
        self.generator._load_and_compile_grammar_entries = get_grammar
        self.generator.warning = ""
        self.generator._grammar_compiler = self._grammar_compiler

    def _create_mock_ddd(self):
        def create_mocked_service_interface():
            mocked_interface = Mock(spec=ServiceInterface)
            mocked_interface.actions = self._service_actions
            mocked_interface.queries = []
            mocked_interface.validators = self._service_validators
            mocked_interface.entity_recognizers = []
            return mocked_interface

        self._ensure_ontology_exists()
        self._ensure_domain_exists()

        self._ddd = Mock(spec=DDD)
        self._ddd.domain = self._domain
        self._ddd.service_interface = create_mocked_service_interface()
        self._ddd.name = "MockupDdd"
        self._ddd.ontology = self._ontology

    def given_service_interface_has_action(self, action):
        self._service_actions.append(action)

    def given_service_interface_has_validity(self, validator):
        self._service_validators.append(validator)

    def _ensure_ontology_exists(self):
        if self._ontology is None:
            self._create_ontology()

    def _ensure_domain_exists(self):
        if self._domain is None:
            self._domain = Domain(self._ddd_name, "mockup_domain", self._ontology)

    def given_py_grammar(self):
        self._grammar_compiler = DddPyCompiler()

    def given_xml_grammar(self):
        self._grammar_compiler = DddXmlCompiler()

    def expect_warning(self, expected_warning):
        self.assertEquals(expected_warning, self.generator.warning.strip())

    def expect_no_warning(self):
        self.assertEquals("", self.generator.warning)

    def assert_abstract(self, expected):
        self.assertEquals(expected, self.generator._abstract_gf_content.getvalue())

    def assert_abstract_contains(self, expected):
        self.assertIn(expected, self.generator._abstract_gf_content.getvalue())

    def assert_abstract_contains_function(self, expected):
        actual_functions_section = self._get_section(self.generator._abstract_gf_content.getvalue(), "fun")
        self.assertIn(expected, actual_functions_section)

    def assert_abstract_not_contains_function(self, expected):
        actual_functions_section = self._get_section(self.generator._abstract_gf_content.getvalue(), "fun")
        self.assertNotIn(expected, actual_functions_section)

    def _get_section(self, gf_content, start_line, end_line="}\n"):
        match = re.search("%s\n(.*)%s" % (start_line, end_line), gf_content, re.DOTALL)
        if match:
            return match.group(1)
        else:
            self.fail(
                "failed to find section with start_line=%r, end_line=%r in %r" % (start_line, end_line, gf_content)
            )

    def assert_abstract_contains_category(self, expected):
        actual_categories_section = self._get_section(
            self.generator._abstract_gf_content.getvalue(), start_line="cat", end_line="fun"
        )
        self.assertIn(expected, actual_categories_section)

    def assert_abstract_not_contains_category(self, expected):
        actual_categories_section = self._get_section(
            self.generator._abstract_gf_content.getvalue(), start_line="cat", end_line="fun"
        )
        self.assertNotIn(expected, actual_categories_section)

    def assert_semantic_contains_lincat(self, expected):
        actual_lincat_section = self._get_section(
            self.generator._semantic_gf_content.getvalue(), start_line="lincat", end_line="lin"
        )
        self.assertIn(expected, actual_lincat_section)

    def assert_semantic_not_contains_lincat(self, expected):
        actual_lincat_section = self._get_section(
            self.generator._semantic_gf_content.getvalue(), start_line="lincat", end_line="lin"
        )
        self.assertNotIn(expected, actual_lincat_section)

    def assert_semantic(self, expected):
        self.assertEquals(expected, self.generator._semantic_gf_content.getvalue())

    def assert_semantic_contains(self, expected):
        self.assertIn(expected, self.generator._semantic_gf_content.getvalue())

    def assert_semantic_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._semantic_gf_content.getvalue(), "lin")
        self.assertIn(expected, actual_linearizations_section)

    def assert_semantic_not_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._semantic_gf_content.getvalue(), "lin")
        self.assertNotIn(expected, actual_linearizations_section)

    def assert_natural_language(self, expected):
        self.assertEquals(expected, self.generator._natural_language_gf_content.getvalue())

    def assert_natural_language_contains(self, expected):
        self.assertIn(expected, self.generator._natural_language_gf_content.getvalue())

    def assert_natural_language_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._natural_language_gf_content.getvalue(), "lin")
        self.assertIn(expected, actual_linearizations_section)

    def assert_natural_language_not_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._natural_language_gf_content.getvalue(), "lin")
        self.assertNotIn(expected, actual_linearizations_section)

    def get_predicate(self, predicate_name):
        return self.generator._ontology.get_predicate(predicate_name)

    def when_generating_action_content(self, action_name):
        action_node = Node(Constants.ACTION, {"name": action_name})
        self._grammar.add_child(action_node)
        if self._form.type == Constants.VP:
            action_node.add_child(Node(Constants.ITEM, {}, [self._form]))
        else:
            action_node.add_child(self._form)
        self.generator._grammar = self._grammar
        self.generator._generate_action_content(action_name)

    def when_generating_predicate_content(self, predicate_name):
        self._grammar.add_child(Node(Constants.PREDICATE, {"name": predicate_name}, [self._form]))
        self.generator._grammar = self._grammar
        self.generator._generate_predicate_content(predicate_name)

    def assert_abstract_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._abstract_gf_content.getvalue())

    def assert_semantic_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._semantic_gf_content.getvalue())

    def assert_natural_language_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._natural_language_gf_content.getvalue())

    def _assert_begins_with(self, expected_beginning, actual_string):
        self.assertTrue(
            actual_string.startswith(expected_beginning),
            "expected %r to begin with %r" % (actual_string, expected_beginning)
        )


class HeaderTestCase(AutoGeneratorTestCase):
    def test_header(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_begins_with("abstract MockupDdd = TDM, Integers ** {")
        self.assert_semantic_begins_with(
            "concrete MockupDdd_sem of MockupDdd = TDM_sem, Integers_sem ** open Utils_sem in {"
        )
        self.assert_natural_language_begins_with(
            "concrete MockupDdd_eng of MockupDdd = TDM_eng, Integers_eng ** open Utils_eng, Prelude in {"
        )


class CategoriesTestCase(AutoGeneratorTestCase):
    def test_sortal_category(self):
        self.given_ontology(sorts={"city": {}}, predicates={}, actions=set([]), individuals={})
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_category("Sort_city;\n")

    def test_predicate_category(self):
        self.given_ontology(sorts={"city": {}}, predicates={"dest_city": "city"}, actions=set([]), individuals={})
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_category("Predicate_dest_city;\n")


class ActionTestCase(AutoGeneratorTestCase):
    def test_action_base_case(self):
        self.given_grammar([
            Node(Constants.ACTION, {"name": "settings"}, [Node(Constants.ITEM, {}, [u"inställningar"])])
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : VpAction;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization(
            u'settings = (mkverb "inställningar" "inställningar" "inställningar");'
        )

    def test_vp_action_as_single_variant(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "set_time"}, [
                    Node(
                        Constants.ITEM, {}, [
                            Node(
                                Constants.VP, {}, [
                                    Node(Constants.INFINITIVE, {}, [u"ställ in"]),
                                    Node(Constants.IMPERATIVE, {}, [u"ställ in"]),
                                    Node(Constants.ING_FORM, {}, [u"ställer in"]),
                                    Node(Constants.OBJECT, {}, ["klockan"])
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('set_time : VpAction;')
        self.assert_semantic_contains_linearization('set_time = pp "set_time";')
        self.assert_natural_language_contains_linearization(
            u'set_time = (mkverb "ställ in" "ställ in" "ställer in" "klockan");'
        )

    def test_vp_action_among_multiple_variants(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "set_time"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    Node(
                                        Constants.VP, {}, [
                                            Node(Constants.INFINITIVE, {}, [u"ställ in"]),
                                            Node(Constants.IMPERATIVE, {}, [u"ställ in"]),
                                            Node(Constants.ING_FORM, {}, [u"ställer in"]),
                                            Node(Constants.OBJECT, {}, ["klockan"])
                                        ]
                                    )
                                ]
                            ),
                            Node(Constants.ITEM, {}, [u"sätt klockan"])
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('set_time : VpAction;')
        self.assert_semantic_contains_linearization('set_time = pp "set_time";')
        self.assert_natural_language_contains_linearization(
            u'set_time = (mkverb "ställ in" "ställ in" "ställer in" "klockan"|mkverb "sätt klockan" "sätt klockan" "sätt klockan");'
        )

    def test_np_action_with_explicit_definite(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "settings"}, [
                    Node(
                        Constants.NP, {}, [
                            Node(Constants.INDEFINITE, {}, [u"inställningar"]),
                            Node(Constants.DEFINITE, {}, [u"inställningarna"])
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : NpAction;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization(u'settings = (mkdef "inställningar" "inställningarna");')

    def test_np_action_with_implicit_definite(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "settings"},
                [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"preferences"])])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : NpAction;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization('settings = (mkdef "preferences");')

    def test_singular_feminine_np_action(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {
                    "name": "settings",
                    "number": tala.nl.gf.resource.SINGULAR,
                    "gender": tala.nl.gf.resource.FEMININE
                }, [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"impostazione"])])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : NpActionSF;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization('settings = (mkdef "impostazione");')

    def test_singular_masculine_np_action(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {
                    "name": "top",
                    "number": tala.nl.gf.resource.SINGULAR,
                    "gender": tala.nl.gf.resource.MASCULINE
                }, [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"menu principale"])])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('top : NpActionSM;')
        self.assert_semantic_contains_linearization('top = pp "top";')
        self.assert_natural_language_contains_linearization('top = (mkdef "menu principale");')

    def test_plural_feminine_np_action(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {
                    "name": "settings",
                    "number": tala.nl.gf.resource.PLURAL,
                    "gender": tala.nl.gf.resource.FEMININE
                }, [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"impostazioni"])])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : NpActionPF;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization('settings = (mkdef "impostazioni");')

    def test_plural_masculine_np_action(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {
                    "name": "top",
                    "number": tala.nl.gf.resource.PLURAL,
                    "gender": tala.nl.gf.resource.MASCULINE
                }, [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"menu principali"])])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('top : NpActionPM;')
        self.assert_semantic_contains_linearization('top = pp "top";')
        self.assert_natural_language_contains_linearization('top = (mkdef "menu principali");')

    def test_np_action_among_multiple_variants(self):
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "settings"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(Constants.ITEM, {}, ["options"]),
                            Node(
                                Constants.ITEM, {},
                                [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"preferences"])])]
                            )
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('settings : NpAction;')
        self.assert_semantic_contains_linearization('settings = pp "settings";')
        self.assert_natural_language_contains_linearization('settings = (mkdef "preferences");')
        self.assert_natural_language_contains_linearization('settings_request = ss (("options"));')


class PredicateTestCase(AutoGeneratorTestCase):
    def test_predicate_base_case(self):
        self.given_grammar([
            Node(Constants.PREDICATE, {"name": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])
        self.when_generating()
        self.assert_abstract_contains_function('price : Predicate;')
        self.assert_semantic_contains_linearization('price = pp "price";')
        self.assert_natural_language_contains_linearization('price = ss (("price information"));')


class TitleTestCase(AutoGeneratorTestCase):
    def test_issue_title(self):
        self.given_grammar([
            Node(Constants.ISSUE_TITLE, {"predicate": "price"}, [Node(Constants.ITEM, {}, ["Price Information"])])
        ])
        self.when_generating()
        self.assert_abstract_contains_function('price_title : SysTitle;')
        self.assert_semantic_contains_linearization('price_title = issueTitle price;')
        self.assert_natural_language_contains_linearization('price_title = ss "Price Information";')

    def test_action_title(self):
        self.given_compulsory_grammar_for_app()
        self.given_grammar([Node(Constants.ACTION_TITLE, {"action": "top"}, [Node(Constants.ITEM, {}, ["Main Menu"])])])
        self.when_generating()
        self.assert_abstract_contains_function('top_title : SysTitle;')
        self.assert_semantic_contains_linearization('top_title = actionTitle (pp "top");')
        self.assert_natural_language_contains_linearization('top_title = ss "Main Menu";')


class test_parameterized_sys_form_answer(AutoGeneratorTestCase):
    def test_in_middle(self):
        self.given_form(
            Node(
                Constants.ITEM, {},
                ["cannot set the hour to ",
                 Node(Constants.SLOT, {"predicate": "hour_to_set"}), "."]
            )
        )
        self.given_generator()
        self.when_called()
        self.then_result_is('"cannot set the hour to " ++ hour_to_set.alt ++ "."')

    def test_at_start(self):
        self.given_form(
            Node(Constants.ITEM, {}, [Node(Constants.SLOT, {"predicate": "hour_to_set"}), " is not an OK hour."])
        )
        self.given_generator()
        self.when_called()
        self.then_result_is('hour_to_set.alt ++ " is not an OK hour."')

    def test_at_end(self):
        self.given_form(
            Node(Constants.ITEM, {}, ["cannot set the hour to ",
                                      Node(Constants.SLOT, {"predicate": "hour_to_set"})])
        )
        self.given_generator()
        self.when_called()
        self.then_result_is('"cannot set the hour to " ++ hour_to_set.alt')

    def test_two_parameters(self):
        self.given_form(
            Node(
                Constants.ITEM, {}, [
                    "cannot set the time to ",
                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                    Node(Constants.SLOT, {"predicate": "minute_to_set"})
                ]
            )
        )
        self.given_generator()
        self.when_called()
        self.then_result_is('"cannot set the time to " ++ hour_to_set.alt ++ " " ++ minute_to_set.alt')

    def test_two_parameters_switched_order(self):
        self.given_form(
            Node(
                Constants.ITEM, {}, [
                    "cannot set the time to ",
                    Node(Constants.SLOT, {"predicate": "minute_to_set"}), " past ",
                    Node(Constants.SLOT, {"predicate": "hour_to_set"})
                ]
            )
        )
        self.given_generator()
        self.when_called()
        self.then_result_is('"cannot set the time to " ++ minute_to_set.alt ++ " past " ++ hour_to_set.alt')

    def test_in_middle_unicode(self):
        self.given_form(
            Node(
                Constants.ITEM, {},
                [u"kan inte ställa timmen till ",
                 Node(Constants.SLOT, {"predicate": "hour_to_set"}), "."]
            )
        )
        self.given_generator()
        self.when_called()
        self.then_result_is(u'"kan inte ställa timmen till " ++ hour_to_set.alt ++ "."')

    def when_called(self):
        self._actual_result = self.generator._parameterized_sys_form(self._form)

    def then_result_is(self, expected_gf_content):
        self.assertEquals(expected_gf_content, self._actual_result)


class UsrRequestTest(AutoGeneratorTestCase):
    def _create_mock_ddd(self):
        self._ensure_ontology_exists()
        self._ensure_domain_exists()

        self._ddd = Mock(spec=DDD)
        self._ddd.domain = self._domain
        self._ddd.name = "MockupDdd"
        self._ddd.ontology = self._ontology

    def test_two_parameters(self):
        self.given_form(
            Node(
                Constants.ITEM, {}, [
                    "set the time to ",
                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                    Node(Constants.SLOT, {"predicate": "minute_to_set"})
                ]
            )
        )
        self.given_generator()
        self.when_generating_action_content("set_time")
        self.assert_abstract_contains(
            'set_time_request_1 : Predicate_hour_to_set -> Predicate_minute_to_set -> UsrRequest;'
        )
        self.assert_semantic_contains(
            'set_time_request_1 hour_to_set minute_to_set = request (pp "set_time") hour_to_set minute_to_set;\n'
        )
        self.assert_natural_language(
            'set_time_request_1 hour_to_set minute_to_set = ss ("set the time to " ++ hour_to_set.s ++ " " ++ minute_to_set.s);\n'
        )

    def test_two_parameters_unicode(self):
        self.given_form(
            Node(
                Constants.ITEM, {}, [
                    u"ställ klockan på ",
                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                    Node(Constants.SLOT, {"predicate": "minute_to_set"})
                ]
            )
        )
        self.given_generator()
        self.when_generating_action_content("set_time")
        self.assert_abstract_contains(
            'set_time_request_1 : Predicate_hour_to_set -> Predicate_minute_to_set -> UsrRequest;'
        )
        self.assert_semantic_contains(
            'set_time_request_1 hour_to_set minute_to_set = request (pp "set_time") hour_to_set minute_to_set;\n'
        )
        self.assert_natural_language(
            u'set_time_request_1 hour_to_set minute_to_set = ss ("ställ klockan på " ++ hour_to_set.s ++ " " ++ minute_to_set.s);\n'
        )

    def test_action_with_literal_parameter(self):
        self.given_form(
            Node(
                Constants.ITEM, {},
                ["leave a comment to the housing owner that ",
                 Node(Constants.SLOT, {"predicate": "comment"})]
            )
        )
        self.given_generator()
        self.when_generating_action_content("leave_comment")
        self.assert_abstract_contains(
            'leave_comment : VpAction;\n'
            'leave_comment_request_1 : Predicate_comment -> UsrRequest;\n'
        )
        self.assert_semantic_contains(
            'leave_comment = pp "leave_comment";\n'
            'leave_comment_request_1 comment = request (pp "leave_comment") comment;\n'
        )
        self.assert_natural_language(
            'leave_comment_request_1 comment = ss ("leave a comment to the housing owner that " ++ comment.s);\n'
        )

    def test_action_with_literal_and_non_literal_parameter(self):
        self.given_form(
            Node(
                Constants.ITEM, {}, [
                    "I will arrive at ",
                    Node(Constants.SLOT, {"predicate": "hour_to_set"}),
                    "and leave a comment to the housing owner that ",
                    Node(Constants.SLOT, {"predicate": "comment"})
                ]
            )
        )
        self.given_generator()
        self.when_generating_action_content("leave_comment")
        self.assert_abstract_contains(
            'leave_comment : VpAction;\n'
            'leave_comment_request_1 : Predicate_hour_to_set -> Predicate_comment -> UsrRequest;\n'
        )
        self.assert_semantic_contains(
            'leave_comment = pp "leave_comment";\n'
            'leave_comment_request_1 hour_to_set comment = request (pp "leave_comment") hour_to_set comment;\n'
        )
        self.assert_natural_language(
            'leave_comment_request_1 hour_to_set comment = ss ("I will arrive at " ++ hour_to_set.s ++ "and leave a comment to the housing owner that " ++ comment.s);\n'
        )


class ValidityTest(AutoGeneratorTestCase):
    def test_all_parameters_in_grammar(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "cannot go from ",
                            Node(Constants.SLOT, {"predicate": "dept_city"}), " to ",
                            Node(Constants.SLOT, {"predicate": "dest_city"})
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_1 : SysAnswer -> SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_1 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_1 dept_city dest_city = ss ("cannot go from " ++ dept_city.alt ++ " to " ++ dest_city.alt);'
        )

    def test_honour_parameter_order_in_grammar(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "cannot go to ",
                            Node(Constants.SLOT, {"predicate": "dest_city"}), " from ",
                            Node(Constants.SLOT, {"predicate": "dept_city"})
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_1 : SysAnswer -> SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_1 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_1 dept_city dest_city = ss ("cannot go to " ++ dest_city.alt ++ " from " ++ dept_city.alt);'
        )

    def test_only_one_optional_parameter_in_grammar(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"},
                [Node(Constants.ITEM, {},
                      ["cannot go from ", Node(Constants.SLOT, {"predicate": "dept_city"})])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_1 : SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_1 dept_city = ss ("cannot go from " ++ dept_city.alt);'
        )

    def test_dont_confuse_parameters(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {},
                                ["cannot go from ", Node(Constants.SLOT, {"predicate": "dept_city"})]
                            ),
                            Node(
                                Constants.ITEM, {},
                                ["cannot go to ", Node(Constants.SLOT, {"predicate": "dest_city"})]
                            )
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_1 : SysAnswer -> SysICM;")
        self.assert_abstract_contains_function("CityValidity_2 : SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.assert_semantic_contains_linearization(
            'CityValidity_2 dest_city = rejectICM (set (list dest_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_1 dept_city = ss ("cannot go from " ++ dept_city.alt);'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_2 dest_city = ss ("cannot go to " ++ dest_city.alt);'
        )

    def test_grammar_may_exclude_some_optional_parameter(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"},
                [Node(Constants.ITEM, {},
                      ["cannot go from ", Node(Constants.SLOT, {"predicate": "dept_city"})])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_2 : SysAnswer -> SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_2 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization(
            'CityValidity_2 dept_city dest_city = ss ("cannot go from " ++ dept_city.alt);'
        )

    def test_grammar_may_exclude_all_optional_parameter(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_grammar([
            Node(Constants.VALIDITY, {"name": "CityValidity"}, [Node(Constants.ITEM, {}, ["invalid parameters"])])
        ])
        self.when_generating()
        self.assert_abstract_contains_function("CityValidity_1 : SysAnswer -> SysICM;")
        self.assert_abstract_contains_function("CityValidity_2 : SysAnswer -> SysICM;")
        self.assert_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.assert_semantic_contains_linearization(
            'CityValidity_2 dest_city = rejectICM (set (list dest_city)) "CityValidity";'
        )
        self.assert_natural_language_contains_linearization('CityValidity_1 dept_city = ss ("invalid parameters");')
        self.assert_natural_language_contains_linearization('CityValidity_2 dest_city = ss ("invalid parameters")')


class MockAutoGenerator(AutoGenerator):
    def _missing_entry(self, reporting_method, *args):
        self.missing_entry_warned = True
        reporting_method(*args)

    def _warn(self, line):
        self.warning += line
        self.warning += '\n'


class ReportTestCase(AutoGeneratorTestCase):
    def test_multiple_parameters_base(self):
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "the time was set to ",
                            Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                            Node(Constants.SLOT, {"predicate": "minute_to_set"}), "."
                        ]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("hour_to_set"),
                    ServiceParameter("minute_to_set"),
                ],
                failure_reasons=[]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysAnswer -> SysAnswer -> SysReportEnded;\n')
        self.assert_semantic_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = report_ended "SetTime" (list hour_to_set minute_to_set);\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = ss ("the time was set to " ++ hour_to_set.alt ++ " " ++ minute_to_set.alt ++ ".");\n'
        )

    def test_multiple_parameters_with_other_order_in_grammar_entry(self):
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "the time was set to ",
                            Node(Constants.SLOT, {"predicate": "minute_to_set"}), " past ",
                            Node(Constants.SLOT, {"predicate": "hour_to_set"}), "."
                        ]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("hour_to_set"),
                    ServiceParameter("minute_to_set"),
                ],
                failure_reasons=[]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysAnswer -> SysAnswer -> SysReportEnded;\n')
        self.assert_semantic_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = report_ended "SetTime" (list hour_to_set minute_to_set);\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = ss ("the time was set to " ++ minute_to_set.alt ++ " past " ++ hour_to_set.alt ++ ".");\n'
        )

    def test_multiple_parameters_with_default(self):
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "the time was set to ",
                            Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                            Node(Constants.SLOT, {"predicate": "minute_to_set"}), "."
                        ]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("hour_to_set", is_optional=True),
                    ServiceParameter("minute_to_set", is_optional=True),
                ],
                failure_reasons=[]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysAnswer -> SysAnswer -> SysReportEnded;\n')
        self.assert_semantic_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = report_ended "SetTime" (list hour_to_set minute_to_set);\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = ss ("the time was set to " ++ hour_to_set.alt ++ " " ++ minute_to_set.alt ++ ".");\n'
        )

    def test_parameters_ignored_in_grammar_entry(self):
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(Constants.ITEM, {}, ["the time was set."])])
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("hour_to_set"),
                    ServiceParameter("minute_to_set"),
                ],
                failure_reasons=[]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysAnswer -> SysAnswer -> SysReportEnded;\n')
        self.assert_semantic_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = report_ended "SetTime" (list hour_to_set minute_to_set);\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_ended_SetTime_1 hour_to_set minute_to_set = ss ("the time was set.");\n'
        )

    def test_no_parameters(self):
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(Constants.ITEM, {}, ["the time was set."])])
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysReportEnded;\n')
        self.assert_semantic_contains_linearization('report_ended_SetTime_1 = report_ended "SetTime" (empty_list);\n')
        self.assert_natural_language_contains_linearization('report_ended_SetTime_1 = ss ("the time was set.");\n')

    def test_empty_form(self):
        self.given_grammar([Node(Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(Constants.ITEM, {}, [])])])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_generator()
        self.when_generating()
        self._then_no_exception_is_raised()

    def test_unicode(self):
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(Constants.ITEM, {}, [u"klockan har ställts in."])]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_ended_SetTime_1 : SysReportEnded;\n')
        self.assert_semantic_contains_linearization('report_ended_SetTime_1 = report_ended "SetTime" (empty_list);\n')
        self.assert_natural_language_contains_linearization(
            u'report_ended_SetTime_1 = ss ("klockan har ställts in.");\n'
        )

    def test_reason_and_no_parameters(self):
        self.given_grammar([
            Node(
                Constants.REPORT_FAILED, {
                    "action": "Snooze",
                    "reason": "not_ringing"
                }, [Node(Constants.ITEM, {}, ["the alarm is not ringing."])]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "Snooze",
                DeviceModuleTarget(device="MockedDevice"),
                parameters=[],
                failure_reasons=[
                    ActionFailureReason("not_ringing"),
                ]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_failed_Snooze_not_ringing_2 : SysReportFailed;\n')
        self.assert_semantic_contains_linearization(
            'report_failed_Snooze_not_ringing_2 = report_failed "Snooze" (empty_list) "not_ringing";\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_Snooze_not_ringing_2 = ss ("the alarm is not ringing.");\n'
        )

    def test_reason_and_optional_parameter(self):
        self.given_grammar([
            Node(
                Constants.REPORT_FAILED, {
                    "action": "SetTime",
                    "reason": "invalid_time"
                }, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    "failed to set the time to ",
                                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " hours."
                                ]
                            ),
                            Node(
                                Constants.ITEM, {}, [
                                    "failed to set the time to ",
                                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                                    Node(Constants.SLOT, {"predicate": "minute_to_set"}), "."
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                DeviceModuleTarget(device="MockedDevice"),
                parameters=[ServiceParameter("hour_to_set"),
                            ServiceParameter("minute_to_set", is_optional=True)],
                failure_reasons=[
                    ActionFailureReason("invalid_time"),
                ]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_failed_SetTime_invalid_time_3 : SysAnswer -> SysReportFailed;\n')
        self.assert_abstract_contains_function(
            'report_failed_SetTime_invalid_time_4 : SysAnswer -> SysAnswer -> SysReportFailed;\n'
        )
        self.assert_semantic_contains_linearization(
            'report_failed_SetTime_invalid_time_3 hour_to_set = report_failed "SetTime" (list hour_to_set) "invalid_time";\n'
        )
        self.assert_semantic_contains_linearization(
            'report_failed_SetTime_invalid_time_4 hour_to_set minute_to_set = report_failed "SetTime" (list hour_to_set minute_to_set) "invalid_time";\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_SetTime_invalid_time_3 hour_to_set = ss ("failed to set the time to " ++ hour_to_set.alt ++ " hours.");\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_SetTime_invalid_time_4 hour_to_set minute_to_set = ss ("failed to set the time to " ++ hour_to_set.alt ++ " " ++ minute_to_set.alt ++ ".");\n'
        )

    def test_unknown_failure_without_parameters(self):
        class Snooze(DeviceAction):
            PARAMETERS = []

        self.given_grammar([])
        self.given_service_interface_has_action(
            ServiceActionInterface("Snooze", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('report_failed_Snooze_undefined_failure_1 : SysReportFailed;\n')
        self.assert_semantic_contains_linearization(
            'report_failed_Snooze_undefined_failure_1 = report_failed "Snooze" (empty_list) "%s";\n' %
            UNDEFINED_SERVICE_ACTION_FAILURE
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_Snooze_undefined_failure_1 = undefined_service_action_failure;\n'
        )

    def test_unknown_failure_with_parameters(self):
        self.given_grammar([
            Node(
                Constants.REPORT_FAILED, {
                    "action": "SetTime",
                    "reason": "invalid_time"
                }, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    "failed to set the time to ",
                                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " hours."
                                ]
                            ),
                            Node(
                                Constants.ITEM, {}, [
                                    "failed to set the time to ",
                                    Node(Constants.SLOT, {"predicate": "hour_to_set"}), " ",
                                    Node(Constants.SLOT, {"predicate": "minute_to_set"}), "."
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime",
                self.mock_service_target,
                parameters=[ServiceParameter("hour_to_set"),
                            ServiceParameter("minute_to_set", is_optional=True)],
                failure_reasons=[]
            )
        )
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function(
            'report_failed_SetTime_undefined_failure_1 : SysAnswer -> SysReportFailed;\n'
        )
        self.assert_abstract_contains_function(
            'report_failed_SetTime_undefined_failure_2 : SysAnswer -> SysAnswer -> SysReportFailed;\n'
        )
        self.assert_semantic_contains_linearization(
            'report_failed_SetTime_undefined_failure_1 hour_to_set = report_failed "SetTime" (list hour_to_set) "%s";\n'
            % UNDEFINED_SERVICE_ACTION_FAILURE
        )
        self.assert_semantic_contains_linearization(
            'report_failed_SetTime_undefined_failure_2 hour_to_set minute_to_set = report_failed "SetTime" (list hour_to_set minute_to_set) "%s";\n'
            % UNDEFINED_SERVICE_ACTION_FAILURE
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_SetTime_undefined_failure_1 hour_to_set = undefined_service_action_failure;\n'
        )
        self.assert_natural_language_contains_linearization(
            'report_failed_SetTime_undefined_failure_2 hour_to_set minute_to_set = undefined_service_action_failure;\n'
        )


class VerbPhraseTest(AutoGeneratorTestCase):
    def test_verb_phrase(self):
        self.given_form(
            Node(
                Constants.VP, {}, [
                    Node(Constants.INFINITIVE, {}, ["set"]),
                    Node(Constants.IMPERATIVE, {}, ["set"]),
                    Node(Constants.ING_FORM, {}, ["setting"]),
                    Node(Constants.OBJECT, {}, ["the time"])
                ]
            )
        )
        self.given_generator()
        self.when_generating_action_content("set_time")
        self.assert_abstract_contains("set_time : VpAction;")
        self.assert_semantic_contains('set_time = pp "set_time";')
        self.assert_natural_language_contains('set_time = (mkverb "set" "set" "setting" "the time")')


class WarningsAndErrorsTest(AutoGeneratorTestCase):
    def test_warn_about_missing_entry_for_postconfirmed_action(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("SetAlarm", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_postconfirmed("SetAlarm")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system report that the service action SetAlarm ended? Specify the utterance:\n\n'
            'SetAlarm_ended = "performed SetAlarm."'
        )

    def test_warn_about_missing_entry_for_preconfirmation(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("SetAlarm", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_preconfirmed("SetAlarm")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system ask the user to confirm the service action SetAlarm, before performing the action? The entry is used in questions such as "Do you want to X?" where X is the grammar entry. Example:\n\n'
            'SetAlarm_preconfirm = "perform SetAlarm."'
        )

    def test_warn_about_missing_entry_for_prereport(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("SetAlarm", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_prereported("SetAlarm")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system give positive feedback about the service action SetAlarm, before performing the action? Specify the utterance:\n\nSetAlarm_prereport = "performing SetAlarm."'
        )

    def test_not_warn_about_missing_entry_if_entry_exists(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("AlarmRings", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_postconfirmed("AlarmRings")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "AlarmRings"}, [Node(Constants.ITEM, {}, ["Beep beep!"])])
        ])
        self.when_generating()
        self.expect_no_warning()

    def test_not_warn_about_missing_entry_if_no_postconfirmation(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("AlarmRings", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_not_postconfirmed("AlarmRings")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_no_warning()

    def test_generates_report_ended_if_entry_exists_even_without_postconfirmation(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("AlarmRings", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_not_postconfirmed("AlarmRings")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "AlarmRings"}, [Node(Constants.ITEM, {}, ["The alarm stopped"])])
        ])
        self.when_generating()
        self.expect_report_ended_was_generated_for_action("AlarmRings")

    def test_unexpected_parameter_name(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "HourValidity", self.mock_service_target, parameters=[ServiceParameter("hour_to_set")]
            )
        )
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "HourValidity"}, [
                    Node(
                        Constants.ITEM, {},
                        ["cannot set the hour to ",
                         Node(Constants.SLOT, {"predicate": "dest_city"}), "."]
                    )
                ]
            )
        ])
        with self.assertRaises(UnexpectedParameter) as cm:
            self.when_generating()
        self.assertIn("unexpected parameter name dest_city ", unicode(cm.exception))

    def test_warn_about_missing_entry_for_action_py_grammar(self):
        self.given_py_grammar()
        self.given_domain_has_plan_for_goal("perform(settings)")
        self.given_compulsory_grammar_for_app(exclude=(Constants.ACTION, {"name": "settings"}))
        self.when_generating()
        self.expect_warning(
            'How do speakers talk about the action settings? Specify the utterance:\n\nsettings = "settings"\n\nAlternatively, you can specify several possible utterances in a list:\n\nsettings = [\n  "settings one way",\n  "settings another way",\n  "settings <answer:city>",\n]'
        )

    def test_warn_about_missing_entry_for_action_xml_grammar(self):
        self.given_xml_grammar()
        self.given_domain_has_plan_for_goal("perform(settings)")
        self.given_compulsory_grammar_for_app(exclude=(Constants.ACTION, {"name": "settings"}))
        self.when_generating()
        self.expect_warning(
            'How do speakers talk about the action settings? Specify the utterance:\n\n  <action name="settings">settings</action>\n\nAlternatively, you can specify several possible utterances in a list:\n\n  <action name="settings">\n    <one-of>\n      <item>settings one way</item>\n      <item>settings another way</item>\n      <item>settings <slot predicate="city" type="individual"/></item>\n    </one-of>\n  </action>'
        )

    def test_warn_about_missing_entry_for_goal_issue_py_grammar(self):
        self.given_py_grammar()
        self.given_domain_has_plan_for_goal("resolve(?X.price(X))")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(Constants.USER_QUESTION, {"predicate": "price"}, [Node(Constants.ITEM, {}, ['what is the price'])])
        ])
        self.when_generating()
        self.expect_warning(
            'How do the speakers talk about the issue price? The entry is used in questions such as "Do you want to know X?" or "I want to know X", where X is the grammar entry.\n\nExample:\n\nprice = "price"\n\nAlternatively, you can specify several possible utterances in a list:\n\nprice = [\n  "price one way",\n  "price another way",\n]'
        )

    def test_warn_about_missing_entry_for_goal_issue_xml_grammar(self):
        self.given_xml_grammar()
        self.given_domain_has_plan_for_goal("resolve(?X.price(X))")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(Constants.USER_QUESTION, {"predicate": "price"}, [Node(Constants.ITEM, {}, ['what is the price'])])
        ])
        self.when_generating()
        self.expect_warning(
            'How do the speakers talk about the issue price? The entry is used in questions such as "Do you want to know X?" or "I want to know X", where X is the grammar entry.\n\nExample:\n\n  <question speaker="all" predicate="price" type="wh_question">price</question>\n\nAlternatively, you can specify several possible utterances in a list:\n\n  <question speaker="all" predicate="price" type="wh_question">\n    <one-of>\n      <item>price one way</item>\n      <item>price another way</item>\n    </one-of>\n  </question>'
        )

    def test_warn_about_missing_entry_for_user_question(self):
        self.given_domain_has_plan_for_goal("resolve(?X.price(X))")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([Node(Constants.PREDICATE, {"name": "price"}, [Node(Constants.ITEM, {}, ['price'])])])
        self.when_generating()
        self.expect_warning(
            'How does the user ask about price?\n\nExample:\n\nprice_user_question = [\n  "what is price",\n  "i want to know price"\n]'
        )

    def test_warn_about_missing_entry_for_system_question_py_grammar(self):
        self.given_py_grammar()
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system ask about dest_city?\n\nExample:\n\ndest_city_sys_question = "what is dest city"'
        )

    def test_warn_about_missing_entry_for_system_question_xml_grammar(self):
        self.given_xml_grammar()
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system ask about dest_city?\n\nExample:\n\n  <question speaker="system" predicate="dest_city" type="wh_question">what is dest city</question>'
        )

    def test_not_warn_about_system_question_due_to_explicit_entry(self):
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(
                Constants.SYS_QUESTION, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, ["where do you want to go"])]
            )
        ])
        self.when_generating()
        self.expect_no_warning()

    def test_not_warn_about_system_question_due_to_general_entry(self):
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(Constants.PREDICATE, {"name": "dest_city"}, [Node(Constants.ITEM, {}, ["the destination"])])
        ])
        self.when_generating()
        self.expect_no_warning()

    def test_warn_about_missing_entry_for_individual_py_grammar(self):
        self.given_py_grammar()
        self.given_compulsory_grammar_for_app(exclude=(Constants.INDIVIDUAL, {"name": "new_york"}))
        self.when_generating()
        self.expect_warning(
            'How do speakers talk about the individual new_york? Specify the utterance:\n\nnew_york = "new york"\n\nAlternatively, you can specify several possible utterances in a list:\n\nnew_york = [\n  "new york one way",\n  "new york another way",\n]'
        )

    def test_warn_about_missing_entry_for_individual_xml_grammar(self):
        self.given_xml_grammar()
        self.given_compulsory_grammar_for_app(exclude=(Constants.INDIVIDUAL, {"name": "new_york"}))
        self.when_generating()
        self.expect_warning(
            'How do speakers talk about the individual new_york? Specify the utterance:\n\n  <individual name="new_york">new york</individual>\n\nAlternatively, you can specify several possible utterances in a list:\n\n  <individual name="new_york">\n    <one-of>\n      <item>new york one way</item>\n      <item>new york another way</item>\n    </one-of>\n  </individual>'
        )

    def test_warn_about_missing_validity_entry(self):
        self.given_service_interface_has_validity(
            ServiceValidatorInterface(
                "CityValidity",
                self.mock_service_target,
                parameters=[
                    ServiceParameter("dept_city", is_optional=True),
                    ServiceParameter("dest_city", is_optional=True),
                ]
            )
        )
        self.given_compulsory_grammar_for_app()
        self.when_generating()
        self.expect_warning(
            'How does the system report that the device validity CityValidity is unsatisfied? Specify the utterance:\n\nCityValidity = "invalid parameters <answer:dept_city> <answer:dest_city>"'
        )

    def test_background_with_string_answer_raises_exception(self):
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "location"}, [
                    Node(
                        Constants.ITEM, {}, [
                            Node(Constants.SLOT, {"predicate": "frequent_flyer_points"}),
                            " blablabla ",
                            Node(Constants.SLOT, {"predicate": "location"}),
                        ]
                    )
                ]
            )
        ])
        with self.assertRaises(InvalidSortOfBackgroundPredicateException) as e:
            self.when_generating()
        self.assertIn(
            "Background is not allowed for predicate 'location' of sort 'string'. Perhaps you can create a new sort for it?",
            e.exception
        )

    def test_background_with_integer_answer_raises_exception(self):
        self.given_compulsory_grammar_for_app()
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "frequent_flyer_points"}, [
                    Node(
                        Constants.ITEM, {}, [
                            Node(Constants.SLOT, {"predicate": "frequent_flyer_points"}),
                            " blablabla ",
                            Node(Constants.SLOT, {"predicate": "location"}),
                        ]
                    )
                ]
            )
        ])
        with self.assertRaises(InvalidSortOfBackgroundPredicateException) as e:
            self.when_generating()
        self.assertIn(
            "Background is not allowed for predicate 'frequent_flyer_points' of sort 'integer'. Perhaps you can create a new sort for it?",
            e.exception
        )

    def test_can_be_asked_by_system_true(self):
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_generator()
        self.assertEquals(True, self.generator._can_be_asked_by_system("dest_city"))

    def test_can_be_asked_by_system_false(self):
        self.given_some_plan_contains("findout(?X.goal(X))")
        self.given_generator()
        self.assertEquals(False, self.generator._can_be_asked_by_system("dest_city"))

    def test_can_be_asked_by_system_false_for_features(self):
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_generator()
        self.assertEquals(False, self.generator._can_be_asked_by_system("dest_city_type"))

    def given_device_has_mockup_actions(self, action_names):
        for action_name in action_names:
            setattr(self._device_class, action_name, self._create_service_action(action_name))

    def given_action_is_postconfirmed(self, action_name):
        self._add_to_any_plan("invoke_service_action(%s, {postconfirm=True})" % action_name)

    def given_action_is_not_postconfirmed(self, action_name):
        pass

    def given_action_is_preconfirmed(self, action_name):
        self._add_to_any_plan("invoke_service_action(%s, {preconfirm=interrogative})" % action_name)

    def given_action_is_prereported(self, action_name):
        self._add_to_any_plan("invoke_service_action(%s, {preconfirm=assertive})" % action_name)

    def given_domain_has_plan_for_goal(self, goal_as_string):
        self._ensure_ontology_exists()
        self._ensure_domain_exists()
        goal = self._parser.parse(goal_as_string)
        self._domain.plans[goal] = {"goal": goal, "plan": Plan([])}

    def given_some_plan_contains(self, plan_item_as_string):
        self._add_to_any_plan(plan_item_as_string)

    def _add_to_any_plan(self, plan_item_as_string):
        self._ensure_ontology_exists()
        self._ensure_domain_exists()
        plan_item = self._parser.parse(plan_item_as_string)
        any_goal = self._domain.plans.keys()[0]
        self._domain.plans[any_goal]["plan"].push(plan_item)

    def expect_warning(self, expected_warning):
        self.assertEquals(expected_warning, self.generator.warning.strip())

    def expect_no_warning(self):
        self.assertEquals("", self.generator.warning)

    def expect_report_ended_was_generated_for_action(self, action_name):
        self.assert_abstract_contains_function('report_ended_AlarmRings_1 : SysReportEnded;\n')


class SysAnswerTest(AutoGeneratorTestCase):
    def setUp(self):
        AutoGeneratorTestCase.setUp(self)
        self._form = None

    def test_default_unary_propositional_system_answer_of_custom_sort(self):
        self.given_generator()
        self.when_generating_system_answer_content("dest_city")
        self.assert_abstract("dest_city_sys_answer : Sort_city -> SysAnswer;\n")
        self.assert_semantic("dest_city_sys_answer individual = pp dest_city.s individual;\n")
        self.assert_natural_language("dest_city_sys_answer individual = answer (individual.s) individual.s;\n")

    def test_overridden_unary_propositional_system_answer_of_custom_sort(self):
        self.given_generator()
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, [u"på ", Node(Constants.SLOT, {})])]
            )
        ])
        self.when_generating_system_answer_content("dest_city")
        self.assert_abstract("dest_city_sys_answer : Sort_city -> SysAnswer;\n")
        self.assert_semantic("dest_city_sys_answer individual = pp dest_city.s individual;\n")
        self.assert_natural_language(u'dest_city_sys_answer individual = answer ("på" ++ individual.s) individual.s;\n')

    def test_nullary_propositional_system_answer(self):
        self.given_generator()
        self.given_grammar([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                [Node(Constants.ITEM, {}, ["you are qualified for membership"])]
            ),
            Node(
                Constants.NEGATIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                [Node(Constants.ITEM, {}, ["you are not qualified for membership"])]
            )
        ])
        self.when_generating_system_answer_content("qualified_for_membership")
        self.assert_abstract(
            "qualified_for_membership_positive_sys_answer : SysAnswer;\n"
            "qualified_for_membership_negative_sys_answer : SysAnswer;\n"
        )
        self.assert_semantic(
            'qualified_for_membership_positive_sys_answer = pp qualified_for_membership.s;\n'
            'qualified_for_membership_negative_sys_answer = pp ("~" ++ qualified_for_membership.s);\n'
        )
        self.assert_natural_language(
            'qualified_for_membership_positive_sys_answer = answer "you are qualified for membership";\n'
            'qualified_for_membership_negative_sys_answer = answer "you are not qualified for membership";\n'
        )

    def test_no_entry_for_nullary_predicate(self):
        self.given_generator()
        self.when_generating_system_answer_content("qualified_for_membership")
        self.assert_abstract("")
        self.assert_semantic("")
        self.assert_natural_language("")

    def test_nullary_no_sortal_user_answer(self):
        self.given_generator()
        self.given_grammar([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                [Node(Constants.ITEM, {}, ["you are qualified for membership"])]
            ),
            Node(
                Constants.NEGATIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"},
                [Node(Constants.ITEM, {}, ["you are not qualified for membership"])]
            )
        ])
        self.when_generating_sortal_answer_content("qualified_for_membership")
        self.assert_abstract("")
        self.assert_semantic("")
        self.assert_natural_language("")

    def test_default_integer_system_answer(self):
        self.given_generator()
        self.when_generating_system_answer_content("distance")
        self.assert_abstract("distance_sys_answer : Integer -> SysAnswer;\n")
        self.assert_semantic('distance_sys_answer individual = pp "distance" individual;\n')
        self.assert_natural_language("distance_sys_answer individual = individual;\n")

    def test_overridden_integer_system_answer(self):
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "distance"},
                [Node(Constants.ITEM, {}, ["the distance is ", Node(Constants.SLOT, {}), "meters"])]
            )
        ])
        self.given_generator()
        self.when_generating_system_answer_content("distance")
        self.assert_abstract("distance_sys_answer : Integer -> SysAnswer;\n")
        self.assert_semantic('distance_sys_answer individual = pp "distance" individual;\n')
        self.assert_natural_language(
            'distance_sys_answer individual = answer ("the distance is" ++ individual.s ++ "meters") individual.s;\n'
        )

    def when_generating_system_answer_content(self, predicate_name):
        self.generator._grammar = self._grammar
        self.generator._generate_system_answer_content(self.get_predicate(predicate_name))

    def when_generating_sortal_answer_content(self, predicate_name):
        self.generator._grammar = self._grammar
        self.generator._generate_sortal_user_answer(
            self.get_predicate(predicate_name),
            self.get_predicate(predicate_name).getSort()
        )

    def test_default_string_system_answer(self):
        self.given_generator()
        self.when_generating_system_answer_content("location")
        self.assert_abstract_contains("location_sys_answer_0 : SysAnswer;\n")
        self.assert_semantic_contains('location_sys_answer_0 = pp "location" string_placeholder_0;\n')
        self.assert_natural_language_contains('location_sys_answer_0 = answer ("_STR0_");\n')

    def test_overridden_string_system_answer(self):
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "location"},
                [Node(Constants.ITEM, {}, [u"du är på ", Node(Constants.SLOT, {})])]
            )
        ])
        self.given_generator()
        self.when_generating_system_answer_content("location")
        self.assert_abstract_contains("location_sys_answer_0 : SysAnswer;\n")
        self.assert_semantic_contains('location_sys_answer_0 = pp "location" string_placeholder_0;\n')
        self.assert_natural_language_contains(u'location_sys_answer_0 = answer ("du är på _STR0_");\n')

    def test_default_datetime_system_answer(self):
        self.given_generator()
        self.when_generating_system_answer_content("flight_departure")
        self.assert_abstract_contains("flight_departure_sys_answer_0 : SysAnswer;\n")
        self.assert_semantic_contains('flight_departure_sys_answer_0 = pp "flight_departure" datetime_placeholder_0;\n')
        self.assert_natural_language_contains('flight_departure_sys_answer_0 = answer ("_datetime_placeholder_0_");\n')

    def test_overridden_datetime_system_answer(self):
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "flight_departure"},
                [Node(Constants.ITEM, {}, [u"The flight departs at", Node(Constants.SLOT, {})])]
            )
        ])
        self.given_generator()
        self.when_generating_system_answer_content("flight_departure")
        self.assert_abstract_contains("flight_departure_sys_answer_0 : SysAnswer;\n")
        self.assert_semantic_contains('flight_departure_sys_answer_0 = pp "flight_departure" datetime_placeholder_0;\n')
        self.assert_natural_language_contains(
            u'flight_departure_sys_answer_0 = answer ("The flight departs at" ++ "_datetime_placeholder_0_");\n'
        )


class UserAnswerTest(AutoGeneratorTestCase):
    def test_default_short_answer_content(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_function("city_user_answer : Sort_city -> UsrAnswer;\n")
        self.assert_semantic_contains_linearization("city_user_answer answer = answer;\n")
        self.assert_natural_language_contains_linearization("city_user_answer answer = answer;\n")

    def test_no_boolean_answer_content(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_not_contains_function("boolean_user_answer : Sort_boolean -> UsrAnswer;\n")
        self.assert_semantic_not_contains_linearization("boolean_user_answer answer = answer;\n")
        self.assert_natural_language_not_contains_linearization("boolean_user_answer answer = answer;\n")

    def test_answer_combination(self):
        self.given_grammar([
            Node(
                Constants.ANSWER_COMBINATION, {}, [
                    Node(
                        Constants.ITEM, {}, [
                            Node(Constants.SLOT, {"predicate": "passenger_quantity_to_add"}), " ",
                            Node(Constants.SLOT, {"predicate": "passenger_type_to_add"})
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function(
            "user_answer_sequence_1 : Predicate_passenger_quantity_to_add -> Predicate_passenger_type_to_add -> UserAnswerSequence;\n"
        )
        self.assert_semantic_contains_linearization(
            'user_answer_sequence_1 passenger_quantity_to_add passenger_type_to_add = moveseq (move "answer" passenger_quantity_to_add) (move "answer" passenger_type_to_add);\n'
        )
        self.assert_natural_language_contains_linearization(
            'user_answer_sequence_1 passenger_quantity_to_add passenger_type_to_add = ss (passenger_quantity_to_add.s ++ " " ++ passenger_type_to_add.s);\n'
        )

    def test_propositional_user_answer_for_custom_sort(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_function(
            "dest_city_propositional_usr_answer : Sort_city -> Predicate_dest_city;\n"
        )
        self.assert_semantic_contains_linearization(
            "dest_city_propositional_usr_answer answer = pp dest_city.s answer;\n"
        )
        self.assert_natural_language_contains_linearization('dest_city_propositional_usr_answer answer = answer;\n')

    def test_propositional_user_answer_for_string_sort(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_function('comment_propositional_usr_answer : Unknown -> Predicate_comment;\n')
        self.assert_semantic_contains_linearization(
            'comment_propositional_usr_answer answer = pp comment.s (ss ("\\"" ++ answer.s ++ "\\""));\n'
        )
        self.assert_natural_language_contains_linearization('comment_propositional_usr_answer answer = answer;\n')

    def test_propositional_user_answer_for_integer_sort(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_function(
            'hour_to_set_propositional_usr_answer : Integer -> Predicate_hour_to_set;\n'
        )
        self.assert_semantic_contains_linearization(
            'hour_to_set_propositional_usr_answer answer = pp hour_to_set.s answer;\n'
        )
        self.assert_natural_language_contains_linearization('hour_to_set_propositional_usr_answer answer = answer;\n')

    def test_generate_sortal_user_answer(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_abstract_contains_function("dest_city_sortal_usr_answer : Sort_city -> UsrAnswer;\n")
        self.assert_semantic_contains_linearization("dest_city_sortal_usr_answer answer = answer;\n")
        self.assert_natural_language_contains_linearization('dest_city_sortal_usr_answer answer = answer;\n')

    def test_generate_sortal_user_answer_with_sort_string(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_generated_gf_contains_sort_user_answer_with_sort_string()

    def assert_generated_gf_contains_sort_user_answer_with_sort_string(self):
        self.assert_abstract_contains_function("comment_sortal_usr_answer : Sort_string -> UsrAnswer;\n")
        self.assert_semantic_contains_linearization("comment_sortal_usr_answer answer = answer;\n")
        self.assert_natural_language_contains_linearization('comment_sortal_usr_answer answer = answer;\n')

    def test_generate_unknown_category(self):
        self.given_grammar([])
        self.when_generating()
        self.assert_unknown_category_is_generated()

    def assert_unknown_category_is_generated(self):
        self.assert_abstract_contains_category(UNKNOWN_CATEGORY)
        self.assert_abstract_contains_function(UNKNOWN_FUNCTION)
        self.assert_abstract_contains_function(MK_UNKNOWN_FUNCTION)

        self.assert_semantic_contains_lincat(UNKNOWN_LINCAT)
        self.assert_semantic_contains_linearization(UNKNOWN_LINERARIZATION)
        self.assert_semantic_contains_linearization(MK_UNKNOWN_LINEARIZATION)

        self.assert_natural_language_contains_linearization(UNKNOWN_NL_LINEARIZATION)
        self.assert_natural_language_contains_linearization(MK_UNKNOWN_NL_LINEARIZATION)


class UserQuestionTest(AutoGeneratorTestCase):
    def test_without_answers(self):
        self.given_grammar([
            Node(Constants.USER_QUESTION, {"predicate": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])
        self.when_generating()
        self.assert_abstract_contains_function("ask_price : UsrWHQ;\n")
        self.assert_semantic_contains_linearization("ask_price = ask_whq price;\n")
        self.assert_natural_language_contains_linearization('ask_price = ss (("price information"));\n')

    def test_with_sortal_answer_of_custom_sort(self):
        self.given_grammar([
            Node(
                Constants.USER_QUESTION, {"predicate": "price"},
                [Node(Constants.ITEM, {}, ["price to ", Node(Constants.SLOT, {"sort": "city"})])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function('price_user_question_1 : Sort_city -> UsrWHQ;\n')
        self.assert_semantic_contains_linearization("price_user_question_1 city = ask_whq price city;\n")
        self.assert_natural_language_contains_linearization(
            'price_user_question_1 city = ss ("price to " ++ city.s);\n'
        )

    def test_with_propositional_answer_of_custom_sort(self):
        self.given_grammar([
            Node(
                Constants.USER_QUESTION, {"predicate": "price"},
                [Node(Constants.ITEM, {}, ["price to ", Node(Constants.SLOT, {"predicate": "dest_city"})])]
            )
        ])
        self.when_generating()
        self.assert_abstract_contains_function("price_user_question_1 : Predicate_dest_city -> UsrWHQ;\n")
        self.assert_semantic_contains_linearization("price_user_question_1 dest_city = ask_whq price dest_city;\n")
        self.assert_natural_language_contains_linearization(
            'price_user_question_1 dest_city = ss ("price to " ++ dest_city.s);\n'
        )

    def test_with_propositional_literal_answer(self):
        self.given_grammar([
            Node(
                Constants.USER_QUESTION, {"predicate": "attraction_information"},
                [Node(Constants.ITEM, {},
                      ["tell me about ", Node(Constants.SLOT, {"predicate": "attraction"})])]
            )
        ])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function(
            'attraction_information_user_question_1 : Predicate_attraction -> UsrWHQ;\n'
        )
        self.assert_semantic_contains_linearization(
            'attraction_information_user_question_1 attraction = ask_whq attraction_information attraction;\n'
        )
        self.assert_natural_language_contains_linearization(
            'attraction_information_user_question_1 attraction = ss ("tell me about " ++ attraction.s);\n'
        )


class SysQuestionTest(AutoGeneratorTestCase):
    def test_base_case(self):
        self.given_form(Node(Constants.ITEM, {}, ["where do you want to go"]))
        self.given_generator()
        self.when_generating_system_question("dest_city")
        self.assert_natural_language('dest_city = ss "where do you want to go";\n')

    def when_generating_system_question(self, predicate_name):
        self.generator._generate_system_question(self.get_predicate(predicate_name), self._form)


class BackgroundEmbeddingTest(AutoGeneratorTestCase):
    def test_single_background_for_wh_question(self):
        self.given_form(Node(Constants.ITEM, {}, ["which hour ", Node(Constants.SLOT, {"predicate": "day_to_set"})]))
        self.given_generator()
        self.when_generating_predicate_content("hour_to_set")
        self.assert_abstract_contains('hour_to_set_ask_whq_with_background_1 : SysAnswer -> System;\n')
        self.assert_semantic_contains(
            'hour_to_set_ask_whq_with_background_1 day_to_set = pp "Move" (move "ask" (eta_expand hour_to_set) (list day_to_set));\n'
        )
        self.assert_natural_language_contains(
            'hour_to_set_ask_whq_with_background_1 day_to_set = ss (CAPIT ++ "which hour " ++ day_to_set.s ++ "?");\n'
        )

    def test_single_background_for_positive_nullary_answer(self):
        self.given_grammar([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "you have ",
                            Node(Constants.SLOT, {"predicate": "frequent_flyer_points"}),
                            " frequent flyer points and are qualified for membership"
                        ]
                    )
                ]
            )
        ])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function(
            'qualified_for_membership_positive_sys_answer : '
            'SysAnswer -> System;\n'
        )
        self.assert_semantic_contains_linearization(
            'qualified_for_membership_positive_sys_answer '
            'frequent_flyer_points = '
            'pp "Move" (move "answer" '
            '(qualified_for_membership) (list frequent_flyer_points));\n'
        )
        self.assert_natural_language_contains_linearization(
            'qualified_for_membership_positive_sys_answer '
            'frequent_flyer_points = '
            'ss (CAPIT ++ "you have" ++ frequent_flyer_points.s ++ '
            '"frequent flyer points and are qualified for membership" '
            '++ ".");\n'
        )

    def test_multi_background_for_positive_nullary_answer(self):
        self.given_grammar([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified_for_membership"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "you have ",
                            Node(Constants.SLOT, {"predicate": "frequent_flyer_points"}),
                            " frequent flyer points and are qualified for "
                            "membership and you are in ",
                            Node(Constants.SLOT, {"predicate": "current_position"})
                        ]
                    )
                ]
            )
        ])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function(
            'qualified_for_membership_positive_sys_answer : '
            'SysAnswer -> SysAnswer -> System;\n'
        )
        self.assert_semantic_contains_linearization(
            'qualified_for_membership_positive_sys_answer '
            'frequent_flyer_points current_position = '
            'pp "Move" (move "answer" '
            '(qualified_for_membership) '
            '(list frequent_flyer_points current_position));\n'
        )
        self.assert_natural_language_contains_linearization(
            'qualified_for_membership_positive_sys_answer '
            'frequent_flyer_points current_position = '
            'ss (CAPIT ++ "you have" ++ frequent_flyer_points.s ++ '
            '"frequent flyer points and are qualified for membership '
            'and you are in" ++ current_position.s ++ ".");\n'
        )

    def test_background_for_propositional_answer_of_custom_sort(self):
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "next_membership_level"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "you need ",
                            Node(Constants.SLOT, {"predicate": "next_membership_points"}), " to reach ",
                            Node(Constants.SLOT, {}), " level"
                        ]
                    )
                ]
            )
        ])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function(
            'next_membership_level_sys_answer : '
            'Sort_membership -> SysAnswer -> System;\n'
        )
        self.assert_semantic_contains_linearization(
            'next_membership_level_sys_answer '
            'individual next_membership_points = '
            'pp "Move" (move "answer" '
            '(pp next_membership_level.s individual) (list next_membership_points));\n'
        )
        self.assert_natural_language_contains_linearization(
            'next_membership_level_sys_answer '
            'individual next_membership_points = '
            'ss (CAPIT ++ "you need" ++ next_membership_points.s ++ '
            '"to reach" ++ individual.s ++ "level" ++ ".");\n'
        )


class SysResolveYnqTest(AutoGeneratorTestCase):
    def test_base_case_no_background(self):
        self.given_form(Node(Constants.ITEM, {}, ["the price"]))
        self.given_generator()
        self.when_generating_predicate_content("price")
        self.assert_abstract_contains('price_resolve_ynq_1 : SysResolveGoal;\n')
        self.assert_semantic_contains('price_resolve_ynq_1 = resolve_ynq price;\n')
        self.assert_natural_language_contains('price_resolve_ynq_1 = resolve_ynq price;\n')

    def test_single_background(self):
        self.given_form(Node(Constants.ITEM, {}, ["the price ", Node(Constants.SLOT, {"predicate": "dest_city"})]))
        self.given_generator()
        self.when_generating_predicate_content("price")
        self.assert_abstract_contains('price_resolve_ynq_2 : SysAnswer -> SysResolveGoal;\n')
        self.assert_semantic_contains(
            'price_resolve_ynq_2 dest_city = resolve_ynq_with_background price (list dest_city);\n'
        )
        self.assert_natural_language_contains(
            'price_resolve_ynq_2 dest_city = resolve_ynq_with_background (ss ("the price " ++ dest_city.s));\n'
        )


class DevicelessDddTest(AutoGeneratorTestCase):
    def test_deviceless_ddd(self):
        self._given_generator_created_for_deviceless_ddd()
        self._when_generating()
        self._then_no_exception_is_raised()

    def _given_generator_created_for_deviceless_ddd(self):
        self._create_mock_ddd()

        def get_grammar(language_code):
            return self._grammar

        self.generator = MockAutoGenerator(self._ddd)
        self.generator._load_and_compile_grammar_entries = get_grammar
        self.generator.warning = ""
        self.generator._grammar_compiler = self._grammar_compiler

    def _when_generating(self):
        self.generator.generate("eng")


class GreetingTest(AutoGeneratorTestCase):
    def test_greeting(self):
        self.given_grammar([Node(Constants.GREETING, {}, [Node(Constants.ITEM, {}, ["Welcome to the Service!"])])])
        self.given_generator()
        self.when_generating()
        self.assert_natural_language_contains_linearization('sysGreet = ss "Welcome to the Service!";')

    def test_greeting_entry_is_optional(self):
        self.given_grammar([])
        self.given_generator()
        self.when_generating()
        self._then_no_exception_is_raised()

    def test_greeting_contains_unicode(self):
        self.given_grammar([Node(Constants.GREETING, {}, [Node(Constants.ITEM, {}, [u"Hallå!"])])])
        self.given_generator()
        self.when_generating()
        self.assert_natural_language_contains_linearization(u'sysGreet = ss "Hallå!";')


class IndividualTest(AutoGeneratorTestCase):
    def test_base_case(self):
        self.given_grammar([Node(Constants.INDIVIDUAL, {"name": "new_york"}, [Node(Constants.ITEM, {}, ["New York"])])])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('new_york : Sort_city;\n')
        self.assert_semantic_contains_linearization('new_york = pp "new_york";\n')
        self.assert_natural_language_contains_linearization('new_york = ss (("New York"));\n')

    def test_placeholders_for_dynamic_sorts(self):
        self.given_grammar([])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('placeholder_keyword0 : Sort_keyword;\n')
        self.assert_semantic_contains_linearization('placeholder_keyword0 = pp "_sem_placeholder_keyword0_";\n')
        self.assert_natural_language_contains_linearization('placeholder_keyword0 = ss "_nl_placeholder_keyword0_";\n')


class PlaceholdersForBuiltinSortsTestCase(AutoGeneratorTestCase):
    def test_integer(self):
        self.given_grammar([])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('integer_placeholder_0 : Integer;\n')
        self.assert_semantic_contains_linearization('integer_placeholder_0 = pp "_integer_placeholder_0_";\n')
        self.assert_natural_language_contains_linearization(
            'integer_placeholder_0 = integer "_integer_placeholder_0_" "_integer_placeholder_0_";\n'
        )

    def test_datetime(self):
        self.given_grammar([])
        self.given_generator()
        self.when_generating()
        self.assert_abstract_contains_function('datetime_placeholder_0 : DateTime;\n')
        self.assert_semantic_contains_linearization('datetime_placeholder_0 = pp "_datetime_placeholder_0_";\n')
        self.assert_natural_language_contains_linearization('datetime_placeholder_0 = ss "_datetime_placeholder_0_";\n')


class LoadingAndCompilationTestCase(AutoGeneratorTestCase):
    def setUp(self):
        self._temp_dir = tempfile.mkdtemp(prefix="AutoGeneratorTestCase")
        self._cwd = os.getcwd()
        self._schema_absolute_path = os.path.abspath(tala.ddd.schemas.__path__[0])
        os.chdir(self._temp_dir)
        AutoGeneratorTestCase.setUp(self)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    def test_load_and_compile_grammar_entries_from_py(self):
        self._given_grammar_source_file("grammar_eng.py", 'top = "start view"')
        self._when_load_and_compile_grammar_entries("eng")
        self._then_result_is(
            Node(
                Constants.GRAMMAR, {},
                [Node(Constants.ACTION, {"name": "top"}, [Node(Constants.ITEM, {}, ["start view"])])]
            )
        )

    def _given_grammar_source_file(self, filename, contents):
        with open(filename, "w") as f:
            f.write(contents)

    def _when_load_and_compile_grammar_entries(self, language_code):
        self._create_mock_ddd()

        def get_grammar(language_code):
            return self._grammar

        generator = MockAutoGenerator(self._ddd)
        self._result = generator._load_and_compile_grammar_entries(language_code)

    def _then_result_is(self, expected_result):
        self.assertEquals(expected_result, self._result)

    def test_load_and_compile_grammar_entries_from_xml(self):
        self._given_grammar_source_file("grammar_eng.xml", '<grammar><action name="top">start view</action></grammar>')
        self._when_load_and_compile_grammar_entries("eng")
        self._then_result_is(
            Node(
                Constants.GRAMMAR, {},
                [Node(Constants.ACTION, {"name": "top"}, [Node(Constants.ITEM, {}, ["start view"])])]
            )
        )

    def test_validate_valid_xml_grammar(self):
        self._given_grammar_source_file("grammar_eng.xml", '<grammar><action name="top">start view</action></grammar>')
        self._when_load_and_compile_grammar_entries("eng")
        self._then_no_exception_is_raised()

    def test_validate_invalid_xml_grammar(self):
        with self.assertRaises(ViolatesSchemaException) as context:
            self._given_grammar_source_file(
                "grammar_eng.xml", '<grammar><invalid_element name="top">start view</invalid_element></grammar>'
            )
            self._when_load_and_compile_grammar_entries("eng")
        self.assertIn(
            "Expected grammar_eng.xml compliant with schema but it's in violation: "
            "Element 'invalid_element': This element is not expected., line 1", context.exception
        )
