# flake8: noqa

import os
import re
import warnings
import xml.dom.minidom

from lxml import etree

from tala.ddd.services.service_interface import ServiceActionInterface, ServiceParameter, ServiceQueryInterface, ServiceValidatorInterface, ServiceEntityRecognizerInterface, ServiceInterface, DeviceModuleTarget, FrontendTarget, HttpTarget, ActionFailureReason, PlayAudioActionInterface, AudioURLServiceParameter
from tala.model.ask_feature import AskFeature
from tala.model.domain import Domain
from tala.model.goal import HandleGoal, PerformGoal, ResolveGoal
from tala.model.speaker import Speaker
from tala.model.plan import Plan
from tala.model.plan_item import JumpToPlanItem, IfThenElse, ForgetAllPlanItem, ForgetPlanItem, InvokeServiceQueryPlanItem, InvokeServiceActionPlanItem, AssumeSharedPlanItem, AssumeIssuePlanItem, LogPlanItem, AssumePlanItem, GetDonePlanItem
from tala.model.predicate import Predicate
from tala.model.proposition import GoalProposition, PropositionSet, PredicateProposition
from tala.model import condition
from tala.model.question import AltQuestion, YesNoQuestion
from tala.model.action import Action
from tala.model.question_raising_plan_item import QuestionRaisingPlanItem
from tala.model.sort import CustomSort, BuiltinSortRepository, UndefinedSort, BOOLEAN
from tala.nl.gf import rgl_grammar_entry_types as rgl_types
from tala.nl.gf.grammar_entry_types import Node, Constants
import tala.ddd.schemas
from tala.ddd.maker.ddd_py_to_xml import GrammarConverter


class DddXmlCompilerException(Exception):
    pass


class ViolatesSchemaException(Exception):
    pass


class UnexpectedAttributeException(Exception):
    pass


class DddXmlCompiler(object):
    def compile_ontology(self, *args, **kwargs):
        return OntologyCompiler().compile(*args, **kwargs)

    def compile_domain(self, *args, **kwargs):
        return DomainCompiler().compile(*args, **kwargs)

    def compile_grammar(self, *args, **kwargs):
        return GrammarCompiler().compile(*args, **kwargs)

    def decompile_grammar_node(self, ddd, languages, node):
        return GrammarConverter(ddd, languages).convert_node(node)

    def compile_rgl_grammar(self, *args, **kwargs):
        return RglGrammarCompiler().compile(*args, **kwargs)

    def compile_service_interface(self, *args, **kwargs):
        return ServiceInterfaceCompiler().compile(*args, **kwargs)


class XmlCompiler(object):
    def _parse_string_attribute(self, element, name):
        attribute = element.getAttribute(name)
        if attribute != "":
            return attribute

    def _parse_xml(self, string):
        self._document = xml.dom.minidom.parseString(string)

    def _get_root_element(self, name):
        elements = self._document.getElementsByTagName(name)
        if len(elements) != 1:
            raise DddXmlCompilerException("expected 1 %s element" % name)
        return elements[0]

    def _parse_boolean(self, string):
        return string == "true"

    def _find_child_nodes(self, element, node_name):
        return [node for node in element.childNodes if node.localName == node_name]

    def _get_mandatory_attribute(self, element, name):
        if not element.hasAttribute(name):
            raise DddXmlCompilerException("%s requires attribute %r" % (element, name))
        return element.getAttribute(name)

    def _get_optional_attribute(self, element, name):
        if not element.hasAttribute(name):
            return None
        return element.getAttribute(name)

    def _has_attribute(self, element, attribute):
        return element.getAttribute(attribute) != ""

    def _validate(self, xml_string):
        xml_schema = self.get_schema()
        parsed_grammar_object = etree.fromstring(xml_string)
        try:
            xml_schema.assertValid(parsed_grammar_object)
        except etree.DocumentInvalid as exception:
            raise ViolatesSchemaException(
                "Expected %s compliant with schema but it's in violation: %s" % (self._filename, exception)
            )

    @property
    def _filename(self):
        raise NotImplementedError("Needs to be implemented in subclass %s" % self.__class__.__name__)

    @property
    def _schema_absolute_path(self):
        absolute_path = os.path.abspath(os.path.dirname(tala.ddd.schemas.__file__))
        return os.path.join(absolute_path, self._schema_name)

    @property
    def _schema_name(self):
        raise NotImplementedError("Needs to be implemented in subclass %s" % self.__class__.__name__)

    def load_schema(self):
        schema_object = open(self._schema_absolute_path, "r")
        return schema_object

    def parse_schema(self, loaded_schema):
        parsed_as_xml = etree.parse(loaded_schema)
        parsed_as_schema = etree.XMLSchema(parsed_as_xml)
        return parsed_as_schema

    def get_schema(self):
        loaded_schema = self.load_schema()
        parsed_schema = self.parse_schema(loaded_schema)
        return parsed_schema


class OntologyCompiler(XmlCompiler):
    @property
    def _name(self):
        return "ontology"

    @property
    def _filename(self):
        return "%s.xml" % self._name

    @property
    def _schema_name(self):
        return "%s.xsd" % self._name

    def compile(self, xml_string):
        self._validate(xml_string)
        self._parse_xml(xml_string)
        self._ontology_element = self._get_root_element(self._name)
        self._compile_name()
        self._compile_sorts()
        self._compile_predicates()
        self._compile_individuals()
        self._compile_actions()
        return {
            "name": self._ontology_name,
            "sorts": set(self._custom_sorts_dict.values()),
            "predicates": self._predicates,
            "individuals": self._individuals,
            "actions": self._actions
        }

    def _compile_name(self):
        self._ontology_name = self._ontology_element.getAttribute("name")

    def _compile_sorts(self):
        elements = self._document.getElementsByTagName("sort")
        self._custom_sorts_dict = {}
        for element in elements:
            self._compile_sort_element(element)

    def _compile_sort_element(self, element):
        name = self._get_mandatory_attribute(element, "name")
        dynamic = self._parse_boolean(element.getAttribute("dynamic"))
        self._custom_sorts_dict[name] = CustomSort(self._ontology_name, name, dynamic)

    def _compile_predicates(self):
        elements = self._document.getElementsByTagName("predicate")
        self._predicates = {self._compile_predicate_element(element) for element in elements}

    def _compile_predicate_element(self, element):
        name = self._get_mandatory_attribute(element, "name")
        sort_name = self._get_mandatory_attribute(element, "sort")
        sort = self._get_sort(sort_name)
        feature_of_name = self._parse_string_attribute(element, "feature_of")
        multiple_instances = self._parse_boolean(element.getAttribute("multiple_instances"))
        return Predicate(
            self._ontology_name,
            name,
            sort=sort,
            feature_of_name=feature_of_name,
            multiple_instances=multiple_instances
        )

    def _get_sort(self, name):
        if name in self._custom_sorts_dict:
            return self._custom_sorts_dict[name]
        elif BuiltinSortRepository.has_sort(name):
            return BuiltinSortRepository.get_sort(name)
        else:
            raise UndefinedSort("Expected a defined sort but got '%s'." % name)

    def _compile_individuals(self):
        elements = self._document.getElementsByTagName("individual")
        self._individuals = {}
        for element in elements:
            name = self._get_mandatory_attribute(element, "name")
            sort_name = self._get_mandatory_attribute(element, "sort")
            sort = self._get_sort(sort_name)
            self._individuals[name] = sort

    def _compile_actions(self):
        elements = self._document.getElementsByTagName("action")
        self._actions = set()
        for element in elements:
            name = self._get_mandatory_attribute(element, "name")
            self._actions.add(name)


class DomainCompiler(XmlCompiler):
    @property
    def _name(self):
        return "domain"

    @property
    def _schema_name(self):
        return "domain.xsd"

    @property
    def _filename(self):
        return "domain.xml"

    def compile(self, ddd_name, xml_string, ontology, parser, service_interface):
        self._validate(xml_string)
        self._ddd_name = ddd_name
        self._ontology = ontology
        self._parser = parser
        self._service_interface = service_interface
        self._parse_xml(xml_string)
        self._domain_element = self._get_root_element("domain")
        self._compile_name()
        self._compile_plans()
        self._compile_default_questions()
        self._compile_parameters()
        self._compile_dependencies()
        return {
            "ddd_name": self._ddd_name,
            "name": self._domain_name,
            "plans": self._plans,
            "default_questions": self._default_questions,
            "parameters": self._parameters,
            "dependencies": self._dependencies
        }

    def get_name(self, xml_string):
        self._parse_xml(xml_string)
        self._domain_element = self._get_root_element("domain")
        self._compile_name()
        return self._domain_name

    def _compile_name(self):
        self._domain_name = self._domain_element.getAttribute("name")

    def _compile_plans(self):
        elements = self._document.getElementsByTagName("goal")
        self._plans = [self._compile_goal_element(element) for element in elements]

    def _compile_goal_element(self, element):
        goal = self._compile_goal(element)
        plan = {"goal": goal}
        self._compile_plan(plan, element, "plan", default=Plan([]))
        self._compile_plan_element_with_one_child(plan, element, "preferred", "preferred", self._compile_preferred)
        self._compile_plan_single_attribute(plan, element, "accommodate_without_feedback", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "dynamic_title", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "restart_on_completion", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "reraise_on_resume", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "io_status", self._parse_io_status)
        self._compile_plan(plan, element, "postplan")
        self._compile_plan_element_with_multiple_children(
            plan, element, "gui_context", "gui_context", self._compile_gui_context
        )
        self._compile_plan_element_with_multiple_children(
            plan, element, "postconds", "downdate_condition", self._compile_downdate_condition
        )
        self._compile_plan_element_with_multiple_children(
            plan, element, "postconds", "postcond", self._compile_deprecated_postconds
        )
        self._compile_plan_element_with_multiple_children(
            plan, element, "superactions", "superaction", self._compile_superaction
        )
        return plan

    def _compile_plan(self, plan, element, attribute_name, default=None):
        plan_elements = self._find_child_nodes(element, attribute_name)
        if len(plan_elements) == 1:
            plan_items = self._compile_plan_item_nodes(plan_elements[0].childNodes)
            plan[attribute_name] = Plan(reversed(plan_items))
        elif len(plan_elements) > 1:
            raise DddXmlCompilerException("expected max 1 %r element" % attribute_name)
        elif default is not None:
            plan[attribute_name] = default

    def _compile_goal(self, element):
        goal_type = self._get_mandatory_attribute(element, "type")
        if goal_type == "perform":
            action_name = self._get_mandatory_attribute(element, "action")
            action = self._ontology.create_action(action_name)
            return PerformGoal(action, Speaker.SYS)
        elif goal_type == "resolve":
            question = self._compile_question(element, "question_type")
            return ResolveGoal(question, Speaker.SYS)
        elif goal_type == "handle":
            service_action = self._get_mandatory_attribute(element, "action")
            return HandleGoal(self._ontology.name, service_action)
        else:
            raise DddXmlCompilerException("unsupported goal type %r" % goal_type)

    def _compile_question(self, element, type_attribute="type"):
        question_type = self._get_mandatory_attribute(element, type_attribute)
        if question_type == "wh_question":
            predicate = self._get_mandatory_attribute(element, "predicate")
            return self._parse("?X.%s(X)" % predicate)
        elif question_type == "alt_question":
            return self._compile_alt_question(element)
        elif question_type == "yn_question":
            return self._compile_yn_question(element)
        elif question_type == "goal":
            return self._parse("?X.goal(X)")
        else:
            raise DddXmlCompilerException('unsupported question type %r' % question_type)

    def _compile_alt_question(self, element):
        proposition_set = self._compile_proposition_set(element, "alt")
        return AltQuestion(proposition_set)

    def _compile_proposition_set(self, element, node_name):
        child_nodes = self._find_child_nodes(element, node_name)
        propositions = [self._compile_proposition_child_of(child) for child in child_nodes]
        return PropositionSet(propositions)

    def _compile_yn_question(self, element):
        proposition = self._compile_proposition_child_of(element)
        return YesNoQuestion(proposition)

    def _compile_plan_item_nodes(self, nodes):
        return [self._compile_plan_item_element(node) for node in nodes if node.__class__ == xml.dom.minidom.Element]

    def _compile_plan_item_element(self, element):
        if element.localName in ["findout", "raise", "bind"]:
            return self._compile_question_raising_plan_item_element(element.localName, element)
        elif element.localName == "if":
            return self._compile_if_element(element)
        elif element.localName == "forget":
            return self._compile_forget_element(element)
        elif element.localName == "forget_all":
            return ForgetAllPlanItem()
        elif element.localName == "invoke_service_query":
            return self._compile_invoke_service_query_element(element)
        elif element.localName == "dev_query":
            return self._compile_deprecated_dev_query_element(element)
        elif element.localName == "invoke_service_action":
            return self._compile_invoke_service_action_element(element)
        elif element.localName == "get_done":
            return self._compile_get_done_element(element)
        elif element.localName == "dev_perform":
            warnings.warn(
                "<dev_perform> is deprecated. Use <invoke_service_action> instead.",
                DeprecationWarning)
            return self._compile_deprecated_dev_perform_element(element)
        elif element.localName == "jumpto":
            return self._compile_jumpto_element(element)
        elif element.localName == "assume_shared":
            return self._compile_assume_shared_element(element)
        elif element.localName == "assume_issue":
            return self._compile_assume_issue_element(element)
        elif element.localName == "assume_system_belief":
            return self._compile_assume_element(element)
        elif element.localName == "log":
            return self._compile_log_element(element)
        else:
            raise DddXmlCompilerException("unknown plan item element %s" % element.toxml())

    def _compile_question_raising_plan_item_element(self, item_type, element):
        question_type = self._get_mandatory_attribute(element, "type")
        question = self._compile_question(element)
        return QuestionRaisingPlanItem(self._domain_name, item_type, question)

    def _compile_if_element(self, element):
        condition = self._compile_condition_element(element)
        consequent = self._compile_if_then_child_plan(element, "then")
        alternative = self._compile_if_then_child_plan(element, "else")
        return IfThenElse(condition, consequent, alternative)

    def _compile_condition_element(self, element):
        condition_element = self._get_single_child_element(element, ["condition"])
        return self._compile_proposition_child_of(condition_element)

    def _get_single_child_element(self, node, allowed_names):
        child_elements = [child for child in node.childNodes if child.localName in allowed_names]
        if len(child_elements) == 1:
            return child_elements[0]
        else:
            raise DddXmlCompilerException(
                "expected exactly 1 child element among types %s in %s, was %s." %
                (allowed_names, node.toxml(), child_elements)
            )

    def _compile_forget_element(self, element):
        if element.getAttribute("predicate"):
            predicate_name = self._get_mandatory_attribute(element, "predicate")
            predicate = self._ontology.get_predicate(predicate_name)
            return ForgetPlanItem(predicate)
        elif len(element.childNodes) == 1:
            proposition = self._compile_proposition_child_of(element)
            return ForgetPlanItem(proposition)

    def _compile_invoke_service_query_element(self, element):
        question = self._compile_question(element)
        self._check_deprecation_of_device(question, element, "invoke_service_query")
        return InvokeServiceQueryPlanItem(question, min_results=1, max_results=1)

    def _compile_deprecated_dev_query_element(self, element):
        warnings.warn(
            '<dev_query> is deprecated. Use <invoke_service_query> instead.', DeprecationWarning)
        question = self._compile_question(element)
        self._check_deprecation_of_device(question, element, "dev_query")
        return InvokeServiceQueryPlanItem(question, min_results=1, max_results=1)

    def _check_deprecation_of_device(self, question, element, name):
        def fail(query, device, tag_name):
            message = "Attribute 'device=\"%s\"' is not supported in <%s ... predicate='%s'>. " "Use 'service_interface.xml' instead." % (
                device, tag_name, query
            )
            raise UnexpectedAttributeException(message)

        device = self._get_optional_attribute(element, "device")
        if device:
            query = question.get_predicate().get_name()
            fail(query, device, name)

    def _compile_invoke_service_action_element(self, element):
        return self._compile_invoke_service_action_or_deprecated_dev_perform_element(element, "name")

    def _compile_deprecated_dev_perform_element(self, element):
        return self._compile_invoke_service_action_or_deprecated_dev_perform_element(element, "action")

    def _compile_invoke_service_action_or_deprecated_dev_perform_element(self, element, action_attribute):
        def fail(action, device):
            message = "Attribute 'device=\"%s\"' is not supported in <invoke_service_action name='%s'>. Use 'service_interface.xml' instead." % (
                device, action
            )
            raise UnexpectedAttributeException(message)

        def parse_downdate_plan():
            if element.hasAttribute("downdate_plan"):
                return self._parse_boolean(element.getAttribute("downdate_plan"))
            else:
                return True

        action = self._get_mandatory_attribute(element, action_attribute)
        device = self._get_optional_attribute(element, "device")
        if device:
            fail(action, device)
        preconfirm = self._parse_preconfirm_value(element.getAttribute("preconfirm"))
        postconfirm = self._parse_boolean(element.getAttribute("postconfirm"))
        downdate_plan = parse_downdate_plan()
        return InvokeServiceActionPlanItem(
            self._ontology.name, action, preconfirm=preconfirm, postconfirm=postconfirm, downdate_plan=downdate_plan
        )

    def _compile_get_done_element(self, element):
        action_string = self._get_mandatory_attribute(element, "action")
        action = Action(action_string, self._ontology.name)
        return GetDonePlanItem(action)

    def _compile_jumpto_element(self, element):
        goal = self._compile_goal(element)
        return JumpToPlanItem(goal)

    def _compile_assume_shared_element(self, element):
        predicate_proposition = self._compile_predicate_proposition_child_of(element)
        return AssumeSharedPlanItem(predicate_proposition)

    def _compile_assume_element(self, element):
        predicate_proposition = self._compile_predicate_proposition_child_of(element)
        return AssumePlanItem(predicate_proposition)

    def _compile_predicate_proposition_child_of(self, element):
        child = self._get_single_child_element(element, ["proposition"])
        return self._compile_predicate_proposition(child)

    def _compile_assume_issue_element(self, element):
        question_type = self._get_mandatory_attribute(element, "type")
        question = self._compile_question(element)
        return AssumeIssuePlanItem(question)

    def _compile_log_element(self, element):
        message = self._get_mandatory_attribute(element, "message")
        return LogPlanItem(message)

    def _parse_preconfirm_value(self, string):
        if string == "":
            return None
        else:
            return self._parser.parse_preconfirm_value(string)

    def _compile_proposition_child_of(self, element):
        child = self._get_single_child_element(element, ["proposition", "resolve", "perform"])
        if child.localName == "proposition":
            return self._compile_predicate_proposition(child)
        elif child.localName == "perform":
            return self._compile_perform_proposition(child)
        elif child.localName == "resolve":
            return self._compile_resolve_proposition(child)

    def _compile_predicate_proposition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        value = element.getAttribute("value")
        predicate = self._ontology.get_predicate(predicate_name)
        if value:
            individual = self._ontology.create_individual(value, sort=predicate.getSort())
        else:
            individual = None
        return PredicateProposition(predicate, individual)

    def _compile_deprecated_postconds(self, element):
        warnings.warn("<postcond> is deprecated. Use <downdate_condition> instead.",
                      DeprecationWarning)
        return self._compile_proposition_child_of(element)

    def _compile_downdate_condition(self, element):
        child = self._get_single_child_element(element, ["has_value", "is_shared_fact"])
        if child.localName == "has_value":
            return self._compile_has_value_condition(child)
        elif child.localName == "is_shared_fact":
            return self._compile_is_shared_fact_condition(child)

    def _compile_has_value_condition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        predicate = self._ontology.get_predicate(predicate_name)
        return condition.HasValue(predicate)

    def _compile_is_shared_fact_condition(self, element):
        child = self._get_single_child_element(element, ["proposition"])
        proposition = self._compile_predicate_proposition(child)
        return condition.IsSharedFact(proposition)

    def _compile_perform_proposition(self, element):
        action_name = self._get_mandatory_attribute(element, "action")
        action = self._ontology.create_action(action_name)
        return GoalProposition(PerformGoal(action))

    def _compile_resolve_proposition(self, element):
        question = self._compile_question(element, "type")
        speaker = Speaker.SYS
        speaker_attribute = element.getAttribute("speaker")
        if speaker_attribute == "user":
            speaker = Speaker.USR
        return GoalProposition(ResolveGoal(question, speaker))

    def _compile_if_then_child_plan(self, element, node_name):
        nodes = self._find_child_nodes(element, node_name)
        if len(nodes) == 0:
            return None
        elif len(nodes) == 1:
            child_node = nodes[0]
            if len(child_node.childNodes) == 0:
                return None
            else:
                plan_items = self._compile_plan_item_nodes(child_node.childNodes)
                if len(plan_items) == 0:
                    return None
                elif len(plan_items) == 1:
                    return plan_items[0]
                else:
                    raise DddXmlCompilerException("if element only support single-item consequents and alternatives")
        else:
            raise DddXmlCompilerException("expected only one %r element" % node_name)

    def _compile_plan_single_attribute(self, plan, element, attribute_name, compilation_method):
        attribute = element.getAttribute(attribute_name)
        if attribute:
            plan[attribute_name] = compilation_method(attribute)

    def _compile_plan_element_with_multiple_children(
        self, plan, element, attribute_name, node_name, compilation_method
    ):
        child_nodes = self._find_child_nodes(element, node_name)
        if len(child_nodes) > 0:
            plan[attribute_name] = [compilation_method(node) for node in child_nodes]

    def _compile_plan_element_with_one_child(self, plan, element, attribute_name, node_name, compilation_method):
        child_nodes = self._find_child_nodes(element, node_name)
        if len(child_nodes) > 1:
            raise DddXmlCompilerException("Expected at most one child for %s, found %s." % (element, child_nodes))
        elif len(child_nodes) == 1:
            plan[attribute_name] = compilation_method(child_nodes[0])

    def _compile_gui_context(self, node):
        return self._ontology.get_predicate(node.getAttribute("predicate"))

    def _compile_superaction(self, node):
        return self._ontology.create_action(node.getAttribute("name"))

    def _compile_default_questions(self):
        self._default_questions = [
            self._compile_question(element) for element in self._document.getElementsByTagName("default_question")
        ]

    def _compile_parameters(self):
        elements = self._document.getElementsByTagName("parameters")
        self._parameters = dict([self._compile_parameters_element(element) for element in elements])

    def _compile_dependencies(self):
        elements = self._document.getElementsByTagName("dependency")
        self._dependencies = dict([self._compile_dependency_element(element) for element in elements])

    def _compile_dependency_element(self, element):
        dependent_question = self._compile_question(element)
        others = {self._compile_question(element) for element in self._find_child_nodes(element, "question")}
        return dependent_question, others

    def _compile_parameters_element(self, element):
        try:
            obj = self._compile_question(element, "question_type")
        except DddXmlCompilerException:
            try:
                obj = self._compile_predicate(element)
            except DddXmlCompilerException:
                raise DddXmlCompilerException("expected question or predicate")

        parameters = self._compile_question_parameters(obj, element)
        return obj, parameters

    def _compile_question_parameters(self, question, element):
        result = self._compile_simple_parameters(element)
        self._compile_question_valued_parameter(element, "service_query", result)
        self._compile_question_valued_parameter(element, "default", result)
        self._compile_questions_valued_parameter(element, "label_questions", "label_question", result)
        self._compile_questions_valued_parameter(element, "related_information", "related_information", result)
        self._compile_alts_parameter(question, element, result)
        self._compile_predicates_parameter(element, "background", "background", result)
        self._compile_ask_feature_parameter(element, "ask_feature", "ask_features", result)
        return result

    def _compile_simple_parameters(self, element):
        result = {}
        supported_parameters = [
            "graphical_type",
            "source",
            "incremental",
            "verbalize",
            "format",
            "sort_order",
            "allow_goal_accommodation",
            "max_spoken_alts",
        ]
        for name in supported_parameters:
            value_as_string = element.getAttribute(name)
            if value_as_string:
                value = self._parser.parse_parameter(name, value_as_string)
                result[name] = value
        return result

    def _compile_alts_parameter(self, question, element, result):
        alt_nodes = self._find_child_nodes(element, "alt")
        if len(alt_nodes) > 0:
            result["alts"] = PropositionSet([self._compile_proposition_child_of(node) for node in alt_nodes])

    def _compile_question_valued_parameter(self, element, parameter_name, result):
        child_nodes = self._find_child_nodes(element, parameter_name)
        if len(child_nodes) == 1:
            node = child_nodes[0]
            result[parameter_name] = self._compile_question(node)
        elif len(child_nodes) > 1:
            raise DddXmlCompilerException("expected max 1 %s" % parameter_name)

    def _compile_questions_valued_parameter(self, element, parameter_name, node_name, result):
        child_nodes = self._find_child_nodes(element, node_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_question(node) for node in child_nodes]

    def _compile_predicates_parameter(self, parent, element_name, parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_predicate(node) for node in child_nodes]

    def _compile_ask_feature_parameter(self,
                                       parent,
                                       element_name,
                                       parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [
                self._compile_ask_feature_node(node)
                for node in child_nodes]

    def _compile_ask_feature_node(self, node):
        predicate_name = self._get_mandatory_attribute(node, "predicate")
        kpq = bool(self._get_optional_attribute(node, "kpq"))
        return AskFeature(predicate_name, kpq)

    def _compile_predicate(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        return self._ontology.get_predicate(predicate_name)

    def _parse(self, string):
        return self._parser.parse(string)

    def _compile_preferred(self, element):
        if len(element.childNodes) > 0:
            child = self._get_single_child_element(element, ["proposition"])
            return self._compile_proposition_child_of(element)
        else:
            return True

    def _parse_io_status(self, io_status_string):
        valid_io_statuses = [
            Domain.DEFAULT_IO_STATUS, Domain.EXCLUDED_IO_STATUS, Domain.HIDDEN_IO_STATUS, Domain.SILENT_IO_STATUS,
            Domain.DISABLED_IO_STATUS
        ]
        if io_status_string in valid_io_statuses:
            return io_status_string
        else:
            raise DddXmlCompilerException("Invalid io_status: %r" % io_status_string)


class GrammarCompiler(XmlCompiler):
    ELEMENT_TO_NODE = {
        "one-of": Constants.ONE_OF,
        "item": Constants.ITEM,
        "np": Constants.NP,
        "indefinite": Constants.INDEFINITE,
        "definite": Constants.DEFINITE,
        "vp": Constants.VP,
        "infinitive": Constants.INFINITIVE,
        "imperative": Constants.IMPERATIVE,
        "ing-form": Constants.ING_FORM,
        "object": Constants.OBJECT
    }

    def __init__(self):
        super(GrammarCompiler, self).__init__()
        self._current_filename = "grammar_<language>.xml"

    @property
    def _filename(self):
        return self._current_filename

    @_filename.setter
    def _filename(self, filename):
        self._current_filename = filename

    @property
    def _schema_name(self):
        return "grammar.xsd"

    def compile(self, xml_string, ontology, service_interface, language_code):
        self._filename = "grammar_%s.xml" % language_code
        self._validate(xml_string)
        self._text_node_re = re.compile("[\t\n ]+")
        self._parse_xml(xml_string)
        self._grammar_node = Node(Constants.GRAMMAR, {})
        root_element = self._get_root_element("grammar")
        for child in self._get_child_elements(root_element):
            self.compile_grammar_child_element(child)
        return self._grammar_node

    def _get_child_elements(self, element):
        return [child for child in element.childNodes if child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE]

    def compile_grammar_child_element(self, element):
        self.compile_grammar_entry_element(element)

    def compile_grammar_entry_element(self, element):
        node_type, parameters = self.compile_key(element)
        compiled_children = self._compile_children(element, itemize=True)
        if len(compiled_children) > 1:
            unitemized_compiled_children = [self._unitemize(child) for child in compiled_children]
            form_nodes = [Node(Constants.ITEM, {}, unitemized_compiled_children)]
        elif len(compiled_children) == 1:
            form_nodes = compiled_children
        else:
            raise DddXmlCompilerException("failed to compile grammar element %s" % element)
        self._perform_node_type_specific_post_processing(node_type, parameters, form_nodes)
        entry_node = Node(node_type, parameters, form_nodes)
        self._fix_whitespacing_recurse(entry_node)
        self._grammar_node.add_child(entry_node)

    def _fix_whitespacing_recurse(self, node):
        if isinstance(node, Node):
            if len(node.children) > 0:
                self._fix_text_nodes_whitespacing(node.children)
            for child in node.children:
                self._fix_whitespacing_recurse(child)

    def _fix_text_nodes_whitespacing(self, nodes):
        self._fix_whitespace_at_start(nodes)
        self._fix_whitespace_at_end(nodes)

    def _fix_whitespace_at_start(self, nodes):
        if isinstance(nodes[0], str):
            nodes[0] = nodes[0].lstrip()

    def _fix_whitespace_at_end(self, nodes):
        if isinstance(nodes[-1], str):
            nodes[-1] = nodes[-1].rstrip()

    def _perform_node_type_specific_post_processing(self, node_type, parameters, form_nodes):
        if node_type == Constants.SYS_ANSWER:
            self._mark_slot_as_individual(parameters["predicate"], form_nodes)

    def _mark_slot_as_individual(self, predicate, nodes):
        for node in nodes:
            if isinstance(node, Node) and node.type == Constants.SLOT and node.parameters["predicate"] == predicate:
                node.parameters = {}
            elif isinstance(node, Node) and node.type == Constants.ITEM:
                self._mark_slot_as_individual(predicate, node.children)

    def compile_key(self, element):
        if element.localName == "action":
            name = element.getAttribute("name")
            return Constants.ACTION, {"name": name}
        elif element.localName == "question":
            return self._compile_question_key(element)
        elif element.localName == "answer":
            return self._compile_answer_key(element)
        elif element.localName == "report":
            return self._compile_report_key(element)
        elif element.localName == "preconfirm":
            action = element.getAttribute("action")
            return Constants.PRECONFIRM, {"action": action}
        elif element.localName == "individual":
            name = element.getAttribute("name")
            return Constants.INDIVIDUAL, {"name": name}
        elif element.localName == "string":
            predicate = element.getAttribute("predicate")
            return Constants.STRING, {"predicate": predicate}
        elif element.localName == "title":
            return self._compile_title_key(element)
        elif element.localName == "validity":
            name = element.getAttribute("name")
            return Constants.VALIDITY, {"name": name}
        elif element.localName == "greeting":
            return Constants.GREETING, {}
        else:
            raise DddXmlCompilerException("unexpected grammar entry element %r" % element.localName)

    def _compile_question_key(self, element):
        predicate = element.getAttribute("predicate")
        speaker = element.getAttribute("speaker")
        if speaker == "system":
            return Constants.SYS_QUESTION, {"predicate": predicate}
        elif speaker == "user":
            return Constants.USER_QUESTION, {"predicate": predicate}
        elif speaker in ["", "all"]:
            return Constants.PREDICATE, {"name": predicate}
        else:
            raise DddXmlCompilerException("unexpected speaker attribute %r" % speaker)

    def _compile_answer_key(self, element):
        speaker = element.getAttribute("speaker")
        if speaker == "user":
            return Constants.ANSWER_COMBINATION, {}
        elif speaker == "system":
            return self._compile_system_answer_key(element)
        else:
            raise DddXmlCompilerException("unsupported speaker %r" % speaker)

    def _compile_system_answer_key(self, element):
        predicate = self._get_system_answer_predicate(element)
        node_type = self._get_system_answer_node_type(element)
        return node_type, {"predicate": predicate}

    def _get_system_answer_predicate(self, element):
        if element.getAttribute("predicate"):
            return element.getAttribute("predicate")
        else:
            return self._get_single_slot_predicate(element)

    def _get_system_answer_node_type(self, element):
        polarity = element.getAttribute("polarity")
        if polarity == "":
            return Constants.SYS_ANSWER
        elif polarity == "positive":
            return Constants.POSITIVE_SYS_ANSWER
        elif polarity == "negative":
            return Constants.NEGATIVE_SYS_ANSWER
        else:
            raise DddXmlCompilerException("unsupported polarity %r" % polarity)

    def _get_single_slot_predicate(self, element):
        compiled_children = self._compile_children(element)
        slots = [child for child in compiled_children if isinstance(child, Node)]
        if len(slots) == 1:
            slot = slots[0]
            return slot.parameters["predicate"]
        else:
            raise DddXmlCompilerException("expected a single slot but found %s" % element)

    def _compile_report_key(self, element):
        status = element.getAttribute("status")
        if status == "started":
            action = element.getAttribute("action")
            source = element.getAttribute("source")
            if source == "":
                return Constants.REPORT_STARTED, {"action": action}
            elif source == "dialogue":
                return Constants.PREREPORT, {"action": action}
            else:
                raise DddXmlCompilerException("unsupported source %r" % source)
        elif status == "ended":
            action = element.getAttribute("action")
            return Constants.REPORT_ENDED, {"action": action}
        elif status == "failed":
            action = element.getAttribute("action")
            reason = element.getAttribute("reason")
            return Constants.REPORT_FAILED, {"action": action, "reason": reason}
        else:
            raise DddXmlCompilerException("unexpected report status %r" % status)

    def _compile_title_key(self, element):
        title_type = element.getAttribute("type")
        if title_type == "action":
            action = element.getAttribute("action")
            return Constants.ACTION_TITLE, {"action": action}
        elif title_type == "question":
            predicate = element.getAttribute("predicate")
            return Constants.ISSUE_TITLE, {"predicate": predicate}
        else:
            raise DddXmlCompilerException("unsupported title type %r" % title_type)

    def _unitemize(self, node):
        if isinstance(node, Node) and node.type == Constants.ITEM and len(node.children) == 1:
            return node.children[0]
        else:
            return node

    def _compile_children(self, element, itemize=False):
        compiled_children = [self.compile_form(child, itemize) for child in element.childNodes]
        if len(compiled_children) >= 3:
            compiled_children = self._remove_nones_except_between_slots(compiled_children)
        return compiled_children

    def _remove_nones_except_between_slots(self, nodes):
        result = []
        if nodes[0] is not None:
            result.append(nodes[0])
        for n in range(1, len(nodes) - 1):
            if nodes[n] is None:
                if self._is_slot(nodes[n - 1]) and self._is_slot(nodes[n + 1]):
                    result.append(" ")
            else:
                result.append(nodes[n])
        if nodes[-1] is not None:
            result.append(nodes[-1])
        return result

    def _is_slot(self, node):
        return node.type == Constants.SLOT

    def compile_form(self, element, itemize):
        if element.nodeType == xml.dom.minidom.Node.TEXT_NODE:
            return self._compile_text_node(element, itemize)
        elif element.localName == "slot":
            return self._compile_slot_element(element)
        elif element.localName in self.ELEMENT_TO_NODE:
            node_type = self.ELEMENT_TO_NODE[element.localName]
            return self._compile_element(element, node_type)
        else:
            raise DddXmlCompilerException("unexpected form child element %s" % element)

    def _compile_text_node(self, node, itemize):
        if node.nodeValue.strip() == "":
            return None
        else:
            if itemize:
                return Node(Constants.ITEM, {}, [node.nodeValue])
            else:
                return node.nodeValue

    def _compile_element(self, element, node_type):
        return Node(node_type, {}, self._compile_children(element))

    def _compile_slot_element(self, element):
        predicate = element.getAttribute("predicate")
        sort = element.getAttribute("sort")
        if predicate:
            return Node(Constants.SLOT, {"predicate": predicate})
        elif sort:
            return Node(Constants.SLOT, {"sort": sort})
        else:
            raise DddXmlCompilerException("expected slot element to define predicate or sort")


class RglGrammarCompiler(GrammarCompiler):
    GENERICALLY_COMPILABLE_ELEMENTS = [
        rgl_types.NOUN_PHRASE, rgl_types.VERB_PHRASE, Constants.ONE_OF, Constants.ITEM, rgl_types.PROPER_NOUN,
        rgl_types.UTTERANCE, Constants.INDIVIDUAL
    ]

    @property
    def _schema_name(self):
        return "grammar_rgl.xsd"

    def compile_key(self, element):
        if element.localName == rgl_types.REQUEST:
            action = element.getAttribute("action")
            return rgl_types.REQUEST, {"action": action}
        elif element.localName == Constants.PREDICATE:
            name = element.getAttribute("name")
            return Constants.PREDICATE, {"name": name}
        else:
            return GrammarCompiler.compile_key(self, element)

    def compile_grammar_child_element(self, element):
        if element.localName == "lexicon":
            return self._compile_lexicon_element(element)
        else:
            return GrammarCompiler.compile_grammar_entry_element(self, element)

    def _compile_lexicon_element(self, element):
        compiled_children = [self._compile_lexicon_child(child) for child in self._get_child_elements(element)]
        node = Node(rgl_types.LEXICON, {}, compiled_children)
        self._grammar_node.add_child(node)

    def _compile_lexicon_child(self, element):
        return self._compile_generically(element)

    def _compile_generically(self, element):
        if element.nodeType == xml.dom.minidom.Node.TEXT_NODE:
            return self._compile_text_node(element, itemize=False)
        else:
            compiled_attributes = dict(list(element.attributes.items()))
            compiled_children = [self._compile_generically(child) for child in self._get_non_empty_child_nodes(element)]
            return Node(element.localName, compiled_attributes, compiled_children)

    def _get_non_empty_child_nodes(self, element):
        return [child for child in element.childNodes if not self._is_empty(child)]

    def _is_empty(self, node):
        return node.nodeType == xml.dom.minidom.Node.TEXT_NODE and node.nodeValue.strip() == ""

    def compile_form(self, element, itemize):
        if element.nodeType == xml.dom.minidom.Node.TEXT_NODE:
            return self._compile_text_node(element, itemize)
        elif element.localName == rgl_types.NOUN:
            return self._compile_noun_element(element)
        elif element.localName == rgl_types.VERB:
            return self._compile_verb_element(element)
        elif element.localName in self.GENERICALLY_COMPILABLE_ELEMENTS:
            node_type = element.localName
            return self._compile_generically(element)
        else:
            raise DddXmlCompilerException("unexpected form child element %s" % element)

    def _compile_noun_element(self, element):
        return Node(rgl_types.NOUN, {"ref": element.getAttribute("ref")})

    def _compile_verb_element(self, element):
        return Node(rgl_types.VERB, {"ref": element.getAttribute("ref")})


class ServiceInterfaceCompiler(XmlCompiler):
    @property
    def _name(self):
        return "service_interface"

    @property
    def _filename(self):
        return "%s.xml" % self._name

    @property
    def _schema_name(self):
        return "%s.xsd" % self._name

    def compile(self, xml_string):
        self._validate(xml_string)
        self._parse_xml(xml_string)
        self._device_element = self._get_root_element("service_interface")
        play_audio_actions = list(self._compile_play_audio_actions())
        custom_actions = list(self._compile_actions())
        actions = play_audio_actions + custom_actions
        queries = list(self._compile_queries())
        entity_recognizers = list(self._compile_entity_recognizers())
        validities = list(self._compile_validities())
        return ServiceInterface(actions, queries, entity_recognizers, validities)

    def _compile_play_audio_actions(self):
        elements = self._document.getElementsByTagName("play_audio_action")
        for element in elements:
            name = self._get_mandatory_attribute(element, "name")
            target = self._compile_target(element)
            audio_url = self._compile_audio_url(element)
            parameters = self._compile_parameters(element)
            action = PlayAudioActionInterface(name, target, parameters, audio_url)
            yield action

    def _compile_actions(self):
        elements = self._document.getElementsByTagName("action")
        for element in elements:
            name = self._get_mandatory_attribute(element, "name")
            target = self._compile_target(element)
            parameters = self._compile_parameters(element)
            failure_reasons = self._compile_failure_reasons(element)
            action = ServiceActionInterface(name, target, parameters, failure_reasons)
            yield action

    def _compile_audio_url(self, element):
        audio_url_elements = element.getElementsByTagName("audio_url_parameter")
        audio_url_element = audio_url_elements[0]
        name = self._get_mandatory_attribute(audio_url_element, "predicate")
        return AudioURLServiceParameter(name)

    def _compile_parameters(self, element):
        parameter_elements = element.getElementsByTagName("parameter")
        return [self._compile_parameter(element) for element in parameter_elements]

    def _compile_parameter(self, element):
        name = self._get_mandatory_attribute(element, "predicate")
        is_optional = self._parse_boolean(self._get_optional_attribute(element, "optional"))
        format = self._get_optional_attribute(element, "format")
        return ServiceParameter(name, format, is_optional)

    def _compile_failure_reasons(self, element):
        failure_reason_elements = element.getElementsByTagName("failure_reason")
        return [self._compile_failure_reason(element) for element in failure_reason_elements]

    def _compile_failure_reason(self, element):
        name = self._get_mandatory_attribute(element, "name")
        return ActionFailureReason(name)

    def _compile_queries(self):
        elements = self._document.getElementsByTagName("query")
        for element in elements:
            predicate = self._get_mandatory_attribute(element, "name")
            target = self._compile_target(element)
            parameters = self._compile_parameters(element)
            query = ServiceQueryInterface(predicate, target, parameters)
            yield query

    def _compile_entity_recognizers(self):
        elements = self._document.getElementsByTagName("entity_recognizer")
        for element in elements:
            entity_recognizer = self._compile_entity_recognizer(element)
            yield entity_recognizer

    def _compile_entity_recognizer(self, element):
        name = self._get_mandatory_attribute(element, "name")
        target = self._compile_target(element)
        return ServiceEntityRecognizerInterface(name, target)

    def _compile_validities(self):
        elements = self._document.getElementsByTagName("validator")
        for element in elements:
            name = self._get_mandatory_attribute(element, "name")
            parameters = self._compile_parameters(element)
            target = self._compile_target(element)
            validity = ServiceValidatorInterface(name, target, parameters)
            yield validity

    def _compile_target(self, element):
        target_elements = element.getElementsByTagName("target")
        target_element = target_elements[0]
        device_module_elements = target_element.getElementsByTagName("device_module")
        if any(device_module_elements):
            return self._compile_device_module_target(device_module_elements[0])
        frontend_elements = target_element.getElementsByTagName("frontend")
        if any(frontend_elements):
            return self._compile_frontend_target(frontend_elements[0])
        http_elements = target_element.getElementsByTagName("http")
        if any(http_elements):
            return self._compile_http_target(http_elements[0])

    def _compile_device_module_target(self, element):
        device = self._get_mandatory_attribute(element, "device")
        return DeviceModuleTarget(device)

    def _compile_frontend_target(self, element):
        return FrontendTarget()

    def _compile_http_target(self, element):
        endpoint = self._get_mandatory_attribute(element, "endpoint")
        return HttpTarget(endpoint)
