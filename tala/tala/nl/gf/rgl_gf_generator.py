# -*- coding: utf-8 -*-

import codecs
import itertools
from io import StringIO
import sys

from tala.nl import languages
from tala.ddd.ddd_xml_compiler import DddXmlCompiler
from tala.ddd.services.constants import UNDEFINED_SERVICE_ACTION_FAILURE
from tala.ddd.grammar.reader import GrammarReader
from tala.nl.gf import rgl_grammar_entry_types as rgl_types, utils
from tala.nl.gf.auto_generator import LowerCaseGfFileWriter
from tala.nl.gf.grammar_entry_types import Constants, Node
from tala.nl.gf.naming import abstract_gf_filename, natural_language_gf_filename, semantic_gf_filename, \
    probabilities_filename


class MissingEntry(Exception):
    pass


class GrammarProcessingException(Exception):
    pass


class RglGfFilesGeneratorException(Exception):
    pass


class FunctionNames:
    NP_ACTION = 'NpAction'
    VP_ACTION = 'VpAction'


class Directives:
    FUNCTION = "fun"
    CATEGORY = "cat"
    LINEARIZATION_CATEGORY = "lincat"
    LINEARIZATION = "lin"


DEFAULT_ABSTRACT_GRAMMAR = [
    Node(Constants.ACTION, {"name": "top"}, [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "menu"})])]),
    Node(
        Constants.ACTION, {"name": "up"}, [Node(rgl_types.VERB_PHRASE, {}, [Node(rgl_types.VERB, {"ref": "return"})])]
    ),
]

DEFAULT_LEXICONS = {
    languages.ENGLISH: [
        Node(rgl_types.NOUN, {"id": "menu"}, [Node("singular", {}, ["menu"])]),
        Node(rgl_types.VERB, {"id": "return"}, [Node("infinitive", {}, ["return"])]),
    ],
    languages.FRENCH: [
        Node(rgl_types.NOUN, {"id": "menu"}, [Node("singular", {}, ["menu"])]),
        Node(rgl_types.VERB, {"id": "return"}, [Node("infinitive", {}, ["retourner"])]),
    ],
    languages.DUTCH: [
        Node(rgl_types.NOUN, {"id": "menu"}, [Node("singular", {}, ["menu"])]),
        Node(rgl_types.VERB, {"id": "return"}, [Node("infinitive", {}, ["terugkeren"])]),
    ],
    languages.CHINESE: [
        Node(rgl_types.NOUN, {"id": "menu"}, [Node("singular", {}, ["菜单"])]),
        Node(rgl_types.VERB, {"id": "return"}, [Node("infinitive", {}, ["返回"])]),
    ],
}

MAX_NUM_ENTITIES_PER_PARSE = 10


class GfGenerator(object):
    def generate_list(self, strings):
        if len(strings) == 0:
            return '(empty_list)'
        else:
            return '(list %s)' % ' '.join(strings)

    def generate_string_as_utterance(self, string):
        return '(strUtt "%s")' % string.strip()

    def generate_gf_concatenation(self, gf_strings):
        if len(gf_strings) == 1:
            return gf_strings[0]
        else:
            return self._generate_concatentation_tree(gf_strings)

    def _generate_concatentation_tree(self, gf_strings):
        if len(gf_strings) == 1:
            return gf_strings[0]
        else:
            return '(concatUtt %s %s)' % (gf_strings[0], self._generate_concatentation_tree(gf_strings[1:]))

    def get_sort_category(self, sort):
        return 'Sort_%s' % sort

    def get_predicate_category(self, predicate):
        return 'Predicate_%s' % predicate

    def generate_disjunction(self, gf_strings):
        if len(gf_strings) > 1:
            return "(%s)" % "|".join(gf_strings)
        else:
            return gf_strings[0]


class GrammarProcessor(object):
    def get_options_from_node(self, node):
        if node is None:
            return []
        elif node.type == Constants.ONE_OF:
            return self.get_contents_of_items(node.children)
        else:
            return [node]

    def get_contents_of_items(self, nodes):
        return [self.get_content_of_item(node) for node in nodes]

    def get_content_of_item(self, node):
        if node.type == Constants.ITEM and len(node.children) == 1:
            return node.children[0]
        else:
            raise GrammarProcessingException("expected ITEM node with a single child but found %s" % node)

    def has_single_child_node(self, node, child_type):
        return self.get_single_child_node(node, child_type, optional=True) is not None

    def get_single_child_node(self, node, child_type, optional=False):
        child_nodes_of_desired_type = [child for child in node.children if child.type == child_type]
        if len(child_nodes_of_desired_type) == 1:
            return child_nodes_of_desired_type[0]
        elif len(child_nodes_of_desired_type) == 0:
            if optional:
                return None
            else:
                raise GrammarProcessingException("expected a child node of type %s in %s" % (child_type, node))
        else:
            raise GrammarProcessingException(
                "expected exactly 1 child node of type %s in %s, was %s" %
                (child_type, node, child_nodes_of_desired_type)
            )

    def is_individual(self, obj):
        return isinstance(obj, Node) and obj.type == Constants.INDIVIDUAL

    def is_individual_with_predicate(self, obj):
        return isinstance(obj, Node) and obj.type == Constants.INDIVIDUAL and "predicate" in obj.parameters

    def is_background_individual(self, form_part, predicate_name):
        return self.is_individual_with_predicate(form_part
                                                 ) and self.get_individual_predicate(form_part) != predicate_name

    def has_background(self, form, predicate):
        if form is None:
            return False
        else:
            form_parts = self.get_utterance_content(form)
            return any([self.is_background_individual(form_part, predicate.get_name()) for form_part in form_parts])

    def get_individual_sort(self, node):
        return node.parameters["sort"]

    def get_individual_predicate(self, node):
        return node.parameters["predicate"]

    def get_individual_argument(self, node):
        if "sort" in node.parameters:
            sort = node.parameters["sort"]
            return Argument(name=sort, category=self.get_sort_category(sort))
        else:
            raise GrammarProcessingException(
                "expected individual parameters to contain sort but got %s" % node.parameters
            )

    def is_string(self, obj):
        return isinstance(obj, str)

    def is_text(self, form_parts):
        return all([self.is_string(form_part) for form_part in form_parts])

    def get_text(self, form_parts):
        return ' '.join(form_parts)

    def get_text_from_utterance_node(self, node):
        options = self.get_utterance_options(node)
        if len(options) == 1 and self.is_text(options[0]):
            return self.get_text(options[0])
        else:
            raise GrammarProcessingException("expected utterance to contain pure text but got\n%s" % node)

    def get_utterance_content(self, node):
        if node.type == rgl_types.UTTERANCE:
            return node.children
        else:
            raise GrammarProcessingException("expected an utterance but got\n%s" % node)

    def get_utterance_options(self, node):
        children = self.get_utterance_content(node)
        if len(children) == 1:
            child = children[0]
            if self.is_string(child):
                return [[child]]
            elif child.type == Constants.ONE_OF:
                return self.get_utterance_options_for_items(child.children)
            else:
                raise GrammarProcessingException(
                    "expected single child of utterance to be string or one-of but got %s" % child
                )
        else:
            self._assert_form_parts_are_string_or_individual(children)
            return [children]

    def _assert_form_parts_are_string_or_individual(self, form_parts):
        for form_part in form_parts:
            if not (self.is_string(form_part) or self.is_individual(form_part)):
                raise GrammarProcessingException("expected a string or an individual but got %s" % form_part)

    def get_utterance_options_for_items(self, items):
        result = []
        for item in items:
            form_parts = self.get_item_content(item)
            result += [form_parts]
        return result

    def get_item_content(self, item):
        if isinstance(item, Node) and item.type == Constants.ITEM:
            self._assert_form_parts_are_string_or_individual(item.children)
            return item.children
        else:
            raise GrammarProcessingException("expected an item node but got\n" % item)

    def get_lexicon_field_from_entry(self, lexicon_entry_nodes, field_name):
        for node in lexicon_entry_nodes:
            if node.type == field_name:
                if len(node.children) == 1:
                    return node.children[0]
                else:
                    raise GrammarProcessingException(
                        "expected lexicon field to contain a single node but found %s" % node.children
                    )
        raise GrammarProcessingException("failed to get lexicon field %r in %s" % (field_name, lexicon_entry_nodes))

    def get_lexicon_entry_from_lexicon(self, lexicon_nodes, type_, id_):
        for node in lexicon_nodes:
            if node.type == type_ and node.parameters["id"] == id_:
                if len(node.children) == 1:
                    return node.children
        raise GrammarProcessingException("failed to get lexicon entry for type=%s id=%s" % (type_, id_))

    def nodes_contain(self, nodes, node_type):
        return any([node for node in nodes if node.type == node_type])


class RglGfFilesGenerator(GfGenerator, GrammarProcessor):
    def __init__(self, ddd, ignore_warnings=False, cwd=None):
        super(RglGfFilesGenerator, self).__init__()
        self._ddd = ddd
        self._ddd_name = ddd.name
        self._ontology = self._ddd.ontology
        self._domain = self._ddd.domain
        self._ignore_warnings = ignore_warnings
        self._sort_categories = self._get_sort_categories()
        self._predicate_categories = self._get_predicate_categories()
        self._rule_count = 1

        self._abstract_gf_content = StringIO()
        self._semantic_gf_content = StringIO()
        self._natural_language_gf_content = StringIO()
        self._probabilities_file_content = StringIO()

    def _get_sort_categories(self):
        return dict([(sort, self.get_sort_category(sort)) for sort in self._ontology.get_sorts()])

    def _get_predicate_categories(self):
        return dict([(predicate, self.get_predicate_category(predicate))
                     for predicate in self._ontology.get_predicates()])

    def generate(self, tdm_language_code):
        self._tdm_language_code = tdm_language_code
        self._gf_language_code = self._tdm_to_gf_language_code(tdm_language_code)
        self._grammar = self._load_and_compile_grammar_entries()
        self._default_grammar = self._create_default_grammar()
        self._lexicon_nodes = self._get_lexicon()
        self._add_header_in_generated_gf_files()
        self._add_content_in_generated_gf_files()
        self._add_footer_in_generated_gf_files()

    def write_to_file(self, _):
        self._write_to_gf_files()

    def clear(self):
        self._clear_io_buffers()

    def _tdm_to_gf_language_code(self, tdm_language_code):
        return tdm_language_code.capitalize()

    def _load_and_compile_grammar_entries(self):
        grammar_source = GrammarReader.read(self._tdm_language_code)
        self._grammar_compiler = DddXmlCompiler()
        return self._grammar_compiler.compile_rgl_grammar(
            grammar_source, self._ontology, self._ddd.service_interface, self._tdm_language_code
        )

    def _get_lexicon(self):
        return self._get_lexicon_from_grammar(self._grammar) + self._get_lexicon_from_grammar(self._default_grammar)

    def _get_lexicon_from_grammar(self, grammar):
        for node in grammar.children:
            if node.type == rgl_types.LEXICON:
                return node.children
        return []

    def _get_lexicon_entry_as_nodes(self, type_, id_):
        return self.get_lexicon_entry_from_lexicon(self._lexicon_nodes, type_, id_)

    def get_noun_singular_form(self, form):
        noun_form = self.get_single_child_node(form, "noun")
        noun_lexicon_entry_as_nodes = self._get_lexicon_entry_as_nodes(rgl_types.NOUN, noun_form.parameters["ref"])
        return self.get_lexicon_field_from_entry(noun_lexicon_entry_as_nodes, "singular")

    def get_verb_infinite_form(self, form):
        verb_form = self.get_single_child_node(form, "verb", optional=False)
        verb_lexicon_entry_as_nodes = self._get_lexicon_entry_as_nodes(rgl_types.VERB, verb_form.parameters["ref"])
        return self.get_lexicon_field_from_entry(verb_lexicon_entry_as_nodes, "infinitive")

    def _clear_io_buffers(self):
        self._abstract_gf_content = StringIO()
        self._semantic_gf_content = StringIO()
        self._natural_language_gf_content = StringIO()
        self._probabilities_file_content = StringIO()

    def _name_of_natural_language_gf_file(self):
        return "build/%s/%s" % (
            self._tdm_language_code, natural_language_gf_filename(self._ddd_name, self._tdm_language_code)
        )

    def _name_of_probabilities_file(self):
        return "build/%s/%s" % (self._tdm_language_code, probabilities_filename(self._ddd_name))

    def _add_header_in_generated_gf_files(self):
        self._abstract_gf_content.write(self._generate_abstract_header())
        self._semantic_gf_content.write(self._generate_semantic_header())
        self._natural_language_gf_content.write(self._generate_natural_language_header())

    def _generate_abstract_header(self):
        header = (
            "--# -coding=utf8\n"
            "abstract %s = TDM, Integers ** {\n" % self._ddd_name + "\n"
            "%s\n\n" % Directives.CATEGORY
        )
        for category in self._get_categories_for_sorts_and_predicates():
            header += "%s;\n" % category
        header += "\n%s\n\n" % Directives.FUNCTION
        return header

    def _get_categories_for_sorts_and_predicates(self):
        return list(self._sort_categories.values()) + list(self._predicate_categories.values())

    def _generate_semantic_header(self):
        return (
            "--# -coding=utf8\n"
            "concrete %s_sem of %s = TDM_sem, Integers_sem ** open Utils_sem in {\n\n" %
            (self._ddd_name, self._ddd_name) + "\nlin\n\n"
        )

    def _generate_natural_language_header(self):
        header_format = (
            "--# -coding=utf8\n"
            "concrete {ddd_name}_{tdm_language_code} of {ddd_name} =\n"
            "  TDM{gf_language_code} - [sysGreet],\n"
            "  Integers{gf_language_code}\n"
            "** open\n"
            "  Utils{gf_language_code},\n"
            "  TDMInterface{gf_language_code},\n"
            "  Syntax{gf_language_code},\n"
            "  Paradigms{gf_language_code},\n"
            "  Prelude\n"
            "\n"
            "in {{\n"
            "{linearization_category_directive}\n\n"
            "{linearization_categories}\n"
            "{linearization_directive}\n\n"
        )
        return header_format.format(
            ddd_name=self._ddd_name,
            tdm_language_code=self._tdm_language_code,
            gf_language_code=self._gf_language_code,
            linearization_category_directive=Directives.LINEARIZATION_CATEGORY,
            linearization_categories=self._generate_linearization_categories(),
            linearization_directive=Directives.LINEARIZATION
        )

    def _generate_linearization_categories(self):
        sort_lines = ["%s = Sort;\n" % category for category in list(self._sort_categories.values())]
        predicate_lines = ["%s = Pred;\n" % category for category in list(self._predicate_categories.values())]
        return "".join(sort_lines + predicate_lines)

    def _add_footer_in_generated_gf_files(self):
        self._abstract_gf_content.write("}\n")
        self._semantic_gf_content.write("}\n")
        self._natural_language_gf_content.write("}\n")

    def _write_to_gf_files(self):
        def write_abstract_file():
            with codecs.open(self._name_of_abstract_gf_file(), "w", encoding="utf-8") as abstract_file:
                self._abstract_gf_content.seek(0)
                for line in self._abstract_gf_content:
                    abstract_file.write(line)

        def write_semantic_file():
            with codecs.open(self._name_of_semantic_gf_file(), "w", encoding="utf-8") as semantic_file:
                self._semantic_gf_content.seek(0)
                for line in self._semantic_gf_content:
                    semantic_file.write(line)

        def write_natural_language_file():
            with LowerCaseGfFileWriter.open(
                self._name_of_natural_language_gf_file(), "w", encoding="utf-8"
            ) as natural_language_file:
                self._natural_language_gf_content.seek(0)
                for line in self._natural_language_gf_content:
                    natural_language_file.write(line)

        def write_probabilities_file():
            with open(self._name_of_probabilities_file(), "w") as probabilities_file:
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

    def _name_of_abstract_gf_file(self):
        return "build/%s/%s" % (self._tdm_language_code, abstract_gf_filename(self._ddd_name))

    def _name_of_semantic_gf_file(self):
        return "build/%s/%s" % (self._tdm_language_code, semantic_gf_filename(self._ddd_name))

    def _add_content_in_generated_gf_files(self):
        self._add_content_based_on_ontology()
        if self._ddd.service_interface:
            self._add_content_based_on_service_interface()

    def _add_content_based_on_ontology(self):
        self._generate_actions()
        self._generate_individuals()
        self._generate_mock_individuals_for_dynamic_sorts()
        self._generate_predicates()

    def _generate_actions(self):
        for action in self._ontology.get_actions():
            self._generate_action(action)

    def _generate_action(self, action):
        try:
            forms = self._get_form_as_options(Node(Constants.ACTION, {"name": action}))
            ActionFunctionGenerator(self, action, forms).generate()
        except MissingEntry:
            self._warn_about_missing_entry(
                """How do speakers talk about the action '%s'? Possible contents of the <action> element:

  <verb-phrase>
  <noun-phrase>
  <one-of>""" % action
            )
        self._generate_potential_request(action)

    def _generate_potential_request(self, action):
        form = self._get_form(Node(rgl_types.REQUEST, {"action": action}), optional=True)
        if form:
            self._generate_requests(action, form)

    def _generate_requests(self, action, form):
        options = self.get_utterance_options(form)
        for option in options:
            RequestFunctionGenerator(self, action, option).generate()

    def _get_form(self, key, optional=False):
        node = self._grammar.get_child(key.type, key.parameters)
        if node is not None:
            return node.get_single_child()
        elif self._has_default_form(key):
            return self._get_default_form(key)
        elif optional:
            return None
        else:
            raise MissingEntry("missing entry %s" % str(key))

    def _get_form_as_options(self, key, optional=False):
        node = self._get_form(key, optional)
        return self.get_options_from_node(node)

    def _warn_about_missing_entry(self, warning):
        if not self._ignore_warnings:
            print("\nMissing grammar entry:", end=' ', file=sys.stderr)
            print(warning, file=sys.stderr)

    def _add_content_based_on_service_interface(self):
        for action_interface in self._ddd.service_interface.actions:
            self._generate_report_ended_and_failed_content(action_interface)
            self._generate_report_started_content(action_interface)
        for validator_interface in self._ddd.service_interface.validators:
            self._generate_validity_content(validator_interface)

    def _generate_report_ended_and_failed_content(self, action_interface):
        key = Node(Constants.REPORT_ENDED, {"action": action_interface.name})
        try:
            form = self._get_form(key)
            ReportEndedFunctionGenerator(self, action_interface.name, form).generate()
            FunctionGeneratorForReportFailedWithUnknownFailure(self, action_interface.name, form).generate()
        except MissingEntry:
            if self._service_action_has_postconfirm(action_interface.name):
                warning = self._get_warning_for_missing_report_ended(key, action_interface.name)
                self._warn_about_missing_entry(warning)

    def _get_warning_for_missing_report_ended(self, key, action_name):
        example_phrase = "performed %s" % action_name
        example_form = Node(rgl_types.UTTERANCE, {}, [example_phrase])
        example_xml = self._decompile_entry(key, example_form)
        return "How does the system report that the service action '%s' ended? Example:\n\n%s\n" % (
            action_name, example_xml
        )

    def _generate_report_started_content(self, action_interface):
        key = Node(Constants.REPORT_STARTED, {"action": action_interface.name})
        try:
            form = self._get_form(key)
            ReportStartedFunctionGenerator(self, action_interface.name, form).generate()
        except MissingEntry:
            pass

    def _generate_predicates(self):
        for predicate in list(self._ontology.get_predicates().values()):
            predicate_name = predicate.get_name()
            self._generate_predicate_content(predicate_name)
            self._generate_potential_system_question(predicate_name)
            self._generate_potential_user_question(predicate_name)
            self._generate_system_answer_content(predicate)
            self._generate_user_answer_content(predicate)

    def _generate_predicate_content(self, predicate_name):
        function_name = predicate_name
        self._abstract_gf_content.write('%s : Predicate;\n' % function_name)
        self._semantic_gf_content.write('%s = pp "%s";\n' % (function_name, predicate_name))
        form = self._get_form(Node(rgl_types.PREDICATE, {"name": predicate_name}), optional=True)
        if form:
            self._generate_speaker_independent_predicate_content(function_name, form)
            self._generate_resolve_ynq(predicate_name, form)

    def _generate_speaker_independent_predicate_content(self, function_name, form):
        noun = self.get_noun_singular_form(form)
        self._natural_language_gf_content.write('%s = mkPred (mkNP the_Det (mkN "%s"));\n' % (function_name, noun))

    def _generate_resolve_ynq(self, predicate_name, form):
        function_name = '%s_resolve_ynq' % predicate_name
        self._abstract_gf_content.write('%s : SysResolveGoal;\n' % function_name)
        self._semantic_gf_content.write('%s = resolve_ynq %s;\n' % (function_name, predicate_name))
        noun = self.get_noun_singular_form(form)
        self._natural_language_gf_content.write(
            '%s = mkSysResolveGoal (mkVP know_V2 (mkNP the_Det (mkN "%s")));\n' % (function_name, noun)
        )

    def _generate_potential_system_question(self, predicate):
        if self._can_be_asked_by_system(predicate):
            self._generate_system_question(predicate)

    def _generate_system_question(self, predicate):
        key = Node(Constants.SYS_QUESTION, {"predicate": predicate})
        try:
            form = self._get_form(key)
            function_name = predicate
            natural_language_content = self._generate_natural_language_for_system_question(form)
            self._natural_language_gf_content.write('%s = %s;\n' % (function_name, natural_language_content))
        except MissingEntry:
            warning = self._get_warning_for_missing_system_question(key, predicate)
            self._warn_about_missing_entry(warning)

    def _can_be_asked_by_system(self, predicate_name):
        for question in self._domain.get_plan_questions():
            if self._question_has_predicate_name(question, predicate_name) and not self._question_is_feature(question):
                return True
            elif self._question_has_ask_feature(question, predicate_name):
                return True

    def _question_has_predicate_name(self, question, predicate_name):
        return question.get_content().is_lambda_abstracted_predicate_proposition() and question.get_predicate(
        ).get_name() == predicate_name

    def _question_is_feature(self, question):
        return question.get_predicate().get_feature_of_name() is not None

    def _question_has_ask_feature(self, question, feature_name):
        ask_features = self._domain.get_ask_features(question)
        if ask_features is not None:
            for feature_predicate in ask_features:
                if feature_predicate.name == feature_name:
                    return True

    def _get_warning_for_missing_system_question(self, key, predicate):
        example_phrase = "what is %s" % self._example_phrase_from_semantic_value(predicate)
        example_form = Node(rgl_types.UTTERANCE, {}, [example_phrase])
        example_xml = self._decompile_entry(key, example_form)
        return "How does the system ask about '%s'?\n\nExample:\n\n%s\n" % (predicate, example_xml)

    def _example_phrase_from_semantic_value(self, string):
        return string.replace("_", " ")

    def _decompile_entry(self, key, value):
        node = Node(key.type, key.parameters, [value])
        return self._decompile_node(node)

    def _decompile_node(self, node):
        return self._grammar_compiler.decompile_grammar_node(self._ddd, self._ddd.language_codes, node)

    def _generate_potential_user_question(self, predicate_name):
        form = self._get_form(Node(Constants.USER_QUESTION, {"predicate": predicate_name}), optional=True)
        if form:
            form_variants = self.get_utterance_options(form)
            for form_variant in form_variants:
                UserQuestionFunctionGenerator(self, predicate_name, form_variant).generate()

    def _generate_natural_language_for_system_question(self, form):
        return 'mkPred "%s"' % self.get_text_from_utterance_node(form)

    def _generate_system_answer_content(self, predicate):
        sort = predicate.getSort()
        if sort.is_boolean_sort():
            raise RglGfFilesGeneratorException("system answers of boolean sort not supported")
        else:
            self._generate_unary_system_answer_content(predicate)

    def _generate_unary_system_answer_content(self, predicate):
        form = self._get_form(Node(Constants.SYS_ANSWER, {"predicate": predicate.get_name()}), optional=True)
        sort = predicate.getSort()
        if sort.is_builtin():
            raise RglGfFilesGeneratorException("system answers of built-in sorts such as %s are not supported" % sort)
        else:
            self._generate_system_answer_of_custom_sort(predicate, form)

    def _generate_system_answer_of_custom_sort(self, predicate, form):
        if self.has_background(form, predicate):
            FunctionGeneratorForSystemAnswerOfCustomSortWithBackground(self, predicate, form).generate()
        else:
            FunctionGeneratorForSystemAnswerOfCustomSortWithoutBackground(self, predicate, form).generate()

    def _generate_user_answer_content(self, predicate):
        sort = predicate.getSort()
        self._generate_sortal_user_answer(predicate, sort)

    def _generate_sortal_user_answer(self, predicate, sort):
        self.write_function(
            function_name='%s_sortal_usr_answer' % predicate,
            category='UsrAnswer',
            arguments=[Argument(name="answer", category=self.get_sort_category(sort.get_name()))],
            semantic_content='answer',
            natural_language_content='mkUsr answer'
        )

    def _generate_individuals(self):
        for individual, sort in self._ontology.get_individuals().items():
            self._generate_individual(individual, sort)

    def _generate_individual(self, individual, sort):
        try:
            key = Node(Constants.INDIVIDUAL, {"name": individual})
            form = self._get_form(key)
        except MissingEntry:
            return
        self.write_function(
            function_name=individual,
            category=self.get_sort_category(sort.get_name()),
            semantic_content='pp "%s"' % individual,
            natural_language_content=self._generate_natural_language_for_individual(form)
        )

    def _generate_natural_language_for_individual(self, form):
        if form.type == rgl_types.PROPER_NOUN and len(form.children) == 1:
            return 'mkSort (mkPN ("%s"))' % form.children[0]
        else:
            raise RglGfFilesGeneratorException("expected proper noun with single child but got %s" % form)

    def _generate_validity_content(self, validator_interface):
        key = Node(Constants.VALIDITY, {"name": validator_interface.name})
        try:
            forms = self._get_form_as_options(key)
            ValidityGenerator(self, validator_interface, forms).generate()
        except MissingEntry:
            warning = 'How does the system report that the device validity %s is unsatisfied?' % validator_interface.name
            self._warn_about_missing_entry(warning)

    def _create_default_grammar(self):
        lexicon = DEFAULT_LEXICONS[self._tdm_language_code]
        return Node(Constants.GRAMMAR, {}, DEFAULT_ABSTRACT_GRAMMAR + [Node(rgl_types.LEXICON, {}, lexicon)])

    def _has_default_form(self, key):
        node = self._default_grammar.get_child(key.type, key.parameters)
        return node is not None

    def _get_default_form(self, key):
        node = self._default_grammar.get_child(key.type, key.parameters)
        if node is not None:
            return node.get_single_child()

    def _generate_mock_individuals_for_dynamic_sorts(self):
        for sort in list(self._ontology.get_sorts().values()):
            if sort.is_dynamic():
                for i in range(0, MAX_NUM_ENTITIES_PER_PARSE):
                    placeholder_name = utils.name_of_user_answer_placeholder_of_sort(sort.get_name(), i)
                    sem_placeholder = utils.semantic_user_answer_placeholder_of_sort(sort.get_name(), i)
                    nl_placeholder = utils.nl_user_answer_placeholder_of_sort(sort.get_name(), i)

                    self._abstract_gf_content.write(
                        "%s : %s;\n" % (placeholder_name, self.get_sort_category(sort.get_name()))
                    )
                    self._semantic_gf_content.write('%s = pp "%s";\n' % (placeholder_name, sem_placeholder))
                    self._natural_language_gf_content.write(
                        '%s = mkSort (mkPN ("%s"));\n' % (placeholder_name, nl_placeholder)
                    )

    def generate_new_function_name(self, prefix):
        function_name = "%s_%d" % (prefix, self._rule_count)
        self._rule_count += 1
        return function_name

    def write_function(self, function_name, category, semantic_content, natural_language_content, arguments=[]):
        self._write_abstract(function_name, category, arguments)
        self._write_semantic(function_name, arguments, semantic_content)
        self._write_natural_language(function_name, arguments, natural_language_content)

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

    def _service_action_has_postconfirm(self, action_name):
        for item in self._domain.get_invoke_service_action_items_for_action(action_name):
            if item.has_postconfirmation():
                return True


class FunctionGenerator(GrammarProcessor, GfGenerator):
    def __init__(self, files_generator):
        self._files_generator = files_generator

    def generate(self):
        self._files_generator.write_function(
            function_name=self.get_function_name(),
            category=self.get_function_category(),
            arguments=self.get_arguments(),
            semantic_content=self.get_semantic_content(),
            natural_language_content=self.get_natural_language_content()
        )

    def generate_new_function_name(self, prefix):
        return self._files_generator.generate_new_function_name(prefix)

    def get_arguments(self):
        return []


class ActionFunctionGenerator(FunctionGenerator):
    def __init__(self, files_generator, action, forms):
        self._files_generator = files_generator
        self._action = action
        self._forms = forms

    def get_function_name(self):
        return self._action

    def get_function_category(self):
        forms_contain_noun_phrase = self.nodes_contain(self._forms, rgl_types.NOUN_PHRASE)
        forms_contain_verb_phrase = self.nodes_contain(self._forms, rgl_types.VERB_PHRASE)
        if forms_contain_noun_phrase and forms_contain_verb_phrase:
            raise RglGfFilesGeneratorException(
                "Exception when generating action %s: Cannot mix noun and verb phrase." % self._action
            )
        elif forms_contain_noun_phrase:
            return FunctionNames.NP_ACTION
        elif forms_contain_verb_phrase:
            return FunctionNames.VP_ACTION
        else:
            raise RglGfFilesGeneratorException(
                "Exception when generating action %s: Expected entry to contain either "
                "a noun phrase or a verb phrase." % self._action
            )

    def get_semantic_content(self):
        return 'pp "%s"' % self._action

    def get_natural_language_content(self):
        generated_forms = [self._generate_natural_language_content(form) for form in self._forms]
        return self.generate_disjunction(generated_forms)

    def _generate_natural_language_content(self, form):
        if form.type == rgl_types.NOUN_PHRASE:
            return self._generate_noun_phrase(form)
        elif form.type == rgl_types.VERB_PHRASE:
            return self._generate_verb_phrase(form)
        else:
            raise GrammarProcessingException("don't know how to generate natural language content for %r" % form)

    def _generate_noun_phrase(self, form):
        noun_singular_form = self._files_generator.get_noun_singular_form(form)
        return 'mkNpAction (mkNP (mkPN "%s") | mkNP the_Det (mkCN (mkN "%s")))' % (
            noun_singular_form, noun_singular_form
        )

    def _generate_verb_phrase(self, form):
        verb_infinitive_form = self._files_generator.get_verb_infinite_form(form)
        if self._has_noun(form):
            noun_singular_form = self._files_generator.get_noun_singular_form(form)
            return 'mkVpAction (mkVP (mkV2 (mkV "%s")) (mkNP (a_Det|the_Det) (mkCN (mkN "%s"))))' % (
                verb_infinitive_form, noun_singular_form
            )
        else:
            return 'mkVpAction "%s"' % verb_infinitive_form

    def _has_noun(self, form):
        return self.has_single_child_node(form, "noun")


class UserQuestionFunctionGenerator(FunctionGenerator):
    def __init__(self, rgl_gf_generator, predicate_name, form_parts):
        self._predicate_name = predicate_name
        self._form_parts = form_parts
        FunctionGenerator.__init__(self, rgl_gf_generator)

    def get_function_name(self):
        return self.generate_new_function_name("ask_%s" % self._predicate_name)

    def get_function_category(self):
        return 'UsrQuestion'

    def get_arguments(self):
        return [
            self.get_individual_argument(form_part) for form_part in self._form_parts if self.is_individual(form_part)
        ]

    def get_semantic_content(self):
        result = 'ask_whq %s' % self._predicate_name
        for sort in self._get_individual_sorts(self._form_parts):
            result += ' %s' % sort
        return result

    def _get_individual_sorts(self, form_parts):
        return [self.get_individual_sort(form_part) for form_part in form_parts if self.is_individual(form_part)]

    def get_natural_language_content(self):
        generated_parts = [self._generate_form_part(form_part) for form_part in self._form_parts]
        return 'mkUsr %s' % self.generate_gf_concatenation(generated_parts)

    def _generate_form_part(self, form_part):
        if self.is_individual(form_part):
            return '(mkUtt %s)' % self.get_individual_sort(form_part)
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException("expected an individual or a string but got %s" % form_part)


class RequestFunctionGenerator(FunctionGenerator):
    def __init__(self, files_generator, action, form_parts):
        self._action = action
        self._form_parts = form_parts
        FunctionGenerator.__init__(self, files_generator)

    def get_function_name(self):
        return self.generate_new_function_name("%s_request" % self._action)

    def get_function_category(self):
        return 'UsrRequest'

    def get_arguments(self):
        return [
            self.get_individual_argument(form_part) for form_part in self._form_parts if self.is_individual(form_part)
        ]

    def get_semantic_content(self):
        result = 'request (pp "%s")' % self._action
        for sort in self._get_individual_sorts(self._form_parts):
            result += ' %s' % sort
        return result

    def _get_individual_sorts(self, form_parts):
        return [self.get_individual_sort(form_part) for form_part in form_parts if self.is_individual(form_part)]

    def get_natural_language_content(self):
        generated_parts = [self._generate_form_part(form_part) for form_part in self._form_parts]
        return 'mkUsr %s' % self.generate_gf_concatenation(generated_parts)

    def _generate_form_part(self, form_part):
        if self.is_individual(form_part):
            return '(mkUtt %s)' % self.get_individual_sort(form_part)
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException("expected an individual or a string but got %s" % form_part)


class ReportFunctionGenerator(FunctionGenerator):
    def __init__(self, files_generator, action, form):
        FunctionGenerator.__init__(self, files_generator)
        self._action = action
        self._form_parts = self.get_utterance_content(form)

    def get_arguments(self):
        return [
            Argument(name=self.get_individual_predicate(form_part), category='SysAnswer')
            for form_part in self._form_parts if self.is_individual_with_predicate(form_part)
        ]

    def get_parameter_list(self):
        predicates = [
            self.get_individual_predicate(form_part) for form_part in self._form_parts
            if self.is_individual_with_predicate(form_part)
        ]
        return self.generate_list(predicates)

    def get_natural_language_content(self):
        generated_parts = [self._generate_form_part(form_part) for form_part in self._form_parts]
        return 'mkSys %s' % self.generate_gf_concatenation(generated_parts)

    def _generate_form_part(self, form_part):
        if self.is_individual_with_predicate(form_part):
            return self.get_individual_predicate(form_part)
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException(
                "expected an individual with a predicate or a string but got %s" % form_part
            )


class ReportEndedFunctionGenerator(ReportFunctionGenerator):
    def get_function_name(self):
        return 'report_ended_%s' % self._action

    def get_function_category(self):
        return 'SysReportEnded'

    def get_semantic_content(self):
        return 'report_ended "%s" %s' % (self._action, self.get_parameter_list())


class ReportStartedFunctionGenerator(ReportFunctionGenerator):
    def get_function_name(self):
        return 'report_started_%s' % self._action

    def get_function_category(self):
        return 'SysReportStarted'

    def get_semantic_content(self):
        return 'report_started "%s" %s' % (self._action, self.get_parameter_list())


class FunctionGeneratorForReportFailedWithUnknownFailure(FunctionGenerator):
    def __init__(self, files_generator, action, form):
        FunctionGenerator.__init__(self, files_generator)
        self._action = action
        self._form_parts = self.get_utterance_content(form)

    def get_function_name(self):
        return 'report_failed_%s_undefined_failure' % self._action

    def get_function_category(self):
        return 'SysReportFailed'

    def get_arguments(self):
        return [
            Argument(name=self.get_individual_predicate(form_part), category='SysAnswer')
            for form_part in self._form_parts if self.is_individual_with_predicate(form_part)
        ]

    def get_semantic_content(self):
        return 'report_failed "%s" %s "%s"' % (
            self._action, self._get_parameter_list(), UNDEFINED_SERVICE_ACTION_FAILURE
        )

    def _get_parameter_list(self):
        predicates = [
            self.get_individual_predicate(form_part) for form_part in self._form_parts
            if self.is_individual_with_predicate(form_part)
        ]
        return self.generate_list(predicates)

    def get_natural_language_content(self):
        return 'mkSys undefined_service_action_failure'


class FunctionGeneratorForSystemAnswerOfCustomSort(FunctionGenerator):
    def __init__(self, files_generator, predicate, form):
        FunctionGenerator.__init__(self, files_generator)
        self._predicate = predicate
        self._form = form

    def get_function_name(self):
        return '%s_sys_answer' % self._predicate.get_name()

    def _get_answer_argument(self):
        sort = self._predicate.getSort()
        argument_category = self.get_sort_category(sort.get_name())
        return Argument('individual', argument_category)

    def _is_individual_of_same_predicate_as_answer(self, form_part):
        return self.is_individual_with_predicate(form_part) and self.get_individual_predicate(
            form_part
        ) == self._predicate.get_name()


class FunctionGeneratorForSystemAnswerOfCustomSortWithoutBackground(FunctionGeneratorForSystemAnswerOfCustomSort):
    def __init__(self, files_generator, predicate, form):
        FunctionGeneratorForSystemAnswerOfCustomSort.__init__(self, files_generator, predicate, form)

    def get_function_category(self):
        return 'SysAnswer'

    def get_arguments(self):
        return [self._get_answer_argument()]

    def get_semantic_content(self):
        return 'pp "%s" individual' % self._predicate.get_name()

    def get_natural_language_content(self):
        if self._form is None:
            return self._default_natural_language_content()
        else:
            form_parts = self.get_utterance_content(self._form)
            generated_parts = [self._generate_form_part(form_part) for form_part in form_parts]
            return 'mkSysAnswer %s' % self.generate_gf_concatenation(generated_parts)

    def _default_natural_language_content(self):
        return 'mkSysAnswer individual'

    def _generate_form_part(self, form_part):
        if self._is_individual_of_same_predicate_as_answer(form_part):
            return '(mkUtt individual)'
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException(
                "expected individual of predicate %s or a string but got %r" % (self._predicate, form_part)
            )


class FunctionGeneratorForSystemAnswerOfCustomSortWithBackground(FunctionGeneratorForSystemAnswerOfCustomSort):
    def __init__(self, files_generator, predicate, form):
        FunctionGeneratorForSystemAnswerOfCustomSort.__init__(self, files_generator, predicate, form)
        self._background_predicates = self._get_background_predicates()

    def _get_background_predicates(self):
        form_parts = self.get_utterance_content(self._form)
        return [
            self.get_individual_predicate(form_part) for form_part in form_parts
            if self._is_background_individual(form_part)
        ]

    def _is_background_individual(self, form_part):
        return self.is_background_individual(form_part, self._predicate.get_name())

    def get_function_category(self):
        return 'System'

    def get_arguments(self):
        return [self._get_answer_argument()] + self._get_background_arguments()

    def _get_background_arguments(self):
        return [Argument(name=predicate, category='SysAnswer') for predicate in self._background_predicates]

    def get_semantic_content(self):
        return 'pp "Move" (move "answer" (pp "%s" individual) %s)' % (
            self._predicate.get_name(), self.generate_list(self._background_predicates)
        )

    def get_natural_language_content(self):
        form_parts = self.get_utterance_content(self._form)
        generated_parts = [self._generate_form_part(form_part) for form_part in form_parts]
        return 'mkSys %s' % self.generate_gf_concatenation(generated_parts)

    def _generate_form_part(self, form_part):
        if self._is_individual_of_same_predicate_as_answer(form_part):
            return '(mkUtt individual)'
        elif self._is_background_individual(form_part):
            return self.get_individual_predicate(form_part)
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException("expected individual or a string but got %r" % form_part)


class ValidityGenerator(GrammarProcessor, GfGenerator):
    def __init__(self, files_generator, validator_interface, forms):
        self._files_generator = files_generator
        self._validator_interface = validator_interface
        self._forms = forms

    def generate(self):
        for parameter_subset in self._get_parameter_subsets_for_validity():
            self._potentially_generate_function_for_parameter_subset(parameter_subset)

    def _get_parameter_subsets_for_validity(self):
        parameters = self._validator_interface.parameters
        for subset_size in range(1, len(parameters) + 1):
            for subset in itertools.combinations(parameters, subset_size):
                yield subset

    def _potentially_generate_function_for_parameter_subset(self, parameter_subset):
        form = self._get_form_for_parameter_subset(parameter_subset)
        if form:
            self._generate_function_for_parameter_subset(form, parameter_subset)

    def _generate_function_for_parameter_subset(self, form, parameter_subset):
        validity_name = self._validator_interface.name
        function_name = self._files_generator.generate_new_function_name(validity_name)
        parameter_names = [parameter.name for parameter in parameter_subset]
        semantic_content = 'rejectICM (set (list %s)) "%s"' % (' '.join(parameter_names), validity_name)
        natural_language_content = self._generate_natural_language_content(form)

        self._files_generator.write_function(
            function_name=function_name,
            category="SysICM",
            arguments=[Argument(parameter.name, "SysAnswer") for parameter in parameter_subset],
            semantic_content=semantic_content,
            natural_language_content=natural_language_content
        )

    def _generate_natural_language_content(self, form):
        form_parts = self.get_utterance_content(form)
        generated_parts = [self._generate_form_part(form_part) for form_part in form_parts]
        return 'mkSys %s' % self.generate_gf_concatenation(generated_parts)

    def _generate_form_part(self, form_part):
        if self.is_individual_with_predicate(form_part):
            return self.get_individual_predicate(form_part)
        elif self.is_string(form_part):
            return self.generate_string_as_utterance(form_part)
        else:
            raise GrammarProcessingException(
                "expected an individual with a predicate or a string but got %s" % form_part
            )

    def _get_form_for_parameter_subset(self, parameter_subset):
        for form in self._forms:
            if not self._form_contains_parameter_not_in_subset(form, parameter_subset):
                return form

    def _form_contains_parameter_not_in_subset(self, form, parameter_subset):
        parameter_names_in_form = set(self._parameters_in_form(form))
        parameter_names_in_subset = set([parameter.name for parameter in parameter_subset])
        parameters_in_form_but_not_in_subset = parameter_names_in_form.difference(parameter_names_in_subset)
        return len(parameters_in_form_but_not_in_subset) > 0

    def _parameters_in_form(self, form):
        parameter_names_in_device = [parameter.name for parameter in self._validator_interface.parameters]
        result = []
        for part in form.children:
            if self.is_individual_with_predicate(part):
                parameter_name = self.get_individual_predicate(part)
                if parameter_name in parameter_names_in_device:
                    result.append(parameter_name)
                else:
                    raise GrammarProcessingException(
                        "unexpected parameter name %s in form %s (device declares %s)" %
                        (parameter_name, form, parameter_names_in_device)
                    )
        return result


class Argument:
    def __init__(self, name, category):
        self.name = name
        self.category = category
