#!/usr/bin/env python2.7

import io
import codecs
import os
import sys
from collections import OrderedDict

from lxml import etree

from tala.nl import languages
from tala.config import BackendConfig
from tala.ddd.ddd_py_compiler import DddPyCompiler
from tala.model.plan_item import PlanItem
from tala.nl.gf import rgl_grammar_entry_types as rgl_types
from tala.nl.gf.grammar_entry_types import Constants, Node


class PyToXmlConverter:
    def __init__(self, ddd, languages):
        self._ddd = ddd
        self._languages = languages

    def convert(self):
        OntologyConverter(self._ddd, self._languages).convert()
        DomainConverter(self._ddd, self._languages).convert()
        GrammarConverter(self._ddd, self._languages).convert()

    def _create_element(self, tag_name, **attributes):
        element = etree.Element(tag_name, OrderedDict())
        self._set_attributes(element, **attributes)
        return element

    def _set_attributes(self, element, **attributes):
        for attribute, value in list(attributes.items()):
            if value is not None:
                self._set_attribute(element, attribute, str(value))

    def _set_attribute(self, element, name, value):
        element.attrib[name] = value

    def _write_xml_header(self):
        self._write('<?xml version="1.0" encoding="utf-8"?>\n')

    def _write(self, string):
        self._output.write(string)


class OntologyConverter(PyToXmlConverter):
    def convert(self):
        self._root = self._create_element("ontology", name=self._ddd.ontology.get_name())
        self._convert_sorts()
        self._convert_predicates()
        self._convert_actions()
        self._convert_individuals()
        xml = etree.tostring(self._root, pretty_print=True)
        with open("%s/ontology.xml" % self._ddd.name, "w") as f:
            f.write(xml)

    def _convert_sorts(self):
        for sort in list(self._ddd.ontology.get_sorts().values()):
            if not sort.is_builtin():
                self._convert_sort(sort)

    def _convert_sort(self, sort):
        element = self._create_element("sort", name=sort.get_name())
        if sort.is_dynamic():
            self._set_attribute(element, "dynamic", "true")
        self._root.append(element)

    def _convert_predicates(self):
        for predicate in list(self._ddd.ontology.get_predicates().values()):
            self._convert_predicate(predicate)

    def _convert_predicate(self, predicate):
        element = self._create_element("predicate", name=predicate.get_name())
        self._set_attribute(element, "sort", predicate.getSort().get_name())
        if predicate.allows_multiple_instances():
            self._set_attributes(element, multiple_instances="true")
        if predicate.get_feature_of_name():
            self._set_attributes(element, feature_of=predicate.get_feature_of_name())
        self._root.append(element)

    def _convert_actions(self):
        for action in self._ddd.ontology.get_actions():
            if action != "up":
                self._convert_action(action)

    def _convert_action(self, action):
        element = self._create_element("action", name=action)
        self._root.append(element)

    def _convert_individuals(self):
        individuals = self._ddd.ontology.get_individuals()
        for individual, sort in list(individuals.items()):
            self._convert_individual(individual, sort.get_name())

    def _convert_individual(self, individual, sort_name):
        element = self._create_element("individual", name=individual)
        self._set_attribute(element, "sort", sort_name)
        self._root.append(element)


class DomainConverter(PyToXmlConverter):
    def convert(self):
        self._root = self._create_element("domain", name=self._ddd.domain.get_name())
        self._convert_goals()
        self._convert_dependencies()
        self._convert_parameters()
        self._convert_default_questions()
        xml = etree.tostring(self._root, pretty_print=True)
        xml = xml.replace("</goal>", "</goal>\n")
        with open("%s/domain.xml" % self._ddd.name, "w") as f:
            f.write(xml)

    def _convert_goals(self):
        for goal in self._ddd.domain.get_all_goals_in_defined_order():
            if not (goal.is_perform_goal() and goal.get_action().get_value() == "up"):
                self._convert_goal(goal)

    def _convert_goal(self, goal):
        element = self._create_element("goal")
        self._set_goal_attributes(element, goal)
        if self._ddd.domain.has_dynamic_title(goal):
            self._set_attributes(element, dynamic_title="true")
        if self._ddd.domain.goal_allows_accommodation_without_feedback(goal):
            self._set_attributes(element, accommodate_without_feedback="true")
        if self._ddd.domain.restart_on_completion(goal):
            self._set_attributes(element, restart_on_completion="true")
        io_status = self._ddd.domain.get_goal_attribute(goal, "io_status")
        if io_status:
            self._set_attributes(element, io_status=io_status)
        self._add_preferred_element_if_present(goal, element)
        self._convert_plan(element, "plan", self._ddd.domain.get_plan(goal))
        self._convert_postconds(element, self._ddd.domain.get_postconds(goal))
        if self._ddd.domain.get_postplan(goal):
            self._convert_plan(element, "postplan", self._ddd.domain.get_postplan(goal))
        self._convert_gui_context(goal, element)
        self._convert_superactions(goal, element)
        self._root.append(element)

    def _set_goal_attributes(self, element, goal):
        if goal.is_perform_goal():
            self._set_attribute(element, "type", "perform")
            self._set_attribute(element, "action", goal.get_action().get_value())
        elif goal.is_resolve_goal():
            question = goal.get_question()
            self._set_attribute(element, "type", "resolve")
            self._set_question_attributes(element, question, "question_type")
        elif goal.is_handle_goal():
            self._set_attribute(element, "type", "handle")
            self._set_attribute(element, "action", goal.get_device_event())
        else:
            raise Exception("unsupported goal %s" % goal)
        if self._ddd.domain.goal_allows_accommodation_without_feedback(goal):
            self._set_attribute(element, "accommodate_without_feedback", "true")

    def _add_preferred_element_if_present(self, goal, goal_element):
        node = self._ddd.domain.get_goal_attribute(goal, "preferred")
        if node:
            preferred_element = self._create_element("preferred")
            goal_element.append(preferred_element)
            if node is not True and node.is_predicate_proposition():
                proposition_element = self._create_element(
                    "proposition", predicate=node.getPredicate(), value=node.getArgument()
                )
                preferred_element.append(proposition_element)

    def _create_goal_element(self, goal):
        if goal.is_perform_goal():
            type_ = "perform"
        if goal.is_resolve_goal():
            type_ = "resolve"
        if goal.is_handle_goal():
            type_ = "handle"
        element = self._create_element(type_)
        if goal.is_perform_goal():
            self._set_attribute(element, "action", goal.get_action().get_value())
        elif goal.is_resolve_goal():
            question = goal.get_question()
            self._set_question_attributes(element, question, "type")
        elif goal.is_handle_goal():
            self._set_attribute(element, "action", goal.get_device_event())
        else:
            raise Exception("unsupported goal %s" % goal)
        return element

    def _set_question_attributes(self, element, question, type_attribute="type"):
        if question.is_wh_question():
            if question.get_content().is_lambda_abstracted_goal_proposition():
                self._set_attribute(element, type_attribute, "goal")
            else:
                self._set_attribute(element, type_attribute, "wh_question")
                if question.get_content().is_lambda_abstracted_predicate_proposition():
                    self._set_attributes(element, predicate=question.get_predicate())
        elif question.is_alt_question():
            self._set_attribute(element, type_attribute, "alt_question")
        elif question.is_yes_no_question():
            self._set_attribute(element, type_attribute, "yn_question")
            if question.get_content().is_goal_proposition():
                if question.get_content().get_goal().is_perform_goal():
                    action = question.get_content().get_goal().get_content()
                    perform_element = self._create_element("perform", action=action)
                    element.append(perform_element)
                elif question.get_content().get_goal().is_resolve_goal():
                    predicate = question.get_content().get_goal().get_content().get_predicate()
                    perform_element = self._create_element("resolve", type="wh_question", predicate=predicate)
                    element.append(perform_element)
            else:
                proposition_element = self._create_element("proposition")
                self._set_proposition_attributes(proposition_element, question.get_content())
                element.append(proposition_element)
        else:
            raise Exception("unsupported question %s" % question)

    def _set_proposition_attributes(self, element, proposition, typed_by_parent=False):
        if proposition.is_goal_proposition():
            self._set_goal_attributes(element, proposition.get_goal())
        elif proposition.is_predicate_proposition():
            self._set_predicate_proposition_attributes(element, proposition, typed_by_parent)
        else:
            raise Exception("unsupported proposition %s" % proposition)

    def _set_predicate_proposition_attributes(self, element, proposition, typed_by_parent=False):
        if not typed_by_parent:
            self._set_attributes(element, type="predicate")
            self._set_attributes(element, predicate=proposition.getPredicate())
        if proposition.getArgument() is not None:
            self._set_attributes(element, value=proposition.getArgument().getValue())

    def _convert_plan(self, parent, tag, plan):
        element = self._create_element(tag)
        for item in plan:
            self._convert_plan_item(element, item)
        parent.append(element)

    def _convert_plan_item(self, parent, item):
        if item.get_type() in [PlanItem.TYPE_FINDOUT, PlanItem.TYPE_RAISE, PlanItem.TYPE_BIND]:
            self._convert_question_raising_item(parent, item)
        # elif item.get_type() == PlanItem.TYPE_IF_THEN_ELSE:
        #     self._convert_if_then_else(parent, item)
        elif item.get_type() == PlanItem.TYPE_FORGET:
            self._convert_forget(parent, item)
        elif item.get_type() == PlanItem.TYPE_FORGET_ALL:
            self._convert_forget_all(parent)
        elif item.get_type() == PlanItem.TYPE_INVOKE_SERVICE_QUERY:
            self._convert_invoke_service_query(parent, item)
        elif item.get_type() == PlanItem.TYPE_INVOKE_SERVICE_ACTION:
            self._convert_invoke_service_action(parent, item)
        elif item.get_type() == PlanItem.TYPE_JUMPTO:
            self._convert_jumpto(parent, item)
        elif item.get_type() == PlanItem.TYPE_ASSUME_SHARED:
            self._convert_assume_shared(parent, item)
        else:
            raise Exception("unsupported plan item %s" % item)

    def _convert_question_raising_item(self, parent, item):
        element = self._create_element(item.get_type())
        self._set_question_attributes(element, item.get_question())
        self._add_potential_question_alts(element, item.get_question())
        parent.append(element)

    def _add_potential_question_alts(self, parent, question):
        if question.is_alt_question():
            self._add_alts(parent, question.get_content())

    def _add_alts(self, parent, alts):
        for alt in alts:
            element = self._create_alt_element(alt)
            parent.append(element)

    def _create_alt_element(self, alt):
        element = self._create_element("alt")
        if alt.is_goal_proposition():
            child = self._create_goal_element(alt.get_goal())
            element.append(child)
        elif alt.is_predicate_proposition():
            child = self._create_element("proposition")
            self._set_proposition_attributes(child, alt)
            element.append(child)
        else:
            raise Exception("unsupported alt %s" % alt)
        return element

    def _convert_forget(self, parent, item):
        element = self._create_element("forget")
        if item.getContent().is_predicate_proposition():
            self._set_predicate_proposition_attributes(element, item.getContent())
        elif item.getContent().is_predicate():
            self._set_attribute(element, "predicate", item.getContent().get_name())
        parent.append(element)

    def _convert_forget_all(self, parent):
        element = self._create_element("forget_all")
        parent.append(element)

    def _convert_invoke_service_query(self, parent, item):
        element = self._create_element("invoke_service_query")
        self._set_question_attributes(element, item.getContent())
        parent.append(element)

    def _convert_invoke_service_action(self, parent, item):
        element = self._create_element("invoke_service_action", action=item.get_service_action())
        if item.preconfirm:
            self._set_attribute(element, "preconfirm", item.preconfirm.lower())
        if item.postconfirm:
            self._set_attribute(element, "postconfirm", "true")
        if item.should_downdate_plan():
            self._set_attribute(element, "downdate_plan", "true")
        parent.append(element)

    def _convert_postconds(self, parent, postconds):
        for postcond in postconds:
            self._convert_postcond(parent, postcond)

    def _convert_postcond(self, parent, postcond):
        element = self._create_element("postcond")
        if postcond.is_predicate_proposition():
            predicate = postcond.getPredicate()
            individual = postcond.getArgument()
            child = self._create_element("proposition", predicate=predicate, value=individual)
            element.append(child)
        parent.append(element)

    def _convert_jumpto(self, parent, item):
        element = self._create_element("jumpto")
        self._set_goal_attributes(element, item.getContent())
        parent.append(element)

    def _convert_assume_shared(self, parent, item):
        element = self._create_element("assume_shared")
        proposition_element = self._create_element("proposition")
        self._set_proposition_attributes(proposition_element, item.getContent())
        element.append(proposition_element)
        parent.append(element)

    def _convert_dependencies(self):
        for dependent_question, others in list(self._ddd.domain.dependencies.items()):
            element = self._create_element("dependency")
            self._set_question_attributes(element, dependent_question)
            for other in others:
                child = self._create_element("question")
                self._set_question_attributes(child, other)
                element.append(child)
            self._root.append(element)

    def _convert_parameters(self):
        for obj, parameters in list(self._ddd.domain.parameters.items()):
            self._convert_object_parameters(obj, parameters)

    def _convert_object_parameters(self, obj, parameters):
        element = self._create_element("parameters")
        if obj.is_question():
            self._set_question_attributes(element, obj, "question_type")
        elif obj.is_predicate():
            self._set_attribute(element, "predicate", obj.get_name())
        else:
            raise Exception("parameters supported only for questions and predicates")
        for name, value in list(parameters.items()):
            self._convert_parameter(element, name, value)
        self._root.append(element)

    def _convert_parameter(self, parent, parameter, value):
        if parameter == "alts":
            self._add_alts(parent, value)
        elif parameter == "background":
            self._add_background_parameter(parent, value)
        elif parameter in ["service_query", "default"]:
            self._set_question_valued_parameter(parent, parameter, value)
        elif parameter == "related_information":
            self._set_questions_valued_parameter(parent, parameter, value)
        elif parameter == "label_questions":
            self._set_questions_valued_parameter(parent, "label_question", value)
        elif parameter in ["incremental", "verbalize"]:
            self._set_attribute(parent, parameter, self._convert_boolean_value(value))
        elif parameter == "ask_features":
            self._add_ask_features(parent, value)
        elif parameter in [
            "graphical_type", "source", "format", "sort_order", "allow_goal_accommodation", "max_spoken_alts"
        ]:
            self._set_attribute(parent, parameter, str(value))
        else:
            raise Exception("unsupported parameter %r" % parameter)

    def _convert_boolean_value(self, value):
        if value:
            return "true"
        else:
            return "false"

    def _add_background_parameter(self, parent, predicates):
        for predicate in predicates:
            element = self._create_element("background", predicate=predicate)
            parent.append(element)

    def _set_question_valued_parameter(self, parent, parameter, value):
        element = self._create_element(parameter)
        self._set_question_attributes(element, value)
        parent.append(element)

    def _set_questions_valued_parameter(self, parent, parameter, questions):
        for question in questions:
            element = self._create_element(parameter)
            self._set_question_attributes(element, question)
            parent.append(element)

    def _convert_gui_context(self, goal, goal_element):
        gui_context = self._ddd.domain.get_gui_context(goal)
        for item in gui_context:
            predicate = item.get_name()
            element = self._create_element("gui_context", predicate=predicate)
            goal_element.append(element)

    def _convert_superactions(self, goal, goal_element):
        for superaction in self._ddd.domain.get_superactions(goal):
            superaction_element = self._create_element("superaction", name=superaction.get_value())
            goal_element.append(superaction_element)

    def _add_ask_features(self, parent, predicates):
        for predicate in predicates:
            ask_feature_element = self._create_element("ask_feature", predicate=predicate)
            parent.append(ask_feature_element)

    def _convert_default_questions(self):
        for question in self._ddd.domain.default_questions:
            if question.is_wh_question():
                predicate = question.get_predicate()
                question_element = self._create_element("default_question", type="wh_question", predicate=predicate)
                self._root.append(question_element)


class GrammarConverter(PyToXmlConverter):
    def __init__(self, ddd, languages):
        PyToXmlConverter.__init__(self, ddd, languages)
        self._conversion_methods = {
            Constants.GRAMMAR: self._convert_grammar_node,
            Constants.ITEM: self._convert_item_node,
            Constants.ONE_OF: self._convert_one_of_node,
            Constants.PREDICATE: self._convert_predicate_node,
            Constants.VALIDITY: self._convert_validity_node,
            Constants.ACTION: self._convert_action_node,
            Constants.PREREPORT: self._convert_prereport_node,
            Constants.REPORT_STARTED: self._convert_report_started_node,
            Constants.REPORT_ENDED: self._convert_report_ended_node,
            Constants.REPORT_FAILED: self._convert_report_failed_node,
            Constants.PRECONFIRM: self._convert_preconfirm_node,
            Constants.SLOT: self._convert_slot_node,
            Constants.NP: self._convert_np_node,
            Constants.ACTION_TITLE: self._convert_action_title_node,
            Constants.ISSUE_TITLE: self._convert_issue_title_node,
            Constants.SYS_QUESTION: self._convert_sys_question_node,
            Constants.USER_QUESTION: self._convert_user_question_node,
            Constants.INDIVIDUAL: self._convert_individual,
            Constants.ANSWER_COMBINATION: self._convert_answer_combination,
            Constants.VP: self._convert_simple_node,
            Constants.INDEFINITE: self._convert_simple_node,
            Constants.DEFINITE: self._convert_simple_node,
            Constants.SYS_ANSWER: self._convert_sys_answer,
            Constants.INFINITIVE: self._convert_simple_node,
            Constants.IMPERATIVE: self._convert_simple_node,
            Constants.ING_FORM: self._convert_simple_node,
            Constants.OBJECT: self._convert_simple_node,
            Constants.GREETING: self._convert_simple_node,
            Constants.POSITIVE_SYS_ANSWER: self._convert_positive_sys_answer,
            Constants.NEGATIVE_SYS_ANSWER: self._convert_negative_sys_answer,
            rgl_types.UTTERANCE: self._convert_utterance,
        }

    def convert(self):
        for language_code in self._languages:
            grammar = self._load_and_compile_grammar_entries(language_code)
            self._convert_grammar(language_code, grammar)

    def _load_and_compile_grammar_entries(self, language_code):
        grammar_source = self._load_grammar_source(language_code)
        return DddPyCompiler().compile_grammar(grammar_source, self._ddd.ontology, self._ddd.service_interface)

    def _load_grammar_source(self, language_code):
        with open("%s/grammar/grammar_%s.py" % (self._ddd.name, language_code)) as f:
            return f.read()

    def _convert_grammar(self, language_code, input_root_node):
        self._output = codecs.open("%s/grammar/grammar_%s.xml" % (self._ddd.name, language_code), "w", "utf-8")
        self._generate_and_write_output(input_root_node)
        self._output.close()

    def _generate_and_write_output(self, input_root_node):
        self._write_xml_header()
        self._convert_node(input_root_node)

    def _convert_node(self, node, parent=None):
        if isinstance(node, str):
            if len(node) > 0:
                self._write(node)
            else:
                print(("warning: can not convert empty grammar node: %s" % parent))
        elif node.type in self._conversion_methods:
            self._conversion_methods[node.type](node, parent)
        else:
            print(("WARNING: don't know how to convert grammar node of type %r" % node.type))

    def _convert_grammar_node(self, node, parent):
        self._write('<grammar>\n')
        self._convert_children(node.children, parent, delimeter="\n")
        self._write('</grammar>\n')

    def _convert_children(self, children, parent, itemize=False, indent=0, delimeter=""):
        for idx in range(len(children)):
            child = children[idx]
            if itemize:
                self._write('\n%s<item>' % ("  " * indent))
            self._convert_node(child, parent)
            if itemize:
                self._write('</item>')
            if idx < (len(children) - 1):
                self._write(delimeter)

    def _convert_simple_node(self, node, parent):
        self._write_element(node, 0, trailing_newline=False)

    def _convert_item_node(self, node, parent):
        self._convert_children(node.children, parent, indent=2)

    def _convert_one_of_node(self, node, parent):
        self._write('\n')
        self._write_element(node, 2, itemize_children=True)
        self._write('  ')

    def _convert_predicate_node(self, node, parent):
        attributes = {"type": "wh_question", "speaker": "all", "predicate": node.parameters["name"]}
        self._write_element(node, 1, attributes, "question")

    def _convert_validity_node(self, node, parent):
        attributes = {"name": node.parameters["name"]}
        self._write_element(node, 1, attributes)

    def _convert_action_node(self, node, parent):
        attributes = {"name": node.parameters["name"]}
        self._write_element(node, 1, attributes)

    def _convert_prereport_node(self, node, parent):
        attributes = {"action": node.parameters["action"], "status": "started", "source": "dialogue"}
        self._write_element(node, 1, attributes, "report")

    def _convert_report_started_node(self, node, parent):
        attributes = {"action": node.parameters["action"], "status": "started"}
        self._write_element(node, 1, attributes, "report")

    def _convert_report_ended_node(self, node, parent):
        attributes = {"action": node.parameters["action"], "status": "ended"}
        self._write_element(node, 1, attributes, "report")

    def _convert_report_failed_node(self, node, parent):
        attributes = {"action": node.parameters["action"], "status": "failed", "reason": node.parameters["reason"]}
        self._write_element(node, 1, attributes, "report")

    def _convert_preconfirm_node(self, node, parent):
        attributes = {"action": node.parameters["action"]}
        self._write_element(node, 1, attributes)

    def _convert_slot_node(self, node, parent):
        if "predicate" in node.parameters:
            attributes = {"type": "individual", "predicate": node.parameters["predicate"]}
            self._write_element(node, 0, attributes, trailing_newline=False)
        elif "predicate" in parent.parameters:
            attributes = {"type": "individual", "predicate": parent.parameters["predicate"]}
            self._write_element(node, 0, attributes, trailing_newline=False)
        elif "sort" in node.parameters:
            attributes = {"sort": node.parameters["sort"]}
            self._write_element(node, 0, attributes, trailing_newline=False)

    def _convert_np_node(self, node, parent):
        self._write('\n')
        self._write_element(node, 2)

    def _convert_action_title_node(self, node, parent):
        attributes = {"type": "action", "action": node.parameters["action"]}
        self._write_element(node, 1, attributes, "title")

    def _convert_issue_title_node(self, node, parent):
        attributes = {"type": "question", "predicate": node.parameters["predicate"]}
        self._write_element(node, 1, attributes, "title")

    def _convert_sys_question_node(self, node, parent):
        attributes = {"type": "wh_question", "predicate": node.parameters["predicate"], "speaker": "system"}
        self._write_element(node, 1, attributes, "question")

    def _convert_user_question_node(self, node, parent):
        attributes = {"type": "wh_question", "predicate": node.parameters["predicate"], "speaker": "user"}
        self._write_element(node, 1, attributes, "question")

    def _convert_individual(self, node, parent):
        attributes = {"name": node.parameters["name"]}
        self._write_element(node, 1, attributes)

    def _convert_answer_combination(self, node, parent):
        attributes = {"speaker": "user"}
        self._write_element(node, 1, attributes, "answer")

    def _convert_sys_answer(self, node, parent):
        attributes = self._handle_potential_multi_slot_system_answer(node)
        self._write_element(node, 1, attributes, "answer")

    def _convert_positive_sys_answer(self, node, parent):
        attributes = {"speaker": "system", "predicate": node.parameters["predicate"], "polarity": "positive"}
        self._write_element(node, 1, attributes, "answer")

    def _convert_negative_sys_answer(self, node, parent):
        attributes = {"speaker": "system", "predicate": node.parameters["predicate"], "polarity": "negative"}
        self._write_element(node, 1, attributes, "answer")

    def _write_element(
        self, node, indent=0, attributes={}, override_name=None, itemize_children=False, trailing_newline=True
    ):
        if override_name is not None:
            name = override_name
        else:
            name = node.type
        self._write("%s<%s" % ("  " * indent, name))
        for key, value in list(attributes.items()):
            self._write(' %s="%s"' % (key, value))

        if len(node.children) == 0:
            self._write("/>")
        else:
            self._write(">")
            self._convert_children(node.children, node, itemize=itemize_children, indent=indent + 1)
            if itemize_children:
                self._write("\n%s</%s>" % ("  " * indent, name))
            else:
                self._write("</%s>" % name)

        if trailing_newline:
            self._write("\n")

    def _handle_potential_multi_slot_system_answer(self, node):
        if self._count_answer_slots(node) > 1:
            return {"speaker": "system", "predicate": node.parameters["predicate"]}
        else:
            return {"speaker": "system"}

    def _count_answer_slots(self, node):
        answer_slots = []
        answer_slots = self._collect_answer_slots(node, answer_slots)
        return len(answer_slots)

    def _collect_answer_slots(self, node, answer_slots):
        for child in node.children:
            if child.__class__ == Node:
                if len(child.children) > 0:
                    self._collect_answer_slots(child, answer_slots)
                if child.type == Constants.SLOT:
                    answer_slots.append(child)
        return answer_slots

    def convert_node(self, node):
        self._output = io.StringIO()
        self._convert_node(node)
        return self._output.getvalue()

    def _convert_utterance(self, node, parent):
        self._write('\n')
        self._write_element(node, 2)
        self._write('  ')


if __name__ == "__main__":
    import argparse
    from tala.ddd.loading.ddd_set_loader import DDDSetLoader

    parser = argparse.ArgumentParser()
    parser.add_argument("--ddds", "-d", nargs="+", dest="ddds", required=True)
    parser.add_argument("--languages", nargs="+", choices=languages.SUPPORTED_LANGUAGES, required=True)
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())
    config = BackendConfig().read()
    ddd_set_loader = DDDSetLoader()
    ddds = ddd_set_loader.ddds_as_list(args.ddds, languages=args.languages)
    for ddd in ddds:
        print(("Converting %s to XML" % ddd.name))
        PyToXmlConverter(ddd, args.languages).convert()
