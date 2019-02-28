# -*- coding: utf-8 -*-

from collections import OrderedDict

import pytest

import tala.nl.gf.resource
from tala.ddd.ddd_py_compiler import DddPyCompiler, DddPyCompilerException, GrammarCompiler
from tala.ddd.parser import Parser
from tala.ddd.test.ddd_compiler_test_case import DddCompilerTestCase
from tala.model.ontology import Ontology
from tala.model.plan import Plan
from tala.model.plan_item import ForgetAllPlanItem
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition
from tala.model.sort import CustomSort, RealSort
from tala.model.individual import Individual
from tala.nl.gf.grammar_entry_types import Constants, Node


class MockGrammarCompiler(GrammarCompiler):
    def _warn(self, warning):
        self.actual_warning = warning


class DddPyCompilerTestCase(DddCompilerTestCase):
    def _given_compiled_ontology(self, domain_name="Domain", **kwargs):
        ontology_args = self._compile_ontology(**kwargs)
        self._ontology = Ontology(**ontology_args)
        self._parser = Parser(self.DDD_NAME, self._ontology, domain_name)

    def _when_compile_ontology(self, **kwargs):
        self._result = self._compile_ontology(**kwargs)

    def _compile_ontology(self, name="Ontology", sorts={}, predicates={}, individuals={}, actions=set()):
        class Ontology:
            pass

        Ontology.__name__ = name
        Ontology.sorts = sorts
        Ontology.predicates = predicates
        Ontology.individuals = individuals
        Ontology.actions = actions
        self._ontology_name = name
        return DddPyCompiler().compile_ontology(Ontology)

    def _when_compile_domain(self, **kwargs):
        class Domain:
            plans = []

        for key, value in kwargs.iteritems():
            setattr(Domain, key, value)

        self._result = DddPyCompiler().compile_domain(self.DDD_NAME, Domain, self._ontology, self._parser)

    def _when_compile_domain_with_plan(self, plan):
        self._when_compile_domain(plans=[{"goal": "perform(top)", "plan": plan}])

    def _when_compile_plan_with_attribute(self, key, value):
        self._when_compile_domain(plans=[{"goal": "perform(top)", "plan": [], key: value}])

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
        self._grammar_compiler = MockGrammarCompiler()
        self._result = self._grammar_compiler.compile(string, self._ontology, self._service_interface)

    def _then_result_is(self, expected_result):
        assert expected_result == self._result

    def _then_grammar_is(self, expected_grammar_children):
        expected_grammar_node = Node(Constants.GRAMMAR, {}, expected_grammar_children)
        assert expected_grammar_node == self._result

    def _then_warning(self, expected_warning):
        assert expected_warning == self._grammar_compiler.actual_warning

    def _predicate(self, *args, **kwargs):
        return Predicate(self._ontology_name, *args, **kwargs)

    def _individual(self, *args, **kwargs):
        return Individual(self._ontology_name, *args, **kwargs)


class TestOntologyCompiler(DddPyCompilerTestCase):
    def test_name(self):
        self._when_compile_ontology(name="MockupOntology")
        self._then_result_has_field("name", "MockupOntology")

    def test_custom_sort(self):
        self._when_compile_ontology(sorts={"city": {}})
        self._then_result_has_field("sorts", set([CustomSort(self._ontology_name, "city")]))

    def test_dynamic_sort(self):
        self._when_compile_ontology(sorts={"city": {"dynamic": True}})
        self._then_result_has_field("sorts", set([CustomSort(self._ontology_name, "city", dynamic=True)]))

    def test_predicate_of_custom_sort(self):
        self._when_compile_ontology(predicates={"dest_city": "city"}, sorts={"city": {}})
        self._then_result_has_field(
            "predicates", set([self._predicate("dest_city", CustomSort(self._ontology_name, "city"))])
        )

    def test_predicate_of_builtin_sort(self):
        self._when_compile_ontology(predicates={"price": "real"})
        self._then_result_has_field("predicates", set([self._predicate("price", RealSort())]))

    def test_predicate_of_dynamic_sort(self):
        self._when_compile_ontology(predicates={"dest_city": "city"}, sorts={"city": {"dynamic": True}})
        self._then_result_has_field(
            "predicates", set([self._predicate("dest_city", CustomSort(self._ontology_name, "city", dynamic=True))])
        )

    def test_feature_of(self):
        self._when_compile_ontology(
            sorts={"city": {}},
            predicates={
                "dest_city": "city",
                "dest_city_type": {
                    "sort": "city",
                    "feature_of": "dest_city"
                }
            }
        )
        self._then_result_has_field(
            "predicates",
            set([
                self._predicate("dest_city", sort=CustomSort(self._ontology_name, "city")),
                self._predicate(
                    "dest_city_type", sort=CustomSort(self._ontology_name, "city"), feature_of_name="dest_city"
                )
            ])
        )

    def test_individuals(self):
        self._when_compile_ontology(individuals={"paris": "city"}, sorts={"city": {}})
        self._then_result_has_field("individuals", {"paris": CustomSort(self._ontology_name, "city")})

    def test_actions(self):
        self._when_compile_ontology(actions=set(["buy"]))
        self._then_result_has_field("actions", set(["buy"]))


class TestPlanCompilation(DddPyCompilerTestCase):
    def test_plan_for_perform_goal(self):
        self._given_compiled_ontology()

        self._when_compile_domain(plans=[{"goal": "perform(top)", "plan": []}])

        self._then_result_has_field("plans", [{"goal": self._parse("perform(top)"), "plan": Plan([])}])

    def test_plan_for_resolve_goal(self):
        self._given_compiled_ontology(predicates={"price": "real"})

        self._when_compile_domain(plans=[{"goal": "resolve(?X.price(X))", "plan": []}])

        self._then_result_has_field("plans", [{"goal": self._parse("resolve(?X.price(X))"), "plan": Plan([])}])

    def test_exception_yielded_if_plans_is_not_list(self):
        self._given_compiled_ontology()
        with pytest.raises(DddPyCompilerException):
            self._when_compile_domain(plans={})

    def test_exception_yielded_if_plan_not_list(self):
        self._given_compiled_ontology()
        with pytest.raises(DddPyCompilerException):
            self._when_compile_domain(plans=[{"goal": "perform(top)", "plan": None}])

    def test_plan_for_action_yields_helpful_exception(self):
        self._given_compiled_ontology()

        with pytest.raises(
                DddPyCompilerException, match='.*: "top" is not a goal\. Perhaps you mean "perform\(top\)"\?'):
            self._when_compile_domain(plans=[{"goal": "top", "plan": []}])

    def test_plan_for_issue_yields_helpful_exception(self):
        self._given_compiled_ontology(predicates={"price": "real"})

        with pytest.raises(
                DddPyCompilerException,
                match='.*: "\?X.price\(X\)" is not a goal\. Perhaps you mean "resolve\(\?X.price\(X\)\)"\?'):
            self._when_compile_domain(plans=[{"goal": "?X.price(X)", "plan": []}])

    def test_plan_stack_order(self):
        self._given_compiled_ontology(
            sorts={
                "how": {},
                "city": {},
            }, predicates={
                "means_of_transport": "how",
                "dest_city": "city",
            }
        )

        self._when_compile_domain_with_plan(["findout(?X.means_of_transport(X))", "findout(?X.dest_city(X))"])

        self._then_result_has_plan(
            Plan([self._parse("findout(?X.dest_city(X))"),
                  self._parse("findout(?X.means_of_transport(X))")])
        )

    def test_preferred(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("preferred", True)
        self._then_result_has_plan_with_attribute("preferred", True)

    def test_accommodate_without_feedback(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("accommodate_without_feedback", True)
        self._then_result_has_plan_with_attribute("accommodate_without_feedback", True)

    def test_dynamic_title(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("dynamic_title", True)
        self._then_result_has_plan_with_attribute("dynamic_title", True)

    def test_restart_on_completion(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("restart_on_completion", True)
        self._then_result_has_plan_with_attribute("restart_on_completion", True)

    def test_gui_context(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_plan_with_attribute("gui_context", ["price"])
        self._then_result_has_plan_with_attribute("gui_context", [self._ontology.get_predicate("price")])

    def test_postplan(self):
        self._given_compiled_ontology()
        self._when_compile_plan_with_attribute("postplan", ["forget_all"])
        self._then_result_has_plan_with_attribute("postplan", Plan([ForgetAllPlanItem()]))

    def test_postconds(self):
        self._given_compiled_ontology(
            predicates={"dest_city": "city"}, sorts={"city": {}}, individuals={"gothenburg": "city"}
        )
        self._when_compile_plan_with_attribute("postconds", ["dest_city(gothenburg)"])
        self._then_result_has_plan_with_attribute(
            "postconds", [
                PredicateProposition(
                    self._predicate("dest_city", CustomSort(self._ontology_name, "city")),
                    self._individual("gothenburg", CustomSort(self._ontology_name, "city"))
                )
            ]
        )

    def test_unsupported_key_in_plan_description_yields_exception(self):
        self._given_compiled_ontology()
        with pytest.raises(DddPyCompilerException):
            self._when_compile_domain(plans=[{"goal": "perform(top)", "plan": [], "unsupported_key": True}])


class DomainCompilerTests(DddPyCompilerTestCase):
    def test_name(self):
        self._given_compiled_ontology()
        self._when_compile_domain()
        self._then_result_has_field("name", "Domain")

    def test_dependency(self):
        self._given_compiled_ontology(
            sorts={
                "city": {},
                "country": {}
            }, predicates={
                "dest_city": "city",
                "dest_country": "country",
            }
        )

        self._when_compile_domain(dependencies={"?X.dest_country(X)": ["?X.dest_city(X)"]})

        self._then_result_has_field(
            "dependencies", {self._parse("?X.dest_country(X)"): set([self._parse("?X.dest_city(X)")])}
        )

    def test_default_questions(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_domain(default_questions=["?X.price(X)"])
        self._then_result_has_field("default_questions", [self._parse("?X.price(X)")])

    def test_default_questions_empty_by_default(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_domain()
        self._then_result_has_field("default_questions", [])

    def test_superactions(self):
        self._given_compiled_ontology(actions=set(["top", "buy"]))

        self._when_compile_domain(
            plans=[{
                "goal": "perform(top)",
                "plan": []
            }, {
                "goal": "perform(buy)",
                "plan": [],
                "superactions": ["top"]
            }]
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
        self._given_compiled_ontology(predicates={"price": "real"})

        self._when_compile_domain(parameters={"?X.price(X)": "{graphical_type=list}"})

        self._then_result_has_field("parameters", {self._parse("?X.price(X)"): {"graphical_type": "list"}})

    def test_predicate_parameters(self):
        self._given_compiled_ontology(sorts={"city": {}}, predicates={"price": "real", "dest_city": "city"})

        self._when_compile_domain(parameters={"price": "{background=[dest_city]}"})

        self._then_result_has_field("parameters", {self._parse("price"): {"background": [self._parse("dest_city")]}})


class TestGrammarCompiler(DddPyCompilerTestCase):
    def test_multiple_variants(self):
        self._given_compiled_ontology(actions=set(["buy"]))
        self._when_compile_grammar('buy = ["buy", "purchase"]')
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
        self._given_compiled_ontology(actions=set(["buy"]))
        self._when_compile_grammar('buy = "purchase"')
        self._then_grammar_is([Node(Constants.ACTION, {"name": "buy"}, [Node(Constants.ITEM, {}, ["purchase"])])])

    def test_action_with_sortal_answer_of_custom_sort(self):
        self._given_compiled_ontology(actions=set(["buy"]), sorts={"city": {}})
        self._when_compile_grammar('buy = "purchase trip to <answer:city>"')
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"},
                [Node(Constants.ITEM, {},
                      ["purchase trip to ", Node(Constants.SLOT, {"sort": "city"})])]
            )
        ])

    def test_action_with_sortal_string_answer(self):
        self._given_compiled_ontology(actions=set(["set_comment"]), predicates={"comment": "string"})
        self._when_compile_grammar('set_comment = "tell the hotel that <answer:string>"')
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "set_comment"},
                [Node(Constants.ITEM, {},
                      ["tell the hotel that ", Node(Constants.SLOT, {"sort": "string"})])]
            )
        ])

    def test_action_with_propositional_answer(self):
        self._given_compiled_ontology(actions=set(["buy"]), sorts={"city": {}}, predicates={"dest_city": "city"})
        self._when_compile_grammar('buy = "purchase trip to <answer:dest_city>"')
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "buy"},
                [Node(Constants.ITEM, {},
                      ["purchase trip to ", Node(Constants.SLOT, {"predicate": "dest_city"})])]
            )
        ])

    def test_predicate(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_grammar('price = "price information"')
        self._then_grammar_is([
            Node(Constants.PREDICATE, {"name": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_user_question_with_sortal_answer_of_custom_sort(self):
        self._given_compiled_ontology(sorts={"city": {}}, predicates={"price": "real"})
        self._when_compile_grammar('price_user_question = "price for travelling to <answer:city>"')
        self._then_grammar_is([
            Node(
                Constants.USER_QUESTION, {"predicate": "price"},
                [Node(Constants.ITEM, {},
                      ["price for travelling to ", Node(Constants.SLOT, {"sort": "city"})])]
            )
        ])

    def test_user_question_with_propositional_answer(self):
        self._given_compiled_ontology(sorts={"city": {}}, predicates={"price": "real", "dest_city": "city"})
        self._when_compile_grammar('price_user_question = "price for travelling to <answer:dest_city>"')
        self._then_grammar_is([
            Node(
                Constants.USER_QUESTION, {"predicate": "price"}, [
                    Node(
                        Constants.ITEM, {},
                        ["price for travelling to ",
                         Node(Constants.SLOT, {"predicate": "dest_city"})]
                    )
                ]
            )
        ])

    def test_user_question_warning_for_undeclared_predicate(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('undeclaredpredicate_user_question = "foo"')
        self._then_warning("failed to parse grammar entry key 'undeclaredpredicate_user_question'")

    def test_system_question(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_grammar('price_sys_question = "price information"')
        self._then_grammar_is([
            Node(Constants.SYS_QUESTION, {"predicate": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_system_question_warning_for_undeclared_predicate(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('undeclaredpredicate_sys_question = "foo"')
        self._then_warning("failed to parse grammar entry key 'undeclaredpredicate_sys_question'")

    def test_noun_phrase_as_single_variant(self):
        self._given_compiled_ontology()
        self._when_compile_grammar_with_noun_phrase_as_single_variant()
        self._then_result_has_expected_noun_phrase_as_single_variant()

    def _when_compile_grammar_with_noun_phrase_as_single_variant(self):
        self._compile_grammar("""
from tala.nl.gf.resource_eng import NP
top = NP("start view")
""")

    def _then_result_has_expected_noun_phrase_as_single_variant(self):
        self._then_grammar_is([
            Node(
                Constants.ACTION, {"name": "top"},
                [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, ["start view"])])]
            )
        ])

    def test_english_verb_phrase_as_single_variant(self):
        self._given_compiled_ontology(actions=set(["buy"]))
        self._when_compile_english_grammar_with_verb_phrase_as_single_variant()
        self._then_result_has_expected_english_verb_phrase_as_single_variant()

    def _when_compile_english_grammar_with_verb_phrase_as_single_variant(self):
        self._compile_grammar(
            """
from tala.nl.gf.resource_eng import VP
buy = VP("buy", "buy", "buying", "a ticket")
"""
        )

    def _then_result_has_expected_english_verb_phrase_as_single_variant(self):
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

    def test_swedish_verb_phrase_as_single_variant(self):
        self._given_compiled_ontology(actions=set(["buy"]))
        self._when_compile_swedish_grammar_with_verb_phrase_as_single_variant()
        self._then_result_has_expected_swedish_verb_phrase_as_single_variant()

    def _when_compile_swedish_grammar_with_verb_phrase_as_single_variant(self):
        self._compile_grammar(
            """
#-*- coding: utf-8 -*-
from tala.nl.gf.resource_sv import VP
buy = VP(u"köpa", u"köp", u"köper", u"en biljett")
"""
        )

    def _then_result_has_expected_swedish_verb_phrase_as_single_variant(self):
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

    def test_english_verb_phrase_among_multiple_variants(self):
        self._given_compiled_ontology(actions=set(["buy"]))
        self._when_compile_english_grammar_with_verb_phrase_among_multiple_variants()
        self._then_result_has_expected_english_verb_phrase_among_multiple_variants()

    def _when_compile_english_grammar_with_verb_phrase_among_multiple_variants(self):
        self._compile_grammar(
            """
from tala.nl.gf.resource_eng import VP
buy = [VP("buy", "buy", "buying", "a ticket"), "purchase"]
"""
        )

    def _then_result_has_expected_english_verb_phrase_among_multiple_variants(self):
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

    def test_italian_noun_phrase_as_single_variant(self):
        self._given_compiled_ontology(actions=set(["settings"]))
        self._when_compile_italian_noun_phrase_as_single_variant()
        self._then_result_has_expected_italian_noun_phrase_as_single_variant()

    def _when_compile_italian_noun_phrase_as_single_variant(self):
        self._compile_grammar(
            """#-*- coding: utf-8 -*-
from tala.nl.gf.resource_it import NP, PLURAL, FEMININE
settings = NP(u"impostazioni", number=PLURAL, gender=FEMININE)
"""
        )

    def _then_result_has_expected_italian_noun_phrase_as_single_variant(self):
        self._then_grammar_is([
            Node(
                Constants.ACTION, {
                    "name": "settings",
                    "number": tala.nl.gf.resource.PLURAL,
                    "gender": tala.nl.gf.resource.FEMININE
                }, [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"impostazioni"])])]
            )
        ])

    def test_italian_noun_phrase_among_multiple_variants(self):
        self._given_compiled_ontology(actions=set(["settings"]))
        self._when_compile_italian_noun_phrase_among_multiple_variants()
        self._then_result_has_expected_italian_noun_phrase_among_multiple_variants()

    def _when_compile_italian_noun_phrase_among_multiple_variants(self):
        self._compile_grammar(
            """#-*- coding: utf-8 -*-
from tala.nl.gf.resource_it import NP, PLURAL, FEMININE
settings = [NP(u"impostazioni", number=PLURAL, gender=FEMININE), u"vedere l'impostazioni"]
"""
        )

    def _then_result_has_expected_italian_noun_phrase_among_multiple_variants(self):
        self._then_grammar_is([
            Node(
                Constants.ACTION, {
                    "name": "settings",
                    "number": tala.nl.gf.resource.PLURAL,
                    "gender": tala.nl.gf.resource.FEMININE
                }, [
                    Node(
                        Constants.ONE_OF, {}, [
                            Node(
                                Constants.ITEM, {},
                                [Node(Constants.NP, {}, [Node(Constants.INDEFINITE, {}, [u"impostazioni"])])]
                            ),
                            Node(Constants.ITEM, {}, [u"vedere l'impostazioni"])
                        ]
                    )
                ]
            )
        ])

    def test_noun_phrase_among_multiple_variants(self):
        self._given_compiled_ontology()
        self._when_compile_grammar_with_noun_phrase_among_multiple_variants()
        self._then_result_has_expected_noun_phrase_among_multiple_variants()

    def _when_compile_grammar_with_noun_phrase_among_multiple_variants(self):
        self._compile_grammar(
            """
from tala.nl.gf.resource_eng import NP
top = [NP("start view", "the start view"), "main menu"]
"""
        )

    def _then_result_has_expected_noun_phrase_among_multiple_variants(self):
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

    def test_answer_combination(self):
        self._given_compiled_ontology(sorts={"city": {}}, predicates={"dest_city": "city", "dept_city": "city"})
        self._when_compile_grammar(
            '''ANSWER = ["from <answer:dept_city> to <answer:dest_city>",
                                                "from <answer:dept_city>"]'''
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
        self._when_compile_grammar('IncomingCall_started = "incoming call"')
        self._then_grammar_is([
            Node(Constants.REPORT_STARTED, {"action": "IncomingCall"}, [Node(Constants.ITEM, {}, ["incoming call"])])
        ])

    def test_report_ended(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_grammar('IncomingCall_ended = "call ended"')
        self._then_grammar_is([
            Node(Constants.REPORT_ENDED, {"action": "IncomingCall"}, [Node(Constants.ITEM, {}, ["call ended"])])
        ])

    def test_action_with_empty_string(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("IncomingCall")
        self._when_compile_grammar('IncomingCall_ended = ""')
        self._then_grammar_is([
            Node(Constants.REPORT_ENDED, {"action": "IncomingCall"}, [Node(Constants.ITEM, {}, [])])
        ])

    def test_report_ended_warning_for_undeclared_service_action(self):
        self._given_compiled_ontology()
        self._given_service_interface_without_actions()
        self._when_compile_grammar('undeclared_action_ended = "string"')
        self._then_warning("failed to parse grammar entry key 'undeclared_action_ended'")

    def test_report_failed(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("CancelReservation")
        self._when_compile_grammar('CancelReservation_failed_no_reservation_exists = "there is no reservation"')
        self._then_grammar_is([
            Node(
                Constants.REPORT_FAILED, {
                    "action": "CancelReservation",
                    "reason": "no_reservation_exists"
                }, [Node(Constants.ITEM, {}, ["there is no reservation"])]
            )
        ])

    def test_individual(self):
        self._given_compiled_ontology(individuals={"city_1": "city"}, sorts={"city": {}})
        self._when_compile_grammar('city_1 = "paris"')
        self._then_grammar_is([Node(Constants.INDIVIDUAL, {"name": "city_1"}, [Node(Constants.ITEM, {}, ["paris"])])])

    def test_system_answer(self):
        self._given_compiled_ontology(predicates={"dest_city": "city"}, sorts={"city": {}})
        self._when_compile_grammar('dest_city_sys_answer = "to <individual>"')
        self._then_grammar_is([
            Node(
                Constants.SYS_ANSWER, {"predicate": "dest_city"},
                [Node(Constants.ITEM, {}, ["to ", Node(Constants.SLOT, {})])]
            )
        ])

    def test_system_answer_with_embedded_answer(self):
        self._given_compiled_ontology(predicates={"price": "real", "dest_city": "city"}, sorts={"city": {}})
        self._when_compile_grammar('price_sys_answer = "the price to <answer:dest_city> is <individual>"')
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
        self._given_compiled_ontology(predicates={"qualified": "boolean"})
        self._when_compile_grammar('qualified_positive_sys_answer = "you are qualified"')
        self._then_grammar_is([
            Node(
                Constants.POSITIVE_SYS_ANSWER, {"predicate": "qualified"},
                [Node(Constants.ITEM, {}, ["you are qualified"])]
            )
        ])

    def test_negative_system_answer(self):
        self._given_compiled_ontology(predicates={"qualified": "boolean"})
        self._when_compile_grammar('qualified_negative_sys_answer = "you are not qualified"')
        self._then_grammar_is([
            Node(
                Constants.NEGATIVE_SYS_ANSWER, {"predicate": "qualified"},
                [Node(Constants.ITEM, {}, ["you are not qualified"])]
            )
        ])

    def test_action_title(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('top_title = "main menu"')
        self._then_grammar_is([
            Node(Constants.ACTION_TITLE, {"action": "top"}, [Node(Constants.ITEM, {}, ["main menu"])])
        ])

    def test_issue_title(self):
        self._given_compiled_ontology(predicates={"price": "real"})
        self._when_compile_grammar('price_title = "price information"')
        self._then_grammar_is([
            Node(Constants.ISSUE_TITLE, {"predicate": "price"}, [Node(Constants.ITEM, {}, ["price information"])])
        ])

    def test_warning_for_invalid_title_key(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('somethinginvalid_title = "foo"')
        self._then_warning("failed to parse grammar entry key 'somethinginvalid_title'")

    def test_validity(self):
        self._given_compiled_ontology(predicates={"dest_city": "city"}, sorts={"city": {}})
        self._given_service_interface_with_validity("CityValidity")
        self._when_compile_grammar('CityValidity = "invalid city <answer:dest_city>"')
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
        self._when_compile_grammar('MakeReservation_prereport = "making the reservation"')
        self._then_grammar_is([
            Node(
                Constants.PREREPORT, {"action": "MakeReservation"},
                [Node(Constants.ITEM, {}, ["making the reservation"])]
            )
        ])

    def test_preconfirm(self):
        self._given_compiled_ontology()
        self._given_service_interface_with_action("MakeReservation")
        self._when_compile_grammar('MakeReservation_preconfirm = "would you like to make the reservation"')
        self._then_grammar_is([
            Node(
                Constants.PRECONFIRM, {"action": "MakeReservation"},
                [Node(Constants.ITEM, {}, ["would you like to make the reservation"])]
            )
        ])

    def test_greeting(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('greeting = "Welcome"')
        self._then_grammar_is([Node(Constants.GREETING, {}, [Node(Constants.ITEM, {}, ["Welcome"])])])

    def test_invalid_key_is_causes_warning(self):
        self._given_compiled_ontology()
        self._when_compile_grammar('invalid_key = "string"')
        self._then_warning("failed to parse grammar entry key 'invalid_key'")

    def test_decompile_key_with_single_arg(self):
        assert "price_user_question" == GrammarCompiler()._decompile_key(
            Node(Constants.USER_QUESTION, {"predicate": "price"}))

    def test_decompile_key_with_multiple_args(self):
        parameters = OrderedDict()
        parameters["reason"] = "no_reservation_exists"
        parameters["action"] = "CancelReservation"
        assert "CancelReservation_failed_no_reservation_exists" == GrammarCompiler()._decompile_key(
            Node(Constants.REPORT_FAILED, parameters))

    def test_decompile_key_without_args(self):
        assert "ANSWER" == GrammarCompiler()._decompile_key(Node(Constants.ANSWER_COMBINATION, {}))

    def test_decompile_node(self):
        assert u'make_reservation = "make reservation"\n' == GrammarCompiler().decompile_node(
                Node(Constants.ACTION, {'name': 'make_reservation'}, [u'make reservation'])
            )
