import pytest
from unittest.mock import Mock, patch

import tala.ddd.ddd_xml_compiler
from tala.ddd.ddd_xml_compiler import DDDXMLCompiler, DDDXMLCompilerException, ViolatesSchemaException, UnexpectedAttributeException, OntologyWarning
from tala.ddd.parser import Parser
from tala.ddd.services.service_interface import ServiceParameter, ServiceActionInterface, ServiceQueryInterface, ServiceValidatorInterface, FrontendTarget, DeviceModuleTarget, HttpTarget, ServiceInterface, ActionFailureReason, ParameterField

from tala.ddd.test.ddd_compiler_test_case import DddCompilerTestCase
from tala.model.ask_feature import AskFeature
from tala.model.hint import Hint
from tala.model.ontology import Ontology
from tala.model.plan import Plan
from tala.model.plan_item import (
    IfThenElse,
    ForgetAllPlanItem,
    InvokeServiceQueryPlanItem,
    InvokeDomainQueryPlanItem,
    InvokeServiceActionPlanItem,
    LogPlanItem,
    EndTurnPlanItem,
    UnexpectedLogLevelException,
)
from tala.model import plan_item
from tala.model import condition
from tala.model.predicate import Predicate
from tala.model.proposition import ImplicationProposition
from tala.model.sort import CustomSort, RealSort


class DDDXMLCompilerTestCase(DddCompilerTestCase):
    def _given_compiled_ontology(
        self, xml='<ontology name="MockupOntology"/>', domain_name="Domain", ddd_name="mock_ddd"
    ):
        self._ddd_name = ddd_name
        ontology_args = DDDXMLCompiler().compile_ontology(xml)
        self._ontology = Ontology(**ontology_args)
        self._parser = Parser(self._ddd_name, self._ontology, domain_name)
        self._service_interface = Mock(spec=ServiceInterface)

    def _when_compile_ontology(self, ontology_xml):
        self._compile_ontology(ontology_xml)

    def _compile_ontology(self, ontology_xml):
        self._result = DDDXMLCompiler().compile_ontology(ontology_xml)
        self._ontology = Ontology(**self._result)

    def _predicate(self, *args, **kwargs):
        return Predicate(self._ontology.name, *args, **kwargs)

    def _when_compile_ontology_then_exception_is_raised(self, ontology_xml, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._compile_ontology(ontology_xml)

    def _when_compile_domain(self, domain_xml='<domain name="Domain" />'):
        self._result = DDDXMLCompiler().compile_domain(self._ddd_name, domain_xml, self._ontology, self._parser)

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

    def _when_compile_goal_with_content(self, xml):
        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="top">%s</goal>
</domain>""" % xml
        )

    def _then_result_has_keys(self, expected_keys):
        self.assertItemsEqual(expected_keys, list(self._result.keys()))

    def _then_result_has_field(self, expected_key, expected_value):
        assert expected_value == self._result[expected_key]

    def _then_result_has_plan(self, expected_plan):
        actual_plans = self._result["plans"]
        actual_plan = actual_plans[0]["plan"]
        assert expected_plan == actual_plan

    def _then_findout_allows_pcom(self, allow):
        plans = self._result["plans"]
        plan = plans[0]["plan"]
        findout = plan.top()
        assert allow == findout.allow_answer_from_pcom

    def _then_result_has_plan_with_attribute(self, expected_key, expected_value):
        actual_plans = self._result["plans"]
        actual_plan = actual_plans[0]
        assert expected_value == actual_plan[expected_key]

    def _parse(self, string):
        return self._parser.parse(string)

    def _then_result_is(self, expected_result):
        assert expected_result == self._result

    def _mock_warnings(self):
        return patch("%s.warnings" % tala.ddd.ddd_xml_compiler.__name__)

    def _then_warning_is_issued(self, mocked_warnings, expected_message, expected_class):
        mocked_warnings.warn.assert_called_once_with(expected_message, expected_class)


class TestOntologyCompiler(DDDXMLCompilerTestCase):
    def test_name(self):
        self._when_compile_ontology('<ontology name="MockupOntology"/>')
        self._then_result_has_field("name", "MockupOntology")

    def test_custom_sort(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <sort name="city"/>
</ontology>""")
        self._then_result_has_field("sorts", {self._create_sort("city")})

    def test_dynamic_sort(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <sort name="city" dynamic="true"/>
</ontology>""")
        self._then_result_has_field("sorts", {self._create_sort("city", dynamic=True)})

    def test_predicate_of_custom_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._then_result_has_field("predicates", {self._predicate("dest_city", self._create_sort("city"))})

    def test_predicate_of_builtin_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._then_result_has_field("predicates", {self._predicate("price", RealSort())})

    def test_predicate_of_dynamic_sort(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city" dynamic="true"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates", {self._predicate("dest_city", self._create_sort("city", dynamic=True))}
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
            "predicates", {
                self._predicate("dest_city", sort=self._create_sort("city")),
                self._predicate("dest_city_type", sort=self._create_sort("city"), feature_of_name="dest_city")
            }
        )

    def _create_sort(self, *args, **kwargs):
        return CustomSort(self._ontology.name, *args, **kwargs)

    def test_multiple_instances(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city" multiple_instances="true"/>
</ontology>"""
        )
        self._then_result_has_field(
            "predicates", {self._predicate("dest_city", sort=self._create_sort("city"), multiple_instances=True)}
        )

    def test_individuals(self):
        self._when_compile_ontology(
            """
<ontology name="Ontology">
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._then_result_has_field("individuals", {"paris": self._create_sort("city")})

    def test_actions(self):
        self._when_compile_ontology("""
<ontology name="Ontology">
  <action name="buy"/>
</ontology>""")
        self._then_result_has_field("actions", {"buy"})

    def test_warning_for_undefined_sort_in_predicate(self):
        self._when_compile_ontology_then_warning_is_issued(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="undefined_sort"/>
</ontology>""", "Expected a defined sort but got 'undefined_sort'. Adding it to the ontology as a static sort."
        )

    def _when_compile_ontology_then_warning_is_issued(self, ontology_xml, expected_warning_message):
        with self._mock_warnings() as mocked_warnings:
            self._compile_ontology(ontology_xml)
            self._then_warning_is_issued(mocked_warnings, expected_warning_message, OntologyWarning)


class TestGoalCompilation(DDDXMLCompilerTestCase):
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

    def test_plan_for_resolve_goal_for_wh_question_as_default(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain("""
<domain name="Domain">
  <goal type="resolve" predicate="price" />
</domain>""")

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

    def test_exception_raised_for_goal_without_type(self):
        self._given_compiled_ontology()

        with pytest.raises(DDDXMLCompilerException):
            self._when_compile_domain("""
<domain name="Domain">
  <goal />
</domain>""")

    def test_plan_stack_order_use_default_wh_question(self):
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
<findout predicate="means_of_transport" />
<findout predicate="dest_city" />"""
        )

        self._then_result_has_plan(
            Plan([self._parse("findout(?X.dest_city(X))"),
                  self._parse("findout(?X.means_of_transport(X))")])
        )

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

    def test_query_as_complex_plan(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="means_of_travel" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <query predicate="means_of_transport" type="wh_question">
    <implication>
        <antecedent predicate="means_of_travel" value="train"/>
        <consequent predicate="means_of_travel" value="train"/>
    </implication>
  </query>
</domain>"""
        )

        self._then_result_has_field(
            "queries", [{
                "query": self._parse("?X.means_of_transport(X)"),
                "implications": [
                    ImplicationProposition(
                        self._parse("means_of_travel(train)"), self._parse("means_of_travel(train)")
                    )
                ]
            }]
        )

    def test_query_select_at_random(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="means_of_travel" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
  <individual name="plane" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <query predicate="means_of_transport" type="wh_question">
    <select_at_random>
        <individual value="train"/>
        <individual value="plane"/>
    </select_at_random>
  </query>
</domain>"""
        )

        self._then_result_has_field(
            "queries", [{
                "query": self._parse("?X.means_of_transport(X)"),
                "for_random_selection": [
                    self._parse("means_of_transport(train)"),
                    self._parse("means_of_transport(plane)")
                ]
            }]
        )

    def test_query_enumerate(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="means_of_travel" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
  <individual name="plane" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <query predicate="means_of_transport">
    <enumerate>
        <individual value="train"/>
        <individual value="plane"/>
    </enumerate>
  </query>
</domain>"""
        )

        self._then_result_has_field(
            "queries", [{
                "query": self._parse("?X.means_of_transport(X)"),
                "for_enumeration": [self._parse("means_of_transport(train)"),
                                    self._parse("means_of_transport(plane)")]
            }]
        )

    def test_query_enumerate_random(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="means_of_travel" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
  <individual name="plane" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <query predicate="means_of_transport">
    <enumerate randomize="true">
        <individual value="train"/>
        <individual value="plane"/>
    </enumerate>
  </query>
</domain>"""
        )

        self._then_result_has_field(
            "queries", [{
                "query": self._parse("?X.means_of_transport(X)"),
                "for_random_enumeration": [
                    self._parse("means_of_transport(train)"),
                    self._parse("means_of_transport(plane)")
                ]
            }]
        )

    def test_iterator(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <sort name="train_type"/>
  <predicate name="means_of_transport" sort="how"/>
  <predicate name="means_of_travel" sort="how"/>
  <predicate name="transport_train_type" sort="train_type"/>
  <individual name="train" sort="how"/>
  <individual name="plane" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <iterator name="some_name">
    <enumerate>
        <proposition predicate="means_of_transport" value="train"/>
        <proposition predicate="means_of_travel" value="train"/>
    </enumerate>
  </iterator>
</domain>"""
        )

        self._then_result_has_field(
            "queries", [{
                "query": "some_name",
                "for_enumeration": [self._parse("means_of_transport(train)"),
                                    self._parse("means_of_travel(train)")],
                "limit": "-1"
            }]
        )

    def test_domain_validator(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <individual name="train" sort="how"/>
  <individual name="plane" sort="how"/>
  <individual name="bike" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <validator name="ValidatorName">
    <configuration>
      <proposition predicate="means_of_transport" value="train"/>
    </configuration>
    <configuration>
      <proposition predicate="means_of_transport" value="plane"/>
    </configuration>
  </validator>
</domain>"""
        )

        self._then_result_has_field(
            "validators", [{
                "validator": "ValidatorName",
                "valid_configurations": [
                    [self._parse("means_of_transport(train)")],
                    [self._parse("means_of_transport(plane)")]
                ]
            }]
        )  # yapf: disable

    def test_preferred_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
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
        self._when_compile_goal_with_content("""
<preferred/>
""")
        self._then_result_has_plan_with_attribute("preferred", True)

    def test_accommodate_without_feedback(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("accommodate_without_feedback", "true")
        self._then_result_has_plan_with_attribute("accommodate_without_feedback", True)

    def test_restart_on_completion(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("restart_on_completion", "true")
        self._then_result_has_plan_with_attribute("restart_on_completion", True)

    def test_reraise_on_resume(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("reraise_on_resume", "true")
        self._then_result_has_plan_with_attribute("reraise_on_resume", True)

    def test_postplan(self):
        self._given_compiled_ontology()
        self._when_compile_goal_with_content('<postplan><forget_all/></postplan>')
        self._then_result_has_plan_with_attribute("postplan", Plan([ForgetAllPlanItem()]))

    @pytest.mark.filterwarnings("ignore:<postcond>")
    def test_postcond_with_whitespace(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<postcond>
  <proposition predicate="dest_city" value="paris"/>
</postcond>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [self._parse("dest_city(paris)")])

    @pytest.mark.filterwarnings("ignore:<postcond>")
    def test_postcond_for_predicate_proposition(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content('<postcond><proposition predicate="dest_city" value="paris"/></postcond>')
        self._then_result_has_plan_with_attribute("postconds", [self._parse("dest_city(paris)")])

    @pytest.mark.filterwarnings("ignore:<postcond>")
    def test_postcond_with_multiple_propositions(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <predicate name="dept_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <individual name="gothenburg" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<postcond>
  <proposition predicate="dept_city" value="gothenburg"/>
</postcond>
<postcond>
  <proposition predicate="dest_city" value="paris"/>
</postcond>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds", [
                self._parse("dept_city(gothenburg)"),
                self._parse("dest_city(paris)"),
            ]
        )

    def test_postcond_deprecation_warning(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_domain_with_goal_content_then_deprecation_warning_is_issued(
            '<postcond><proposition predicate="dest_city" value="paris"/></postcond>',
            "<postcond> is deprecated. Use <downdate_condition> instead."
        )

    def _when_compile_domain_with_goal_content_then_deprecation_warning_is_issued(
        self, goal_xml, expected_warning_message
    ):
        with self._mock_warnings() as mocked_warnings:
            self._when_compile_goal_with_content(goal_xml)
            self._then_warning_is_issued(mocked_warnings, expected_warning_message, DeprecationWarning)

    def test_is_shared_fact_deprecation_warning(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_domain_with_goal_content_then_deprecation_warning_is_issued(
            '<downdate_condition><is_shared_fact>'
            '<proposition predicate="dest_city" value="paris"/>'
            '</is_shared_fact></downdate_condition>', "<is_shared_fact> is deprecated."
        )


class TestDomainCompiler(DDDXMLCompilerTestCase):
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
            "dependencies", {self._parse("?X.dest_country(X)"): {self._parse("?X.dest_city(X)")}}
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

    def test_parameters_for_ynq(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
    <predicate name="need_visa" sort="boolean"/>
    <sort name="city"/>
    <predicate name="dest_city" sort="city"/>
    <individual name="paris" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
    <parameters question_type="yn_question">
        <proposition predicate="need_visa"/>
        <hint>
            <inform>
               <proposition predicate="dest_city" value="paris"/>
            </inform>
        </hint>
    </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?need_visa"): {
                    "hints": [
                        Hint([
                            IfThenElse(
                                condition.HasSharedValue(self._parse("dest_city")), [],
                                [self._parse("assume(dest_city(paris))"),
                                 self._parse("assume_issue(?X.dest_city(X))")]
                            )
                        ])
                    ]
                }
            }
        )

    def test_parameters_for_ynq_alternative_syntax(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
    <predicate name="need_visa" sort="boolean"/>
    <sort name="city"/>
    <predicate name="dest_city" sort="city"/>
    <individual name="paris" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
    <parameters question_type="yn_question" predicate="need_visa">
        <hint>
            <inform>
               <proposition predicate="dest_city" value="paris"/>
            </inform>
        </hint>
    </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?need_visa"): {
                    "hints": [
                        Hint([
                            IfThenElse(
                                condition.HasSharedValue(self._parse("dest_city")), [],
                                [self._parse("assume(dest_city(paris))"),
                                 self._parse("assume_issue(?X.dest_city(X))")]
                            )
                        ])
                    ]
                }
            }
        )

    def test_mitigation_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
  <action name="mitigate_search_for_price"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price" on_zero_hits_action="mitigate_search_for_price"/>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.price(X)"): self._parser.parse_parameters(
                    "{on_zero_hits_action=mitigate_search_for_price}"
                )
            }
        )  # yapf: disable

    def test_too_many_hits_mitigation_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
  <action name="mitigate_search_for_price"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price" on_too_many_hits_action="mitigate_search_for_price"/>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.price(X)"): self._parser.parse_parameters(
                    "{on_too_many_hits_action=mitigate_search_for_price}"
                )
            }
        )  # yapf: disable

    @pytest.mark.filterwarnings("ignore:<has_value>")
    def test_downdate_condition_for_has_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <has_value predicate="dest_city"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [condition.HasValue(self._parse("dest_city"))])

    @pytest.mark.filterwarnings("ignore:<has_value>")
    def test_downdate_condition_for_boolean_has_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="need_visa" sort="boolean"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <has_value predicate="need_visa"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [condition.HasValue(self._parse("need_visa"))])

    @pytest.mark.filterwarnings("ignore:<is_true>")
    def test_downdate_condition_with_is_true(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <is_true>
    <proposition predicate="dest_city" value="paris"/>
  </is_true>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [condition.IsTrue(self._parse("dest_city(paris)"))])

    def test_downdate_condition_with_is_shared_commitment(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <is_shared_commitment predicate="dest_city" value="paris"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds", [condition.IsSharedCommitment(self._parse("dest_city(paris)"))]
        )

    def test_downdate_condition_with_is_private_belief(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <is_private_belief predicate="dest_city" value="paris"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds", [condition.IsPrivateBelief(self._parse("dest_city(paris)"))]
        )

    def test_downdate_condition_with_is_private_belief_or_shared_commitment(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <is_private_belief_or_shared_commitment predicate="dest_city" value="paris"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds", [condition.IsPrivateBeliefOrSharedCommitment(self._parse("dest_city(paris)"))]
        )

    def test_downdate_condition_with_has_shared_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <has_shared_value predicate="dest_city"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [condition.HasSharedValue(self._parse("dest_city"))])

    def test_downdate_condition_with_has_private_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <has_private_value predicate="dest_city"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute("postconds", [condition.HasPrivateValue(self._parse("dest_city"))])

    def test_downdate_condition_with_has_shared_or_private_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <has_shared_or_private_value predicate="dest_city"/>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds", [condition.HasSharedOrPrivateValue(self._parse("dest_city"))]
        )

    @pytest.mark.filterwarnings("ignore:<is_true>")
    def test_downdate_condition_with_multiple_conditions(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="dest_city" sort="city"/>
  <predicate name="dept_city" sort="city"/>
  <individual name="paris" sort="city"/>
  <individual name="gothenburg" sort="city"/>
  <sort name="city"/>
</ontology>"""
        )
        self._when_compile_goal_with_content(
            """
<downdate_condition>
  <is_true>
    <proposition predicate="dest_city" value="paris"/>
  </is_true>
</downdate_condition>
<downdate_condition>
  <is_true>
    <proposition predicate="dept_city" value="gothenburg"/>
  </is_true>
</downdate_condition>"""
        )
        self._then_result_has_plan_with_attribute(
            "postconds",
            [condition.IsTrue(self._parse("dest_city(paris)")),
             condition.IsTrue(self._parse("dept_city(gothenburg)"))]
        )

    def test_schema_violation_yields_exception(self):
        self._given_compiled_ontology('<ontology name="Ontology"/>')
        self._when_compile_domain_then_exception_is_raised_matching(
            '<domain name="Domain">invalid_content</domain>', ViolatesSchemaException,
            "Expected domain.xml compliant with schema but it's in violation: "
            "Element 'domain': Character content other than whitespace is not allowed because the content type is "
            "'element-only'., line 1"
        )

    def _when_compile_domain_then_exception_is_raised_matching(self, xml, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._when_compile_domain(xml)

    def test_malformed_log_element(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<log/>', ViolatesSchemaException, "The attribute 'message' is required but missing."
        )

    def test_malformed_assume_shared_element(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<assume_shared/>', ViolatesSchemaException,
            r"Element 'assume_shared': Missing child element\(s\). Expected is \( proposition \)."
        )

    def test_malformed_assume_system_belief_element(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<assume_system_belief/>', ViolatesSchemaException,
            r"Element 'assume_system_belief': Missing child element\(s\). Expected is \( proposition \)."
        )

    def _when_compile_domain_with_plan_then_exception_is_raised_matching(
        self, xml, expected_exception, expected_message
    ):
        with pytest.raises(expected_exception, match=expected_message):
            self._when_compile_domain_with_plan(xml)


class TestParameterCompilation(DDDXMLCompilerTestCase):
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
                self._parse("?X.means_of_transport(X)"): self._parser.parse_parameters(
                    "{service_query=?X.available_means_of_transport(X)}"
                )
            }
        )  # yapf: disable

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
  <parameters question_type="wh_question" predicate="product_to_add"/>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {self._parse("?X.product_to_add(X)"): self._parser.parse_parameters("{}")}
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

    def test_ask_feature_minimal_case(self):
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
            {self._parse("?X.dest_city(X)"): {
                 "ask_features": [AskFeature(predicate_name="dest_city_type")]
             }}
        )

    def test_ask_feature_with_kpq(self):
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
    <ask_feature predicate="dest_city_type" kpq="true"/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters",
            {self._parse("?X.dest_city(X)"): {
                 "ask_features": [AskFeature(predicate_name="dest_city_type", kpq=True)]
             }}
        )

    def test_hints_minimal_case(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="dest_city">
    <hint>
        <inform>
            <proposition predicate="dest_city" value="paris"/>
        </inform>
    </hint>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.dest_city(X)"): {
                    "hints": [
                        Hint([
                            IfThenElse(
                                condition.HasSharedValue(self._parse("dest_city")), [],
                                [self._parse("assume(dest_city(paris))"),
                                 self._parse("assume_issue(?X.dest_city(X))")]
                            )
                        ])
                    ]
                }
            }
        )

    def test_several_hints(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="city"/>
  <predicate name="dest_city" sort="city"/>
  <individual name="paris" sort="city"/>

  <sort name="hint_sort"/>
  <predicate name="hint_about_destination" sort="hint_sort"/>
  <individual name="french_capital" sort="hint_sort"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="dest_city">
    <hint>
        <inform>
            <proposition predicate="hint_about_destination" value="french_capital"/>
        </inform>
    </hint>
    <hint>
        <inform>
            <proposition predicate="dest_city" value="paris"/>
        </inform>
    </hint>
  </parameters>
</domain>"""
        )

        self._then_result_has_field(
            "parameters", {
                self._parse("?X.dest_city(X)"): {
                    "hints": [
                        Hint([
                            IfThenElse(
                                condition.HasSharedValue(self._parse("hint_about_destination")), [], [
                                    self._parse("assume(hint_about_destination(french_capital))"),
                                    self._parse("assume_issue(?X.hint_about_destination(X))")
                                ]
                            )
                        ]),
                        Hint([
                            IfThenElse(
                                condition.HasSharedValue(self._parse("dest_city")), [],
                                [self._parse("assume(dest_city(paris))"),
                                 self._parse("assume_issue(?X.dest_city(X))")]
                            )
                        ])
                    ]
                }
            }
        )

    def test_greet(self):
        self._given_compiled_ontology("""
<ontology name="Ontology">
</ontology>""")
        self._when_compile_goal_with_content("<plan><greet/></plan>")
        self._then_result_has_plan(Plan([plan_item.Greet()]))

    def test_person_names_as_alts(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <action name="select_person_to_call"/>
  <predicate name="person_to_call" sort="person_name"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <goal type="perform" action="select_person_to_call">
    <plan>
      <findout type="alt_question">
        <alt><proposition predicate="person_to_call" value="Anna Kronlid"/></alt>
        <alt><proposition predicate="person_to_call" value="Fredrik Kronlid"/></alt>
      </findout>
    </plan>
  </goal>
</domain>"""
        )

        self._then_result_has_plan(
            Plan([
                self._parse(
                    'findout(?set([person_to_call(person_name(Anna Kronlid)), person_to_call(person_name(Fredrik Kronlid))]))'
                )
            ])
        )

    def test_empty_alt_yields_exception(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
</ontology>"""
        )

        with pytest.raises(DDDXMLCompilerException):
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
                self._parse("?X.goal(X)"): self._parser.parse_parameters(
                    "{alts=set([goal(perform(buy)), goal(resolve(?X.price(X)))])}"
                )
            }
        )  # yapf: disable

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
        DDDXMLCompilerTestCase._given_compiled_ontology(self, xml)

    def _when_compile_parameter_for_question(self, name, value):
        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="price" %s="%s" />
</domain>""" % (name, value)
        )

    def _then_result_has_parameter_for_question(self, expected_name, expected_value):
        self._then_result_has_field("parameters", {self._parse("?X.price(X)"): {expected_name: expected_value}})

    def test_hints_always_relevant_parameter(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
    <sort name="city"/>
    <predicate name="dest_city" sort="city"/>
</ontology>"""
        )

        self._when_compile_domain(
            """
<domain name="Domain">
  <parameters question_type="wh_question" predicate="dest_city">
    <always_relevant/>
  </parameters>
</domain>"""
        )

        self._then_result_has_field("parameters", {self._parse("?X.dest_city(X)"): {"always_relevant": True}})


class TestPlanItemCompilation(DDDXMLCompilerTestCase):
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

    def test_allow_answer_from_pcom_is_tolerated_with_findout(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<findout type="wh_question" predicate="price"
         allow_answer_from_pcom="true"/>"""
        )

        self._then_result_has_plan(Plan([self._parse("findout(?X.price(X))")]))

    def test_allow_answer_from_pcom_is_not_tolerated_with_raise(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<raise type="wh_question" predicate="price" allow_answer_from_pcom="true"/>', ViolatesSchemaException,
            "Expected domain.xml compliant with schema but it's in violation: Element 'raise', attribute 'allow_answer_from_pcom': The attribute 'allow_answer_from_pcom' is not allowed., line 4"
        )

    def test_allow_answer_from_pcom_is_not_tolerated_with_bind(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<bind type="wh_question" predicate="price" allow_answer_from_pcom="true"/>', ViolatesSchemaException,
            "Expected domain.xml compliant with schema but it's in violation: Element 'bind', attribute 'allow_answer_from_pcom': The attribute 'allow_answer_from_pcom' is not allowed., line 4"
        )

    def test_findout_for_ynq(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="need_visa" sort="boolean"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan("""
<findout type="yn_question" predicate="need_visa"/>""")

        self._then_result_has_plan(Plan([
            self._parse("findout(?need_visa())"),
        ]))

    def test_findout_defaults_to_disallow_answer_from_pcom(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan("""
<findout type="wh_question" predicate="price"/>""")

        self._then_findout_allows_pcom(False)

    def test_findout_allows_answer_from_pcom(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            """
<findout type="wh_question" predicate="price" allow_answer_from_pcom="true"/>"""
        )

        self._then_findout_allows_pcom(True)

    def test_if_then_condition_is_deprecated(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._given_plan(
            """
<if>
  <condition><proposition predicate="means_of_transport" value="train"/></condition>
  <then>
    <findout type="wh_question" predicate="transport_train_type" />
  </then>
  <else />
</if>"""
        )

        self._when_compile_domain_with_plan_then_deprecation_warning_is_issued(
            self._plan,
            '"<if><condition><proposition ..." is deprecated. Use "<if><proposition ..." without <condition> instead.'
        )

    def _given_plan(self, plan):
        self._plan = plan

    @pytest.mark.filterwarnings('ignore:"<if>')
    def test_if_then_condition_still_works(self):
        self._given_compiled_ontology_for_if_then_tests()
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
                    self._parse("means_of_transport(train)"), [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_else(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <proposition predicate="means_of_transport" value="train"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type" />
  </then>
  <else />
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    self._parse("means_of_transport(train)"), [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def _given_compiled_ontology_for_if_then_tests(self):
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

    @pytest.mark.filterwarnings('ignore:<has_value>')
    def test_if_then_else_has_value(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <has_value predicate="means_of_transport"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasValue(self._parse("means_of_transport")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_has_shared_value(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <has_shared_value predicate="means_of_transport"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("means_of_transport")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_has_private_value(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <has_private_value predicate="means_of_transport"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasPrivateValue(self._parse("means_of_transport")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_has_shared_or_private_value(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <has_shared_or_private_value predicate="means_of_transport"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedOrPrivateValue(self._parse("means_of_transport")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_is_shared_commitment(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <is_shared_commitment predicate="means_of_transport" value="train"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.IsSharedCommitment(self._parse("means_of_transport(train)")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_is_private_belief(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <is_private_belief predicate="means_of_transport" value="train"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.IsPrivateBelief(self._parse("means_of_transport(train)")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_is_private_belief_or_shared_commitment(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <is_private_belief_or_shared_commitment predicate="means_of_transport" value="train"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.IsPrivateBeliefOrSharedCommitment(self._parse("means_of_transport(train)")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_else_query_has_more_items(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <has_more_items predicate="means_of_transport"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type"/>
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.QueryHasMoreItems(self._parse("?X.means_of_transport(X)")),
                    [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_no_else(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <proposition predicate="means_of_transport" value="train"/>
  <then>
    <findout type="wh_question" predicate="transport_train_type" />
  </then>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    self._parse("means_of_transport(train)"), [self._parse("findout(?X.transport_train_type(X))")], []
                )
            ])
        )

    def test_if_then_only_else(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan(
            """
<if>
  <proposition predicate="means_of_transport" value="train"/>
  <else>
    <findout type="wh_question" predicate="transport_train_type" />
  </else>
</if>"""
        )

        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    self._parse("means_of_transport(train)"), [], [self._parse("findout(?X.transport_train_type(X))")]
                )
            ])
        )

    def test_if_then_two_then(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<if><proposition predicate="means_of_transport" value="train"/><then/><then/></if>',
            ViolatesSchemaException, r"This element is not expected. Expected is \( else \)"
        )

    def test_if_then_two_elses(self):
        self._given_compiled_ontology_for_if_then_tests()
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<if><proposition predicate="means_of_transport" value="train"/><else/><else/></if>',
            ViolatesSchemaException, "Element 'else': This element is not expected."
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

    def test_forget_proposition_from_com(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan(
            '<forget_shared><proposition predicate="means_of_transport" value="train"/></forget_shared>'
        )

        self._then_result_has_plan(Plan([self._parse("forget_shared(means_of_transport(train))")]))

    def test_forget_predicate_from_com(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan('<forget_shared predicate="means_of_transport"/>')

        self._then_result_has_plan(Plan([self._parse("forget_shared(means_of_transport)")]))

    def test_forget_all(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<forget_all />')
        self._then_result_has_plan(Plan([ForgetAllPlanItem()]))

    def test_log_element(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<log message="log message" />')
        self._then_result_has_plan(Plan([LogPlanItem("log message", log_level="debug")]))

    def test_log_element_with_default_level(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<log message="log message" level="debug"/>')
        self._then_result_has_plan(Plan([LogPlanItem("log message", log_level="debug")]))

    def test_log_element_with_level(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<log message="log message" level="info"/>')
        self._then_result_has_plan(Plan([LogPlanItem("log message", log_level="info")]))

    def test_log_element_with_unexpected_level(self):
        self._given_compiled_ontology()
        with pytest.raises(UnexpectedLogLevelException):
            self._when_compile_domain_with_plan('<log message="log message" level="kalas"/>')

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

    def test_invoke_service_query_use_wh_question_default(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<invoke_service_query predicate="price"/>')
        self._then_result_has_plan(
            Plan([InvokeServiceQueryPlanItem(self._parse("?X.price(X)"), min_results=1, max_results=1)])
        )

    def test_invoke_domain_query(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<invoke_domain_query type="wh_question" predicate="price"/>')
        self._then_result_has_plan(
            Plan([InvokeDomainQueryPlanItem(self._parse("?X.price(X)"), min_results=1, max_results=1)])
        )

    def test_invoke_domain_query_use_wh_question_default(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<invoke_domain_query predicate="price"/>')
        self._then_result_has_plan(
            Plan([InvokeDomainQueryPlanItem(self._parse("?X.price(X)"), min_results=1, max_results=1)])
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
                    "MockupOntology", "MockupAction", preconfirm=InvokeServiceActionPlanItem.ASSERTIVE
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
            self._then_warning_is_issued(mocked_warnings, expected_warning_message, DeprecationWarning)

    def test_jumpto(self):
        self._given_compiled_ontology()
        self._when_compile_domain_with_plan('<jumpto type="perform" action="top"/>')
        self._then_result_has_plan(Plan([self._parse("jumpto(perform(top))")]))

    def test_assume_issue(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<assume_issue type="wh_question" predicate="price"/>')
        self._then_result_has_plan(Plan([self._parse("assume_issue(?X.price(X))")]))

    def test_insist_assume_issue(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan('<assume_issue insist="true" type="wh_question" predicate="price"/>')
        self._then_result_has_plan(Plan([self._parse("insist_assume_issue(?X.price(X))")]))

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
        self._then_result_has_plan(Plan([self._parse("assume_shared(price(123.0))")]))

    def test_assume_system_belief(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<assume_system_belief>
  <proposition predicate="price" value="123.0"/>
</assume_system_belief>"""
        )
        self._then_result_has_plan(Plan([self._parse("assume(price(123.0))")]))

    def test_assume_boolean_true(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="yes_or_no" sort="boolean"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<assume_shared>
  <proposition predicate="yes_or_no" value="true"/>
</assume_shared>"""
        )
        self._then_result_has_plan(Plan([self._parse("assume_shared(yes_or_no())")]))

    def test_assume_boolean_false(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="yes_or_no" sort="boolean"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<assume_shared>
  <proposition predicate="yes_or_no" value="false"/>
</assume_shared>"""
        )
        self._then_result_has_plan(Plan([self._parse("assume_shared(~yes_or_no())")]))

    def test_inform_syntactic_sugar(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan("""
<inform>
  <proposition predicate="price" value="123.0"/>
</inform>
""")
        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("price")), [],
                    [self._parse("assume(price(123.0))"),
                     self._parse("assume_issue(?X.price(X))")]
                )
            ])
        )

    def test_inform_can_insist(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<inform insist="true">
  <proposition predicate="price" value="123.0"/>
</inform>
"""
        )
        self._then_result_has_plan(
            Plan(
                reversed([
                    self._parse("forget(price)"),
                    self._parse("assume(price(123.0))"),
                    self._parse("assume_issue(?X.price(X))")
                ])
            )
        )

    def test_inform_insist_false(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<inform insist="false">
  <proposition predicate="price" value="123.0"/>
</inform>
"""
        )
        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("price")), [],
                    [self._parse("assume(price(123.0))"),
                     self._parse("assume_issue(?X.price(X))")]
                )
            ])
        )

    def test_inform_can_generate_end_turn_with_default_0(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<inform insist="false" generate_end_turn="true">
  <proposition predicate="price" value="123.0"/>
</inform>
"""
        )
        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("price")), [], [
                        self._parse("assume(price(123.0))"),
                        self._parse("assume_issue(?X.price(X))"),
                        EndTurnPlanItem(0.0)
                    ]
                )
            ])
        )

    def test_inform_can_be_without_end_turn(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<inform insist="false" generate_end_turn="false">
  <proposition predicate="price" value="123.0"/>
</inform>
"""
        )
        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("price")), [],
                    [self._parse("assume(price(123.0))"),
                     self._parse("assume_issue(?X.price(X))")]
                )
            ])
        )

    def test_inform_can_generate_end_turn_with_custom_value(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan(
            """
<inform insist="false" generate_end_turn="true" expected_passivity="1.0">
  <proposition predicate="price" value="123.0"/>
</inform>
"""
        )
        self._then_result_has_plan(
            Plan([
                IfThenElse(
                    condition.HasSharedValue(self._parse("price")), [], [
                        self._parse("assume(price(123.0))"),
                        self._parse("assume_issue(?X.price(X))"),
                        EndTurnPlanItem(1.0)
                    ]
                )
            ])
        )

    def test_signal_action_completion(self):

        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan("""
<signal_action_completion/>
            """)
        self._then_result_has_plan(Plan([self._parse("signal_action_completion(true)")]))

    def test_signal_action_completion_with_report_parameter(self):

        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan("""
<signal_action_completion postconfirm="false"/>
            """)
        self._then_result_has_plan(Plan([self._parse("signal_action_completion(false)")]))

    def test_signal_action_failure_needs_reason(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan_then_exception_is_raised_matching(
            '<signal_action_failure/>', ViolatesSchemaException, "The attribute 'reason' is required but missing."
        )

    def test_signal_action_failure_with_reason(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <predicate name="price" sort="real"/>
</ontology>"""
        )
        self._when_compile_domain_with_plan("""
<signal_action_failure reason="some_reason"/>
            """)
        self._then_result_has_plan(Plan([self._parse("signal_action_failure(some_reason)")]))

    def test_change_ddd(self):
        self._given_compiled_ontology(
            """
<ontology name="Ontology">
  <sort name="how"/>
  <predicate name="means_of_transport" sort="how"/>
  <individual name="train" sort="how"/>
</ontology>"""
        )

        self._when_compile_domain_with_plan('<change_ddd name="some_ddd"/>')

        self._then_result_has_plan(Plan([self._parse("change_ddd(some_ddd)")]))


class TestServiceInterfaceCompiler(DDDXMLCompilerTestCase):
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
        self._result = DDDXMLCompiler().compile_service_interface(device_xml)

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
            r"Expected service_interface.xml compliant with schema but it's in violation: Element 'parameter', "
            r"attribute 'format': \[facet 'enumeration'\] The value 'something_else' is not an element of the set "
            r"\{'value', 'grammar_entry'\}., line 5"
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
            r"This element is not expected. Expected is one of \( device_module, http \)., line 8"
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
            r"This element is not expected. Expected is one of \( device_module, http \)., line 9"
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
