# -*- coding: utf-8 -*-
import pytest
from mock import Mock, patch

import tala.ddd.ddd_xml_compiler
from tala.ddd.ddd_xml_compiler import DddXmlCompiler, DddXmlCompilerException, ViolatesSchemaException, UnexpectedAttributeException
from tala.ddd.parser import Parser
from tala.ddd.services.service_interface import ServiceParameter, ServiceActionInterface, ServiceEntityRecognizerInterface, ServiceQueryInterface, ServiceValidatorInterface, FrontendTarget, DeviceModuleTarget, HttpTarget, ServiceInterface, ActionFailureReason, PlayAudioActionInterface, AudioURLServiceParameter
from tala.ddd.test.ddd_compiler_test_case import DddCompilerTestCase
from tala.model.device import ParameterField
from tala.model.domain import Domain
from tala.model.ontology import Ontology
from tala.model.plan import Plan
from tala.model.plan_item import IfThenElse, ForgetAllPlanItem, InvokeServiceQueryPlanItem, InvokeServiceActionPlanItem
from tala.model.predicate import Predicate
from tala.model.sort import CustomSort, RealSort, UndefinedSort
from tala.nl.gf import rgl_grammar_entry_types as rgl_types
from tala.nl.gf.grammar_entry_types import Node, Constants


class DddXmlCompilerTestCase(DddCompilerTestCase):
    def _given_compiled_ontology(
        self, xml='<ontology name="MockupOntology"/>', domain_name="Domain", ddd_name="mock_ddd"
    ):
        self._ddd_name = ddd_name
        ontology_args = DddXmlCompiler().compile_ontology(xml)
        self._ontology = Ontology(**ontology_args)
        self._parser = Parser(self._ddd_name, self._ontology, domain_name)
        self._service_interface = Mock(spec=ServiceInterface)

    def _when_compile_ontology(self, ontology_xml):
        self._compile_ontology(ontology_xml)

    def _compile_ontology(self, ontology_xml):
        self._result = DddXmlCompiler().compile_ontology(ontology_xml)
        self._ontology = Ontology(**self._result)

    def _predicate(self, *args, **kwargs):
        return Predicate(self._ontology.name, *args, **kwargs)

    def _when_compile_ontology_then_exception_is_raised(self, ontolog_xml, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._compile_ontology(ontolog_xml)

    def _when_compile_domain(self, domain_xml='<domain name="Domain" />'):
        self._result = DddXmlCompiler().compile_domain(
            self._ddd_name, domain_xml, self._ontology, self._parser, self._service_interface
        )

    def _when_compile_domain_with_plan(self, plan_xml):
        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="top">
    <plan>%s</plan>
  </goal>
</domain>""" % plan_xml
        )

    def _when_compile_plan_with_attribute(self, key, value):
        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="top" %s="%s" />
</domain>""" % (key, value)
        )

    def _when_compile_plan_with_content(self, xml):
        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="top">%s</goal>
</domain>""" % xml
        )

    def _then_result_has_keys(self, expected_keys):
        self.assertItemsEqual(expected_keys, self._result.keys())

    def _then_result_has_field(self, expected_key, expected_value):
        assert expected_value == self._result[expected_key]

    def _then_result_has_plan(self, expected_plan):
        actual_plans = self._result["plans"]
        actual_plan = actual_plans[0]["plan"]
        assert expected_plan == actual_plan

    def _then_result_has_plan_with_attribute(self, expected_key, expected_value):
        actual_plans = self._result["plans"]
        actual_plan = actual_plans[0]
        assert expected_value == actual_plan[expected_key]

    def _parse(self, string):
        return self._parser.parse(string)

    def _when_compile_grammar(self, *args):
        self._compile_grammar(*args)

    def _compile_grammar(self, string):
        self._result = DddXmlCompiler().compile_grammar(string, self._ontology, self._device_handler, "eng")

    def _when_compile_rgl_grammar(self, string):
        self._result = DddXmlCompiler().compile_rgl_grammar(string, self._ontology, self._service_interface, "eng")

    def _then_result_is(self, expected_result):
        assert expected_result == self._result

    def _then_grammar_is(self, expected_grammar_children):
        expected_grammar_node = Node(Constants.GRAMMAR, {}, expected_grammar_children)
        assert expected_grammar_node == self._result

    def _mock_warnings(self):
        return patch("%s.warnings" % tala.ddd.ddd_xml_compiler.__name__)

    def _then_warning_is_issued(self, mocked_warnings, expected_message):
        mocked_warnings.warn.assert_called_once_with(expected_message)


class TestOntologyCompiler(DddXmlCompilerTestCase):
    def test_name(self):
        self._when_compile_ontology('<ontology name="MockupOntology"/>')
        self._then_result_has_field("name", "MockupOntology")

    def test_custom_sort(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <sort name="city"/>
</ontology>""")
        self._then_result_has_field("sorts", set([CustomSort(self._ontology.name, "city")]))

    def test_dynamic_sort(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <sort name="city" dynamic="true"/>
</ontology>""")
        self._then_result_has_field("sorts", set([CustomSort(self._ontology.name, "city", dynamic=True)]))

    def test_predicate_of_custom_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates", set([self._predicate("dest_city", CustomSort(self._ontology.name, "city"))])
        )

    def test_predicate_of_builtin_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._then_result_has_field("predicates", set([self._predicate("price", RealSort())]))

    def test_predicate_of_dynamic_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city" dynamic="true"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates", set([self._predicate("dest_city", CustomSort(self._ontology.name, "city", dynamic=True))])
        )

    def test_feature_of(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
  <predicate name="dest_city_type" sort="city" feature_of="dest_city"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates",
            set([
                self._predicate("dest_city", sort=CustomSort(self._ontology.name, "city")),
                self._predicate(
                    "dest_city_type", sort=CustomSort(self._ontology.name, "city"), feature_of_name="dest_city"
                )
            ])
        )

    def test_multiple_instances(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city" multiple_instances="true"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates",
            set([self._predicate("dest_city", sort=CustomSort(self._ontology.name, "city"), multiple_instances=True)])
        )

    def test_individuals(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._then_result_has_field("individuals", {"paris": CustomSort(self._ontology.name, "city")})

    def test_actions(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")
        self._then_result_has_field("actions", set(["buy"]))

    def test_exception_for_undefined_sort_in_predicate(self):
        self._when_compile_ontology_then_exception_is_raised(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="undefined_sort"/>
</ontology>""", UndefinedSort, "Expected a defined sort but got 'undefined_sort'."
        )


class TestPlanCompilation(DddXmlCompilerTestCase):
    def test_plan_for_perform_goal(self):
        self._given_compiled_ontology()

        self._when_compile_domain("""
<domain name="Domain">
  <goal type="perform" action="top" />
</domain>""")

        self._then_result_has_field("plans", [{"goal": self._parse("perform(top)"), "plan": Plan([])}])

    def test_plan_for_resolve_goal_for_wh_question(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="resolve" question_type="wh_question" predicate="price" />
</domain>"""
        )

        self._then_result_has_field("plans", [{"goal": self._parse("resolve(?X.price(X))"), "plan": Plan([])}])

    def test_plan_for_resolve_goal_for_nullary_predicate_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="need_visa" sort="boolean"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="resolve" question_type="yn_question">
    <proposition predicate="need_visa"/>
  </goal>
</domain>"""
        )

        self._then_result_has_field("plans", [{"goal": self._parse("resolve(?need_visa())"), "plan": Plan([])}])

    def test_plan_for_handle_goal(self):
        self._given_compiled_ontology()

        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="handle" action="MockupAction" />
</domain>"""
        )

        self._then_result_has_field("plans", [{"goal": self._parse("handle(MockupAction)"), "plan": Plan([])}])

    def test_exception_raised_for_goal_without_type(self):
        self._given_compiled_ontology()

        with pytest.raises(DddXmlCompilerException):
            self._when_compile_domain("""
<domain name="Domain">
  <goal />
</domain>""")

    def test_plan_stack_order(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="city"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<findout type="wh_question" predicate="means_of_transport" />
<findout type="wh_question" predicate="dest_city" />"""
        )

        self._then_result_has_plan(
            Plan([self._parse("findout(?X.dest_city(X))"),
                  self._parse("findout(?X.means_of_transport(X))")])
        )

    def test_preferred_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_plan_with_content(
            """
<preferred>
  <proposition predicate="dest_city" value="paris"/>
</preferred>
"""
        )
        self._then_result_has_plan_with_attribute("preferred", self._parse("dest_city(paris)"))

    def test_preferred_boolean(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <action name="apply_for_membership"/>
</ontology>"""
        )
        self._when_compile_plan_with_content("""
<preferred/>
""")
        self._then_result_has_plan_with_attribute("preferred", True)

    def test_accommodate_without_feedback(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("accommodate_without_feedback", "true")
        self._then_result_has_plan_with_attribute("accommodate_without_feedback", True)

    def test_dynamic_title(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("dynamic_title", "true")
        self._then_result_has_plan_with_attribute("dynamic_title", True)

    def test_restart_on_completion(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("restart_on_completion", "true")
        self._then_result_has_plan_with_attribute("restart_on_completion", True)

    def test_reraise_on_resume(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("reraise_on_resume", "true")
        self._then_result_has_plan_with_attribute("reraise_on_resume", True)

    def test_io_status(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("io_status", "disabled")
        self._then_result_has_plan_with_attribute("io_status", Domain.DISABLED_IO_STATUS)

    def test_gui_context(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_plan_with_content('<gui_context predicate="price" />')
        self._then_result_has_plan_with_attribute("gui_context", [self._ontology.get_predicate("price")])

    def test_postplan(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_content('<postplan><forget_all/></postplan>')
        self._then_result_has_plan_with_attribute("postplan", Plan([ForgetAllPlanItem()]))

    def test_postcond_with_whitespace(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_plan_with_content(
            """
<postcond>
  <proposition predicate="dest_city" value="paris"/>
</postcond>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [self._parse("dest_city(paris)")])

    def test_postcond_for_predicate_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_plan_with_content('<postcond><proposition predicate="dest_city" value="paris"/></postcond>')
        self._then_result_has_plan_with_attribute("postconds", [self._parse("dest_city(paris)")])


class TestDomainCompiler(DddXmlCompilerTestCase):
    def test_name(self):
        self._given_compiled_ontology()
        self._when_compile_domain()
        self._then_result_has_field("name", "Domain")

    def test_dependency(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <sort name="country"/>
  <predicate name="dest_city" sort="city"/>
  <predicate name="dest_country" sort="country"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <dependency type="wh_question" predicate="dest_country">
    <question type="wh_question" predicate="dest_city" />
  </dependency>
</domain>"""
        )

        self._then_result_has_field(
            "dependencies", {self._parse("?X.dest_country(X)"): set([self._parse("?X.dest_city(X)")])}
        )

    def test_default_questions(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <default_question type="wh_question" predicate="price" />
</domain>"""
        )

        self._then_result_has_field("default_questions", [self._parse("?X.price(X)")])

    def test_superactions(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <action name="top"/>
  <action name="buy"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="top" />
  <goal type="perform" action="buy">
    <superaction name="top" />
  </goal>
</domain>"""
        )

        self._then_result_has_field(
            "plans", [{
                "goal": self._parse("perform(top)"),
                "plan": Plan([])
            }, {
                "goal": self._parse("perform(buy)"),
                "plan": Plan([]),
                "superactions": [self._parse("top")]
            }]
        )

    def test_parameters(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price" graphical_type="list" />
</domain>"""
        )

        self._then_result_has_field("parameters", {self._parse("?X.price(X)"): {"graphical_type": "list"}})

    def test_schema_violation_yields_exception(self):
        self._given_compiled_ontology('<ontology name="Ontology"/>')
        self._when_compile_domain_then_exception_is_raised_matching(
            '<domain name="Domain">invalid_content</domain>',
            ViolatesSchemaException,
            "Expected domain.xml compliant with schema but it's in violation: "
            "Element 'domain': Character content other than whitespace is not allowed because the content type is "
            "'element-only'., line 1")

    def _when_compile_domain_then_exception_is_raised_matching(self, xml, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._when_compile_domain(xml)


class TestParameterCompilation(DddXmlCompilerTestCase):
    def test_choice_parameter(self):
        self._given_compiled_ontology()
        self._when_compile_parameter_for_question("graphical_type", "list")
        self._then_result_has_parameter_for_question("graphical_type", "list")

    def test_boolean_parameter(self):
        self._given_compiled_ontology()
        self._when_compile_parameter_for_question("incremental", "true")
        self._then_result_has_parameter_for_question("incremental", True)

    def test_question_valued_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="available_means_of_transport" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="means_of_transport">
    <service_query type="wh_question" predicate="available_means_of_transport"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.means_of_transport(X)"):
                self._parser.parse_parameters("{service_query=?X.available_means_of_transport(X)}")
            }
        )

    def test_questions_valued_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="product"/>
  <predicate name="product_to_add" sort="product"/>
  <predicate name="product_tag" sort="string"/>
  <predicate name="product_title" sort="string"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="product_to_add">
    <label_question type="wh_question" predicate="product_tag"/>
    <label_question type="wh_question" predicate="product_title"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.product_to_add(X)"):
                self._parser.parse_parameters("{label_questions=[?X.product_tag(X), ?X.product_title(X)]}")
            }
        )

    def test_background_for_wh_question(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="city"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="means_of_transport">
    <background predicate="dest_city"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?X.means_of_transport(X)"): self._parser.parse_parameters("{background=[dest_city]}")}
        )

    def test_background_for_yn_question_for_perform_goal(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="price" sort="real"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="yn_question">
    <perform action="top"/>
    <background predicate="dest_city"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?goal(perform(top))"): self._parser.parse_parameters("{background=[dest_city]}")}
        )

    def test_background_for_yn_question_for_resolve_goal(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="price" sort="real"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="yn_question">
    <resolve type="wh_question" predicate="price"/>
    <background predicate="dest_city"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?goal(resolve(?X.price(X)))"): self._parser.parse_parameters("{background=[dest_city]}")}
        )

    def test_ask_feature(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
  <predicate name="dest_city_type" sort="city" feature_of="dest_city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="dest_city">
    <ask_feature predicate="dest_city_type"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?X.dest_city(X)"): self._parser.parse_parameters("{ask_features=[dest_city_type]}")}
        )

    def test_predicate_alts_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <individual name="bus" sort="how"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="means_of_transport">
    <alt><proposition predicate="means_of_transport" value="bus"/></alt>
    <alt><proposition predicate="means_of_transport" value="train"/></alt>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.means_of_transport(X)"):
                self._parser.parse_parameters("{alts=set([means_of_transport(bus), means_of_transport(train)])}")
            }
        )

    def test_empty_alt_yields_exception(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
</ontology>"""
        )

        with pytest.raises(DddXmlCompilerException):
            self._when_compile_domain(
                """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="means_of_transport">
    <alt/>
  </parameters>
</domain>"""
            )

    def test_goal_alts_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
  <action name="buy"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="goal">
    <alt><perform action="buy"/></alt>
    <alt><resolve type="wh_question" predicate="price"/></alt>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.goal(X)"):
                self._parser.parse_parameters("{alts=set([goal(perform(buy)), goal(resolve(?X.price(X)))])}")
            }
        )

    def test_parameters_for_predicate(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
  <predicate name="dest_city" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price">
    <related_information type="wh_question" predicate="dest_city"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?X.price(X)"): self._parser.parse_parameters("{related_information=[?X.dest_city(X)]}")}
        )

    def _given_compiled_ontology(self, xml=None):
        if xml is None:
            xml = """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        DddXmlCompilerTestCase._given_compiled_ontology(self, xml)

    def _when_compile_parameter_for_question(self, name, value):
        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price" %s="%s" />
</domain>""" % (name, value)
        )

    def _then_result_has_parameter_for_question(self, expected_name, expected_value):
        self._then_result_has_field("parameters", {self._parse("?X.price(X)"): {expected_name: expected_value}})


class TestPlanItemCompilation(DddXmlCompilerTestCase):
    ELEMENT_NAMES_FOR_QUESTION_RAISING_PLAN_ITEMS = ["findout", "raise", "bind"]

    @pytest.mark.parametrize("element_name", ELEMENT_NAMES_FOR_QUESTION_RAISING_PLAN_ITEMS)
    def test_question_raising_plan_item_for_wh_question(self, element_name):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan('<%s type="wh_question" predicate="means_of_transport" />' % element_name)

        self._then_result_has_plan(Plan([self._parse("%s(?X.means_of_transport(X))" % element_name)]))

    @pytest.mark.parametrize("element_name", ELEMENT_NAMES_FOR_QUESTION_RAISING_PLAN_ITEMS)
    def test_question_raising_plan_item_for_goal_alt_question(self, element_name):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <action name="action1"/>
  <action name="action2"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<{element_name} type="alt_question">
  <alt><perform action="action1"/></alt>
  <alt><perform action="action2"/></alt>
</{element_name}>""".format(element_name=element_name)
        )

        self._then_result_has_plan(
            Plan([self._parse("%s(?set([goal(perform(action1)), goal(perform(action2))]))" % element_name)])
        )

    @pytest.mark.parametrize("element_name", ELEMENT_NAMES_FOR_QUESTION_RAISING_PLAN_ITEMS)
    def test_question_raising_plan_item_for_yn_question_for_goal_proposition(self, element_name):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<{element_name} type="yn_question">
  <resolve type="wh_question" predicate="price"/>
</{element_name}>""".format(element_name=element_name)
        )

        self._then_result_has_plan(Plan([self._parse("%s(?goal(resolve(?X.price(X))))" % element_name)]))

    @pytest.mark.parametrize("element_name", ELEMENT_NAMES_FOR_QUESTION_RAISING_PLAN_ITEMS)
    def test_question_raising_plan_item_for_yn_question_for_goal_proposition_perform(self, element_name):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <action name="apply_for_membership"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<{element_name} type="yn_question">
  <perform action="apply_for_membership"/>
</{element_name}>""".format(element_name=element_name)
        )

        self._then_result_has_plan(Plan([self._parse("%s(?goal(perform(apply_for_membership)))" % element_name)]))

    def test_if_then_else(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<if>
  <condition><proposition predicate="means_of_transport" value="train"/></condition>
  <then>
    <findout type="wh_question" predicate="transport_train_type" />
  </then>
  <else />
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    self._parse("means_of_transport(train)"), self._parse("findout(?X.transport_train_type(X))"), None
                )
            ])
        )

    def test_forget_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            '<forget><proposition predicate="means_of_transport" value="train"/></forget>'
        )

        self._then_result_has_plan(Plan([self._parse("forget(means_of_transport(train))")]))

    def test_forget_predicate(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan('<forget predicate="means_of_transport"/>')

        self._then_result_has_plan(Plan([self._parse("forget(means_of_transport)")]))

    def test_forget_all(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<forget_all />')
        self._then_result_has_plan(Plan([ForgetAllPlanItem()]))

    def test_invoke_service_query(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<invoke_service_query type="wh_question" predicate="price"/>')
        self._then_result_has_plan(
            Plan([InvokeServiceQueryPlanItem(self._parse("?X.price(X)"), min_results=1, max_results=1)])
        )

    def test_invoke_service_action_with_device_attribute(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<invoke_service_action device="MockupDevice" name="MockupAction" />', UnexpectedAttributeException,
            "Attribute 'device=\"MockupDevice\"' is not supported in <invoke_service_action name='MockupAction'>. "
            "Use 'service_interface.xml' instead."
        )

    def test_invoke_service_query_with_device_attribute(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<invoke_service_query type="wh_question" predicate="dest_city" device="MockupDevice"/>',
            UnexpectedAttributeException, "Attribute 'device=\"MockupDevice\"' is not supported in "
            "<invoke_service_query ... predicate='dest_city'>. Use 'service_interface.xml' instead."
        )

    def _when_compile_domain_with_plan_then_exception_is_raised_matching(
        self, plan_xml, expected_exception, expected_message
    ):
        with pytest.raises(expected_exception, match=expected_message):
            self._when_compile_domain_with_plan(plan_xml)

    def test_dev_query_deprecation_warning(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan_then_deprecation_warning_is_issued(
            '<dev_query type="wh_question" predicate="price" />',
            '<dev_query> is deprecated. Use <invoke_service_query> instead.'
        )

    def test_deprecated_dev_query(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan_ignoring_warnings('<dev_query type="wh_question" predicate="price" />')
        self._then_result_has_plan(
            Plan([InvokeServiceQueryPlanItem(self._parse("?X.price(X)"), min_results=1, max_results=1)])
        )

    def _when_compile_domain_with_plan_and_ignoring_warnings_then_exception_is_raised_matching(self, *args, **kwargs):
        with self._mock_warnings():
            self._when_compile_domain_with_plan_then_exception_is_raised_matching(*args, **kwargs)

    def test_invoke_service_action_default_attributes(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<invoke_service_action name="MockupAction" />')
        self._then_result_has_plan(Plan([InvokeServiceActionPlanItem("MockupOntology", "MockupAction")]))

    def test_invoke_service_action_override_preconfirm(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan(
            """
          <invoke_service_action name="MockupAction" preconfirm="assertive" />"""
        )
        self._then_result_has_plan(
            Plan([
                InvokeServiceActionPlanItem(
                    u"MockupOntology", u"MockupAction", preconfirm=InvokeServiceActionPlanItem.ASSERTIVE
                )
            ])
        )

    def test_invoke_service_action_override_postconfirm(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<invoke_service_action name="MockupAction" postconfirm="true" />')
        self._then_result_has_plan(
            Plan([InvokeServiceActionPlanItem("MockupOntology", "MockupAction", postconfirm=True)])
        )

    def test_invoke_service_action_override_downdate_plan(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan(
            """
          <invoke_service_action name="MockupAction" downdate_plan="false" />"""
        )
        self._then_result_has_plan(
            Plan([InvokeServiceActionPlanItem("MockupOntology", "MockupAction", downdate_plan=False)])
        )

    def test_deprecated_dev_perform_default_attributes(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_ignoring_warnings('<dev_perform action="MockupAction" />')
        self._then_result_has_plan(Plan([InvokeServiceActionPlanItem("MockupOntology", "MockupAction")]))

    def _when_compile_domain_with_plan_ignoring_warnings(self, plan_xml):
        with self._mock_warnings():
            self._when_compile_domain_with_plan(plan_xml)

    def test_deprecated_dev_perform_override_preconfirm(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_ignoring_warnings(
            """
          <dev_perform action="MockupAction" preconfirm="assertive" />"""
        )
        self._then_result_has_plan(
            Plan([
                InvokeServiceActionPlanItem(
                    "MockupOntology", "MockupAction", preconfirm=InvokeServiceActionPlanItem.ASSERTIVE
                )
            ])
        )

    def test_deprecated_dev_perform_override_postconfirm(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_ignoring_warnings(
            '<dev_perform action="MockupAction" postconfirm="true" />'
        )
        self._then_result_has_plan(
            Plan([InvokeServiceActionPlanItem("MockupOntology", "MockupAction", postconfirm=True)])
        )

    def test_dev_perform_deprecation_warning(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_then_deprecation_warning_is_issued(
            '<dev_perform action="MockupAction" />', "<dev_perform> is deprecated. Use <invoke_service_action> instead."
        )

    def _when_compile_domain_with_plan_then_deprecation_warning_is_issued(self, plan_xml, expected_warning_message):
        with self._mock_warnings() as mocked_warnings:
            self._when_compile_domain_with_plan(plan_xml)
            self._then_warning_is_issued(mocked_warnings, expected_warning_message)

    def test_jumpto(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<jumpto type="perform" action="top"/>')
        self._then_result_has_plan(Plan([self._parser.parse("jumpto(perform(top))")]))

    def test_assume_shared(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<assume_shared>
  <proposition predicate="price" value="123.0"/>
</assume_shared>"""
        )
        self._then_result_has_plan(Plan([self._parser.parse("assume_shared(price(123.0))")]))


class TestGrammarCompiler(DddXmlCompilerTestCase):
    def test_multiple_variants(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")

        self._when_compile_grammar(
            """
<grammar>
  <action name="buy">
    <one-of>
      <item>buy</item>
      <item>purchase</item>
    </one-of>
  </action>
</grammar>
"""
        )

        self._then_result_is(
            Node(
                Constants.GRAMMAR, {}, [
                    Node(
                        Constants.ACTION, {"name": "buy"}, [
                            Node(
                                Constants.ONE_OF, {},
                                [Node(Constants.ITEM, {}, ["buy"]),
                                 Node(Constants.ITEM, {}, ["purchase"])]
                            )
                        ]
                    )
                ]
            )
        )

    def test_action(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")

        self._when_compile_grammar("""
<grammar>
  <action name="buy">purchase</action>
</grammar>
""")

        self._then_grammar_is([Node(Constants.ACTION, {"name": "buy"}, [Node(Constants.ITEM, {}, ["purchase"])])])

    def test_predicate_explicit_speaker(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_grammar(
            """
<grammar>
  <question predicate="price" speaker="all">price information</question>
</grammar>"""
        )

        self._then_grammar_is([
            Node(Constants.PREDICATE, {"name": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_predicate_implicit_speaker(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_grammar(
            """
<grammar>
  <question predicate="price">price information</question>
</grammar>"""
        )

        self._then_grammar_is([
            Node(Constants.PREDICATE, {"name": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_user_question(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_grammar(
            """
<grammar>
  <question predicate="price" speaker="user">price for travelling to <slot sort="city"/>
  </question>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.USER_QUESTION, {"predicate": "price"},
                [Node(Constants.ITEM, {},
                      ["price for travelling to ", Node(Constants.SLOT, {"sort": "city"})])]
            )
        ])

    def test_system_question(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_grammar(
            """
<grammar>
  <question predicate="dest_city" speaker="system">where do you want to go</question>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.SYS_QUESTION, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, ["where do you want to go"])]
            )
        ])

    def test_english_noun_phrase_as_single_variant(self):
        self._given_compiled_ontology()
        self._when_compile_grammar(
            """
<grammar>
  <action name="top">
    <np>
      <indefinite>start view</indefinite>
      <definite>the start view</definite>
    </np>
  </action>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"}, [
                    Node(
                        Constants.NP, {}, [
                            Node(Constants.INDEFINITE, {}, ["start view"]),
                            Node(Constants.DEFINITE, {}, ["the start view"])
                        ]
                    )
                ]
            )
        ])

    def test_english_noun_phrase_among_multiple_variants(self):
        self._given_compiled_ontology()
        self._when_compile_grammar(
            """
<grammar>
  <action name="top">
    <one-of>
      <item>
        <np>
          <indefinite>start view</indefinite>
          <definite>the start view</definite>
        </np>
      </item>
      <item>main menu</item>
    </one-of>
  </action>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    Node(
                                        Constants.NP, {}, [
                                            Node(Constants.INDEFINITE, {}, ["start view"]),
                                            Node(Constants.DEFINITE, {}, ["the start view"])
                                        ]
                                    )
                                ]
                            ),
                            Node(Constants.ITEM, {}, ["main menu"])
                        ]
                    )
                ]
            )
        ])

    def test_english_verb_phrase_as_single_variant(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")
        self._when_compile_grammar(
            """
<grammar>
  <action name="buy">
    <vp>
      <infinitive>buy</infinitive>
      <imperative>buy</imperative>
      <ing-form>buying</ing-form>
      <object>a ticket</object>
    </vp>
  </action>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"}, [
                    Node(
                        Constants.VP, {}, [
                            Node(Constants.INFINITIVE, {}, ["buy"]),
                            Node(Constants.IMPERATIVE, {}, ["buy"]),
                            Node(Constants.ING_FORM, {}, ["buying"]),
                            Node(Constants.OBJECT, {}, ["a ticket"])
                        ]
                    )
                ]
            )
        ])

    def test_english_verb_phrase_among_multiple_variants(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")
        self._when_compile_grammar(
            """
<grammar>
  <action name="buy">
    <one-of>
      <item>
        <vp>
          <infinitive>buy</infinitive>
          <imperative>buy</imperative>
          <ing-form>buying</ing-form>
          <object>a ticket</object>
        </vp>
      </item>
      <item>purchase</item>
    </one-of>
  </action>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    Node(
                                        Constants.VP, {}, [
                                            Node(Constants.INFINITIVE, {}, ["buy"]),
                                            Node(Constants.IMPERATIVE, {}, ["buy"]),
                                            Node(Constants.ING_FORM, {}, ["buying"]),
                                            Node(Constants.OBJECT, {}, ["a ticket"])
                                        ]
                                    )
                                ]
                            ),
                            Node(Constants.ITEM, {}, ["purchase"])
                        ]
                    )
                ]
            )
        ])

    def test_swedish_verb_phrase(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")
        self._when_compile_grammar(
            """
<grammar>
  <action name="buy">
    <vp>
      <infinitive>köpa</infinitive>
      <imperative>köp</imperative>
      <ing-form>köper</ing-form>
      <object>en biljett</object>
    </vp>
  </action>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"}, [
                    Node(
                        Constants.VP, {}, [
                            Node(Constants.INFINITIVE, {}, [u"köpa"]),
                            Node(Constants.IMPERATIVE, {}, [u"köp"]),
                            Node(Constants.ING_FORM, {}, [u"köper"]),
                            Node(Constants.OBJECT, {}, [u"en biljett"])
                        ]
                    )
                ]
            )
        ])

    def test_spanish_verb_phrase(self):
        self._given_compiled_ontology("""
    <ontology name="Ontology">
      <action name="buy"/>
    </ontology>""")
        self._when_compile_grammar(
            """
    <grammar>
      <action name="buy">
        <vp>
          <infinitive>comprar</infinitive>
          <imperative>compra</imperative>
          <ing-form>comprando</ing-form>
          <object>un billete</object>
        </vp>
      </action>
    </grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"}, [
                    Node(
                        Constants.VP, {}, [
                            Node(Constants.INFINITIVE, {}, ["comprar"]),
                            Node(Constants.IMPERATIVE, {}, ["compra"]),
                            Node(Constants.ING_FORM, {}, ["comprando"]),
                            Node(Constants.OBJECT, {}, ["un billete"])
                        ]
                    )
                ]
            )
        ])

    def test_answer_combination(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dept_city" sort="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="user">
    <one-of>
      <item>
        from <slot type="individual" predicate="dept_city" /> to <slot type="individual" predicate="dest_city" />
      </item>
      <item>
        from <slot type="individual" predicate="dept_city" />
      </item>
    </one-of>
  </answer>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.ANSWER_COMBINATION, {}, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {}, [
                                    "from ",
                                    Node(Constants.SLOT, {"predicate": "dept_city"}), " to ",
                                    Node(Constants.SLOT, {"predicate": "dest_city"})
                                ]
                            ),
                            Node(Constants.ITEM, {},
                                 ["from ", Node(Constants.SLOT, {"predicate": "dept_city"})])
                        ]
                    )
                ]
            )
        ])

    def test_report_started(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_grammar(
            """
<grammar>
  <report action="IncomingCall" status="started">incoming call</report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(Constants.REPORT_STARTED, {"action": "IncomingCall"}, [Node(Constants.ITEM, {}, ["incoming call"])])
        ])

    def test_report_ended(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_grammar(
            """
<grammar>
  <report action="IncomingCall" status="ended">call ended</report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(Constants.REPORT_ENDED, {"action": "IncomingCall"}, [Node(Constants.ITEM, {}, ["call ended"])])
        ])

    def test_action_with_empty_string(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_grammar(
            """
<grammar>
  <report action="IncomingCall" status="ended">
  </report>
</grammar>"""
        )
        self._then_grammar_is([Node(Constants.REPORT_ENDED, {"action": "IncomingCall"}, [None])])

    def test_report_failed(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("CancelReservation")
        self._when_compile_grammar(
            """
<grammar>
  <report action="CancelReservation" status="failed" reason="no_reservation_exists">there is no reservation</report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.REPORT_FAILED, {
                    "action": "CancelReservation",
                    "reason": "no_reservation_exists"
                }, [Node(Constants.ITEM, {}, ["there is no reservation"])]
            )
        ])

    def test_individual(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <individual name="city1" sort="city"/>
</ontology>"""
        )
        self._when_compile_grammar("""
<grammar>
  <individual name="city_1">paris</individual>
</grammar>""")
        self._then_grammar_is([Node(Constants.INDIVIDUAL, {"name": "city_1"}, [Node(Constants.ITEM, {}, ["paris"])])])

    def test_system_answer(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="system">to <slot type="individual" predicate="dest_city"/></answer>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, ["to ", Node(Constants.SLOT, {})])]
            )
        ])

    def test_system_answer_with_embedded_answer(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="system" predicate="price">
    the price to <slot type="individual" predicate="dest_city"/> is <slot type="individual" predicate="price"/>
  </answer>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.SYS_ANSWER, {"predicate": "price"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "the price to ",
                            Node(Constants.SLOT, {"predicate": "dest_city"}), " is ",
                            Node(Constants.SLOT, {})
                        ]
                    )
                ]
            )
        ])

    def test_positive_system_answer(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="qualified" sort="boolean"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="system" predicate="qualified" polarity="positive">you are qualified</answer>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified"},
                [Node(Constants.ITEM, {}, ["you are qualified"])]
            )
        ])

    def test_negative_system_answer(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="qualified" sort="boolean"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="system" predicate="qualified" polarity="negative">you are not qualified</answer>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.NEGATIVE_SYS_ANSWER, {"predicate": "qualified"},
                [Node(Constants.ITEM, {}, ["you are not qualified"])]
            )
        ])

    def test_action_title(self):
        self._given_compiled_ontology()
        self._when_compile_grammar("""
<grammar>
  <title type="action" action="top">main menu</title>
</grammar>""")
        self._then_grammar_is([
            Node(Constants.ACTION_TITLE, {"action": "top"}, [Node(Constants.ITEM, {}, ["main menu"])])
        ])

    def test_issue_title(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <title type="question" predicate="price">price information</title>
</grammar>"""
        )
        self._then_grammar_is([
            Node(Constants.ISSUE_TITLE, {"predicate": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_validity(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )
        self._given_service_interface_with_validity("CityValidity")
        self._when_compile_grammar(
            """
<grammar>
  <validity name="CityValidity">
    invalid city <slot type="individual" predicate="dest_city" />
  </validity>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.VALIDITY, {"name": "CityValidity"},
                [Node(Constants.ITEM, {},
                      ["invalid city ", Node(Constants.SLOT, {"predicate": "dest_city"})])]
            )
        ])

    def test_prereport(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("MakeReservation")
        self._when_compile_grammar(
            """
<grammar>
  <report action="MakeReservation" status="started" source="dialogue">making the reservation</report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.PREREPORT, {"action": "MakeReservation"},
                [Node(Constants.ITEM, {}, ["making the reservation"])]
            )
        ])

    def test_preconfirm(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("MakeReservation")
        self._when_compile_grammar(
            """
<grammar>
  <preconfirm action="MakeReservation">would you like to make the reservation</preconfirm>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.PRECONFIRM, {"action": "MakeReservation"},
                [Node(Constants.ITEM, {}, ["would you like to make the reservation"])]
            )
        ])

    def test_greeting(self):
        self._given_compiled_ontology()
        self._when_compile_grammar("""
<grammar>
  <greeting>Welcome</greeting>
</grammar>""")
        self._then_grammar_is([Node(Constants.GREETING, {}, [Node(Constants.ITEM, {}, ["Welcome"])])])

    def test_whitespacing_for_trailing_text_node(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <answer speaker="system">
    <slot type="individual" predicate="dest_city"/> as destination
  </answer>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, [Node(Constants.SLOT, {}), " as destination"])]
            )
        ])

    def test_whitespacing_between_slots(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="alarm_hour" sort="integer"/>
  <predicate name="alarm_minute" sort="integer"/>
</ontology>"""
        )
        self._when_compile_grammar(
            """
<grammar>
  <report action="AlarmRings" status="started">
    the time is <slot type="individual" predicate="alarm_hour"/> <slot type="individual" predicate="alarm_minute"/>
  </report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(
                Constants.REPORT_STARTED, {"action": "AlarmRings"}, [
                    Node(
                        Constants.ITEM, {}, [
                            "the time is ",
                            Node(Constants.SLOT, {"predicate": "alarm_hour"}), " ",
                            Node(Constants.SLOT, {"predicate": "alarm_minute"})
                        ]
                    )
                ]
            )
        ])

    def test_unexpected_element_yields_exception(self):
        self._given_compiled_ontology()
        with pytest.raises(ViolatesSchemaException):
            self._when_compile_grammar("""
<grammar>
  <unexpected_element/>
</grammar>""")

    def test_tolerate_comment(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")

        self._when_compile_grammar(
            """
<grammar>
  <action name="buy">purchase</action>
  <!-- this is a comment -->
</grammar>
"""
        )

        self._then_grammar_is([Node(Constants.ACTION, {"name": "buy"}, [Node(Constants.ITEM, {}, ["purchase"])])])

    def setup(self):
        super(TestGrammarCompiler, self).setup()
        self._device_handler = None


class TestRglGrammarCompiler(DddXmlCompilerTestCase):
    def test_action_with_noun_phrase(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <action name="top">
    <noun-phrase>
      <noun ref="menu"/>
    </noun-phrase>
  </action>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"},
                [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "menu"})])]
            )
        ])

    def test_lexicon_with_noun(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <lexicon>
    <noun id="menu">
      <singular>menu</singular>
    </noun>
  </lexicon>
</grammar>"""
        )

        self._then_grammar_is([
            Node(rgl_types.LEXICON, {}, [Node(rgl_types.NOUN, {"id": "menu"}, [Node("singular", {}, ["menu"])])])
        ])

    def test_action_with_verb_phrase(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <action name="top">
    <verb-phrase>
      <verb ref="restart"/>
    </verb-phrase>
  </action>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"},
                [Node(rgl_types.VERB_PHRASE, {}, [Node(rgl_types.VERB, {"ref": "restart"})])]
            )
        ])

    def test_predicate_with_noun_phrase(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <predicate name="phone_number_of_contact">
    <noun-phrase>
      <noun ref="number" />
    </noun-phrase>
  </predicate>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.PREDICATE, {"name": "phone_number_of_contact"},
                [Node(rgl_types.NOUN_PHRASE, {}, [Node(rgl_types.NOUN, {"ref": "number"})])]
            )
        ])

    def test_lexicon_with_verb(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <lexicon>
    <verb id="restart">
      <infinitive>restart</infinitive>
    </verb>
  </lexicon>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                rgl_types.LEXICON, {}, [Node(rgl_types.VERB, {"id": "restart"}, [Node("infinitive", {}, ["restart"])])]
            )
        ])

    def test_one_of_for_action(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <action name="top">
    <one-of>
      <item>
        <verb-phrase>
          <verb ref="restart"/>
        </verb-phrase>
      </item>
      <item>
        <verb-phrase>
          <verb ref="forget"/>
        </verb-phrase>
      </item>
    </one-of>
  </action>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"}, [
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
            )
        ])

    def test_simple_request(self):
        self._given_compiled_ontology()

        self._when_compile_rgl_grammar(
            """
<grammar>
  <request action="top"><utterance>forget everything</utterance></request>
</grammar>
"""
        )

        self._then_grammar_is([
            Node(rgl_types.REQUEST, {"action": "top"}, [Node(rgl_types.UTTERANCE, {}, ["forget everything"])])
        ])

    def test_request_with_individual(self):
        self._given_compiled_ontology("""
<ontology>
  <action name="call"/>
  <sort name="contact"/>
</ontology>
""")

        self._when_compile_rgl_grammar(
            """
<grammar>
  <request action="call">
    <utterance>call <individual sort="contact"/></utterance>
  </request>
</grammar>
"""
        )

        self._then_grammar_is([
            Node(
                rgl_types.REQUEST, {"action": "call"},
                [Node(rgl_types.UTTERANCE, {}, ["call ", Node(Constants.INDIVIDUAL, {"sort": "contact"}, [])])]
            )
        ])

    def test_individual_as_proper_noun(self):
        self._given_compiled_ontology(
            """
<ontology>
  <sort name="city"/>
  <individual name="city1" sort="city"/>
</ontology>"""
        )
        self._when_compile_rgl_grammar(
            """
<grammar>
  <individual name="city_1">
    <proper-noun>Paris</proper-noun>
  </individual>
</grammar>"""
        )
        self._then_grammar_is([
            Node(Constants.INDIVIDUAL, {"name": "city_1"}, [Node(rgl_types.PROPER_NOUN, {}, ["Paris"])])
        ])

    def test_report_ended(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_rgl_grammar(
            """
<grammar>
  <report action="IncomingCall" status="ended"><utterance>call ended</utterance></report>
</grammar>"""
        )
        self._then_grammar_is([
            Node(Constants.REPORT_ENDED, {"action": "IncomingCall"}, [Node(rgl_types.UTTERANCE, {}, ["call ended"])])
        ])

    def test_system_question(self):
        self._given_compiled_ontology(
            """
<ontology>
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_rgl_grammar(
            """
<grammar>
  <question predicate="dest_city" speaker="system">
    <utterance>where do you want to go</utterance>
  </question>
</grammar>"""
        )

        self._then_grammar_is([
            Node(
                Constants.SYS_QUESTION, {"predicate": "dest_city"},
                [Node(rgl_types.UTTERANCE, {}, ["where do you want to go"])]
            )
        ])


class TestServiceInterfaceCompiler(DddXmlCompilerTestCase):
    def test_action_without_parameters(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="EndCall">
    <parameters/>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "EndCall", target=DeviceModuleTarget("CallDevice"), parameters=[], failure_reasons=[]
            )
        ])

    def _when_compile_service_interface(self, device_xml):
        self._result = DddXmlCompiler().compile_service_interface(device_xml)

    def _then_service_interface_has_actions(self, expected_actions):
        assert self._result.actions == expected_actions

    def test_action_with_parameters(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call"/>
      <parameter predicate="number_to_call"/>
    </parameters>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "CallContact",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.VALUE, is_optional=False),
                    ServiceParameter("number_to_call", ParameterField.VALUE, is_optional=False),
                ],
                failure_reasons=[]
            )
        ])

    def test_action_with_failure_reasons(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call"/>
      <parameter predicate="number_to_call"/>
    </parameters>
    <failure_reasons>
      <failure_reason name="invalid_number"/>
      <failure_reason name="missing_number"/>
    </failure_reasons>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "CallContact",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.VALUE, is_optional=False),
                    ServiceParameter("number_to_call", ParameterField.VALUE, is_optional=False),
                ],
                failure_reasons=[
                    ActionFailureReason("invalid_number"),
                    ActionFailureReason("missing_number"),
                ]
            )
        ])

    def test_optional_parameter(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="Snooze">
    <parameters>
      <parameter predicate="minutes_to_snooze" optional="true"/>
    </parameters>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "Snooze",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("minutes_to_snooze", ParameterField.VALUE, is_optional=True),
                ],
                failure_reasons=[]
            )
        ])

    def test_parameter_field(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call" format="grammar_entry"/>
    </parameters>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "CallContact",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.GRAMMAR_ENTRY),
                ],
                failure_reasons=[]
            )
        ])

    def test_unexpected_parameter_field(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call" format="something_else"/>
    </parameters>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'parameter', "
            "attribute 'format': \[facet 'enumeration'\] The value 'something_else' is not an element of the set "
            "\{'value', 'grammar_entry'\}., line 5"
        )

    def _when_compile_service_interface_then_exception_is_raised_matching(
        self, xml, expected_exception, expected_message
    ):
        with pytest.raises(expected_exception, match=expected_message):
            self._when_compile_service_interface(xml)

    def test_query_with_device_module_target(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <query name="available_contact">
    <parameters>
      <parameter predicate="contact_to_call"/>
    </parameters>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </query>
</service_interface>
"""
        )
        self._then_service_interface_has_queries([
            ServiceQueryInterface(
                "available_contact",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.VALUE),
                ]
            )
        ])

    def _then_service_interface_has_queries(self, expected_queries):
        assert self._result.queries == expected_queries

    def test_entity_recognizer_with_device_module_target(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <entity_recognizer name="ContactNameRecognizer">
    <target>
      <device_module device="CallDevice"/>
    </target>
  </entity_recognizer>
</service_interface>
"""
        )
        self._then_service_interface_has_entity_recognizers([
            ServiceEntityRecognizerInterface("ContactNameRecognizer", target=DeviceModuleTarget("CallDevice")),
        ])

    def _then_service_interface_has_entity_recognizers(self, expected_entity_recognizers):
        assert self._result.entity_recognizers == expected_entity_recognizers

    def test_validity_with_device_module_target(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <validator name="RouteValidator">
    <parameters>
      <parameter predicate="navigation_origin"/>
      <parameter predicate="navigation_destination"/>
    </parameters>
    <target>
      <device_module device="NavigationDevice"/>
    </target>
  </validator>
</service_interface>
"""
        )
        self._then_service_interface_has_validities([
            ServiceValidatorInterface(
                "RouteValidator",
                target=DeviceModuleTarget("NavigationDevice"),
                parameters=[
                    ServiceParameter("navigation_origin", ParameterField.VALUE),
                    ServiceParameter("navigation_destination", ParameterField.VALUE),
                ]
            )
        ])

    def _then_service_interface_has_validities(self, expected_validities):
        assert self._result.validators == expected_validities

    def test_frontend_target_for_action(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call"/>
    </parameters>
    <failure_reasons/>
    <target>
      <frontend/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "CallContact",
                target=FrontendTarget(),
                parameters=[
                    ServiceParameter("contact_to_call"),
                ],
                failure_reasons=[]
            )
        ])

    def test_frontend_target_for_query(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <query name="available_contact">
    <parameters>
      <parameter predicate="contact_to_call"/>
    </parameters>
    <target>
      <frontend/>
    </target>
  </query>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'frontend': "
            "This element is not expected. Expected is one of \( device_module, http \)., line 8"
        )

    def test_frontend_target_for_validator(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <validator name="RouteValidator">
    <parameters>
      <parameter predicate="navigation_origin"/>
      <parameter predicate="navigation_destination"/>
    </parameters>
    <target>
      <frontend/>
    </target>
  </validator>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'frontend': "
            "This element is not expected. Expected is one of \( device_module, http \)., line 9"
        )

    def test_frontend_target_for_entity_recognizer(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <entity_recognizer name="ContactNameRecognizer">
    <target>
      <frontend/>
    </target>
  </entity_recognizer>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'frontend': "
            "This element is not expected. Expected is one of \( device_module, http \)., line 5"
        )

    def test_http_target_for_action(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call"/>
    </parameters>
    <failure_reasons/>
    <target>
      <http endpoint="mock_endpoint"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            ServiceActionInterface(
                "CallContact",
                target=HttpTarget("mock_endpoint"),
                parameters=[
                    ServiceParameter("contact_to_call"),
                ],
                failure_reasons=[]
            )
        ])

    def test_http_target_for_query(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <query name="available_contact">
    <parameters>
      <parameter predicate="contact_to_call"/>
    </parameters>
    <target>
      <http endpoint="mock_endpoint"/>
    </target>
  </query>
</service_interface>
    """
        )
        self._then_service_interface_has_queries([
            ServiceQueryInterface(
                "available_contact",
                target=HttpTarget("mock_endpoint"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.VALUE),
                ]
            )
        ])

    def test_http_target_for_entity_recognizer(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <entity_recognizer name="ContactNameRecognizer">
    <target>
      <http endpoint="mock_endpoint"/>
    </target>
  </entity_recognizer>
</service_interface>
    """
        )
        self._then_service_interface_has_entity_recognizers([
            ServiceEntityRecognizerInterface("ContactNameRecognizer", target=HttpTarget("mock_endpoint"))
        ])

    def test_http_target_for_validator(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <validator name="RouteValidator">
    <parameters>
      <parameter predicate="navigation_origin"/>
      <parameter predicate="navigation_destination"/>
    </parameters>
    <target>
      <http endpoint="mock_endpoint"/>
    </target>
  </validator>
</service_interface>
"""
        )
        self._then_service_interface_has_validities([
            ServiceValidatorInterface(
                "RouteValidator",
                target=HttpTarget("mock_endpoint"),
                parameters=[
                    ServiceParameter("navigation_origin", ParameterField.VALUE),
                    ServiceParameter("navigation_destination", ParameterField.VALUE),
                ]
            )
        ])

    def test_play_audio_action_without_url_parameter(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <play_audio_action name="PlayAudio">
    <parameters/>
    <target>
      <frontend/>
    </target>
  </play_audio_action>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'parameters': "
            "This element is not expected. Expected is \( audio_url_parameter \)., line 4"
        )

    def test_play_audio_action_with_parameters(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <play_audio_action name="PlayAudio">
    <audio_url_parameter predicate="url_of_song"/>
    <parameters>
      <parameter predicate="artist"/>
    </parameters>
    <target>
      <frontend/>
    </target>
  </play_audio_action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            PlayAudioActionInterface(
                "PlayAudio",
                target=FrontendTarget(),
                parameters=[
                    ServiceParameter("artist"),
                ],
                audio_url_parameter=AudioURLServiceParameter("url_of_song")
            )
        ])

    def test_play_audio_action_and_custom_action_together(self):
        self._when_compile_service_interface(
            """
<service_interface>
  <play_audio_action name="PlayAudio">
    <audio_url_parameter predicate="url_of_song"/>
    <parameters>
      <parameter predicate="artist"/>
    </parameters>
    <target>
      <frontend/>
    </target>
  </play_audio_action>
  <action name="CallContact">
    <parameters>
      <parameter predicate="contact_to_call" format="grammar_entry"/>
    </parameters>
    <failure_reasons/>
    <target>
      <device_module device="CallDevice"/>
    </target>
  </action>
</service_interface>
"""
        )
        self._then_service_interface_has_actions([
            PlayAudioActionInterface(
                "PlayAudio",
                target=FrontendTarget(),
                parameters=[
                    ServiceParameter("artist"),
                ],
                audio_url_parameter=AudioURLServiceParameter("url_of_song")
            ),
            ServiceActionInterface(
                "CallContact",
                target=DeviceModuleTarget("CallDevice"),
                parameters=[
                    ServiceParameter("contact_to_call", ParameterField.GRAMMAR_ENTRY),
                ],
                failure_reasons=[]
            )
        ])

    def test_play_audio_action_with_invalid_target(self):
        self._when_compile_service_interface_then_exception_is_raised_matching(
            """
<service_interface>
  <play_audio_action name="PlayAudio">
    <audio_url_parameter predicate="url_of_song"/>
    <parameters>
      <parameter predicate="artist"/>
    </parameters>
    <target>
      <device_module device="AudioDevice"/>
    </target>
  </play_audio_action>
</service_interface>
""", ViolatesSchemaException,
            "Expected service_interface.xml compliant with schema but it's in violation: Element 'device_module': "
            "This element is not expected. Expected is \( frontend \)., line 9"
        )
