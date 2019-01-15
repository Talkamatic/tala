# flake8: noqa

import re
import unittest

from mock import Mock

from tala.model.ddd import DDD
from tala.ddd.ddd_py_compiler import DddPyCompiler
from tala.ddd.ddd_xml_compiler import DddXmlCompiler
from tala.ddd.services.constants import UNDEFINED_SERVICE_ACTION_FAILURE
from tala.ddd.parser import Parser
from tala.ddd.services.service_interface import ServiceInterface, ServiceActionInterface, ServiceParameter, DeviceModuleTarget, ServiceValidatorInterface
from tala.model.domain import Domain
from tala.model.ontology import Ontology
from tala.model.plan import Plan
from tala.nl.gf import rgl_grammar_entry_types as rgl_types, utils
from tala.nl.gf.grammar_entry_types import Constants, Node
from tala.nl.gf.rgl_gf_generator import GrammarProcessingException
from tala.nl.gf.rgl_gf_generator import RglGfFilesGenerator, Directives, MAX_NUM_ENTITIES_PER_PARSE


class RglGfGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        class MockupDevice:
            actions = {}
            validities = []

        self._device_class = MockupDevice
        self._grammar = Node(Constants.GRAMMAR)
        self._ontology = None
        self._domain = None
        self._ddd_name = "mockup_ddd"

        self._service_actions = []
        self._service_validators = []
        self.mock_service_target = self._create_mock_service_target()

    def given_ontology(self, *args, **kwargs):
        self._create_ontology(*args, **kwargs)

    def _create_ontology(self, sorts={}, predicates={}, actions=set([]), individuals={}):
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

    def given_grammar(self, added_nodes):
        for node in added_nodes:
            self._grammar.add_child(node)

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

    def given_domain_parameter(self, object_as_string, parameter_name, parameter_value_as_string):
        object_ = self._parser.parse(object_as_string)
        parameter_value = self._parser.parse_parameter(parameter_name, parameter_value_as_string)
        object_parameters = {parameter_name: parameter_value}
        self._domain.parameters[object_] = object_parameters

    def given_empty_grammar(self):
        pass

    def given_action_is_postconfirmed(self, action_name):
        self._add_to_any_plan("invoke_service_action(%s, {postconfirm=True})" % action_name)

    def given_action_is_not_postconfirmed(self, action_name):
        self._add_to_any_plan("invoke_service_action(%s, {postconfirm=False})" % action_name)

    def when_generating(self, language_code="eng"):
        self._create_generator(language_code)
        self.generator.generate(language_code)

    def _create_generator(self, language_code):
        self._create_mock_ddd()

        def get_grammar():
            return self._grammar

        self.generator = MockRglGfFilesGenerator(self._ddd)
        self.generator._load_and_compile_grammar_entries = get_grammar
        self.generator.warning = ""
        self.generator._grammar_compiler = DddXmlCompiler()

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

        mocked_ddd = Mock(spec=DDD)
        mocked_ddd.domain = self._domain
        mocked_ddd.name = "MockupDdd"
        mocked_ddd.ontology = self._ontology
        mocked_ddd.service_interface = create_mocked_service_interface()
        self._ddd = mocked_ddd

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

    def then_abstract_contains(self, expected):
        self.assertIn(expected, self.generator._abstract_gf_content.getvalue())

    def then_abstract_contains_function(self, expected):
        actual_functions_section = self._get_section(
            self.generator._abstract_gf_content.getvalue(), Directives.FUNCTION
        )
        self.assertIn(expected, actual_functions_section)

    def then_abstract_contains_category(self, expected):
        actual_categories_section = self._get_section(
            self.generator._abstract_gf_content.getvalue(),
            start_line=Directives.CATEGORY,
            end_line=Directives.FUNCTION
        )
        self.assertIn(expected, actual_categories_section)

    def _get_section(self, gf_content, start_line, end_line="}\n"):
        match = re.search("%s\n(.*)%s" % (start_line, end_line), gf_content, re.DOTALL)
        if match:
            return match.group(1)
        else:
            self.fail(
                "failed to find section with start_line=%r, end_line=%r in %r" % (start_line, end_line, gf_content)
            )

    def then_abstract_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._abstract_gf_content.getvalue())

    def then_semantic_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._semantic_gf_content.getvalue())

    def then_semantic_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._semantic_gf_content.getvalue(), "lin")
        self.assertIn(expected, actual_linearizations_section)

    def then_natural_language_begins_with(self, expected_beginning):
        self._assert_begins_with(expected_beginning, self.generator._natural_language_gf_content.getvalue())

    def then_natural_language_contains_linearization(self, expected):
        actual_linearizations_section = self._get_section(self.generator._natural_language_gf_content.getvalue(), "lin")
        self.assertIn(expected, actual_linearizations_section)

    def then_natural_language_contains_linearization_category(self, expected_string):
        actual_section = self._get_section(
            self.generator._natural_language_gf_content.getvalue(),
            start_line=Directives.LINEARIZATION_CATEGORY,
            end_line=Directives.LINEARIZATION
        )
        self.assertIn(expected_string, actual_section)

    def _assert_begins_with(self, expected_beginning, actual_string):
        actual_string
        self.assertTrue(
            actual_string.startswith(expected_beginning),
            "expected %r to begin with %r" % (actual_string, expected_beginning)
        )

    def then_warning_is_yielded(self, expected_warning):
        self.assertEquals(expected_warning, self.generator.warning.strip())

    def then_no_warning_is_yielded(self):
        self.assertEquals("", self.generator.warning)


class HeaderTestCase(RglGfGeneratorTestCase):
    def test_header(self):
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_begins_with("--# -coding=utf8\n" "abstract MockupDdd = TDM, Integers ** {")
        self.then_semantic_begins_with(
            "--# -coding=utf8\n"
            "concrete MockupDdd_sem of MockupDdd = TDM_sem, Integers_sem ** open Utils_sem in {"
        )
        self.then_natural_language_begins_with(
            "--# -coding=utf8\n"
            "concrete MockupDdd_eng of MockupDdd =\n"
            "  TDMEng - [sysGreet],\n"
            "  IntegersEng\n"
            "** open\n"
            "  UtilsEng,\n"
            "  TDMInterfaceEng,\n"
            "  SyntaxEng,\n"
            "  ParadigmsEng,\n"
            "  Prelude\n"
            "\n"
            "in {\n"
        )


class ActionTestCase(RglGfGeneratorTestCase):
    def test_noun_phrase_with_noun_only(self):
        self.given_ontology(actions=set(["profile"]))
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "profile"},
                [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "profile"})])]
            ),
            Node(rgl_types.LEXICON, {}, [Node(rgl_types.NOUN, {"id": "profile"}, [Node("singular", {}, ["profile"])])])
        ])
        self.when_generating()
        self.then_abstract_contains_function('profile : NpAction;')
        self.then_semantic_contains_linearization('profile = pp "profile";')
        self.then_natural_language_contains_linearization(
            'profile = mkNpAction (mkNP (mkPN "profile") | mkNP the_Det (mkCN (mkN "profile")));'
        )

    def test_verb_phrase_with_verb_only(self):
        self.given_ontology(actions=set(["start_game"]))
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "start_game"},
                [Node(rgl_types.VERB_PHRASE, {}, [Node(rgl_types.VERB, {"ref": "start"})])]
            ),
            Node(rgl_types.LEXICON, {}, [Node(rgl_types.VERB, {"id": "start"}, [Node("infinitive", {}, ["start"])])])
        ])
        self.when_generating()
        self.then_abstract_contains_function('start_game : VpAction;')
        self.then_semantic_contains_linearization('start_game = pp "start_game";')
        self.then_natural_language_contains_linearization('start_game = mkVpAction "start";')

    def test_verb_phrase_with_noun(self):
        self.given_ontology(actions=set(["start_game"]))
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "start_game"}, [
                    Node(
                        rgl_types.VERB_PHRASE, {},
                        [Node(rgl_types.VERB, {"ref": "start"}),
                         Node(rgl_types.NOUN, {"ref": "game"})]
                    )
                ]
            ),
            Node(
                rgl_types.LEXICON, {}, [
                    Node(rgl_types.VERB, {"id": "start"}, [Node("infinitive", {}, ["start"])]),
                    Node(rgl_types.NOUN, {"id": "game"}, [Node("singular", {}, ["game"])])
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('start_game : VpAction;')
        self.then_semantic_contains_linearization('start_game = pp "start_game";')
        self.then_natural_language_contains_linearization(
            'start_game = mkVpAction (mkVP (mkV2 (mkV "start")) (mkNP (a_Det|the_Det) (mkCN (mkN "game"))));'
        )

    def test_one_of_for_verb_phrase(self):
        self.given_ontology(actions=set(["restart"]))
        self.given_grammar([
            Node(
                Constants.ACTION, {"name": "restart"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {},
                                [Node(rgl_types.VERB_PHRASE, {}, [Node(rgl_types.VERB, {"ref": "restart"})])]
                            ),
                            Node(
                                Constants.ITEM, {},
                                [Node(rgl_types.VERB_PHRASE, {}, [Node(rgl_types.VERB, {"ref": "forget"})])]
                            )
                        ]
                    )
                ]
            ),
            Node(
                rgl_types.LEXICON, {}, [
                    Node(rgl_types.VERB, {"id": "restart"}, [Node("infinitive", {}, ["restart"])]),
                    Node(rgl_types.VERB, {"id": "forget"}, [Node("infinitive", {}, ["forget"])])
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('restart : VpAction;')
        self.then_semantic_contains_linearization('restart = pp "restart";')
        self.then_natural_language_contains_linearization('restart = (mkVpAction "restart"|mkVpAction "forget");')


class UserQuestionTestCase(RglGfGeneratorTestCase):
    def test_base_case(self):
        self.given_ontology(sorts={"phonenumber": {}}, predicates={"phonenumber_of_contact": "phonenumber"})
        self.given_grammar([
            Node(
                Constants.USER_QUESTION, {"predicate": "phonenumber_of_contact"},
                [Node(rgl_types.UTTERANCE, {}, ["what is the phone number"])]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('ask_phonenumber_of_contact_1 : UsrWHQ;')
        self.then_semantic_contains_linearization('ask_phonenumber_of_contact_1 = ask_whq phonenumber_of_contact;')
        self.then_natural_language_contains_linearization(
            'ask_phonenumber_of_contact_1 = mkUsr (strUtt "what is the phone number");'
        )


class RequestTestCase(RglGfGeneratorTestCase):
    def test_base_case(self):
        self.given_ontology(actions=set(["restart"]))
        self.given_grammar([
            Node(rgl_types.REQUEST, {"action": "restart"}, [Node(rgl_types.UTTERANCE, {}, ["forget everything"])])
        ])
        self.when_generating()
        self.then_abstract_contains_function('restart_request_1 : UsrRequest;')
        self.then_semantic_contains_linearization('restart_request_1 = request (pp "restart");')
        self.then_natural_language_contains_linearization('restart_request_1 = mkUsr (strUtt "forget everything");')

    def test_one_of_in_utterance(self):
        self.given_ontology(actions=set(["restart"]))
        self.given_grammar([
            Node(
                rgl_types.REQUEST, {"action": "restart"}, [
                    Node(
                        rgl_types.UTTERANCE, {}, [
                            Node(
                                Constants.ONE_OF, {}, [
                                    Node(Constants.ITEM, {}, ["forget everything"]),
                                    Node(Constants.ITEM, {}, ["restart the app"])
                                ]
                            )
                        ]
                    )
                ]
            )
        ])

        self.when_generating()

        self.then_abstract_contains_function('restart_request_1 : UsrRequest;')
        self.then_semantic_contains_linearization('restart_request_1 = request (pp "restart");')
        self.then_natural_language_contains_linearization('restart_request_1 = mkUsr (strUtt "forget everything")')

        self.then_abstract_contains_function('restart_request_2 : UsrRequest;')
        self.then_semantic_contains_linearization('restart_request_2 = request (pp "restart");')
        self.then_natural_language_contains_linearization('restart_request_2 = mkUsr (strUtt "restart the app")')

    def test_with_individual(self):
        self.given_ontology(actions=set(["call"]), sorts={"contact": {}})
        self.given_grammar([
            Node(
                rgl_types.REQUEST, {"action": "call"}, [
                    Node(
                        rgl_types.UTTERANCE, {},
                        ["call ", Node(Constants.INDIVIDUAL, {"sort": "contact"}, []), " please"]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('call_request_1 : Sort_contact -> UsrRequest;')
        self.then_semantic_contains_linearization('call_request_1 contact = request (pp "call") contact;')
        self.then_natural_language_contains_linearization(
            'call_request_1 contact = mkUsr (concatUtt (strUtt "call") (concatUtt (mkUtt contact) (strUtt "please")));'
        )

    def test_one_of_in_utterance_with_individual(self):
        self.given_ontology(actions=set(["call"]), sorts={"contact": {}})
        self.given_grammar([
            Node(
                rgl_types.REQUEST, {"action": "call"}, [
                    Node(
                        rgl_types.UTTERANCE, {}, [
                            Node(
                                Constants.ONE_OF, {}, [
                                    Node(Constants.ITEM, {}, ["make a call"]),
                                    Node(
                                        Constants.ITEM, {},
                                        ["call ", Node(Constants.INDIVIDUAL, {"sort": "contact"}, [])]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ])

        self.when_generating()

        self.then_abstract_contains_function('call_request_1 : UsrRequest;')
        self.then_semantic_contains_linearization('call_request_1 = request (pp "call");')
        self.then_natural_language_contains_linearization('call_request_1 = mkUsr (strUtt "make a call");')

        self.then_abstract_contains_function('call_request_2 : Sort_contact -> UsrRequest;')
        self.then_semantic_contains_linearization('call_request_2 contact = request (pp "call") contact;')
        self.then_natural_language_contains_linearization(
            'call_request_2 contact = mkUsr (concatUtt (strUtt "call") (mkUtt contact));'
        )


class ReportTestCase(RglGfGeneratorTestCase):
    def test_no_parameters(self):
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(rgl_types.UTTERANCE, {}, ["the time was set."])])
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )

        self.when_generating()

        self.then_abstract_contains_function('report_ended_SetTime : SysReportEnded;')
        self.then_semantic_contains_linearization('report_ended_SetTime = report_ended "SetTime" (empty_list);')
        self.then_natural_language_contains_linearization('report_ended_SetTime = mkSys (strUtt "the time was set.");')

    def test_with_parameter(self):
        self.given_ontology(predicates={"time_to_set": "time"}, sorts={"time": {}})
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [
                    Node(
                        rgl_types.UTTERANCE, {},
                        ["the time was set to ",
                         Node(Constants.INDIVIDUAL, {"predicate": "time_to_set"}, [])]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime", self.mock_service_target, parameters=[ServiceParameter("time_to_set")], failure_reasons=[]
            )
        )

        self.when_generating()

        self.then_abstract_contains_function('report_ended_SetTime : SysAnswer -> SysReportEnded;')
        self.then_semantic_contains_linearization(
            'report_ended_SetTime time_to_set = report_ended "SetTime" (list time_to_set);'
        )
        self.then_natural_language_contains_linearization(
            'report_ended_SetTime time_to_set = mkSys (concatUtt (strUtt "the time was set to") time_to_set);'
        )

    def test_unknown_failure_without_parameters(self):
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "SetTime"}, [Node(rgl_types.UTTERANCE, {}, ["the time was set."])])
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )

        self.when_generating()

        self.then_abstract_contains_function('report_failed_SetTime_undefined_failure : SysReportFailed;')
        self.then_semantic_contains_linearization(
            'report_failed_SetTime_undefined_failure = report_failed "SetTime" (empty_list) "%s";' %
            UNDEFINED_SERVICE_ACTION_FAILURE
        )
        self.then_natural_language_contains_linearization(
            'report_failed_SetTime_undefined_failure = mkSys undefined_service_action_failure;'
        )

    def test_unknown_failure_with_parameter(self):
        self.given_ontology(predicates={"time_to_set": "time"}, sorts={"time": {}})
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"}, [
                    Node(
                        rgl_types.UTTERANCE, {},
                        ["the time was set to ",
                         Node(Constants.INDIVIDUAL, {"predicate": "time_to_set"}, [])]
                    )
                ]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface(
                "SetTime", self.mock_service_target, parameters=[ServiceParameter("time_to_set")], failure_reasons=[]
            )
        )

        self.when_generating()

        self.then_abstract_contains_function('report_failed_SetTime_undefined_failure : SysAnswer -> SysReportFailed;')
        self.then_semantic_contains_linearization(
            'report_failed_SetTime_undefined_failure time_to_set = report_failed "SetTime" (list time_to_set) "%s";' %
            UNDEFINED_SERVICE_ACTION_FAILURE
        )
        self.then_natural_language_contains_linearization(
            'report_failed_SetTime_undefined_failure time_to_set = mkSys undefined_service_action_failure;'
        )

    def test_exception_if_not_text_in_utterance(self):
        self.given_grammar([
            Node(
                Constants.REPORT_ENDED, {"action": "SetTime"},
                [Node(rgl_types.UTTERANCE, {}, [Node(rgl_types.NOUN_PHRASE, {}, [])])]
            )
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("SetTime", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        with self.assertRaises(GrammarProcessingException):
            self.when_generating()

    def test_started(self):
        self.given_grammar([
            Node(Constants.REPORT_STARTED, {"action": "Search"}, [Node(rgl_types.UTTERANCE, {}, ["searching."])])
        ])
        self.given_service_interface_has_action(
            ServiceActionInterface("Search", self.mock_service_target, parameters=[], failure_reasons=[])
        )

        self.when_generating()

        self.then_abstract_contains_function('report_started_Search : SysReportStarted;')
        self.then_semantic_contains_linearization('report_started_Search = report_started "Search" (empty_list);')
        self.then_natural_language_contains_linearization('report_started_Search = mkSys (strUtt "searching.");')


class PredicateTestCase(RglGfGeneratorTestCase):
    def test_base_case_with_or_without_grammar_entry(self):
        self.given_ontology(sorts={"number": {}}, predicates={"phone_number_of_contact": "number"})
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_function('phone_number_of_contact : Predicate;')
        self.then_semantic_contains_linearization('phone_number_of_contact = pp "phone_number_of_contact";')

    def test_speaker_independent_content(self):
        self.given_ontology(sorts={"number": {}}, predicates={"phone_number_of_contact": "number"})
        self.given_grammar([
            Node(
                rgl_types.PREDICATE, {"name": "phone_number_of_contact"},
                [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "number"}, [])])]
            ),
            Node(
                rgl_types.LEXICON, {},
                [Node(rgl_types.NOUN, {"id": "number"}, [Node(rgl_types.SINGULAR, {}, ["number"])])]
            )
        ])
        self.when_generating()
        self.then_natural_language_contains_linearization(
            'phone_number_of_contact = mkPred (mkNP the_Det (mkN "number"));'
        )

    def test_resolve_ynq(self):
        self.given_ontology(sorts={"number": {}}, predicates={"phone_number_of_contact": "number"})
        self.given_grammar([
            Node(
                rgl_types.PREDICATE, {"name": "phone_number_of_contact"},
                [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "number"}, [])])]
            ),
            Node(
                rgl_types.LEXICON, {},
                [Node(rgl_types.NOUN, {"id": "number"}, [Node(rgl_types.SINGULAR, {}, ["number"])])]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('phone_number_of_contact_resolve_ynq : SysResolveGoal;')
        self.then_semantic_contains_linearization(
            'phone_number_of_contact_resolve_ynq = resolve_ynq phone_number_of_contact;'
        )
        self.then_natural_language_contains_linearization(
            'phone_number_of_contact_resolve_ynq = mkSysResolveGoal (mkVP know_V2 (mkNP the_Det (mkN "number")));'
        )


class SystemQuestionTestCase(RglGfGeneratorTestCase):
    def test_base_case(self):
        self.given_ontology(sorts={"game": {}}, predicates={"game_to_start": "game"})
        self.given_grammar([
            Node(
                Constants.SYS_QUESTION, {"predicate": "game_to_start"}, [Node(rgl_types.UTTERANCE, {}, ["which game"])]
            )
        ])
        self.given_some_plan_contains("findout(?X.game_to_start(X))")
        self.when_generating()
        self.then_abstract_contains_function('game_to_start : Predicate;')
        self.then_semantic_contains_linearization('game_to_start = pp "game_to_start";')
        self.then_natural_language_contains_linearization('game_to_start = mkPred "which game";')

    def test_feature_question(self):
        self.given_ontology(
            sorts={
                "game": {},
                "game_type": {}
            },
            predicates={
                "game_to_start": "game",
                "type_of_game_to_start": {
                    "sort": "game_type",
                    "feature_of": "game_to_start"
                }
            }
        )
        self.given_grammar([
            Node(
                Constants.SYS_QUESTION, {"predicate": "game_to_start"}, [Node(rgl_types.UTTERANCE, {}, ["which game"])]
            ),
            Node(
                Constants.SYS_QUESTION, {"predicate": "type_of_game_to_start"},
                [Node(rgl_types.UTTERANCE, {}, ["what type of game"])]
            )
        ])
        self.given_some_plan_contains("findout(?X.game_to_start(X))")
        self.given_domain_parameter("?X.game_to_start(X)", "ask_features", "[type_of_game_to_start]")
        self.when_generating()
        self.then_abstract_contains_function('type_of_game_to_start : Predicate;')
        self.then_semantic_contains_linearization('type_of_game_to_start = pp "type_of_game_to_start";')
        self.then_natural_language_contains_linearization('type_of_game_to_start = mkPred "what type of game";')


class CategoriesTestCase(RglGfGeneratorTestCase):
    def test_sortal_category(self):
        self.given_ontology(sorts={"city": {}}, predicates={}, actions=set([]), individuals={})
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_category("Sort_city;\n")
        self.then_natural_language_contains_linearization_category("Sort_city = Sort;\n")

    def test_predicate_category(self):
        self.given_ontology(sorts={"city": {}}, predicates={"dest_city": "city"}, actions=set([]), individuals={})
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_category("Predicate_dest_city;\n")
        self.then_natural_language_contains_linearization_category("Predicate_dest_city = Pred;\n")


class IndividualTestCase(RglGfGeneratorTestCase):
    def test_proper_noun(self):
        self.given_ontology(sorts={"city": {}}, individuals={"new_york": "city"})
        self.given_grammar([
            Node(Constants.INDIVIDUAL, {"name": "new_york"}, [Node(rgl_types.PROPER_NOUN, {}, ["New York"])])
        ])
        self.when_generating()
        self.then_abstract_contains_function('new_york : Sort_city;\n')
        self.then_semantic_contains_linearization('new_york = pp "new_york";\n')
        self.then_natural_language_contains_linearization('new_york = mkSort (mkPN ("New York"));\n')


class UserAnswerTestCase(RglGfGeneratorTestCase):
    def test_sortal_user_answer(self):
        self.given_ontology(sorts={"city": {}}, predicates={"dest_city": "city"})
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_function("dest_city_sortal_usr_answer : Sort_city -> UsrAnswer;\n")
        self.then_semantic_contains_linearization("dest_city_sortal_usr_answer answer = answer;\n")
        self.then_natural_language_contains_linearization('dest_city_sortal_usr_answer answer = mkUsr answer;\n')


class SystemAnswerTestCase(RglGfGeneratorTestCase):
    def test_default_unary_propositional_system_answer_of_custom_sort(self):
        self.given_ontology(sorts={"city": {}}, predicates={"dest_city": "city"})
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_function('dest_city_sys_answer : Sort_city -> SysAnswer;\n')
        self.then_semantic_contains_linearization('dest_city_sys_answer individual = pp "dest_city" individual;\n')
        self.then_natural_language_contains_linearization('dest_city_sys_answer individual = mkSysAnswer individual;\n')

    def test_overridden_unary_propositional_system_answer_of_custom_sort(self):
        self.given_ontology(sorts={"city": {}}, predicates={"dest_city": "city"})
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"},
                [Node(rgl_types.UTTERANCE, {}, [u"to ", Node(Constants.INDIVIDUAL, {"predicate": "dest_city"})])]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('dest_city_sys_answer : Sort_city -> SysAnswer;\n')
        self.then_semantic_contains_linearization('dest_city_sys_answer individual = pp "dest_city" individual;\n')
        self.then_natural_language_contains_linearization(
            'dest_city_sys_answer individual = mkSysAnswer (concatUtt (strUtt "to") (mkUtt individual));\n'
        )

    def test_unary_propositional_system_answer_of_custom_sort_with_background(self):
        self.given_ontology(sorts={"city": {}, "month": {}}, predicates={"dest_city": "city", "dest_month": "month"})
        self.given_grammar([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"}, [
                    Node(
                        rgl_types.UTTERANCE, {}, [
                            u"to ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dest_city"}),
                            u" in ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dest_month"}),
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('dest_city_sys_answer : Sort_city -> SysAnswer -> System;\n')
        self.then_semantic_contains_linearization(
            'dest_city_sys_answer individual dest_month ='
            ' pp "Move" (move "answer" (pp "dest_city" individual) (list dest_month));\n'
        )
        self.then_natural_language_contains_linearization(
            'dest_city_sys_answer individual dest_month ='
            ' mkSys (concatUtt (strUtt "to") (concatUtt (mkUtt individual)'
            ' (concatUtt (strUtt "in") dest_month)));\n'
        )


class DefaultActionsTestCase(RglGfGeneratorTestCase):
    def test_top_action(self):
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_function('top : NpAction;\n')
        self.then_semantic_contains_linearization('top = pp "top";\n')
        self.then_natural_language_contains_linearization(
            'top = mkNpAction (mkNP (mkPN "menu") | mkNP the_Det (mkCN (mkN "menu")));'
        )

    def test_up_action(self):
        self.given_grammar([])
        self.when_generating()
        self.then_abstract_contains_function('up : VpAction;\n')
        self.then_semantic_contains_linearization('up = pp "up";\n')
        self.then_natural_language_contains_linearization('up = mkVpAction "return";')


class EntityRecognitionTestCase(RglGfGeneratorTestCase):
    def test_mock_individuals_for_dynamic_sort(self):
        self._given_ontology_with_dynamic_sort()
        self.given_grammar([])
        self.when_generating()
        self._then_abstract_contains_mock_individuals()
        self._then_semantic_contains_mock_individuals()
        self._then_natural_language_contains_mock_individuals()

    def _then_abstract_contains_mock_individuals(self):
        for n in range(MAX_NUM_ENTITIES_PER_PARSE):
            self.then_abstract_contains_function(
                '%s : Sort_%s;\n' % (
                    utils.name_of_user_answer_placeholder_of_sort(self._name_of_dynamic_sort, n),
                    self._name_of_dynamic_sort
                )
            )

    def _then_semantic_contains_mock_individuals(self):
        for n in range(MAX_NUM_ENTITIES_PER_PARSE):
            self.then_semantic_contains_linearization(
                '%s = pp "%s";\n' % (
                    utils.name_of_user_answer_placeholder_of_sort(self._name_of_dynamic_sort, n),
                    utils.semantic_user_answer_placeholder_of_sort(self._name_of_dynamic_sort, n)
                )
            )

    def _then_natural_language_contains_mock_individuals(self):
        for n in range(MAX_NUM_ENTITIES_PER_PARSE):
            self.then_natural_language_contains_linearization(
                '%s = mkSort (mkPN ("%s"));\n' % (
                    utils.name_of_user_answer_placeholder_of_sort(self._name_of_dynamic_sort, n),
                    utils.nl_user_answer_placeholder_of_sort(self._name_of_dynamic_sort, n)
                )
            )

    def _given_ontology_with_dynamic_sort(self):
        self._name_of_dynamic_sort = "city"
        self.given_ontology(sorts={self._name_of_dynamic_sort: {"dynamic": True}})


class ValidityTestCase(RglGfGeneratorTestCase):
    ONTOLOGY = {"sorts": {"city": {}}, "predicates": {"dest_city": "city", "dept_city": "city"}}

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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        rgl_types.UTTERANCE, {}, [
                            "cannot go from ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dept_city"}), " to ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dest_city"})
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_1 : SysAnswer -> SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_1 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_1 dept_city dest_city = mkSys (concatUtt (strUtt "cannot go from") (concatUtt dept_city (concatUtt (strUtt "to") dest_city)));\n'
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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        rgl_types.UTTERANCE, {}, [
                            "cannot go to ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dest_city"}), " from ",
                            Node(Constants.INDIVIDUAL, {"predicate": "dept_city"})
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_1 : SysAnswer -> SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_1 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_1 dept_city dest_city = mkSys (concatUtt (strUtt "cannot go to") (concatUtt dest_city (concatUtt (strUtt "from") dept_city)));\n'
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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        rgl_types.UTTERANCE, {},
                        ["cannot go from ", Node(Constants.INDIVIDUAL, {"predicate": "dept_city"})]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_1 : SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_1 dept_city = mkSys (concatUtt (strUtt "cannot go from") dept_city);\n'
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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    Node(
                                        rgl_types.UTTERANCE, {},
                                        ["cannot go from ",
                                         Node(Constants.INDIVIDUAL, {"predicate": "dept_city"})]
                                    )
                                ]
                            ),
                            Node(
                                Constants.ITEM, {}, [
                                    Node(
                                        rgl_types.UTTERANCE, {},
                                        ["cannot go to ",
                                         Node(Constants.INDIVIDUAL, {"predicate": "dest_city"})]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_1 : SysAnswer -> SysICM;')
        self.then_abstract_contains_function('CityValidity_2 : SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.then_semantic_contains_linearization(
            'CityValidity_2 dest_city = rejectICM (set (list dest_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_1 dept_city = mkSys (concatUtt (strUtt "cannot go from") dept_city);'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_2 dest_city = mkSys (concatUtt (strUtt "cannot go to") dest_city);'
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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"}, [
                    Node(
                        rgl_types.UTTERANCE, {},
                        ["cannot go from ", Node(Constants.INDIVIDUAL, {"predicate": "dept_city"})]
                    )
                ]
            )
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_2 : SysAnswer -> SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_2 dept_city dest_city = rejectICM (set (list dept_city dest_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_2 dept_city dest_city = mkSys (concatUtt (strUtt "cannot go from") dept_city);\n'
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
        self.given_ontology(**ValidityTestCase.ONTOLOGY)
        self.given_grammar([
            Node(Constants.VALIDITY, {"name": "CityValidity"}, [Node(rgl_types.UTTERANCE, {}, ["invalid parameters"])])
        ])
        self.when_generating()
        self.then_abstract_contains_function('CityValidity_1 : SysAnswer -> SysICM;')
        self.then_abstract_contains_function('CityValidity_2 : SysAnswer -> SysICM;')
        self.then_semantic_contains_linearization(
            'CityValidity_1 dept_city = rejectICM (set (list dept_city)) "CityValidity";'
        )
        self.then_semantic_contains_linearization(
            'CityValidity_2 dest_city = rejectICM (set (list dest_city)) "CityValidity";'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_1 dept_city = mkSys (strUtt "invalid parameters");'
        )
        self.then_natural_language_contains_linearization(
            'CityValidity_2 dest_city = mkSys (strUtt "invalid parameters")'
        )


class WarningsAndErrorsTest(RglGfGeneratorTestCase):
    def test_warn_about_missing_entry_for_action(self):
        self.given_ontology(actions=set(["call"]))
        self.given_domain_has_plan_for_goal("perform(call)")
        self.given_empty_grammar()
        self.when_generating()
        self.then_warning_is_yielded(
            """How do speakers talk about the action 'call'? Possible contents of the <action> element:

  <verb-phrase>
  <noun-phrase>
  <one-of>"""
        )

    def test_warn_about_missing_entry_for_system_question(self):
        self.given_ontology(predicates={"dest_city": "city"}, sorts={"city": {}})
        self.given_some_plan_contains("findout(?X.dest_city(X))")
        self.given_empty_grammar()
        self.when_generating()
        self.then_warning_is_yielded(
            """How does the system ask about 'dest_city'?

Example:

  <question speaker="system" predicate="dest_city" type="wh_question">
    <utterance>what is dest city</utterance>
  </question>"""
        )

    def test_warn_about_missing_entry_for_postconfirmed_action(self):
        self.given_service_interface_has_action(
            ServiceActionInterface("SetAlarm", self.mock_service_target, parameters=[], failure_reasons=[])
        )
        self.given_action_is_postconfirmed("SetAlarm")
        self.given_empty_grammar()
        self.when_generating()
        self.then_warning_is_yielded(
            """How does the system report that the service action 'SetAlarm' ended? Example:

  <report action="SetAlarm" status="ended">
    <utterance>performed SetAlarm</utterance>
  </report>"""
        )

    def test_not_warn_about_postconfirmed_action_if_entry_exists(self):
        self.given_action_is_postconfirmed("AlarmRings")
        self.given_grammar([
            Node(Constants.REPORT_ENDED, {"action": "AlarmRings"}, [Node(rgl_types.UTTERANCE, {}, ["Beep beep!"])])
        ])
        self.when_generating()
        self.then_no_warning_is_yielded()

    def test_not_warn_about_missing_entry_if_no_postconfirmation(self):
        self.given_action_is_not_postconfirmed("AlarmRings")
        self.given_empty_grammar()
        self.when_generating()
        self.then_no_warning_is_yielded()


class MockRglGfFilesGenerator(RglGfFilesGenerator):
    def _warn_about_missing_entry(self, line):
        self.warning += line
        self.warning += '\n'
