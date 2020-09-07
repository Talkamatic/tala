# flake8: noqa

import codecs
import contextlib
import itertools
import os
from io import StringIO
import sys

import tala.nl.gf.resource
import tala.ddd.schemas
from tala.nl import languages
from tala.ddd.ddd_py_compiler import DddPyCompiler
from tala.ddd.ddd_xml_compiler import DddXmlCompiler
from tala.ddd.services.constants import UNDEFINED_SERVICE_ACTION_FAILURE
from tala.model.goal import ResolveGoal
from tala.nl.gf import utils
from tala.nl.gf.grammar_entry_types import Constants, Node
from tala.nl.gf.naming import abstract_gf_filename, natural_language_gf_filename, semantic_gf_filename, \
    probabilities_filename

UNKNOWN_CATEGORY = "Unknown"


class MissingEntry(Exception):
    pass


class UnexpectedParameter(Exception):
    pass


class InvalidSortOfBackgroundPredicateException(Exception):
    pass


class LanguageNotSupportedByPythonFormatException(Exception):
    pass


class LowerCaseGfFileWriter(object):
    def __init__(self, file_):
        super(LowerCaseGfFileWriter, self).__init__()
        self.file_ = file_

    @staticmethod
    @contextlib.contextmanager
    def open(*args, **kwargs):
        with codecs.open(*args, **kwargs) as file_:
            yield LowerCaseGfFileWriter(file_)

    def write(self, gf_string):
        lowered_gf_string = self._lower_gf_string_but_insert_capit_and_bind(gf_string)
        self.file_.write(lowered_gf_string)

    def _lower_gf_string_but_insert_capit_and_bind(self, string):
        language_tokens = utils.language_tokens(string)
        lowered_gf_string = string
        for token in language_tokens:
            lowered_token = utils.lower_gf_string_but_insert_capit_and_bind(token)
            lowered_gf_string = lowered_gf_string.replace('"%s"' % token, '%s' % lowered_token)
        return lowered_gf_string

    def close(self):
        self.file_.close()


class AutoGenerator(object):
    CATEGORY_FOR_SMALL_INTEGERS = "Integer"

    def __init__(self, ddd, ignore_warnings=False, cwd=None):
        self._ddd = ddd
        self._ddd_name = self._ddd.name
        self._ignore_warnings = ignore_warnings
        self._rule_count = 1
        self._ontology = self._ddd.ontology
        self._domain = self._ddd.domain
        self._categories = self._get_categories()

        self._abstract_gf_content = StringIO()
        self._semantic_gf_content = StringIO()
        self._natural_language_gf_content = StringIO()
        self._probabilities_file_content = StringIO()

    @property
    def _schema_absolute_path(self):
        absolute_path = os.path.abspath(os.path.dirname(tala.ddd.schemas.__file__))
        schema_absolute_path = "%s/grammar.xsd" % absolute_path
        return schema_absolute_path

    def generate(self, language_code):
        self._grammar = self._load_and_compile_grammar_entries(language_code)
        self._add_header_in_auto_generated_gf_files(language_code)
        self._add_content_in_auto_generated_gf_files()
        self._add_footer_in_auto_generated_gf_files()

    def write_to_file(self, language_code):
        self._write_to_gf_files(language_code)

    def clear(self):
        self._clear_io_buffers()

    def _get_categories(self):
        categories = {}
        categories.update(self._get_categories_from_sorts())
        categories.update(self._get_categories_from_predicates())
        return categories

    def _is_unknown_category_needed(self):
        return self._ontology.has_sort("string")

    def _get_categories_from_sorts(self):
        categories = {}
        for sort in self._ontology.get_sorts():
            category = "Sort_%s" % sort
            categories[sort] = category

        return categories

    def _get_categories_from_predicates(self):
        categories = {}

        for predicate in list(self._ontology.get_predicates().values()):
            category = "Predicate_%s" % predicate
            categories[predicate.get_name()] = category

        return categories

    def _clear_io_buffers(self):
        self._abstract_gf_content = StringIO()
        self._semantic_gf_content = StringIO()
        self._natural_language_gf_content = StringIO()

    def _name_of_natural_language_gf_file(self, language_code):
        return "build/%s/%s" % (language_code, natural_language_gf_filename(self._ddd_name, language_code))

    def _name_of_probabilities_file(self, language_code):
        return "build/%s/%s" % (language_code, probabilities_filename(self._ddd_name))

    def _add_header_in_auto_generated_gf_files(self, language_code):
        self._natural_language_gf_content.write("--# -coding=utf-8\n")
        self._abstract_gf_content.write("abstract %s = TDM, Integers ** {\n\n" "cat\n\n" % self._ddd_name)
        for category in list(self._categories.values()):
            self._abstract_gf_content.write("%s;\n" % category)
        if self._is_unknown_category_needed():
            self._abstract_gf_content.write("%s;\n" % UNKNOWN_CATEGORY)
        self._abstract_gf_content.write("\n" "fun\n\n")

        self._semantic_gf_content.write(
            "concrete %s_sem of %s = TDM_sem, Integers_sem ** open Utils_sem in {\n\n" %
            (self._ddd_name, self._ddd_name)
        )
        self._semantic_gf_content.write("lincat\n\n")
        for category in list(self._categories.values()):
            self._semantic_gf_content.write("%s = SS;\n" % category)
        if self._is_unknown_category_needed():
            self._semantic_gf_content.write("%s = SS;\n" % UNKNOWN_CATEGORY)
        self._semantic_gf_content.write("\nlin\n\n")

        self._natural_language_gf_content.write(
            "concrete %s_%s of %s = TDM_%s, Integers_%s ** open Utils_%s, Prelude in {\n\n" %
            (self._ddd_name, language_code, self._ddd_name, language_code, language_code, language_code)
        )
        self._natural_language_gf_content.write("lin\n\n")

    def _add_footer_in_auto_generated_gf_files(self):
        self._abstract_gf_content.write("}\n")
        self._semantic_gf_content.write("}\n")
        self._natural_language_gf_content.write("}\n")

    def _write_to_gf_files(self, language_code):
        def write_abstract_file():
            with codecs.open(self._name_of_abstract_gf_file(language_code), "w", encoding="utf-8") as abstract_file:
                self._abstract_gf_content.seek(0)
                for line in self._abstract_gf_content:
                    abstract_file.write(line)

        def write_semantic_file():
            with codecs.open(self._name_of_semantic_gf_file(language_code), "w", encoding="utf-8") as semantic_file:
                self._semantic_gf_content.seek(0)
                for line in self._semantic_gf_content:
                    semantic_file.write(line)

        def write_natural_language_file():
            with LowerCaseGfFileWriter.open(
                self._name_of_natural_language_gf_file(language_code), "w", encoding="utf-8"
            ) as natural_language_file:
                self._natural_language_gf_content.seek(0)
                for line in self._natural_language_gf_content:
                    natural_language_file.write(line)

        def write_probabilities_file():
            with open(self._name_of_probabilities_file(language_code), "w") as probabilities_file:
                self._probabilities_file_content.seek(0)
                for line in self._probabilities_file_content:
                    probabilities_file.write(line)

        write_abstract_file()
        self._abstract_gf_content.close()

        write_semantic_file()
        self._semantic_gf_content.close()

        write_natural_language_file()
        self._natural_language_gf_content.close()

        write_probabilities_file()
        self._probabilities_file_content.close()

    def _name_of_abstract_gf_file(self, language_code):
        return "build/%s/%s" % (language_code, abstract_gf_filename(self._ddd_name))

    def _name_of_semantic_gf_file(self, language_code):
        return "build/%s/%s" % (language_code, semantic_gf_filename(self._ddd_name))

    def _add_content_in_auto_generated_gf_files(self):
        self._add_greeting_content()
        self._add_content_based_on_ontology()
        if self._ddd.service_interface:
            self._add_content_based_on_service_interface()

    def _add_greeting_content(self):
        form = self._get_form(Node(Constants.GREETING), optional=True)
        if form:
            self._generate_greeting_content(form)

    def _generate_greeting_content(self, form):
        self._natural_language_gf_content.write('sysGreet = ss "%s";' % self._form_to_gf_string(form))

    def _add_content_based_on_ontology(self):
        self._generate_actions()
        self._generate_features()
        self._generate_placeholders_for_dynamic_custom_sorts()
        self._generate_individuals()
        self._generate_potential_user_answer_sequences()
        for predicate in list(self._ontology.get_predicates().values()):
            predicate_name = predicate.get_name()
            self._generate_predicate_content(predicate_name)
            self._generate_potential_system_question(predicate_name)
            self._generate_potential_user_question(predicate)
            self._generate_system_answer_content(predicate)
            self._generate_user_answer_content(predicate)
        if self._is_unknown_category_needed():
            self._generate_unknown_type()

    def _generate_unknown_type(self):
        self._add_function_for_unknown_category()
        self._add_semantic_linearization_for_unknown_category()
        self._add_nl_linearization_for_unknown_category()

    def _generate_actions(self):
        for action in self._ontology.get_actions():
            self._generate_action(action)

    def _generate_action(self, action):
        try:
            self._generate_action_content(action)
        except MissingEntry:
            self._missing_entry(self._missing_action, action)

    def _get_form(self, key, optional=False):
        node = self._grammar.get_child(key.type, key.parameters)
        if node is not None:
            return node.get_single_child()
        elif optional:
            return None
        else:
            raise MissingEntry("missing entry %s" % str(key))

    def _get_form_as_options(self, key, optional=False):
        node = self._get_form(key, optional)
        if node is None:
            return []
        elif node.type == Constants.ONE_OF:
            return node.children
        else:
            return [node]

    def _entry_exists(self, key):
        node = self._grammar.get_child(key.type, key.parameters)
        return node is not None

    def _example_phrase_from_semantic_value(self, string):
        return string.replace("_", " ")

    def _generate_individuals(self):
        for (individual, sort) in self._ontology.get_individuals().items():
            self._generate_individual(individual, sort)

    def _generate_placeholders_for_dynamic_custom_sorts(self):
        for sort in list(self._ontology.get_sorts().values()):
            if sort.is_dynamic():
                for index in range(0, utils.MAX_NUM_PLACEHOLDERS):
                    self._generate_placeholder_for_dynamic_custom_sort(sort, index)

    def _generate_placeholder_for_dynamic_custom_sort(self, sort, index):
        placeholder_name = utils.name_of_user_answer_placeholder_of_sort(sort.get_name(), index)
        nl_placeholder = utils.nl_user_answer_placeholder_of_sort(sort.get_name(), index)
        sem_placeholder = utils.semantic_user_answer_placeholder_of_sort(sort.get_name(), index)

        self._abstract_gf_content.write("%s : %s;\n" % (placeholder_name, self._categories[sort.get_name()]))
        self._semantic_gf_content.write('%s = pp "%s";\n' % (placeholder_name, sem_placeholder))
        self._natural_language_gf_content.write('%s = ss "%s";\n' % (placeholder_name, nl_placeholder))

    def _generate_potential_user_answer_sequences(self):
        forms = self._get_form_as_options(Node(Constants.ANSWER_COMBINATION), optional=True)
        for form in forms:
            self._generate_user_answer_sequence(form)

    def _generate_user_answer_sequence(self, form):
        def generate_semantic_value(semantic_value_arguments):
            return "moveseq %s" % " ".join([
                '(move "answer" %s)' % semantic_value_argument for semantic_value_argument in semantic_value_arguments
            ])

        function_name = self._generate_new_function_name("user_answer_sequence")
        self._generate_function_with_answers(function_name, form, "UserAnswerSequence", generate_semantic_value)

    def _generate_features(self):
        for predicate in list(self._ontology.get_predicates().values()):
            if predicate.get_feature_of_name():
                self._generate_feature(predicate)

    def _generate_feature(self, feature):
        super_predicate_name = feature.get_feature_of_name()
        function_name = "%s_%s" % (feature.get_name(), super_predicate_name)
        self._abstract_gf_content.write(
            "%s : %s -> %s;\n" %
            (function_name, self._categories[feature.get_name()], self._categories[super_predicate_name])
        )
        self._semantic_gf_content.write("%s individual = individual;\n" % (function_name))
        self._natural_language_gf_content.write("%s individual = individual;\n" % (function_name))

    def _generate_individual(self, individual, sort):
        try:
            key = Node(Constants.INDIVIDUAL, {"name": individual})
            forms = self._get_form_as_options(key)
            self._abstract_gf_content.write("%s : %s;\n" % (individual, self._categories[sort.get_name()]))
            self._semantic_gf_content.write('%s = pp "%s";\n' % (individual, individual))
            self._natural_language_gf_content.write(
                "%s = ss (%s);\n" % (individual, self._speaker_independent_linearization(forms))
            )
        except MissingEntry:
            self._missing_entry(self._missing_individual, individual)

    def _add_function_for_unknown_category(self):
        self._abstract_gf_content.write("mkUnknown : String -> Unknown;\n")
        self._abstract_gf_content.write("unknown_string : Unknown -> Sort_string;\n")

    def _add_semantic_linearization_for_unknown_category(self):
        self._semantic_gf_content.write("""unknown_string unknown = ss ("\\"" ++ unknown.s ++ "\\"");\n""")
        self._semantic_gf_content.write("""mkUnknown string = ss string.s;\n""")

    def _add_nl_linearization_for_unknown_category(self):
        self._natural_language_gf_content.write("""unknown_string unknown = unknown;\n""")
        self._natural_language_gf_content.write("""mkUnknown string = string;\n""")

    def _add_content_based_on_service_interface(self):
        for action_interface in self._ddd.service_interface.actions:
            self._generate_ended_content(action_interface)
            if self._service_action_has_assertive_preconfirm(action_interface.name):
                self._generate_prereport_content(action_interface)
            elif self._service_action_has_interrogative_preconfirm(action_interface.name):
                self._generate_preconfirm_content(action_interface)
            self._generate_started_content(action_interface)
            self._generate_failed_content(action_interface)
        for validator_interface in self._ddd.service_interface.validators:
            self._generate_validity_content(validator_interface)

    def _service_action_has_assertive_preconfirm(self, action_name):
        for item in self._invoke_service_action_items_for_action(action_name):
            if item.has_assertive_preconfirmation():
                return True

    def _service_action_has_interrogative_preconfirm(self, action_name):
        for item in self._invoke_service_action_items_for_action(action_name):
            if item.has_interrogative_preconfirmation():
                return True

    def _service_action_has_postconfirm(self, action_name):
        for item in self._invoke_service_action_items_for_action(action_name):
            if item.has_postconfirmation():
                return True

    def _invoke_service_action_items_for_action(self, action_name):
        for goal in self._domain.get_all_goals():
            plan = self._domain.get_plan(goal)
            for item in plan:
                if item.is_invoke_service_action_plan_item() and item.get_service_action() == action_name:
                    yield item

    def _generate_validity_content(self, validator_interface):
        key = Node(Constants.VALIDITY, {"name": validator_interface.name})
        try:
            forms = self._get_form_as_options(key)
            self._generate_validity_content_for_grammar_forms(
                validator_interface, forms, validator_interface.parameters
            )
        except MissingEntry:
            self._missing_entry(self._missing_validity, validator_interface, key)

    def _generate_validity_content_for_grammar_forms(self, validator_interface, forms, parameters):
        for r in range(1, len(parameters) + 1):
            for combination in itertools.combinations(parameters, r):
                form = self._pick_validity_form(forms, combination, validator_interface)
                if form:
                    self._generate_validity_content_for_combination(validator_interface, form, combination)

    def _generate_validity_content_for_combination(self, validator_interface, form, combination):
        validity_name = validator_interface.name
        function_name = self._generate_new_function_name(validity_name)
        parameter_names = [parameter.name for parameter in combination]

        self._write_gf(
            function_name,
            category="SysICM",
            arguments=[Argument(parameter.name, "SysAnswer") for parameter in combination],
            semantic='rejectICM (set (list %s)) "%s"' % (" ".join(parameter_names), validity_name),
            natural_language='ss (%s)' % self._parameterized_sys_form(form)
        )

    def _pick_validity_form(self, forms, combination, validator_interface):
        for form in forms:
            if not self._form_contains_parameter_not_in_combination(form, combination, validator_interface):
                return form

    def _form_contains_parameter_not_in_combination(self, form, combination, service_interface):
        parameter_names_in_form = self._parameters_in_form(form, service_interface)
        parameter_names_in_combination = [parameter.name for parameter in combination]
        return any([
            parameter for parameter in parameter_names_in_form if parameter not in parameter_names_in_combination
        ])

    def _parameters_in_form(self, form, service_interface):
        parameter_names_in_device = [parameter.name for parameter in service_interface.parameters]
        result = []
        for part in form.children:
            if self._is_propositional_answer_slot(part):
                parameter_name = part.parameters["predicate"]
                if parameter_name in parameter_names_in_device:
                    result.append(parameter_name)
                else:
                    raise UnexpectedParameter(
                        "unexpected parameter name %s in form %s (device declares %s)" %
                        (parameter_name, form, parameter_names_in_device)
                    )
        return result

    def _generate_ended_content(self, action_interface):
        key = Node(Constants.REPORT_ENDED, {"action": action_interface.name})
        try:
            self._generate_parameterized_service_action_entry("SysReportEnded", "report_ended", key, action_interface)
        except MissingEntry:
            if self._service_action_has_postconfirm(action_interface.name):
                self._missing_entry(self._missing_ended, key, action_interface)

    def _generate_preconfirm_content(self, action_interface):
        key = Node(Constants.PRECONFIRM, {"action": action_interface.name})
        try:
            self._generate_parameterized_service_action_entry("SysYNQ", "ask_preconfirm", key, action_interface)
        except MissingEntry:
            self._missing_entry(self._missing_preconfirm, key, action_interface)

    def _generate_prereport_content(self, action_interface):
        key = Node(Constants.PREREPORT, {"action": action_interface.name})
        try:
            self._generate_parameterized_service_action_entry("SysPreReport", "prereport", key, action_interface)
        except MissingEntry:
            self._missing_entry(self._missing_prereport, key, action_interface)

    def _generate_started_content(self, action_interface):
        key = Node(Constants.REPORT_STARTED, {"action": action_interface.name})
        try:
            self._generate_parameterized_service_action_entry(
                "SysReportStarted", "report_started", key, action_interface
            )
        except MissingEntry:
            pass

    def _generate_failed_content(self, action_interface):
        self._generate_failed_content_for_unknown_failure_reason(action_interface)
        for failure_reason in action_interface.failure_reasons:
            self._generate_failed_content_for_reason(action_interface, failure_reason)

    def _generate_failed_content_for_unknown_failure_reason(self, action_interface):
        for probability, combination in self._enumerate_with_decreasing_probabilities(
            self._service_action_parameter_combinations(action_interface)
        ):
            natural_language_gf = 'undefined_service_action_failure'
            self._generate_parameterized_service_action_content(
                "SysReportFailed", "report_failed", action_interface.name, UNDEFINED_SERVICE_ACTION_FAILURE,
                natural_language_gf, combination, probability
            )

    def _enumerate_with_decreasing_probabilities(self, iterable):
        def rescale_probability_so_that_sum_of_all_explicit_probabilities_is_less_then_1(
            unit_scaled_probability, large_constant=1000000
        ):
            return unit_scaled_probability / large_constant

        items = list(iterable)
        num_items = len(items)
        for index, item in enumerate(items):
            unit_scaled_probability = 1 - float(index) / num_items
            safely_rescaled_probability = rescale_probability_so_that_sum_of_all_explicit_probabilities_is_less_then_1(
                unit_scaled_probability
            )
            yield safely_rescaled_probability, item

    def _generate_failed_content_for_reason(self, action_interface, failure_reason):
        key = Node(Constants.REPORT_FAILED, {"action": action_interface.name, "reason": failure_reason.name})
        try:
            self._generate_parameterized_service_action_entry(
                "SysReportFailed", "report_failed", key, action_interface, failure_reason.name
            )
        except MissingEntry:
            pass

    def _generate_parameterized_service_action_entry(self, gf_category, sem_util, key, action_interface, reason=None):
        forms_for_all_combinations = self._get_form_as_options(key)
        for combination in self._service_action_parameter_combinations(action_interface):
            forms_for_combination = self._pick_service_action_forms(
                forms_for_all_combinations, combination, action_interface
            )
            for probability, form in self._enumerate_with_decreasing_probabilities(forms_for_combination):
                if len(form.children) > 0:
                    natural_language_gf = 'ss (%s)' % self._parameterized_sys_form(form)
                    self._generate_parameterized_service_action_content(
                        gf_category, sem_util, action_interface.name, reason, natural_language_gf, combination,
                        probability
                    )

    def _service_action_parameter_combinations(self, action_interface):
        parameters = action_interface.parameters
        for r in range(0, len(parameters) + 1):
            for combination in itertools.combinations(parameters, r):
                if not self._combination_lacks_mandatory_parameter(combination, parameters):
                    yield combination

    def _combination_lacks_mandatory_parameter(self, combination, parameters):
        for parameter in parameters:
            if not parameter.is_optional and parameter not in combination:
                return True

    def _pick_service_action_forms(self, forms, combination, action_interface):
        relevant_forms = self._relevant_service_action_forms(forms, combination, action_interface)
        if len(relevant_forms) == 0:
            return []
        else:
            return self._select_most_relevant_service_action_forms(relevant_forms, combination, action_interface)

    def _relevant_service_action_forms(self, forms, combination, action_interface):
        return [form for form in forms if self._combination_matches_form(combination, form, action_interface)]

    def _combination_matches_form(self, combination, form, action_interface):
        parameter_names_in_form = self._parameters_in_form(form, action_interface)
        parameter_names_in_combination = [parameter.name for parameter in combination]
        for parameter_name in parameter_names_in_form:
            if parameter_name not in parameter_names_in_combination:
                return False
        return True

    def _select_most_relevant_service_action_forms(self, forms, combination, action_interface):
        max_num_referenced_parameters = max([
            self._num_referenced_parameters(form, combination, action_interface) for form in forms
        ])
        for form in forms:
            if self._num_referenced_parameters(form, combination, action_interface) == max_num_referenced_parameters:
                yield form

    def _num_referenced_parameters(self, form, combination, action_interface):
        parameter_names_in_form = self._parameters_in_form(form, action_interface)
        return len([parameter for parameter in combination if parameter.name in parameter_names_in_form])

    def _generate_parameterized_service_action_content(
        self, gf_category, sem_util, action_name, reason, natural_language_gf, combination, probability
    ):

        function_name_prefix = "%s_%s" % (sem_util, action_name)
        if reason is not None:
            function_name_prefix += "_%s" % reason
        function_name = self._generate_new_function_name(function_name_prefix)
        parameter_names = [parameter.name for parameter in combination]

        self._abstract_gf_content.write("%s :" % function_name)
        for i in range(len(combination)):
            self._abstract_gf_content.write(" SysAnswer ->")
        self._abstract_gf_content.write(" %s;\n" % gf_category)

        self._semantic_gf_content.write(function_name)
        for parameter_name in parameter_names:
            self._semantic_gf_content.write(" %s" % parameter_name)
        self._semantic_gf_content.write(' = %s "%s" %s' % (sem_util, action_name, self._gf_list(parameter_names)))
        if reason:
            self._semantic_gf_content.write(' "%s"' % reason)
        self._semantic_gf_content.write(";\n")

        self._natural_language_gf_content.write(function_name)
        for parameter_name in parameter_names:
            self._natural_language_gf_content.write(" %s" % parameter_name)
        self._natural_language_gf_content.write(' = %s;\n' % natural_language_gf)

        self._probabilities_file_content.write('%s %.8f\n' % (function_name, probability))

    def _gf_list(self, strings):
        if len(strings) == 0:
            return "(empty_list)"
        else:
            return "(list %s)" % " ".join(strings)

    def _join_with_leading_whitespace(self, strings):
        result = ''
        for string in strings:
            result += ' '
            result += string
        return result

    def _parameterized_sys_form(self, form):
        separators = [" ", "."]
        result = ""
        previous_form = None
        for form in form.children:
            gf_string = self._sys_form_to_gf(form)
            if gf_string:
                if result:
                    result += " ++ "
                if previous_form and self._is_propositional_answer_slot(previous_form) and form[0] not in separators:
                    result += " BIND ++ "
                result += gf_string
                previous_form = form
        return result

    def _sys_form_to_gf(self, form):
        if self._is_propositional_answer_slot(form):
            return "%s.alt" % form.parameters["predicate"]
        else:
            return '"%s"' % self._form_to_gf_string(form)

    def _generate_predicate_content(self, predicate_name):
        self._abstract_gf_content.write("%s : Predicate;\n" % predicate_name)
        self._semantic_gf_content.write("%s = pp \"%s\";\n" % (predicate_name, predicate_name))
        try:
            forms = self._get_form_as_options(Node(Constants.PREDICATE, {"name": predicate_name}))
            self._generate_speaker_independent_predicate_content(predicate_name, forms)
            self._generate_system_ask_whq_with_background(predicate_name, forms)
            self._generate_resolve_ynq(predicate_name, forms)
        except MissingEntry:
            if self._is_goal_issue(predicate_name):
                self._missing_entry(self._missing_goal_issue, predicate_name)

    def _generate_speaker_independent_predicate_content(self, predicate, forms):
        forms_without_answers = []
        for form in forms:
            if not self._form_contains_answer_slots(form):
                forms_without_answers.append(form)

        if len(forms_without_answers) > 0:
            self._natural_language_gf_content.write(
                '%s = ss (%s);\n' % (predicate, self._speaker_independent_linearization(forms_without_answers))
            )

    def _generate_system_ask_whq_with_background(self, predicate, forms):
        for form in forms:
            if self._form_contains_answer_slots(form):
                background_predicates = []
                nl_parts = []
                for form_part in form.children:
                    if self._is_propositional_answer_slot(form_part):
                        background_predicate = form_part.parameters["predicate"]
                        background_predicates.append(background_predicate)
                        nl_parts.append("%s.s" % background_predicate)
                    elif form_part:
                        nl_parts.append('"%s"' % self._form_to_gf_string(form_part))

                function_name = self._generate_new_function_name("%s_ask_whq_with_background" % predicate)

                natural_language_content = '%s ++ "?"' % (" ++ ".join(nl_parts))
                self._write_gf(
                    function_name,
                    category="System",
                    arguments=[
                        Argument(background_predicate, "SysAnswer") for background_predicate in background_predicates
                    ],
                    semantic='pp "Move" (move "ask" (eta_expand %s) (list %s))' %
                    (predicate, " ".join(background_predicates)),
                    natural_language=self._capitalize(natural_language_content)
                )

    def _capitalize(self, string):
        return "ss (CAPIT ++ %s)" % string

    def _ss(self, string):
        return "ss (%s)" % string

    def _generate_resolve_ynq(self, predicate, forms):
        for form in forms:
            function_name = self._generate_new_function_name("%s_resolve_ynq" % predicate)
            if self._form_contains_answer_slots(form):
                background_predicates = []
                nl_parts = []
                for form_part in form.children:
                    if self._is_propositional_answer_slot(form_part):
                        background_predicate = form_part.parameters["predicate"]
                        background_predicates.append(background_predicate)
                        nl_parts.append("%s.s" % background_predicate)
                    elif form_part:
                        nl_parts.append('"%s"' % self._form_to_gf_string(form_part))

                self._write_ynq_with_answers_to_abstract_gf(function_name, background_predicates)
                self._write_ynq_with_answers_to_semantic_gf(function_name, background_predicates, predicate)
                self._write_ynq_with_answers_to_natural_language_gf(function_name, background_predicates, nl_parts)

            else:
                self._write_ynq_to_abstract_gf(function_name)
                self._write_ynq_to_semantic_gf(function_name, predicate)
                self._write_ynq_to_natural_language_gf(function_name, predicate)

    def _write_ynq_to_abstract_gf(self, function_name):
        self._abstract_gf_content.write('%s : SysResolveGoal;\n' % function_name)

    def _write_ynq_to_semantic_gf(self, function_name, predicate):
        self._semantic_gf_content.write('%s = resolve_ynq %s;\n' % (function_name, predicate))

    def _write_ynq_to_natural_language_gf(self, function_name, predicate):
        self._natural_language_gf_content.write('%s = resolve_ynq %s;\n' % (function_name, predicate))

    def _write_ynq_with_answers_to_abstract_gf(self, function_name, background_predicates):
        SysAnswer_string = "SysAnswer -> " * len(background_predicates)
        string_to_write = "%s : %sSysResolveGoal;\n" % (function_name, SysAnswer_string)
        self._abstract_gf_content.write(string_to_write)

    def _write_ynq_with_answers_to_semantic_gf(self, function_name, background_predicates, predicate):
        background_predicates_string = " ".join(background_predicates)
        string_to_write = '%s %s = resolve_ynq_with_background %s (list %s);\n' % (
            function_name, background_predicates_string, predicate, background_predicates_string
        )
        self._semantic_gf_content.write(string_to_write)

    def _write_ynq_with_answers_to_natural_language_gf(self, function_name, background_predicates, nl_parts):

        background_predicates_string = " ".join(background_predicates)
        nl_parts_string = " ++ ".join(nl_parts)
        string_to_write = '%s %s = resolve_ynq_with_background (ss (%s));\n' % (
            function_name, background_predicates_string, " ++ ".join(nl_parts)
        )

        self._natural_language_gf_content.write(string_to_write)

    def _generate_potential_system_question(self, predicate):
        key = Node(Constants.SYS_QUESTION, {"predicate": predicate})
        try:
            form = self._get_form(key)
            self._generate_system_question(predicate, form)
        except MissingEntry:
            if self._can_be_asked_by_system(predicate) and not self._entry_exists(
                Node(Constants.PREDICATE, {"name": predicate})
            ):
                self._missing_entry(self._missing_system_question, key, predicate)

    def _generate_potential_user_question(self, predicate):
        key = Node(Constants.USER_QUESTION, {"predicate": predicate.get_name()})
        try:
            forms = self._get_form_as_options(key)
            self._generate_user_question(predicate, forms)
        except MissingEntry:
            if self._is_goal_issue(predicate):
                self._missing_entry(self._missing_user_question, predicate)

    def _generate_system_question(self, predicate, form):
        self._natural_language_gf_content.write('%s = ss "%s";\n' % (predicate, self._form_to_gf_string(form)))

    def _speaker_independent_linearization(self, forms):

        return "(%s)" % "|".join(['"%s"' % self._form_to_gf_string(form) for form in forms])

    def _generate_system_answer_content(self, predicate):
        sort = predicate.getSort()
        if sort.is_boolean_sort():
            self._generate_nullary_system_answer_content(predicate.get_name())
        else:
            self._generate_unary_system_answer_content(predicate)

    def _generate_unary_system_answer_content(self, predicate):
        form = self._get_form(Node(Constants.SYS_ANSWER, {"predicate": predicate.get_name()}), optional=True)
        sort = predicate.getSort()
        if sort.is_builtin():
            self._assert_sorts_of_background_predicates_are_valid(predicate.get_name(), sort.get_name(), form)
            if sort.is_integer_sort():
                self._generate_system_integer_answer_content(predicate.get_name(), form)
            else:
                self._generate_system_placeholder_answer_content(predicate.get_name(), form)
        else:
            self._generate_unary_propositional_system_answer_content_for_custom_sort(predicate, form)

    def _assert_sorts_of_background_predicates_are_valid(self, predicate, sort, form):
        background_predicates = self._background_predicates_of_form(form, key_predicate=predicate)
        if background_predicates:
            msg = "Background is not allowed for predicate %r of sort %r. Perhaps you can create a new sort for it?" % (
                predicate, sort
            )
            raise InvalidSortOfBackgroundPredicateException(msg)

    def _generate_nullary_system_answer_content(self, predicate):
        self._generate_positive_nullary_system_answer_content(predicate)
        self._generate_negative_nullary_system_answer_content(predicate)

    def _generate_positive_nullary_system_answer_content(self, predicate):
        form = self._get_form(Node(Constants.POSITIVE_SYS_ANSWER, {"predicate": predicate}), optional=True)
        if form:
            argument_category = None
            function_name = "%s_positive_sys_answer" % predicate
            self._generate_sys_answer_with_potential_background(predicate, function_name, form, argument_category)

    def _generate_sys_answer_with_potential_background(self, predicate, function_name, form, argument_category):
        if self._form_contains_answer_slots(form):
            self._generate_sys_answer_with_background(predicate, function_name, form, argument_category)
        else:
            self._generate_sys_answer_without_background(predicate, function_name, form, argument_category)

    def _generate_sys_answer_without_background(self, predicate, function_name, form, argument_category):
        self._write_abstract_for_sys_answer_without_background(function_name, argument_category)
        self._write_semantic_for_sys_answer_without_background(function_name, predicate, argument_category)
        self._write_nl_for_sys_answer_without_background(function_name, form, argument_category)

    def _write_abstract_for_sys_answer_without_background(self, function_name, argument_category):
        if argument_category:
            output = "%s : %s -> SysAnswer;\n" % (function_name, argument_category)
        else:
            output = "%s : SysAnswer;\n" % function_name
        self._abstract_gf_content.write(output)

    def _write_semantic_for_sys_answer_without_background(self, function_name, predicate, argument_category):
        if argument_category:
            output = "%s individual = pp %s.s individual;\n" % (function_name, predicate)
        else:
            output = "%s = pp %s.s;\n" % (function_name, predicate)
        self._semantic_gf_content.write(output)

    def _write_nl_for_sys_answer_without_background(self, function_name, form, argument_category):
        if argument_category:
            if form and form.children:
                gf_string = self._generate_nl_for_system_answer(form)
            else:
                gf_string = "individual.s"
            output = "%s individual = answer (%s) individual.s;\n" % (function_name, gf_string)
        else:
            gf_string = self._generate_nl_for_system_answer(form)
            output = '%s = answer %s;\n' % (function_name, gf_string)

        self._natural_language_gf_content.write(output)

    def _generate_sys_answer_with_background(self, predicate, function_name, form, argument_category):

        background_predicates = self._background_predicates_of_form(form)
        predicates_string = " ".join(background_predicates)

        self._write_abstract_for_sys_answer_with_background(
            predicate, function_name, argument_category, background_predicates
        )
        self._write_semantic_for_sys_answer_with_background(
            predicate, function_name, argument_category, predicates_string
        )
        self._write_nl_for_sys_answer_with_background(
            predicate, function_name, argument_category, form, predicates_string
        )

    def _write_abstract_for_sys_answer_with_background(
        self, predicate, function_name, argument_category, background_predicates
    ):
        if argument_category:
            argument_categories_string = "%s -> %s" % (argument_category, "SysAnswer -> " * len(background_predicates))
        else:
            argument_categories_string = "SysAnswer -> " * len(background_predicates)

        output = "%s : %sSystem;\n" % (function_name, argument_categories_string)
        self._abstract_gf_content.write(output)

    def _write_semantic_for_sys_answer_with_background(
        self, predicate, function_name, argument_category, predicates_string
    ):
        if argument_category:
            arguments = "individual %s" % predicates_string
            answer_content = "pp %s.s individual" % predicate
        else:
            arguments = predicates_string
            answer_content = predicate

        self._semantic_gf_content.write(
            '%s %s = pp "Move" '
            '(move "answer" (%s) (list %s));\n' % (function_name, arguments, answer_content, predicates_string)
        )

    def _write_nl_for_sys_answer_with_background(
        self, predicate, function_name, argument_category, form, predicates_string
    ):
        if argument_category:
            arguments = "individual %s" % predicates_string
        else:
            arguments = predicates_string

        gf_string = self._generate_nl_for_system_answer(form)
        capitalized_gf_string = self._capitalize('%s ++ "."' % gf_string)
        self._natural_language_gf_content.write('%s %s = %s;\n' % (function_name, arguments, capitalized_gf_string))

    def _generate_negative_nullary_system_answer_content(self, predicate):
        form = self._get_form(Node(Constants.NEGATIVE_SYS_ANSWER, {"predicate": predicate}), optional=True)
        if form:
            self._abstract_gf_content.write("%s_negative_sys_answer : SysAnswer;\n" % predicate)
            self._semantic_gf_content.write('%s_negative_sys_answer = pp ("~" ++ %s.s);\n' % (predicate, predicate))
            self._natural_language_gf_content.write(
                '%s_negative_sys_answer = answer "%s";\n' % (predicate, self._form_to_gf_string(form))
            )

    def _generate_unary_propositional_system_answer_content_for_custom_sort(self, predicate, form):
        sort = predicate.getSort()
        argument_category = self._categories[sort.get_name()]
        function_name = "%s_sys_answer" % predicate.get_name()
        self._generate_sys_answer_with_potential_background(
            predicate.get_name(), function_name, form, argument_category
        )

    def _generate_nl_for_system_answer(self, form):
        parts = [self._generate_system_answer_part(part) for part in form.children]
        return " ++ ".join(parts)

    def _generate_system_answer_part(self, part):
        if self._is_propositional_answer_slot(part):
            background_predicate = part.parameters["predicate"]
            return "%s.s" % background_predicate
        elif self._is_individual_slot(part):
            return "individual.s"
        else:
            return '"%s"' % self._form_to_gf_string(part.strip())

    def _generate_user_answer_content(self, predicate):
        sort = predicate.getSort()
        if sort.is_integer_sort():
            self._generate_user_integer_answer_content(predicate)
        else:
            self._generate_user_answer_content_with_non_integer_sort(sort, predicate)

    def _generate_user_answer_content_with_non_integer_sort(self, sort, predicate):
        self._generate_sortal_user_answer(predicate, sort)
        self._generate_propositional_user_answer_of_non_integer_sort(predicate, sort)
        if not sort.is_string_sort():
            self._generate_user_short_answer_content(sort)
            self._generate_individual_content(sort)
            if predicate.allows_multiple_instances():
                self._generate_user_multi_answer_content(sort)

    def _generate_user_short_answer_content(self, sort):
        if not sort.is_boolean_sort():
            self._write_gf(
                function_name="%s_user_answer" % sort.get_name(),
                category="UsrAnswer",
                arguments=[Argument("answer", self._categories[sort.get_name()])],
                semantic="answer",
                natural_language="answer"
            )

    def _generate_propositional_user_answer_of_non_integer_sort(self, predicate, sort):
        if sort.is_string_sort():
            self._generate_propositional_user_answer_of_string_sort(predicate)
        else:
            self._generate_propositional_user_answer_of_custom_sort(predicate, sort)

    def _generate_propositional_user_answer_of_string_sort(self, predicate):
        self._abstract_gf_content.write(
            '%s_propositional_usr_answer : Unknown -> %s;\n' % (predicate, self._categories[predicate.get_name()])
        )
        self._semantic_gf_content.write(
            '%s_propositional_usr_answer answer = pp %s.s (ss ("\\"" ++ answer.s ++ "\\""));\n' %
            (predicate, predicate)
        )
        self._natural_language_gf_content.write('%s_propositional_usr_answer answer = answer;\n' % predicate)

    def _generate_propositional_user_answer_of_custom_sort(self, predicate, sort):
        self._abstract_gf_content.write(
            "%s_propositional_usr_answer : Sort_%s -> %s;\n" %
            (predicate, sort.get_name(), self._categories[predicate.get_name()])
        )
        self._semantic_gf_content.write(
            "%s_propositional_usr_answer answer = pp %s.s answer;\n" % (predicate, predicate)
        )
        self._natural_language_gf_content.write("%s_propositional_usr_answer answer = answer;\n" % predicate)

    def _generate_sortal_user_answer(self, predicate, sort):
        if not sort.is_boolean_sort():
            self._abstract_gf_content.write(
                "%s_sortal_usr_answer : Sort_%s -> UsrAnswer;\n" % (predicate, sort.get_name())
            )
            self._semantic_gf_content.write("%s_sortal_usr_answer answer = answer;\n" % predicate)
            self._natural_language_gf_content.write("%s_sortal_usr_answer answer = answer;\n" % predicate)

    def _generate_user_multi_answer_content(self, sort):
        self._abstract_gf_content.write(
            "%s_user_multi_answer : %s -> %s -> User;\n" %
            (sort.get_name(), self._categories[sort.get_name()], self._categories[sort.get_name()])
        )
        self._semantic_gf_content.write(
            "%s_user_multi_answer answer1 answer2 = multi_answer answer1 answer2;\n" % sort.get_name()
        )
        self._natural_language_gf_content.write(
            "%s_user_multi_answer answer1 answer2 = multi_answer answer1 answer2;\n" % sort.get_name()
        )

    def _generate_individual_content(self, sort):
        self._abstract_gf_content.write(
            "%s_individual : %s -> Individual;\n" % (sort.get_name(), self._categories[sort.get_name()])
        )
        self._semantic_gf_content.write("%s_individual individual = individual;\n" % sort.get_name())
        self._natural_language_gf_content.write("%s_individual individual = individual;\n" % sort.get_name())

    def _generate_system_placeholder_answer_content(self, predicate, form):
        function_name = "%s_sys_answer" % predicate
        self._abstract_gf_content.write("%s : Placeholder -> SysAnswer;\n" % function_name)
        self._semantic_gf_content.write('%s individual = pp "%s" individual;\n' % (function_name, predicate))

        if form:
            gf_parts = [self._generate_system_placeholder_answer_part(part) for part in form.children]
            natural_language_gf = 'answer (%s)' % " ++ ".join(gf_parts)
        else:
            natural_language_gf = "answer individual.s"
        self._natural_language_gf_content.write('%s individual = %s;\n' % (function_name, natural_language_gf))

    def _generate_system_placeholder_answer_part(self, part):
        if self._is_individual_slot(part):
            return "individual.s"
        else:
            return '"%s"' % self._form_to_gf_string(part.strip())

    def _generate_system_integer_answer_content(self, predicate, form):
        def generate_for_small_integers():
            self._abstract_gf_content.write(
                "%s_sys_answer_small : %s -> SysAnswer;\n" % (predicate, self.CATEGORY_FOR_SMALL_INTEGERS)
            )
            self._semantic_gf_content.write(
                '%s_sys_answer_small individual = pp "%s" individual;\n' % (predicate, predicate)
            )

            if form:
                parts = [self._generate_system_answer_part(part) for part in form.children]
                natural_language_gf = "answer (%s) individual.s" % " ++ ".join(parts)
            else:
                natural_language_gf = "individual"
            self._natural_language_gf_content.write(
                "%s_sys_answer_small individual = %s;\n" % (predicate, natural_language_gf)
            )

        def generate_for_large_integers():
            self._abstract_gf_content.write("%s_sys_answer_large : Placeholder -> SysAnswer;\n" % predicate)
            self._semantic_gf_content.write(
                '%s_sys_answer_large individual = pp "%s" individual;\n' % (predicate, predicate)
            )

            if form:
                parts = [self._generate_system_answer_part(part) for part in form.children]
                natural_language_gf = "answer (%s) individual.s" % " ++ ".join(parts)
            else:
                natural_language_gf = "answer individual.s"
            self._natural_language_gf_content.write(
                "%s_sys_answer_large individual = %s;\n" % (predicate, natural_language_gf)
            )

        generate_for_small_integers()
        generate_for_large_integers()

    def _generate_user_integer_answer_content(self, predicate):
        self._abstract_gf_content.write(
            "%s_propositional_usr_answer : %s -> %s;\n" %
            (predicate, self.CATEGORY_FOR_SMALL_INTEGERS, self._categories[predicate.get_name()])
        )
        self._semantic_gf_content.write(
            "%s_propositional_usr_answer answer = pp %s.s answer;\n" % (predicate, predicate)
        )
        self._natural_language_gf_content.write("%s_propositional_usr_answer answer = answer;\n" % predicate)

        self._abstract_gf_content.write(
            "%s_sortal_usr_answer : %s -> UsrAnswer;\n" % (predicate, self.CATEGORY_FOR_SMALL_INTEGERS)
        )
        self._semantic_gf_content.write("%s_sortal_usr_answer answer = answer;\n" % predicate)
        self._natural_language_gf_content.write("%s_sortal_usr_answer answer = answer;\n" % predicate)

    def _generate_user_question(self, predicate, forms):
        self._abstract_gf_content.write("ask_%s : UsrQuestion;\n" % predicate)
        semantic_function_name = self._get_gf_function_name_for_predicate(predicate)
        self._semantic_gf_content.write("ask_%s = %s %s;\n" % (predicate, semantic_function_name, predicate))

        forms_without_answers = []
        for form in forms:
            if self._form_contains_answer_slots(form):
                self._generate_user_question_with_answers(predicate, form)
            else:
                forms_without_answers.append(form)

        if len(forms_without_answers) > 0:
            self._natural_language_gf_content.write(
                "ask_%s = ss (%s);\n" % (predicate, self._speaker_independent_linearization(forms_without_answers))
            )

    def _generate_action_content(self, action):
        forms, grammatical_features = self._get_action_forms_and_grammatical_features(action)
        if len(forms) == 0:
            raise MissingEntry()
        has_np = self._has_np(forms)
        has_vp = self._has_vp(forms)
        if has_np and has_vp:
            raise Exception("cannot mix NP and VP forms for an action")
        elif has_np:
            self._generate_action_as_noun_phrase(action, forms, grammatical_features)
        else:
            self._generate_action_as_verb_phrase(action, forms)

    def _get_action_forms_and_grammatical_features(self, action):
        genders = [None, tala.nl.gf.resource.FEMININE, tala.nl.gf.resource.MASCULINE]
        numbers = [None, tala.nl.gf.resource.SINGULAR, tala.nl.gf.resource.PLURAL]
        permutations = [{"gender": gender, "number": number} for gender in genders for number in numbers]

        genderless_forms = self._get_form_as_options(Node(Constants.ACTION, {"name": action}), optional=True)
        for permutation in permutations:
            if permutation['gender'] is None:
                continue
            forms = self._get_form_as_options(
                Node(
                    Constants.ACTION, {
                        "name": action,
                        "gender": permutation['gender'],
                        "number": permutation["number"]
                    }
                ),
                optional=True
            )
            if len(forms) > 0:
                return genderless_forms + forms, permutation
        return genderless_forms, {"gender": None, "number": None}

    def _generate_action_as_verb_phrase(self, action, forms):
        function_name = action
        self._abstract_gf_content.write("%s : VpAction;\n" % function_name)
        self._semantic_gf_content.write('%s = pp "%s";\n' % (function_name, action))
        vp_forms = [form for form in forms if not self._is_np(form)]
        forms_without_answers = []
        for form in vp_forms:
            if self._form_contains_answer_slots(form):
                self._generate_request_with_answers(action, form)
            else:
                forms_without_answers.append(form)
        self._write_forms_without_answers_to_nl_content(self._verb_phrase, function_name, forms_without_answers)

    def _generate_action_as_noun_phrase(self, action, forms, grammatical_features):
        function_name = action
        category = self._get_np_action_category(grammatical_features)
        self._abstract_gf_content.write("%s : %s;\n" % (function_name, category))
        self._semantic_gf_content.write("%s = pp \"%s\";\n" % (function_name, action))

        forms_without_answers = []
        requests_without_answers = []
        for form in forms:
            if self._form_contains_answer_slots(form):
                self._generate_request_with_answers(action, form)
            elif self._is_np(form):
                forms_without_answers.append(form)
            else:
                requests_without_answers.append(form)

        self._write_forms_without_answers_to_nl_content(self._noun_phrase, function_name, forms_without_answers)
        if len(requests_without_answers) > 0:
            self._generate_request_without_answers(action, requests_without_answers)

    def _write_forms_without_answers_to_nl_content(self, phrase_function, function_name, forms_without_answers):
        if len(forms_without_answers) > 0:
            gf_forms = [phrase_function(form) for form in forms_without_answers]
            self._natural_language_gf_content.write("%s = (%s);\n" % (function_name, "|".join(gf_forms)))

    def _get_np_action_category(self, grammatical_features):
        return "NpAction%s%s" % (
            self._get_category_number_substring(grammatical_features["number"]
                                                ), self._get_category_gender_substring(grammatical_features["gender"])
        )

    def _get_category_gender_substring(self, gender):
        if gender is None:
            return ""
        elif gender == tala.nl.gf.resource.FEMININE:
            return "F"
        elif gender == tala.nl.gf.resource.MASCULINE:
            return "M"

    def _get_category_number_substring(self, number):
        if number is None:
            return ""
        elif number == tala.nl.gf.resource.SINGULAR:
            return "S"
        elif number == tala.nl.gf.resource.PLURAL:
            return "P"

    def _generate_request_without_answers(self, action, requests_without_answers):
        function_name = "%s_request" % action
        self._abstract_gf_content.write("%s : UsrRequest;\n" % function_name)
        self._semantic_gf_content.write("%s = request %s;\n" % (function_name, action))
        self._natural_language_gf_content.write(
            "%s = ss (%s);\n" % (function_name, self._speaker_independent_linearization(requests_without_answers))
        )

    def _verb_phrase(self, form):
        if isinstance(form, Node) and form.type == Constants.ITEM:
            return self._verb_phrase(form.get_single_child())
        elif self._is_vp(form):
            return 'mkverb "%s" "%s" "%s" "%s"' % (
                self._form_to_gf_string(form.get_child(Constants.INFINITIVE).get_single_child()),
                self._form_to_gf_string(form.get_child(Constants.IMPERATIVE).get_single_child()),
                self._form_to_gf_string(form.get_child(Constants.ING_FORM).get_single_child()
                                        ), self._form_to_gf_string(form.get_child(Constants.OBJECT).get_single_child())
            )
        else:
            gf_string = self._form_to_gf_string(form)
            return 'mkverb "%s" "%s" "%s"' % (gf_string, gf_string, gf_string)

    def _noun_phrase(self, form):
        if form.type == Constants.ITEM:
            return self._noun_phrase(form.get_single_child())
        elif form.get_child(Constants.DEFINITE):
            return 'mkdef "%s" "%s"' % (
                self._form_to_gf_string(form.get_child(Constants.INDEFINITE).get_single_child()),
                self._form_to_gf_string(form.get_child(Constants.DEFINITE).get_single_child())
            )
        else:
            return 'mkdef "%s"' % (self._form_to_gf_string(form.get_child(Constants.INDEFINITE).get_single_child()))

    def _form_contains_answer_slots(self, form):
        return bool(self._answer_slots_of_form(form))

    def _answer_slots_of_form(self, form):
        answer_slots = []
        if isinstance(form, Node):
            for part in form.children:
                if self._is_propositional_answer_slot(part) or self._is_sortal_answer_slot(part):
                    answer_slots.append(part)
        return answer_slots

    def _background_predicates_of_form(self, form, key_predicate=None):
        if form is None:
            return []
        background_predicates = []
        for part in form.children:
            if self._is_propositional_answer_slot(part):
                background_predicates.append(part.parameters["predicate"])
        if key_predicate is not None and key_predicate in background_predicates:
            background_predicates.remove(key_predicate)
        return background_predicates

    def _generate_user_question_with_answers(self, predicate, form):
        def generate_semantic_value(semantic_value_arguments):
            semantic_function_name = self._get_gf_function_name_for_predicate(predicate)
            return "%s %s %s" % (semantic_function_name, predicate, " ".join(semantic_value_arguments))

        function_name = self._generate_new_function_name("%s_user_question" % predicate)
        self._generate_function_with_answers(function_name, form, "UsrQuestion", generate_semantic_value)

    def _get_gf_function_name_for_predicate(self, predicate):
        if predicate.getSort().is_boolean_sort():
            return "ask_ynq"
        return "ask_whq"

    def _generate_request_with_answers(self, action, form):
        def generate_semantic_value(semantic_value_arguments):
            return 'request (pp "%s") %s' % (action, " ".join(semantic_value_arguments))

        function_name = self._generate_new_function_name("%s_request" % action)
        self._generate_function_with_answers(function_name, form, "UsrRequest", generate_semantic_value, action)

    def _generate_function_with_answers(self, function_name, form, output_category, semantic_value_function, action=""):
        answer_categories = []
        arguments = []
        semantic_value_arguments = []
        nl_parts = []
        for form_part in form.children:
            if self._is_propositional_answer_slot(form_part):
                predicate = form_part.parameters["predicate"]
                arguments.append(predicate)
                semantic_value_arguments.append(predicate)
                answer_categories.append(self._categories[predicate])
                nl_parts.append("%s.s" % predicate)
            elif self._is_sortal_answer_slot(form_part):
                sort = form_part.parameters["sort"]
                arguments.append(sort)
                semantic_value_arguments.append(sort)
                answer_categories.append(self._categories[sort])
                nl_parts.append("%s.s" % sort)
            elif form_part:
                nl_parts.append('"%s"' % self._form_to_gf_string(form_part))

        self._write_function_with_answers_in_abstract_gf(answer_categories, function_name, output_category)
        self._write_function_with_answers_in_semantic_gf(
            answer_categories, function_name, arguments, semantic_value_arguments, semantic_value_function, action
        )
        self._write_function_with_answers_in_natural_language_gf(function_name, nl_parts, arguments)

    def _write_function_with_answers_in_natural_language_gf(self, function_name, nl_parts, arguments):
        natural_content = "{function_name} {joined_arguments} = ss ({concatenated_nl_parts});\n".format(
            function_name=function_name,
            joined_arguments=" ".join(arguments),
            concatenated_nl_parts=" ++ ".join(nl_parts)
        )
        self._natural_language_gf_content.write(natural_content)

    def _write_function_with_answers_in_semantic_gf(
        self, answer_categories, function_name, arguments, semantic_value_arguments, semantic_value_function, action
    ):
        semantic_content = "{function_name} {arguments} = {value};\n".format(
            function_name=function_name,
            arguments=" ".join(arguments),
            value=semantic_value_function(semantic_value_arguments)
        )
        self._semantic_gf_content.write(semantic_content)

    def _write_function_with_answers_in_abstract_gf(self, answer_categories, function_name, output_category):
        abstract_content = "{function_name} : {argument_categories} -> {output_category};\n".format(
            function_name=function_name,
            argument_categories=" -> ".join(answer_categories),
            output_category=output_category
        )
        self._abstract_gf_content.write(abstract_content)

    def _get_predicate_sort(self, predicate_as_string):
        for predicate in list(self._ontology.get_predicates().values()):
            if predicate.get_name() == predicate_as_string:
                sort = predicate.getSort()
        return sort

    def _generate_new_function_name(self, prefix):
        function_name = "%s_%d" % (prefix, self._rule_count)
        self._rule_count += 1
        return function_name

    def _load_and_compile_grammar_entries(self, language_code):
        if self._xml_grammar_exists(language_code):
            return self._load_xml_grammar(language_code)
        elif language_code not in self._supported_py_grammar_languages():
            raise LanguageNotSupportedByPythonFormatException(
                "Expected '%s' but couldn't find it in '%s'" % (self._xml_grammar_path(language_code), os.getcwd())
            )
        elif self._py_grammar_exists(language_code):
            return self._load_py_grammar(language_code)
        else:
            raise Exception(
                "Expected either '%s' or '%s' but found neither in '%s'" %
                (self._xml_grammar_path(language_code), self._py_grammar_path(language_code), os.getcwd())
            )

    def _supported_py_grammar_languages(self):
        supported_languages = [languages.ENGLISH, languages.SWEDISH, languages.ITALIAN]
        return supported_languages

    def _py_grammar_exists(self, language_code):
        expected_path = self._py_grammar_path(language_code)
        return os.path.exists(expected_path)

    def _py_grammar_path(self, language_code):
        return "grammar_%s.py" % language_code

    def _load_py_grammar(self, language_code):
        grammar_source = self._load_py_grammar_source(language_code)
        self._grammar_compiler = DddPyCompiler()
        return self._grammar_compiler.compile_grammar(grammar_source, self._ontology, self._ddd.service_interface)

    def _load_py_grammar_source(self, language_code):
        return open(self._py_grammar_path(language_code)).read()

    def _xml_grammar_exists(self, language_code):
        return os.path.exists(self._xml_grammar_path(language_code))

    def _xml_grammar_path(self, language_code):
        return "grammar_%s.xml" % language_code

    def _load_xml_grammar(self, language_code):
        grammar_string = self._load_xml_grammar_source(language_code)
        self._grammar_compiler = DddXmlCompiler()
        return self._grammar_compiler.compile_grammar(
            grammar_string, self._ontology, self._ddd.service_interface, language_code
        )

    def _load_xml_grammar_source(self, language_code):
        with open(self._xml_grammar_path(language_code), mode="rb") as grammar_object:
            grammar_string = grammar_object.read()
            return grammar_string

    def _missing_entry(self, reporting_method, *args):
        if not self._ignore_warnings:
            print("Missing grammar entry:", end=' ', file=sys.stderr)
            reporting_method(*args)

    def _missing_action(self, action):
        self._warn('How do speakers talk about the action %s? Specify the utterance:\n' % action)
        example_phrase = self._example_phrase_from_semantic_value(action)
        simple_code_example = self._decompile_entry(Node(Constants.ACTION, {"name": action}), example_phrase)
        self._warn(simple_code_example)
        self._warn('Alternatively, you can specify several possible utterances in a list:\n')
        complex_code_example = self._decompile_node(
            Node(
                Constants.ACTION, {"name": action}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(Constants.ITEM, {}, ["%s one way" % example_phrase]),
                            Node(Constants.ITEM, {}, ["%s another way" % example_phrase]),
                            Node(
                                Constants.ITEM, {},
                                ["%s " % example_phrase,
                                 Node(Constants.SLOT, {"predicate": "city"})]
                            )
                        ]
                    )
                ]
            )
        )
        self._warn('%s\n\n' % complex_code_example)

    def _missing_individual(self, individual):
        self._warn('How do speakers talk about the individual %s? Specify the utterance:\n' % individual)
        example_phrase = self._example_phrase_from_semantic_value(individual)
        simple_code_example = self._decompile_entry(Node(Constants.INDIVIDUAL, {"name": individual}), example_phrase)
        self._warn(simple_code_example)
        self._warn('Alternatively, you can specify several possible utterances in a list:\n')
        complex_code_example = self._decompile_node(
            Node(
                Constants.INDIVIDUAL, {"name": individual}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(Constants.ITEM, {}, ["%s one way" % example_phrase]),
                            Node(Constants.ITEM, {}, ["%s another way" % example_phrase]),
                        ]
                    )
                ]
            )
        )
        self._warn('%s\n\n' % complex_code_example)

    def _missing_ended(self, key, action_interface):
        self._warn(
            'How does the system report that the service action %s ended? Specify the utterance:\n' %
            action_interface.name
        )
        example_phrase = "performed %s." % self._example_phrase_for_parameterized_service_action(action_interface)
        self._warn('%s\n\n' % (self._decompile_entry(key, example_phrase)))

    def _missing_preconfirm(self, key, action_interface):
        self._warn(
            'How does the system ask the user to confirm the service action %s, ' % action_interface.name +
            'before performing the action? ' + 'The entry is used in questions such as "Do you want to X?" ' +
            'where X is the grammar entry. Example:\n'
        )
        example_phrase = "perform %s." % self._example_phrase_for_parameterized_service_action(action_interface)
        example_code = self._decompile_entry(key, example_phrase)
        self._warn('%s\n\n' % example_code)

    def _missing_prereport(self, key, action_interface):
        self._warn(
            'How does the system give positive feedback about the service action %s,' % action_interface.name +
            ' before performing the action? Specify the utterance:\n'
        )
        example_phrase = "performing %s." % self._example_phrase_for_parameterized_service_action(action_interface)
        example_code = self._decompile_entry(key, example_phrase)
        self._warn('%s\n\n' % example_code)

    def _missing_validity(self, validator_interface, key):
        self._warn(
            'How does the system report that the device validity %s is unsatisfied? Specify the utterance:\n' %
            validator_interface.name
        )
        children = ["invalid parameters"]
        for parameter in validator_interface.parameters:
            children.append(" ")
            children.append(Node(Constants.SLOT, {"predicate": parameter.name}))
        example_code = self._decompile_node(Node(key.type, key.parameters, children))
        self._warn('%s\n\n' % example_code)

    def _example_phrase_for_parameterized_service_action(self, action_interface):
        phrase = self._example_phrase_from_semantic_value(action_interface.name)
        for parameter_name in self._get_action_parameters(action_interface):
            phrase += " <answer:%s>" % parameter_name
        return phrase

    def _missing_goal_issue(self, predicate):
        self._warn(
            'How do the speakers talk about the issue %s? ' % predicate +
            'The entry is used in questions such as "Do you want to know X?" ' +
            'or "I want to know X", where X is the grammar entry.\n\nExample:\n'
        )
        example_phrase = self._example_phrase_from_semantic_value(predicate)
        simple_code_example = self._decompile_entry(Node(Constants.PREDICATE, {"name": predicate}), example_phrase)
        self._warn(simple_code_example)
        self._warn('Alternatively, you can specify several possible utterances in a list:\n')
        complex_code_example = self._decompile_node(
            Node(
                Constants.PREDICATE, {"name": predicate}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(Constants.ITEM, {}, ["%s one way" % example_phrase]),
                            Node(Constants.ITEM, {}, ["%s another way" % example_phrase]),
                        ]
                    )
                ]
            )
        )
        self._warn('%s\n\n' % complex_code_example)

    def _missing_user_question(self, predicate):
        self._warn(
            'How does the user ask about %s?\n\nExample:\n\n%s_user_question = [\n  "what is %s",\n  "i want to know %s"\n]\n'
            % (predicate, predicate, predicate, predicate)
        )

    def _missing_system_question(self, key, predicate):
        example_phrase = "what is %s" % self._example_phrase_from_semantic_value(predicate)
        self._warn(
            'How does the system ask about %s?\n\nExample:\n\n%s\n' % (
                predicate,
                self._decompile_entry(key, example_phrase),
            )
        )

    def _is_goal_issue(self, predicate):
        goal_string = "resolve(?X.%s(X))" % predicate
        resolve_goals = list(filter(ResolveGoal.filter(), self._domain.get_all_goals()))
        return goal_string in [str(resolve_goal) for resolve_goal in resolve_goals]

    def _warn(self, warning):
        print(warning, file=sys.stderr)

    def _form_to_gf_string(self, form):
        if isinstance(form, str):
            return form
        elif form.type == Constants.ITEM:
            return " ".join([self._form_to_gf_string(child) for child in form.children])
        elif self._is_propositional_answer_slot(form):
            return self._form_to_gf_string(form.parameters["predicate"])
        else:
            raise Exception("_form_to_gf_string() failed for form: %r." % form)

    def _can_be_asked_by_system(self, predicate):
        return predicate in [
            str(question.get_predicate()) for question in self._domain.get_plan_questions() if (
                question.get_content().is_lambda_abstracted_predicate_proposition()
                and question.get_predicate().get_feature_of_name() is None
            )
        ]

    def _get_action_parameters(self, action_interface):
        return [parameter.name for parameter in action_interface.parameters]

    def _decompile_entry(self, key, value):
        node = Node(key.type, key.parameters, [value])
        return self._decompile_node(node)

    def _decompile_node(self, node):
        return self._grammar_compiler.decompile_grammar_node(self._ddd, self._ddd.language_codes, node)

    def _write_gf(self, function_name, category, arguments, semantic, natural_language):
        self._write_abstract(function_name, category, arguments)
        self._write_semantic(function_name, arguments, semantic)
        self._write_natural_language(function_name, arguments, natural_language)

    def _write_abstract(self, function_name, category, arguments):
        self._abstract_gf_content.write("%s : " % function_name)
        for argument in arguments:
            self._abstract_gf_content.write("%s -> " % argument.category)
        self._abstract_gf_content.write("%s;\n" % category)

    def _write_semantic(self, function_name, arguments, semantic):
        self._semantic_gf_content.write("%s " % function_name)
        for argument in arguments:
            self._semantic_gf_content.write("%s " % argument.name)
        self._semantic_gf_content.write("= %s;\n" % semantic)

    def _write_natural_language(self, function_name, arguments, natural_language):
        self._natural_language_gf_content.write("%s " % function_name)
        for argument in arguments:
            self._natural_language_gf_content.write("%s " % argument.name)
        self._natural_language_gf_content.write("= %s;\n" % natural_language)

    def _is_propositional_answer_slot(self, form):
        return self._is_slot(form) and "predicate" in form.parameters

    def _is_slot(self, form):
        return isinstance(form, Node) and form.type == Constants.SLOT

    def _is_sortal_answer_slot(self, form):
        return self._is_slot(form) and "sort" in form.parameters

    def _is_individual_slot(self, form):
        return self._is_slot(form) and len(form.parameters) == 0

    def _has_np(self, forms):
        return any([form for form in forms if self._is_np(form)])

    def _is_np(self, form):
        if isinstance(form, Node) and form.type == Constants.ITEM:
            return self._has_np(form.children)
        else:
            return isinstance(form, Node) and form.type == Constants.NP

    def _has_vp(self, forms):
        return any([form for form in forms if self._is_vp(form)])

    def _is_vp(self, form):
        if isinstance(form, Node) and form.type == Constants.ITEM:
            return self._has_vp(form.children)
        else:
            return isinstance(form, Node) and form.type == Constants.VP


class Argument:
    def __init__(self, name, category):
        self.name = name
        self.category = category
