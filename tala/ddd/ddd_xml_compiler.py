# flake8: noqa

import os
import re
import warnings
import xml.dom.minidom

from lxml import etree

from tala.ddd.services.service_interface import ServiceActionInterface, ServiceParameter, ServiceQueryInterface, ServiceValidatorInterface, ServiceInterface, DeviceModuleTarget, FrontendTarget, HttpTarget, ActionFailureReason, PlayAudioActionInterface, AudioURLServiceParameter
from tala.model.ask_feature import AskFeature
from tala.model.hint import Hint
from tala.model.domain import Domain
from tala.model.goal import HandleGoal, PerformGoal, ResolveGoal
from tala.model.speaker import Speaker
from tala.model.plan import Plan
from tala.model.polarity import Polarity
from tala.model import plan_item
from tala.model.predicate import Predicate
from tala.model.proposition import GoalProposition, PropositionSet, PredicateProposition, ImplicationProposition
from tala.model import condition
from tala.model.question import AltQuestion, YesNoQuestion
from tala.model.action import Action

from tala.model.sort import CustomSort, BuiltinSortRepository, UndefinedSort, BOOLEAN
import tala.ddd.schemas


class DDDXMLCompilerException(Exception):
    pass


class ViolatesSchemaException(Exception):
    pass


class UnexpectedAttributeException(Exception):
    pass


class OntologyWarning(UserWarning):
    pass


class DDDXMLCompiler(object):
    def compile_ontology(self, *args, **kwargs):
        return OntologyCompiler().compile(*args, **kwargs)

    def compile_domain(self, *args, **kwargs):
        return DomainCompiler().compile(*args, **kwargs)

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
            raise DDDXMLCompilerException("expected 1 %s element" % name)
        return elements[0]

    def _parse_boolean(self, string):
        return string == "true"

    def _parse_integer(self, string):
        return int(string)

    def _has_child_node(self, element, node_name):
        for node in element.childNodes:
            if node.localName == node_name:
                return True
        return False

    def _find_child_nodes(self, element, node_name):
        return [node for node in element.childNodes if node.localName == node_name]

    def _get_mandatory_attribute(self, element, name):
        if not element.hasAttribute(name):
            raise DDDXMLCompilerException("%s requires attribute %r" % (element, name))
        return element.getAttribute(name)

    def _get_optional_attribute(self, element, name, default=None):
        if not element.hasAttribute(name):
            return default
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
            self._add_undeclared_static_sort(name)
            return self._custom_sorts_dict[name]

    def _add_undeclared_static_sort(self, name):
        warnings.warn(
            f"Expected a defined sort but got '{name}'. Adding it to the ontology as a static sort.", OntologyWarning
        )
        self._custom_sorts_dict[name] = CustomSort(self._ontology_name, name, False)

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

    def compile(self, ddd_name, xml_string, ontology, parser):
        self._validate(xml_string)
        self._ddd_name = ddd_name
        self._ontology = ontology
        self._parser = parser
        self._parse_xml(xml_string)
        self._domain_element = self._get_root_element("domain")
        self._compile_name()
        self._compile_plans()
        self._compile_default_questions()
        self._compile_parameters()
        self._compile_domain_queries()
        self._compile_iterators()
        self._compile_validators()
        self._compile_dependencies()
        return {
            "ddd_name": self._ddd_name,
            "name": self._domain_name,
            "plans": self._plans,
            "default_questions": self._default_questions,
            "parameters": self._parameters,
            "queries": self._queries + self._iterators,
            "validators": self._validators,
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
        self._compile_plan_single_attribute(plan, element, "restart_on_completion", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "reraise_on_resume", self._parse_boolean)
        self._compile_plan_single_attribute(plan, element, "io_status", self._parse_io_status)
        self._compile_plan_single_attribute(plan, element, "max_answers", self._parse_integer)
        if element.hasAttribute("alternatives_predicate"):
            plan["alternatives_predicate"] = element.getAttribute("alternatives_predicate")
        self._compile_plan(plan, element, "postplan")
        self._compile_plan_element_with_multiple_children(
            plan, element, "postconds", "downdate_condition", self._compile_condition
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
            raise DDDXMLCompilerException("expected max 1 %r element" % attribute_name)
        elif default is not None:
            plan[attribute_name] = default

    def _compile_query_content(self, query, element, question):
        def is_implication_query():
            return self._has_child_node(element, "implication")

        def is_randomized_query():
            return self._has_child_node(element, "select_at_random")

        def is_enumeration_query():
            return self._has_child_node(element, "enumerate")

        if is_implication_query():
            self._compile_implication_query(query, element)
        elif is_randomized_query():
            self._compile_randomized_query(query, element)
        elif is_enumeration_query():
            self._compile_enumeration_query(query, element)
        else:
            raise DDDXMLCompilerException(f"could not compile query for question {question}")

    def _compile_implication_query(self, query, element):
        implication_elements = self._find_child_nodes(element, "implication")
        query["implications"] = self._compile_implications(implication_elements)

    def _compile_implications(self, elements):
        implication_items = [self._compile_implication(node) for node in elements]
        return implication_items

    def _compile_implication(self, element):
        antecedent = self._compile_antecedent_child(element)
        consequent = self._compile_consequent_child(element)
        return ImplicationProposition(antecedent, consequent)

    def _compile_consequent_child(self, element):
        children = self._find_child_nodes(element, "consequent")
        return self._compile_predicate_proposition(children[0])

    def _compile_antecedent_child(self, element):
        children = self._find_child_nodes(element, "antecedent")
        return self._compile_predicate_proposition(children[0])

    def _compile_randomized_query(self, query, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        element_containing_individuals = self._get_single_child_element(element, ["select_at_random"])
        individual_elements = self._find_child_nodes(element_containing_individuals, "individual")
        query["for_random_selection"] = list(self._create_propositions(predicate_name, individual_elements))

    def _compile_enumeration_query(self, query, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        enumerate_element = self._get_single_child_element(element, ["enumerate"])
        randomize = self._get_optional_attribute(enumerate_element, "randomize", "false")
        individual_elements = self._get_child_elements(enumerate_element, ["individual"])

        if randomize == "true":
            query["for_random_enumeration"] = list(self._create_propositions(predicate_name, individual_elements))
        else:
            query["for_enumeration"] = list(self._create_propositions(predicate_name, individual_elements))

    def _create_propositions(self, predicate_name, individual_elements):
        predicate = self._ontology.get_predicate(predicate_name)
        for element in individual_elements:
            individual_name = element.getAttribute("value")
            individual = self._ontology.create_individual(individual_name, sort=predicate.getSort())
            yield PredicateProposition(predicate, individual)

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
            raise DDDXMLCompilerException("unsupported goal type %r" % goal_type)

    def _compile_question(self, element, type_attribute="type"):
        question_type = self._get_optional_attribute(element, type_attribute, "wh_question")
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
            raise DDDXMLCompilerException('unsupported question type %r' % question_type)

    def _compile_alt_question(self, element):
        proposition_set = self._compile_proposition_set(element, "alt")
        return AltQuestion(proposition_set)

    def _compile_proposition_set(self, element, node_name):
        child_nodes = self._find_child_nodes(element, node_name)
        propositions = [self._compile_proposition_child_of(child) for child in child_nodes]
        return PropositionSet(propositions)

    def _compile_yn_question(self, element):
        try:
            proposition = self._compile_proposition_child_of(element)
            return YesNoQuestion(proposition)
        except DDDXMLCompilerException as e:
            pass
        predicate = self._get_mandatory_attribute(element, "predicate")
        return self._parse("?%s" % predicate)

    def _compile_plan_item_nodes(self, nodes):
        def flatten(nested_list):
            flat_list = []
            for sublist in nested_list:
                flat_list.extend(sublist)
            return flat_list

        plan_items = [
            self._compile_plan_item_element(node) for node in nodes if node.__class__ == xml.dom.minidom.Element
        ]
        return flatten(plan_items)

    def _compile_plan_item_element(self, element):
        if element.localName in ["findout", "raise", "bind"]:
            return self._compile_question_raising_plan_item_element(element.localName, element)
        elif element.localName == "if":
            return self._compile_if_element(element)
        elif element.localName == "forget":
            return self._compile_forget_element(element)
        elif element.localName == "forget_shared":
            return self._compile_forget_shared_element(element)
        elif element.localName == "forget_all":
            return [plan_item.ForgetAll()]
        elif element.localName == "invoke_service_query":
            return self._compile_invoke_service_query_element(element)
        elif element.localName == "invoke_domain_query":
            return self._compile_invoke_domain_query_element(element)
        elif element.localName == "iterate":
            return self._compile_iterate_element(element)
        elif element.localName == "change_ddd":
            return self._compile_change_ddd_element(element)
        elif element.localName == "dev_query":
            return self._compile_deprecated_dev_query_element(element)
        elif element.localName == "invoke_service_action":
            return self._compile_invoke_service_action_element(element)
        elif element.localName == "get_done":
            return self._compile_get_done_element(element)
        elif element.localName == "dev_perform":
            warnings.warn("<dev_perform> is deprecated. Use <invoke_service_action> instead.", DeprecationWarning)
            return self._compile_deprecated_dev_perform_element(element)
        elif element.localName == "jumpto":
            return self._compile_jumpto_element(element)
        elif element.localName == "assume_shared":
            return self._compile_assume_shared_element(element)
        elif element.localName == "assume_issue":
            return self._compile_assume_issue_element(element)
        elif element.localName == "assume_system_belief":
            return self._compile_assume_element(element)
        elif element.localName == "inform":
            return self._compile_inform_element(element)
        elif element.localName == "log":
            return self._compile_log_element(element)
        elif element.localName == "signal_action_completion":
            return self._compile_signal_action_completion_element(element)
        elif element.localName == "signal_action_failure":
            return self._compile_signal_action_failure_element(element)
        elif element.localName == "end_turn":
            return self._compile_end_turn_element(element)
        elif element.localName == "reset_domain_query":
            return self._compile_reset_domain_query_element(element)
        else:
            raise DDDXMLCompilerException("unknown plan item element %s" % element.toxml())

    def _compile_question_raising_plan_item_element(self, item_type, element):
        question_type = self._get_optional_attribute(element, "type", "wh_question")
        question = self._compile_question(element)
        answer_from_pcom = self._get_answer_from_pcom(element)

        return [plan_item.QuestionRaisingPlanItem(self._domain_name, item_type, question, answer_from_pcom)]

    def _get_answer_from_pcom(self, element):
        answer_from_pcom = self._get_optional_attribute(element, "allow_answer_from_pcom")
        if answer_from_pcom is None:
            return False
        return True

    def _compile_if_element(self, element):
        def compile_condition():
            try:
                return self._compile_old_condition_element(element)
            except DDDXMLCompilerException:
                pass
            try:
                return self._compile_bare_proposition_element_as_condition(element)
            except DDDXMLCompilerException:
                pass
            return self._compile_condition(element)

        condition = compile_condition()
        consequent = self._compile_if_then_child_plan(element, "then")
        alternative = self._compile_if_then_child_plan(element, "else")
        return [plan_item.IfThenElse(condition, consequent, alternative)]

    def _compile_old_condition_element(self, element):
        condition_element = self._get_single_child_element(element, ["condition"])
        proposition_child = self._compile_proposition_child_of(condition_element)
        warnings.warn(
            '"<if><condition><proposition ..." is deprecated. '
            'Use "<if><proposition ..." without <condition> instead.', DeprecationWarning
        )
        return proposition_child

    def _compile_bare_proposition_element_as_condition(self, element):
        return self._compile_proposition_child_of(element)

    def _get_single_child_element(self, node, allowed_names):
        child_elements = [child for child in node.childNodes if child.localName in allowed_names]
        if len(child_elements) == 1:
            return child_elements[0]
        else:
            raise DDDXMLCompilerException(
                "expected exactly 1 child element among types %s in %s, was %s." %
                (allowed_names, node.toxml(), child_elements)
            )

    def _get_child_elements(self, node, allowed_names):
        child_elements = [child for child in node.childNodes if child.localName in allowed_names]
        return child_elements

    def _compile_forget_element(self, element):
        if element.getAttribute("predicate"):
            predicate_name = self._get_mandatory_attribute(element, "predicate")
            predicate = self._ontology.get_predicate(predicate_name)
            return [plan_item.Forget(predicate)]
        elif len(element.childNodes) == 1:
            proposition = self._compile_proposition_child_of(element)
            return [plan_item.Forget(proposition)]

    def _compile_forget_shared_element(self, element):
        if element.getAttribute("predicate"):
            predicate_name = self._get_mandatory_attribute(element, "predicate")
            predicate = self._ontology.get_predicate(predicate_name)
            return [plan_item.ForgetShared(predicate)]
        elif len(element.childNodes) == 1:
            proposition = self._compile_proposition_child_of(element)
            return [plan_item.ForgetShared(proposition)]

    def _compile_invoke_service_query_element(self, element):
        question = self._compile_question(element)
        self._check_deprecation_of_device(question, element, "invoke_service_query")
        return [plan_item.InvokeServiceQuery(question, min_results=1, max_results=1)]

    def _compile_deprecated_dev_query_element(self, element):
        warnings.warn('<dev_query> is deprecated. Use <invoke_service_query> instead.', DeprecationWarning)
        question = self._compile_question(element)
        self._check_deprecation_of_device(question, element, "dev_query")
        return [plan_item.InvokeServiceQuery(question, min_results=1, max_results=1)]

    def _compile_invoke_domain_query_element(self, element):
        question = self._compile_question(element)
        return [plan_item.InvokeDomainQuery(question, min_results=1, max_results=1)]

    def _compile_iterate_element(self, element):
        iterator_name = self._get_mandatory_attribute(element, "iterator")
        return [plan_item.Iterate(iterator_name)]

    def _compile_change_ddd_element(self, element):
        ddd_name = self._get_mandatory_attribute(element, "name")
        return [plan_item.ChangeDDD(ddd_name)]

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
        return [
            plan_item.InvokeServiceAction(
                self._ontology.name,
                action,
                preconfirm=preconfirm,
                postconfirm=postconfirm,
                downdate_plan=downdate_plan
            )
        ]

    def _compile_get_done_element(self, element):
        action_string = self._get_mandatory_attribute(element, "action")
        action = Action(action_string, self._ontology.name)
        step = self._get_optional_attribute(element, "step")
        return [plan_item.GetDone(action, step)]

    def _compile_jumpto_element(self, element):
        goal = self._compile_goal(element)
        return [plan_item.JumpTo(goal)]

    def _compile_assume_shared_element(self, element):
        predicate_proposition = self._compile_predicate_proposition_child_of(element)
        return [plan_item.AssumeShared(predicate_proposition)]

    def _compile_assume_element(self, element):
        predicate_proposition = self._compile_predicate_proposition_child_of(element)
        return [plan_item.Assume(predicate_proposition)]

    def _compile_inform_element(self, element):
        def create_non_forgetting_plan():
            cond = condition.HasSharedValue(predicate)
            alternative = assume_prop_and_issue + generate_end_turn_plan()
            return [plan_item.IfThenElse(cond, [], alternative)]

        def create_forgetting_plan():
            return [plan_item.Forget(predicate)] + assume_prop_and_issue + generate_end_turn_plan()

        def generate_end_turn_plan():
            if generate_end_turn:
                return [plan_item.EndTurn(float(expected_passivity))]
            else:
                return []

        predicate_proposition = self._compile_predicate_proposition_child_of(element)
        predicate = predicate_proposition.get_predicate()
        question = self._parse("?X.%s(X)" % predicate)
        insist = self._get_optional_attribute(element, "insist")
        generate_end_turn = self._parse_boolean(self._get_optional_attribute(element, "generate_end_turn"))
        expected_passivity = self._get_optional_attribute(element, "expected_passivity", 0.0)
        assume_prop_and_issue = [plan_item.Assume(predicate_proposition), plan_item.AssumeIssue(question)]

        if insist == "true":
            return create_forgetting_plan()
        return create_non_forgetting_plan()

    def _compile_predicate_proposition_child_of(self, element):
        child = self._get_single_child_element(element, ["proposition"])
        return self._compile_predicate_proposition(child)

    def _compile_assume_issue_element(self, element):
        question_type = self._get_mandatory_attribute(element, "type")
        insist = self._parse_boolean(self._get_optional_attribute(element, "insist"))
        question = self._compile_question(element)
        return [plan_item.AssumeIssue(question, insist=insist)]

    def _compile_log_element(self, element):
        message = self._get_mandatory_attribute(element, "message")
        return [plan_item.Log(message)]

    def _compile_signal_action_completion_element(self, element):
        postconfirm = self._get_optional_attribute(element, "postconfirm", default="true")
        return [plan_item.GoalPerformed(self._parse_boolean(postconfirm))]

    def _compile_signal_action_failure_element(self, element):
        reason = self._get_mandatory_attribute(element, "reason")
        return [plan_item.GoalAborted(reason)]

    def _compile_end_turn_element(self, element):
        timeout = self._get_mandatory_attribute(element, "expected_passivity")
        return [plan_item.EndTurn(float(timeout))]

    def _compile_reset_domain_query_element(self, element):
        question = self._compile_question(element)
        return [plan_item.ResetDomainQuery(question)]

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
        predicate = self._ontology.get_predicate(predicate_name)
        value = element.getAttribute("value")
        if value:
            if predicate.getSort().is_boolean_sort():
                if self._parse_boolean(value):
                    return PredicateProposition(predicate, polarity=Polarity.POS)
                return PredicateProposition(predicate, polarity=Polarity.NEG)
            individual = self._ontology.create_individual(value, sort=predicate.getSort())
        else:
            individual = None
        return PredicateProposition(predicate, individual)

    def _compile_deprecated_postconds(self, element):
        warnings.warn("<postcond> is deprecated. Use <downdate_condition> instead.", DeprecationWarning)
        return self._compile_proposition_child_of(element)

    def _compile_condition(self, element):
        HAS_VALUE = "has_value"
        IS_SHARED_FACT = "is_shared_fact"
        HAS_SHARED_VALUE = "has_shared_value"
        HAS_PRIVATE_VALUE = "has_private_value"
        HAS_SHARED_OR_PRIVATE_VALUE = "has_shared_or_private_value"
        IS_SHARED_COMMITMENT = "is_shared_commitment"
        IS_PRIVATE_BELIEF = "is_private_belief"
        IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT = "is_private_belief_or_shared_commitment"
        IS_TRUE = "is_true"
        QUERY_HAS_MORE_ITEMS = "has_more_items"

        child = self._get_single_child_element(
            element, [
                HAS_VALUE, IS_SHARED_FACT, IS_TRUE, HAS_SHARED_VALUE, HAS_PRIVATE_VALUE, HAS_SHARED_OR_PRIVATE_VALUE,
                IS_SHARED_COMMITMENT, IS_PRIVATE_BELIEF, IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT, QUERY_HAS_MORE_ITEMS
            ]
        )
        if child.localName == HAS_VALUE:
            warnings.warn("<has_value> is deprecated.", DeprecationWarning)
            return self._compile_has_value_condition(child)
        elif child.localName == IS_TRUE:
            warnings.warn("<is_true> is deprecated.", DeprecationWarning)
            return self._compile_is_true_condition(child)
        elif child.localName == HAS_SHARED_VALUE:
            return self._compile_has_shared_value_condition(child)
        elif child.localName == HAS_PRIVATE_VALUE:
            return self._compile_has_private_value_condition(child)
        elif child.localName == HAS_SHARED_OR_PRIVATE_VALUE:
            return self._compile_has_shared_or_private_value_condition(child)
        elif child.localName == IS_SHARED_COMMITMENT:
            return self._compile_is_shared_commitment_condition(child)
        elif child.localName == IS_PRIVATE_BELIEF:
            return self._compile_is_private_belief_condition(child)
        elif child.localName == IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT:
            return self._compile_is_private_belief_or_shared_commitment_condition(child)
        elif child.localName == QUERY_HAS_MORE_ITEMS:
            return self._compile_query_has_more_items_condition(child)
        elif child.localName == IS_SHARED_FACT:
            warnings.warn("<is_shared_fact> is deprecated.", DeprecationWarning)
            return self._compile_is_true_condition(child)

    def _compile_has_value_condition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        predicate = self._ontology.get_predicate(predicate_name)
        return condition.HasValue(predicate)

    def _compile_has_shared_value_condition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        predicate = self._ontology.get_predicate(predicate_name)
        return condition.HasSharedValue(predicate)

    def _compile_has_private_value_condition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        predicate = self._ontology.get_predicate(predicate_name)
        return condition.HasPrivateValue(predicate)

    def _compile_has_shared_or_private_value_condition(self, element):
        predicate_name = self._get_mandatory_attribute(element, "predicate")
        predicate = self._ontology.get_predicate(predicate_name)
        return condition.HasSharedOrPrivateValue(predicate)

    def _compile_is_shared_commitment_condition(self, element):
        proposition = self._compile_predicate_proposition(element)
        return condition.IsSharedCommitment(proposition)

    def _compile_is_private_belief_condition(self, element):
        proposition = self._compile_predicate_proposition(element)
        return condition.IsPrivateBelief(proposition)

    def _compile_is_private_belief_or_shared_commitment_condition(self, element):
        proposition = self._compile_predicate_proposition(element)
        return condition.IsPrivateBeliefOrSharedCommitment(proposition)

    def _compile_query_has_more_items_condition(self, element):
        if element.hasAttribute("predicate"):
            iterator = self._compile_question(element)
        else:
            iterator = self._get_optional_attribute(element, "iterator")
        return condition.QueryHasMoreItems(iterator)

    def _compile_is_true_condition(self, element):
        child = self._get_single_child_element(element, ["proposition"])
        proposition = self._compile_predicate_proposition(child)
        return condition.IsTrue(proposition)

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
        def compile_then_or_else_node(then_or_else_node):
            if len(then_or_else_node.childNodes) == 0:
                return []
            else:
                return self._compile_plan_item_nodes(then_or_else_node.childNodes)

        then_or_else_nodes = self._find_child_nodes(element, node_name)
        if len(then_or_else_nodes) == 0:
            return []
        elif len(then_or_else_nodes) == 1:
            return compile_then_or_else_node(then_or_else_nodes[0])
        else:
            raise DDDXMLCompilerException("expected only one %r element" % node_name)

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
            raise DDDXMLCompilerException("Expected at most one child for %s, found %s." % (element, child_nodes))
        elif len(child_nodes) == 1:
            plan[attribute_name] = compilation_method(child_nodes[0])

    def _compile_superaction(self, node):
        return self._ontology.create_action(node.getAttribute("name"))

    def _compile_default_questions(self):
        self._default_questions = [
            self._compile_question(element) for element in self._document.getElementsByTagName("default_question")
        ]

    def _compile_parameters(self):
        elements = self._document.getElementsByTagName("parameters")
        self._parameters = dict([self._compile_parameters_element(element) for element in elements])

    def _compile_domain_queries(self):
        queries = self._document.getElementsByTagName("query")
        self._queries = [self._compile_query_element(element) for element in queries]

    def _compile_iterators(self):
        iterators = self._document.getElementsByTagName("iterator")
        self._iterators = [self._compile_iterator_element(element) for element in iterators]

    def _compile_validators(self):
        validators = self._document.getElementsByTagName("validator")
        self._validators = [self._compile_validator_element(element) for element in validators]

    def _compile_dependencies(self):
        elements = self._document.getElementsByTagName("dependency")
        self._dependencies = dict([self._compile_dependency_element(element) for element in elements])

    def _compile_dependency_element(self, element):
        dependent_question = self._compile_question(element)
        others = {self._compile_question(element) for element in self._find_child_nodes(element, "question")}
        return dependent_question, others

    def _compile_parameters_element(self, element):
        try:
            if not element.hasAttribute("question_type"):
                obj = self._compile_predicate(element)
            else:
                obj = self._compile_question(element, "question_type")
        except DDDXMLCompilerException:
            raise DDDXMLCompilerException("expected question or predicate in ", str(element))
        parameters = self._compile_question_parameters(obj, element)
        return obj, parameters

    def _compile_query_element(self, element):
        question = self._compile_question(element, "question_type")
        query = {"query": question}
        self._compile_query_content(query, element, question)
        return query

    def _compile_iterator_element(self, element):
        name = self._get_mandatory_attribute(element, "name")
        iterator = {"query": name}
        self._compile_enumeration_iterator(iterator, element)
        return iterator

    def _compile_enumeration_iterator(self, query, element):
        selection = self._get_single_child_element(element, ["enumerate"])
        randomize = self._get_optional_attribute(selection, "randomize", "false")
        limit = self._get_optional_attribute(selection, "limit", "-1")
        query["limit"] = limit
        if randomize == "true":
            query["for_random_enumeration"] = self._create_proposition_children_of(selection)
        else:
            query["for_enumeration"] = self._create_proposition_children_of(selection)

    def _create_proposition_children_of(self, parent):
        proposition_nodes = self._find_child_nodes(parent, "proposition")
        return [self._compile_predicate_proposition(node) for node in proposition_nodes]

    def _compile_validator_element(self, element):
        name = self._get_mandatory_attribute(element, "name")
        validator = {"validator": name}
        self._compile_validator(validator, element)
        return validator

    def _compile_validator(self, validator, element):
        config_elems = self._find_child_nodes(element, "configuration")
        configurations = [self._create_proposition_children_of(config_elem) for config_elem in config_elems]
        validator["valid_configurations"] = configurations

    def _compile_question_parameters(self, question, element):
        result = self._compile_simple_parameters(element)
        self._compile_question_valued_parameter(element, "service_query", result)
        self._compile_question_valued_parameter(element, "default", result)
        self._compile_questions_valued_parameter(element, "label_questions", "label_question", result)
        self._compile_questions_valued_parameter(element, "related_information", "related_information", result)
        self._compile_alts_parameter(question, element, result)
        self._compile_predicates_parameter(element, "background", "background", result)
        self._compile_ask_feature_parameter(element, "ask_feature", "ask_features", result)
        self._compile_hint_parameter(element, "hint", "hints", result)
        self._compile_always_relevant_parameter(element, "always_relevant", "always_relevant", result)
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
            "max_reported_hit_count",
            "always_ground",
            "on_zero_hits_action",
            "on_too_many_hits_action",
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
            raise DDDXMLCompilerException("expected max 1 %s" % parameter_name)

    def _compile_questions_valued_parameter(self, element, parameter_name, node_name, result):
        child_nodes = self._find_child_nodes(element, node_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_question(node) for node in child_nodes]

    def _compile_predicates_parameter(self, parent, element_name, parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_predicate(node) for node in child_nodes]

    def _compile_ask_feature_parameter(self, parent, element_name, parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_ask_feature_node(node) for node in child_nodes]

    def _compile_ask_feature_node(self, node):
        predicate_name = self._get_mandatory_attribute(node, "predicate")
        kpq = bool(self._get_optional_attribute(node, "kpq"))
        return AskFeature(predicate_name, kpq)

    def _compile_hint_parameter(self, parent, element_name, parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = [self._compile_hint_node(node) for node in child_nodes]

    def _compile_hint_node(self, node):
        inform_nodes = self._find_child_nodes(node, "inform")
        inform = self._compile_inform_element(inform_nodes[0])
        return Hint(inform)

    def _compile_always_relevant_parameter(self, parent, element_name, parameter_name, result):
        child_nodes = self._find_child_nodes(parent, element_name)
        if len(child_nodes) > 0:
            result[parameter_name] = True

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
            raise DDDXMLCompilerException("Invalid io_status: %r" % io_status_string)


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
        validities = list(self._compile_validities())
        return ServiceInterface(actions, queries, validities)

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
