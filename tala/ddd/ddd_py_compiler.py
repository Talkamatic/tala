# flake8: noqa

import copy
import inspect
import re

from tala.model.plan import Plan
from tala.model.predicate import Predicate
from tala.model.action import Action
from tala.nl.gf.grammar_entry_types import Constants, Node
from tala.nl.gf.resource import NP as NpClass
from tala.nl.gf.resource import VP as VpClass
from tala.model.sort import CustomSort, BuiltinSortRepository


class DddPyCompilerException(Exception):
    pass


IDENTITY = lambda x: x


class DddPyCompiler:
    def compile_ontology(self, *args, **kwargs):
        return OntologyCompiler().compile(*args, **kwargs)

    def compile_domain(self, *args, **kwargs):
        return DomainCompiler().compile(*args, **kwargs)

    def compile_grammar(self, *args, **kwargs):
        return GrammarCompiler().compile(*args, **kwargs)

    def decompile_grammar_node(self, ddd, languages, node):
        return GrammarCompiler().decompile_node(node)


class OntologyCompiler:
    def compile(self, description):
        self._ontology_name = description.__name__
        self._compile_sorts(description.sorts)
        return {
            "name": self._ontology_name,
            "sorts": set(self._sorts_dict.values()),
            "predicates": self._compile_predicates(description.predicates),
            "individuals": self._compile_individuals(description.individuals),
            "actions": description.actions,
        }

    def _compile_sorts(self, sorts_description):
        self._sorts_dict = {}
        for name in sorts_description:
            self._sorts_dict[name] = CustomSort(self._ontology_name, name, **sorts_description[name])

    def _compile_predicates(self, predicates_description):
        predicates = set()
        for name, description in list(predicates_description.items()):
            predicate = self._compile_predicate(name, description)
            predicates.add(predicate)
        return predicates

    def _compile_predicate(self, name, description):
        if isinstance(description, str):
            sort_name = description
            return Predicate(self._ontology_name, name, self._get_sort(sort_name))
        else:
            description_copy = copy.copy(description)
            sort_name = description_copy.pop("sort")
            sort = self._get_sort(sort_name)
            if "feature_of" in description_copy:
                feature_of_name = description_copy.pop("feature_of")
            else:
                feature_of_name = None
            return Predicate(self._ontology_name, name, sort=sort, feature_of_name=feature_of_name, **description_copy)

    def _get_sort(self, name):
        if name in self._sorts_dict:
            return self._sorts_dict[name]
        else:
            return BuiltinSortRepository.get_sort(name)

    def _compile_individuals(self, individuals_description):
        individuals = {}
        for individual_name in individuals_description:
            sort_name = individuals_description[individual_name]
            sort = self._get_sort(sort_name)
            individuals[individual_name] = sort
        return individuals


class DomainCompiler:
    def compile(self, ddd_name, description, ontology, parser):
        self._ddd_name = ddd_name
        self._domain_description = description
        self._domain_name = self._domain_description.__name__
        self._ontology = ontology
        self._parser = parser
        self._parse_plans()
        self._parse_default_questions()
        self._parse_parameters()
        self._parse_dependencies()
        return {
            "ddd_name": self._ddd_name,
            "name": self._domain_name,
            "plans": self._plans,
            "default_questions": self._default_questions,
            "parameters": self._parameters,
            "dependencies": self._dependencies
        }

    def get_name(self, description):
        return description.__name__

    def _parse_plans(self):
        if not isinstance(self._domain_description.plans, list):
            raise DddPyCompilerException("plans should be a list")
        self._plans = []
        for plan_description in self._domain_description.plans:
            parsed_plan = self._parse_plan(plan_description)
            goal = parsed_plan["goal"]
            self._plans.append(parsed_plan)

    def _parse_plan(self, plan_description):
        self._plan_description = copy.copy(plan_description)
        plan = self._parse_plan_from_description()
        if len(self._plan_description) > 0:
            raise DddPyCompilerException("unsupported plan descriptor(s): %s" % self._plan_description)
        return plan

    def _parse_plan_from_description(self):
        plan = {}
        plan["goal"] = self._compile_goal(self._select_plan_descriptor("goal"))
        plan["plan"] = self._compile_plan(self._select_plan_descriptor("plan"))
        self._compile_plan_single_attribute(plan, "preferred", self._parse_boolean)
        self._compile_plan_single_attribute(plan, "accommodate_without_feedback", self._parse_boolean)
        self._compile_plan_single_attribute(plan, "dynamic_title")
        self._compile_plan_single_attribute(plan, "postplan", self._compile_plan)
        self._compile_plan_multi_attribute(plan, "superactions", self._compile_superaction)
        self._compile_plan_multi_attribute(plan, "gui_context", self._compile_gui_context)
        self._compile_plan_multi_attribute(plan, "postconds", self._parse)
        self._compile_plan_single_attribute(plan, "io_status")
        self._compile_plan_single_attribute(plan, "restart_on_completion")
        return plan

    def _compile_goal(self, string):
        potential_goal = self._parse(string)
        if potential_goal.is_goal():
            return potential_goal
        else:
            if potential_goal.is_action():
                raise DddPyCompilerException(
                    'in %s: "%s" is not a goal. Perhaps you mean "perform(%s)"?' %
                    (inspect.getsourcefile(self._domain_description), string, string)
                )
            elif potential_goal.is_question():
                raise DddPyCompilerException(
                    'in %s: "%s" is not a goal. Perhaps you mean "resolve(%s)"?' %
                    (inspect.getsourcefile(self._domain_description), string, string)
                )
            else:
                raise DddPyCompilerException(
                    "in %s: Expected goal but found %s (parsed as %s)" %
                    (inspect.getsourcefile(self._domain_description), str(string), str(potential_goal))
                )

    def _compile_plan_single_attribute(self, plan, attribute_name, compilation_method=IDENTITY):
        if attribute_name in self._plan_description:
            attribute = self._select_plan_descriptor(attribute_name)
            plan[attribute_name] = compilation_method(attribute)

    def _compile_plan_multi_attribute(self, plan, attribute_name, compilation_method=IDENTITY):
        if attribute_name in self._plan_description:
            plan[attribute_name] = [
                compilation_method(string) for string in self._select_plan_descriptor(attribute_name)
            ]

    def _compile_superaction(self, string):
        return Action(string, self._ontology.get_name())

    def _compile_gui_context(self, predicate_name):
        return self._ontology.get_predicate(predicate_name)

    def _select_plan_descriptor(self, key):
        value = self._plan_description[key]
        del self._plan_description[key]
        return value

    def _parse_boolean(self, value):
        if value == True:
            return True
        else:
            return self._parse(value)

    def _compile_plan(self, plan_items_as_strings):
        if not isinstance(plan_items_as_strings, list):
            raise DddPyCompilerException("plan not list: %r" % plan_items_as_strings)
        items = [self._parse(string) for string in plan_items_as_strings]
        return Plan(reversed(items))

    def _parse_default_questions(self):
        if hasattr(self._domain_description, "default_questions"):
            self._default_questions = list(map(self._parse, self._domain_description.default_questions))
        else:
            self._default_questions = []

    def _parse_parameters(self):
        if hasattr(self._domain_description, "parameters"):
            self._parameters = {}
            for question_as_string in list(self._domain_description.parameters.keys()):
                question = self._parse(question_as_string)
                parameters_as_string = self._domain_description.parameters[question_as_string]
                parameters = self._parser.parse_parameters(parameters_as_string)
                self._parameters[question] = parameters
        else:
            self._parameters = {}

    def _parse_dependencies(self):
        self._dependencies = {}
        if hasattr(self._domain_description, "dependencies"):
            for dependent_string in self._domain_description.dependencies:
                dependent = self._parse(dependent_string)
                others = set()
                for other_string in self._domain_description.dependencies[dependent_string]:
                    others.add(self._parse(other_string))
                self._dependencies[dependent] = others

    def _parse(self, string):
        return self._parser.parse(string)


class KeyParser:
    def __init__(self, entry_type, pattern, *conditions):
        self._entry_type = entry_type
        self._pattern = pattern
        self._re = re.compile(self._pattern_to_regexp(pattern))
        self._conditions = conditions

    def _pattern_to_regexp(self, pattern):
        return pattern.replace("$", "(\w+)")

    def parse(self, string):
        match = self._re.match(string)
        if match:
            args = match.groups()
            if self._conditions_apply(args):
                return self._tuple_with_entry_type_and_args(args)

    def _tuple_with_entry_type_and_args(self, args):
        return tuple([self._entry_type] + list(args))

    def _conditions_apply(self, args):
        for arg, condition in zip(args, self._conditions):
            if not condition(arg):
                return False
        return True

    def generate(self, args_dict):
        return self._replace_placeholders_in_pattern_with_args(args_dict)

    def _replace_placeholders_in_pattern_with_args(self, args_dict):
        result = self._pattern
        if self._entry_type in GrammarCompiler.PARAMETER_MAP:
            parameter_names = GrammarCompiler.PARAMETER_MAP[self._entry_type]
            for parameter_name in parameter_names:
                value = args_dict[parameter_name]
                result = result.replace("$", value, 1)
        return result


class GrammarCompiler:
    PARAMETER_MAP = {
        Constants.ACTION_TITLE: ("action", ),
        Constants.ACTION: ("name", ),
        Constants.SYS_ANSWER: ("predicate", ),
        Constants.USER_QUESTION: ("predicate", ),
        Constants.INDIVIDUAL: ("name", ),
        Constants.ISSUE_TITLE: ("predicate", ),
        Constants.VALIDITY: ("name", ),
        Constants.SYS_QUESTION: ("predicate", ),
        Constants.REPORT_STARTED: ("action", ),
        Constants.REPORT_FAILED: ("action", "reason"),
        Constants.REPORT_ENDED: ("action", ),
        Constants.PREREPORT: ("action", ),
        Constants.PREDICATE: ("name", ),
        Constants.PRECONFIRM: ("action", ),
        Constants.POSITIVE_SYS_ANSWER: ("predicate", ),
        Constants.NEGATIVE_SYS_ANSWER: ("predicate", )
    }

    def __init__(self):
        self._key_parsers = {}
        self._add_key_parser(Constants.USER_QUESTION, "$_user_question", self._is_predicate)
        self._add_key_parser(Constants.SYS_QUESTION, "$_sys_question", self._is_predicate)
        self._add_key_parser(Constants.PREDICATE, "$", self._is_predicate)
        self._add_key_parser(Constants.ACTION, "$", self._is_action)
        self._add_key_parser(Constants.ANSWER_COMBINATION, "ANSWER")
        self._add_key_parser(Constants.PREREPORT, "$_prereport", self._is_service_action)
        self._add_key_parser(Constants.PRECONFIRM, "$_preconfirm", self._is_service_action)
        self._add_key_parser(Constants.REPORT_STARTED, "$_started", self._is_service_action)
        self._add_key_parser(Constants.REPORT_ENDED, "$_ended", self._is_service_action)
        self._add_key_parser(Constants.REPORT_FAILED, "$_failed_$", self._is_service_action)
        self._add_key_parser(Constants.INDIVIDUAL, "$", self._is_individual)
        self._add_key_parser(Constants.SYS_ANSWER, "$_sys_answer", self._is_predicate)
        self._add_key_parser(Constants.POSITIVE_SYS_ANSWER, "$_positive_sys_answer", self._is_predicate)
        self._add_key_parser(Constants.NEGATIVE_SYS_ANSWER, "$_negative_sys_answer", self._is_predicate)
        self._add_key_parser(Constants.ACTION_TITLE, "$_title", self._is_action)
        self._add_key_parser(Constants.ISSUE_TITLE, "$_title", self._is_predicate)
        self._add_key_parser(Constants.VALIDITY, "$", self._is_validity)
        self._add_key_parser(Constants.GREETING, "greeting")

    def _add_key_parser(self, entry_type, pattern, *conditions):
        self._key_parsers[entry_type] = KeyParser(entry_type, pattern, *conditions)

    def _is_predicate(self, string):
        return self._ontology.has_predicate(string)

    def _is_action(self, string):
        return self._ontology.is_action(string)

    def _is_individual(self, string):
        return string in self._ontology.get_individuals()

    def _is_validity(self, string):
        if self._service_interface:
            for validator in self._service_interface.validators:
                if validator.name == string:
                    return True

    def _is_service_action(self, string):
        if self._service_interface:
            return self._service_interface.has_action(string)

    def compile(self, string, ontology, service_interface):
        self._ontology = ontology
        self._service_interface = service_interface
        module_dict = dict()
        exec (string, module_dict)
        return self._compile_entries_from_dict(module_dict)

    def _compile_entries_from_dict(self, module_dict):
        grammar_node = Node(Constants.GRAMMAR, {})
        for name, entry in list(module_dict.items()):
            if not self._is_builtin_member(name) and not self._is_resource_class(name):
                self._compile_entry(grammar_node, name, entry)
        return grammar_node

    def _is_builtin_member(self, name):
        return name.startswith("__")

    def _is_resource_class(self, name):
        return name in ["NP", "VP", "MASCULINE", "FEMININE", "SINGULAR", "PLURAL"]

    def _compile_entry(self, parent_node, key_string, form_object):
        key = self._parse_key(key_string)
        if key:
            node_type = key[0]
            form_node = self._compile_form(form_object)
            parameters = self._get_parameters(key, form_object)
            entry_node = Node(node_type, parameters, [form_node])
            parent_node.add_child(entry_node)
        else:
            self._warn("failed to parse grammar entry key %r" % key_string)

    def _get_parameters(self, key, form_object):
        parameters = self._get_parameters_via_map(key)
        node_specific_parameters = self._get_node_specific_parameters(key, form_object)
        if node_specific_parameters is not None:
            parameters.update(node_specific_parameters)
        return parameters

    def _get_parameters_via_map(self, key):
        node_type = key[0]
        parameters = {}
        if len(key) > 1:
            parameter_names = self.PARAMETER_MAP[node_type]
            for name, value in zip(parameter_names, key[1:]):
                parameters[name] = value
        return parameters

    def _get_node_specific_parameters(self, key, form_object):
        node_type = key[0]
        if node_type == Constants.ACTION:
            if isinstance(form_object, list):
                return self._get_action_specific_parameters_from_form_objects(form_object)
            elif isinstance(form_object, NpClass):
                return self._get_action_specific_parameters_from_form_object(form_object)

    def _get_action_specific_parameters_from_form_objects(self, form_objects):
        for form_object in form_objects:
            parameters = self._get_action_specific_parameters_from_form_object(form_object)
            if parameters is not None:
                return parameters

    def _get_action_specific_parameters_from_form_object(self, form_object):
        if isinstance(form_object, NpClass):
            result = {}
            if form_object.gender is not None:
                result["gender"] = form_object.gender
            if form_object.number is not None:
                result["number"] = form_object.number
            return result

    def _parse_key(self, string):
        for parser in list(self._key_parsers.values()):
            key = parser.parse(string)
            if key:
                return key

    def _compile_form(self, form_object):
        if isinstance(form_object, list):
            return self._compile_one_of(form_object)
        elif self._is_of_resource_class(form_object):
            return self._resource_class_node(form_object)
        elif isinstance(form_object, str):
            return self._compile_form_string(form_object)
        else:
            raise DddPyCompilerException("failed to compile grammar form %r" % form_object)

    def _compile_one_of(self, obj):
        result = Node(Constants.ONE_OF, {})
        for child_object in obj:
            compiled_child = self._compile_form(child_object)
            if compiled_child.type == Constants.ITEM:
                result.add_child(compiled_child)
            else:
                result.add_child(Node(Constants.ITEM, {}, [compiled_child]))
        return result

    def _is_of_resource_class(self, obj):
        return self._is_resource_class(obj.__class__.__name__)

    def _resource_class_node(self, resource_object):
        if isinstance(resource_object, NpClass):
            return self._create_np_node(resource_object)
        if isinstance(resource_object, VpClass):
            return self._create_vp_node(resource_object)

    def _create_np_node(self, resource_np):
        children = []
        children.append(Node(Constants.INDEFINITE, {}, [resource_np.indefinite]))
        if resource_np.definite is not None:
            children.append(Node(Constants.DEFINITE, {}, [resource_np.definite]))
        np_node = Node(Constants.NP, {}, children)
        return np_node

    def _create_vp_node(self, resource_vp):
        infinitive_node = Node(Constants.INFINITIVE, {}, [resource_vp.infinitive])
        imperative_node = Node(Constants.IMPERATIVE, {}, [resource_vp.imperative])
        ing_form_node = Node(Constants.ING_FORM, {}, [resource_vp.ing_form])
        object_node = Node(Constants.OBJECT, {}, [resource_vp.object])
        vp_node = Node(Constants.VP, {}, [infinitive_node, imperative_node, ing_form_node, object_node])
        return vp_node

    def _compile_form_string(self, string):
        parts = re.split("(<answer:[^<>]+>|<individual>)", string)
        child_nodes = [self._compile_form_part(part) for part in parts if part != ""]
        return Node(Constants.ITEM, {}, child_nodes)

    def _compile_form_part(self, string):
        if string == "<individual>":
            return Node(Constants.SLOT)
        else:
            match = re.match("^<answer:([^<>]+)>$", string)
            if match:
                predicate_or_sort = match.group(1)
                if self._ontology.has_predicate(predicate_or_sort):
                    return Node(Constants.SLOT, {"predicate": predicate_or_sort})
                elif self._ontology.has_sort(predicate_or_sort):
                    return Node(Constants.SLOT, {"sort": predicate_or_sort})
                else:
                    raise DddPyCompilerException("expected predicate or sort but found %r" % predicate_or_sort)
            else:
                return string

    def decompile_node(self, node):
        key_string = self._decompile_key(node)
        value_string = self._decompile_node_value(node)
        return '%s = %s\n' % (key_string, value_string)

    def _decompile_key(self, key):
        return self._key_parsers[key.type].generate(key.parameters)

    def _decompile_node_value(self, node):
        if isinstance(node, str):
            return node
        elif node.type == Constants.SLOT:
            return "<answer:%s>" % node.parameters["predicate"]
        elif node.type == Constants.ONE_OF:
            result = "[\n"
            for child in node.children:
                result += "  %s,\n" % self._decompile_node_value(child)
            result += "]"
            return result
        else:
            children_string = "".join([self._decompile_node_value(child) for child in node.children])
            if self._children_is_a_one_of(node.children):
                return children_string
            else:
                return '"%s"' % children_string

    def _children_is_a_one_of(self, children):
        return len(children) == 1 and isinstance(children[0], Node) and children[0].type == Constants.ONE_OF

    def _warn(self, warning):
        print(("warning: %s" % warning))
