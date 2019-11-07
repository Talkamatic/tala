import unittest

from tala.ddd.parser import Parser, ParseError
from tala.model.action import Action
from tala.model.domain import Domain
from tala.model.goal import PerformGoal, ResolveGoal, HandleGoal
from tala.model.individual import Individual, Yes, No
from tala.model.lambda_abstraction import LambdaAbstractedGoalProposition
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.speaker import Speaker
from tala.model.set import Set
from tala.model.move import ICMMove, ICMMoveWithStringContent, ICMMoveWithSemanticContent, IssueICMMove, Move, ReportMove, GreetMove, MuteMove, PrereportMove
from tala.model.ontology import Ontology
from tala.model.plan_item import AssumePlanItem, AssumeSharedPlanItem, AssumeIssuePlanItem, RespondPlanItem, EmitIcmPlanItem, BindPlanItem, ConsultDBPlanItem, JumpToPlanItem, IfThenElse
from tala.model.polarity import Polarity
from tala.model.predicate import Predicate
from tala.model.proposition import ResolvednessProposition, RejectedPropositions, ServiceResultProposition, GoalProposition, ServiceActionStartedProposition, ServiceActionTerminatedProposition, PropositionSet, PredicateProposition
from tala.model.question import WhQuestion
from tala.model.question_raising_plan_item import QuestionRaisingPlanItem, FindoutPlanItem, RaisePlanItem
from tala.model.sort import CustomSort, RealSort, IntegerSort, StringSort, BooleanSort
from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction
from tala.testing.move_factory import MoveFactoryWithPredefinedBoilerplate


class ParserTests(unittest.TestCase):
    def setUp(self):
        self._ddd_name = "mockup_ddd"
        self._create_ontology()
        self._create_domain()
        self._create_semantic_objects()
        self.parser = Parser(self._ddd_name, self.ontology, self.domain_name)
        self._move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology.name)

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        sorts = set([CustomSort(self.ontology_name, "city")])
        predicates = set([
            self._create_predicate("dest_city", CustomSort(self.ontology_name, "city")),
            self._create_predicate("dept_city", CustomSort(self.ontology_name, "city")),
            self._create_predicate("available_dest_city", CustomSort(self.ontology_name, "city")),
            self._create_predicate("price", RealSort()),
            self._create_predicate("number_of_passengers", IntegerSort()),
            self._create_predicate("number_to_call", StringSort()),
            self._create_predicate("need_visa", BooleanSort()),
        ])
        individuals = {
            "paris": CustomSort(self.ontology_name, "city"),
            "london": CustomSort(self.ontology_name, "city")
        }
        actions = set(["top", "buy"])
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

        self.empty_ontology = Ontology("empty_ontology", {}, {}, {}, set([]))

    def _create_predicate(self, *args, **kwargs):
        return Predicate(self.ontology_name, *args, **kwargs)

    def _create_domain(self):
        self.domain_name = "mockup_domain"
        self.domain = Domain(self._ddd_name, self.domain_name, self.ontology, plans={})

    def _create_semantic_objects(self):
        self.predicate_dest_city = self.ontology.get_predicate("dest_city")
        self.predicate_dept_city = self.ontology.get_predicate("dept_city")
        self.predicate_price = self.ontology.get_predicate("price")
        self.predicate_number_to_call = self.ontology.get_predicate("number_to_call")
        self.predicate_need_visa = self.ontology.get_predicate("need_visa")
        self.individual_paris = self.ontology.create_individual("paris")
        self.individual_not_paris = self.ontology.create_negative_individual("paris")
        self.individual_london = self.ontology.create_individual("london")
        self.real_individual = self.ontology.create_individual(1234.0)
        self.integer_individual = self.ontology.create_individual(1234)

        self.proposition_dest_city_paris = PredicateProposition(self.predicate_dest_city, self.individual_paris)
        self.proposition_not_dest_city_paris = PredicateProposition(
            self.predicate_dest_city, self.individual_paris, Polarity.NEG
        )
        self.proposition_dest_city_london = PredicateProposition(self.predicate_dest_city, self.individual_london)
        self.price_proposition = PredicateProposition(self.predicate_price, self.real_individual)
        self.proposition_need_visa = PredicateProposition(self.predicate_need_visa)
        self.proposition_not_need_visa = PredicateProposition(self.predicate_need_visa, polarity=Polarity.NEG)

        self.lambda_abstracted_dest_city_prop = LambdaAbstractedPredicateProposition(
            self.predicate_dest_city, self.ontology_name
        )
        self.lambda_abstracted_price_prop = LambdaAbstractedPredicateProposition(
            self.predicate_price, self.ontology_name
        )

        self.dest_city_question = WhQuestion(self.lambda_abstracted_dest_city_prop)
        self.price_question = WhQuestion(self.lambda_abstracted_price_prop)

        self.buy_action = self.ontology.create_action("buy")
        self.top_action = self.ontology.create_action("top")

    def test_understanding_proposition(self):
        und_string = "und(USR, dest_city(paris))"
        und = self.parser.parse(und_string)
        self.assertTrue(und.is_understanding_proposition())
        self.assertEquals(Speaker.USR, und.get_speaker())

    def test_neg_understanding_proposition(self):
        und_string = "~und(USR, dest_city(paris))"
        und = self.parser.parse(und_string)
        self.assertTrue(und.is_understanding_proposition())

    def test_understanding_question(self):
        und_string = "?und(USR, dest_city(paris))"
        und = self.parser.parse(und_string)
        self.assertTrue(und.is_understanding_question())

    def test_understanding_proposition_with_speaker_none(self):
        und_string = "und(None, dest_city(paris))"
        und = self.parser.parse(und_string)
        self.assertTrue(und.is_understanding_proposition())
        self.assertEquals(None, und.get_speaker())

    def test_create_yes_no_question(self):
        question = self.parser.parse("?dest_city(paris)")  # noqa: F841

    def test_create_nullary_yes_no_question_I(self):
        question = self.parser.parse("?need_visa()")  # noqa: F841

    def test_create_yes(self):
        yes = self.parser.parse("yes")
        self.assertEquals(Yes(), yes)

    def test_create_no(self):
        no = self.parser.parse("no")
        self.assertEquals(No(), no)

    def test_create_yes_answer_move(self):
        yes_move = self.parser.parse("answer(yes)")
        self.assertEquals(Yes(), yes_move.get_content())

    def test_create_no_answer_move(self):
        no_move = self.parser.parse("answer(no)")
        self.assertEquals(No(), no_move.get_content())

    def test_ShortAnswer(self):
        answer_move_from_string = self.parser.parse("answer(paris)")
        answer = self.individual_paris
        answer_move = self._move_factory.createAnswerMove(answer)
        self.assertEquals(answer_move, answer_move_from_string)

    def test_PropositionalAnswerMove(self):
        answer_move_from_string = self.parser.parse("answer(dest_city(paris))")
        individual = self.individual_paris
        answer = PredicateProposition(self.predicate_dest_city, individual)
        answer_move = self._move_factory.createAnswerMove(answer)
        self.assertEquals(answer_move, answer_move_from_string)

    def test_integer_short_answer(self):
        move = self.parser.parse("answer(1234)")
        expected_move = self._move_factory.createAnswerMove(self.integer_individual)
        self.assertEquals(expected_move, move)

    def test_integer_short_answer_with_ontology_without_real_sort(self):
        sorts = set([])
        predicates = set([self._create_predicate("number_of_passengers", IntegerSort())])
        individuals = {}
        actions = set([])
        ontology_without_real_sort = Ontology("ontology_without_real_sort", sorts, predicates, individuals, actions)
        move = Parser(self._ddd_name, ontology_without_real_sort, self.domain_name).parse("answer(1234)")
        self.assertEqual(move.get_type(), Move.ANSWER)
        self.assertTrue(move.get_content().is_individual())
        self.assertEqual(move.get_content().getSort().get_name(), "integer")

    def test_float_short_answer(self):
        move = self.parser.parse("answer(1234.0)")
        expected_move = self._move_factory.createAnswerMove(self.real_individual)
        self.assertEquals(expected_move, move)

    def test_float_answer(self):
        move = self.parser.parse("answer(price(1234.0))")
        expected_move = self._move_factory.createAnswerMove(self.price_proposition)
        self.assertEquals(expected_move, move)

    def test_propositional_usr_answer_move_w_score(self):
        self._when_parse(
            "Move(answer(dest_city(paris)), understanding_confidence=0.45, speaker=USR, ddd_name='mockup_ddd')"
        )
        self._then_result_is(
            MoveFactoryWithPredefinedBoilerplate(
                self.ontology.name, understanding_confidence=0.45, speaker=Speaker.USR, ddd_name="mockup_ddd"
            ).createAnswerMove(PredicateProposition(self.predicate_dest_city, self.individual_paris))
        )

    def _when_parse(self, string):
        self._result = self.parser.parse(string)

    def _then_result_is(self, expected_result):
        self.assertEquals(expected_result, self._result)

    def test_move_with_utterance(self):
        self._when_parse(
            "Move(answer(dest_city(paris)), understanding_confidence=0.45, speaker=USR, "
            "utterance='paris', ddd_name='mockup_ddd')"
        )
        self._then_result_is(
            MoveFactoryWithPredefinedBoilerplate(
                self.ontology.name,
                ddd_name="mockup_ddd",
                understanding_confidence=0.45,
                speaker=Speaker.USR,
                utterance="paris"
            ).createAnswerMove(PredicateProposition(self.predicate_dest_city, self.individual_paris))
        )

    def test_undecorated_move_with_Move_classname(self):
        string = "Move(ask(?set([goal(perform(top)), goal(perform(buy))])))"
        expected_move = self.parser.parse("ask(?set([goal(perform(top)), goal(perform(buy))]))")
        self.assertEquals(expected_move, self.parser.parse(string))

    def test_Individual(self):
        individual_from_string = self.parser.parse("paris")
        self.assertEquals(self.individual_paris, individual_from_string)

    def test_NegativeIndividual(self):
        individual_from_string = self.parser.parse("~paris")
        self.assertEquals(self.individual_not_paris, individual_from_string)

    def test_ask_move(self):
        move_from_string = self.parser.parse("ask(?X.dest_city(X))")
        question = self.parser.parse("?X.dest_city(X)")
        move = self._move_factory.create_ask_move(question)
        self.assertEquals(move, move_from_string)

    def test_ask_move_with_speaker_score(self):
        score = 1.0
        speaker = Speaker.SYS
        move_from_string = self.parser.parse(
            "Move(ask(?X.dest_city(X)), speaker=%s, understanding_confidence=%s, ddd_name='mockup_ddd')" %
            (speaker, score)
        )
        question = self.parser.parse("?X.dest_city(X)")
        move = MoveFactoryWithPredefinedBoilerplate(
            self.ontology.name, speaker=speaker, understanding_confidence=score, ddd_name="mockup_ddd"
        ).create_ask_move(question)
        self.assertEquals(move, move_from_string)

    def test_create_request_move(self):
        request = self.parser.parse("request(buy)")
        self.assertEquals(Move.REQUEST, request.get_type())

    def test_create_request_move_w_score_and_usr(self):
        score = 0.55
        speaker = Speaker.USR
        expected_move = self._move_factory.createMove(
            Move.REQUEST,
            content=Action("buy", self.ontology.get_name()),
            speaker=speaker,
            understanding_confidence=score,
            ddd_name="mockup_ddd"
        )
        request = self.parser.parse(
            "Move(request(buy), speaker=%s, understanding_confidence=%s, ddd_name='mockup_ddd')" % (speaker, score)
        )
        self.assertEquals(expected_move, request)

    def test_create_set_with_single_element(self):
        set_of_moves = self.parser.parse("{request(top)}")
        expected_result = Set(Move)
        expected_result.add(self.parser.parse("request(top)"))
        self.assertEquals(expected_result, set_of_moves)

    def test_create_empty_set(self):
        empty_set = self.parser.parse("{}")
        expected_result = Set()
        self.assertEquals(expected_result, empty_set)

    def test_lambda_abstracted_predicate_proposition(self):
        object = self.parser.parse("X.dest_city(X)")
        expected_object = self.lambda_abstracted_dest_city_prop
        self.assertEquals(expected_object, object)

    def test_lambda_abstracted_goal_proposition(self):
        object = self.parser.parse("X.goal(X)")
        expected_object = LambdaAbstractedGoalProposition()
        self.assertEquals(expected_object, object)

    def test_action(self):
        object = self.parser.parse("buy")
        expected_object = self.buy_action
        self.assertEquals(expected_object, object)

    def test_unary_predicate_proposition(self):
        proposition_from_string = self.parser.parse("dest_city(paris)")
        self.assertEquals(self.proposition_dest_city_paris, proposition_from_string)

    def test_nullary_predicate_proposition(self):
        proposition_from_string = self.parser.parse("need_visa()")
        self.assertEquals(self.proposition_need_visa, proposition_from_string)

    def test_negative_unary_predicate_proposition(self):
        proposition_from_string = self.parser.parse("~dest_city(paris)")
        self.assertEquals(self.proposition_not_dest_city_paris, proposition_from_string)

    def test_negative_nullary_predicate_proposition(self):
        proposition_from_string = self.parser.parse("~need_visa()")
        self.assertEquals(self.proposition_not_need_visa, proposition_from_string)

    def test_positive_perform_proposition(self):
        proposition = self.parser.parse("goal(perform(buy))")
        self.assertTrue(proposition.is_positive())
        self.assertEquals(PerformGoal(self.buy_action), proposition.get_goal())

    def test_negative_action_proposition(self):
        proposition = self.parser.parse("~goal(perform(buy))")
        self.assertFalse(proposition.is_positive())
        self.assertEquals(PerformGoal(self.buy_action), proposition.get_goal())

    def test_illegal_perform_goal(self):
        with self.assertRaises(ParseError):
            self.parser.parse("perform(sdfkjsd)")

    def test_issue_proposition(self):
        object = self.parser.parse("goal(resolve_user(?X.dest_city(X)))")
        expected_object = GoalProposition(ResolveGoal(self.dest_city_question, Speaker.USR))
        self.assertEquals(expected_object, object)

    def test_resolve_goal_containing_non_question_yields_exception(self):
        with self.assertRaises(ParseError):
            self.parser.parse("resolve(buy)")

    def test_resolvedness_proposition(self):
        object = self.parser.parse("resolved(?X.dest_city(X))")
        expected_object = ResolvednessProposition(self.dest_city_question)
        self.assertEquals(expected_object, object)

    def test_positive_preconfirmation(self):
        preconfirmation = self.parser.parse("preconfirmed(MakeReservation, [])")
        self.assertTrue(preconfirmation.is_positive())
        self.assertEquals("MakeReservation", preconfirmation.get_service_action())
        self.assertEquals([], preconfirmation.get_arguments())

    def test_negative_preconfirmation(self):
        preconfirmation = self.parser.parse("~preconfirmed(MakeReservation, [])")
        self.assertFalse(preconfirmation.is_positive())
        self.assertEquals("MakeReservation", preconfirmation.get_service_action())
        self.assertEquals([], preconfirmation.get_arguments())

    def test_preconfirmation_w_single_param(self):
        preconfirmation = self.parser.parse("~preconfirmed(MakeReservation, [dest_city(paris)])")
        self.assertEquals(1, len(preconfirmation.get_arguments()))
        self.assertEquals("dest_city(paris)", unicode(preconfirmation.get_arguments()[0]))

    def test_preconfirmation_q_w_single_param(self):
        preconfirmation = self.parser.parse("?preconfirmed(MakeReservation, [dest_city(paris)])")  # noqa: F841

    def test_preconfirmation_q_w_multi_param(self):
        service_action = "MakeReservation"
        prop_1 = "dest_city(paris)"
        prop_2 = "dest_city(london)"
        preconfirmed_string = "?preconfirmed(%s, [%s, %s])" % (service_action, prop_1, prop_2)
        preconfirmation = self.parser.parse(preconfirmed_string)  # noqa: F841

    def test_rejected_proposition(self):
        object = self.parser.parse("rejected(set([dest_city(paris)]))")
        expected_object = RejectedPropositions(PropositionSet([self.proposition_dest_city_paris]))
        self.assertEquals(expected_object, object)

    def test_rejected_proposition_with_reason(self):
        object = self.parser.parse("rejected(set([dest_city(paris)]), some_reason)")
        expected_object = RejectedPropositions(PropositionSet([self.proposition_dest_city_paris]), reason="some_reason")
        self.assertEquals(expected_object, object)

    def test_create_prereport(self):
        confirmation = self.parser.parse("prereported(MakeReservation, [])")
        self.assertEquals("MakeReservation", confirmation.get_service_action())
        self.assertEquals([], confirmation.get_arguments())

    def test_create_prereport_w_single_param(self):
        prereport = self.parser.parse("prereported(MakeReservation, [dest_city(paris)])")
        self.assertEquals(1, len(prereport.get_arguments()))
        self.assertEquals("dest_city(paris)", unicode(prereport.get_arguments()[0]))

    def test_create_prereport_w_multi_param(self):
        service_action = "MakeReservation"
        prop_1 = "dest_city(paris)"
        prop_2 = "dest_city(london)"
        prereport_string = "?prereported(%s, [%s, %s])" % (service_action, prop_1, prop_2)
        prereport = self.parser.parse(prereport_string)  # noqa: F841

    def test_report_move_successful_with_parameters(self):
        object = self.parser.parse(
            "report(ServiceResultProposition("
            "MakeReservation, [dest_city(paris), dest_city(london)], SuccessfulServiceAction()))"
        )
        expected_object = ReportMove(
            ServiceResultProposition(
                self.ontology_name, "MakeReservation",
                [self.proposition_dest_city_paris, self.proposition_dest_city_london], SuccessfulServiceAction()
            )
        )
        self.assertEquals(expected_object, object)

    def test_report_move_successful(self):
        object = self.parser.parse("report(ServiceResultProposition(MakeReservation, [], SuccessfulServiceAction()))")
        expected_object = ReportMove(
            ServiceResultProposition(self.ontology_name, "MakeReservation", [], SuccessfulServiceAction())
        )
        self.assertEquals(expected_object, object)

    def test_report_move_failed(self):
        object = self.parser.parse(
            "report(ServiceResultProposition(MakeReservation, [], FailedServiceAction(no_itinerary_found)))"
        )
        expected_object = ReportMove(
            ServiceResultProposition(
                self.ontology_name, "MakeReservation", [], FailedServiceAction("no_itinerary_found")
            )
        )
        self.assertEquals(expected_object, object)

    def test_prereport_move(self):
        object = self.parser.parse("prereport(MakeReservation, [dest_city(paris), dest_city(london)])")
        expected_object = PrereportMove(
            self.ontology_name, "MakeReservation",
            [self.proposition_dest_city_paris, self.proposition_dest_city_london]
        )
        self.assertEquals(expected_object, object)

    def test_create_DoPlanItem(self):
        action = self.parser.parse("buy")
        do_item = self.parser.parse("do(buy)")
        self.assertEquals(action, do_item.getContent())

    def test_create_EmitIcmPlanItem(self):
        icm_move = self.parser.parse("icm:und*pos:USR*goal(perform(buy))")
        item = EmitIcmPlanItem(icm_move)
        self.assertEquals(icm_move, item.getContent())
        self.assertTrue(item.isEmitIcmPlanItem())

    def test_FindoutPlanItem_with_no_params(self):
        expected_item = FindoutPlanItem(self.domain_name, self.dest_city_question)
        item = self.parser.parse("findout(?X.dest_city(X))")
        self.assertEquals(expected_item, item)
        self.assertEquals(self.dest_city_question, item.getContent())

    def test_multiple_parameters(self):
        string = "{graphical_type=list, incremental=True}"
        params = self.parser.parse_parameters(string)
        expected_params = {"graphical_type": "list", "incremental": True}
        self.assertEquals(expected_params, params)

    def test_boolean_parameter_leading_uppercase(self):
        string = "{incremental=True}"
        params = self.parser.parse_parameters(string)
        expected_params = {"incremental": True}
        self.assertEquals(expected_params, params)

    def test_boolean_parameter_lowercase(self):
        string = "{incremental=true}"
        params = self.parser.parse_parameters(string)
        expected_params = {"incremental": True}
        self.assertEquals(expected_params, params)

    def test_verbalize_parameter(self):
        string = "{verbalize=True}"
        params = self.parser.parse_parameters(string)
        expected_params = {"verbalize": True}
        self.assertEquals(expected_params, params)

    def test_parameters_with_empty_alts(self):
        string = "{alts=set([])}"
        params = self.parser.parse_parameters(string)
        expected_params = {"alts": PropositionSet([])}
        self.assertEquals(expected_params, params)

    def test_parameters_with_single_alt(self):
        string = "{alts=set([goal(perform(buy))])}"
        params = self.parser.parse_parameters(string)
        expected_params = {"alts": PropositionSet([self.parser.parse("goal(perform(buy))")])}
        self.assertEquals(expected_params, params)

    def test_parameters_with_multiple_alts(self):
        string = "{alts=set([goal(perform(top)), goal(perform(buy))])}"
        params = self.parser.parse_parameters(string)
        expected_params = {
            "alts": PropositionSet([self.parser.parse("goal(perform(top))"),
                                    self.parser.parse("goal(perform(buy))")])
        }
        self.assertEquals(expected_params, params)

    def test_graphical_type_param_list(self):
        string = "{graphical_type=list}"
        params = self.parser.parse_parameters(string)
        expected_params = {"graphical_type": QuestionRaisingPlanItem.GRAPHICAL_TYPE_LIST}
        self.assertEquals(expected_params, params)

    def test_graphical_type_param_text(self):
        string = "{graphical_type=text}"
        params = self.parser.parse_parameters(string)
        expected_params = {"graphical_type": QuestionRaisingPlanItem.GRAPHICAL_TYPE_TEXT}
        self.assertEquals(expected_params, params)

    def test_source_param_service(self):
        string = "{source=service}"
        params = self.parser.parse_parameters(string)
        expected_params = {"source": QuestionRaisingPlanItem.SOURCE_SERVICE}
        self.assertEquals(expected_params, params)

    def test_source_param_domain(self):
        string = "{source=domain}"
        params = self.parser.parse_parameters(string)
        expected_params = {"source": QuestionRaisingPlanItem.SOURCE_DOMAIN}
        self.assertEquals(expected_params, params)

    def test_service_query_param(self):
        string = "{service_query=?X.available_dest_city(X)}"
        params = self.parser.parse_parameters(string)
        expected_params = {"service_query": self.parser.parse("?X.available_dest_city(X)")}
        self.assertEquals(expected_params, params)

    def test_device_param(self):
        string = "{device=travel_booker}"
        params = self.parser.parse_parameters(string)
        expected_params = {"device": "travel_booker"}
        self.assertEquals(expected_params, params)

    def test_sort_parameter(self):
        string = "{sort_order=alphabetic}"
        params = self.parser.parse_parameters(string)
        expected_params = {"sort_order": QuestionRaisingPlanItem.ALPHABETIC}
        self.assertEquals(expected_params, params)

    def test_background_parameter(self):
        string = "{background=[dest_city, dept_city]}"
        params = self.parser.parse_parameters(string)
        expected_params = {"background": [self.predicate_dest_city, self.predicate_dept_city]}
        self.assertEquals(expected_params, params)

    def test_background_parameter_with_illegal_value(self):
        string = "{background=?X.dest_city(X)}"
        with self.assertRaises(ParseError):
            self.parser.parse_parameters(string)

    def test_allow_goal_accommodation_parameter(self):
        string = "{allow_goal_accommodation=True}"
        params = self.parser.parse_parameters(string)
        expected_params = {"allow_goal_accommodation": True}
        self.assertEquals(expected_params, params)

    def test_max_spoken_alts_parameter(self):
        string = "{max_spoken_alts=2}"
        params = self.parser.parse_parameters(string)
        expected_params = {"max_spoken_alts": 2}
        self.assertEquals(expected_params, params)

    def test_related_information_parameter(self):
        string = "{related_information=[?X.price(X)]}"
        params = self.parser.parse_parameters(string)
        expected_params = {"related_information": [self.price_question]}
        self.assertEquals(expected_params, params)

    def test_ask_features_parameter(self):
        string = "{ask_features=[dest_city, dept_city]}"
        params = self.parser.parse_parameters(string)
        expected_params = {"ask_features": [self.predicate_dest_city, self.predicate_dept_city]}
        self.assertEquals(expected_params, params)

    def test_illegal_parameter_raises_exception(self):
        with self.assertRaises(ParseError):
            self.parser.parse("{sldkfjs=ksjhdf}")

    def test_create_RaisePlanItem(self):
        item = self.parser.parse("raise(?X.dest_city(X))")
        expected_item = RaisePlanItem(self.domain_name, self.dest_city_question)
        self.assertEquals(expected_item, item)

    def test_create_FindoutPlanItem_with_non_question(self):
        with self.assertRaises(ParseError):
            self.parser.parse("findout(X.dest_city(X))")

    def test_create_RaisePlanItem_with_non_question(self):
        with self.assertRaises(ParseError):
            self.parser.parse("raise(X.dest_city(X))")

    def test_create_BindPlanItem(self):
        item = self.parser.parse("bind(?X.dest_city(X))")
        expected_item = BindPlanItem(self.dest_city_question)
        self.assertEquals(expected_item, item)

    def test_create_BindPlanItem_with_non_question(self):
        with self.assertRaises(ParseError):
            self.parser.parse("bind(X.dest_city(X))")

    def test_create_RespondPlanItem(self):
        item = self.parser.parse("respond(?X.dest_city(X))")
        expected_item = RespondPlanItem(self.dest_city_question)
        self.assertEquals(expected_item, item)

    def test_create_ConsultDBPlanItem(self):
        item = self.parser.parse("consultDB(?X.dest_city(X))")
        expected_item = ConsultDBPlanItem(self.dest_city_question)
        self.assertEquals(expected_item, item)

    def test_create_if_then_else(self):
        string = "if dest_city(paris) then jumpto(perform(top)) else jumpto(perform(buy))"
        item = self.parser.parse(string)
        expected_item = IfThenElse(
            self.proposition_dest_city_paris, JumpToPlanItem(PerformGoal(self.top_action)),
            JumpToPlanItem(PerformGoal(self.buy_action))
        )
        self.assertEquals(expected_item, item)

    def test_create_if_then_else_resolvedness_from_string(self):
        string = "if resolved(?X.dest_city(X))" " then jumpto(perform(top))" " else jumpto(perform(buy))"
        item = self.parser.parse(string)

        expected_item = IfThenElse(
            ResolvednessProposition(self.dest_city_question), JumpToPlanItem(PerformGoal(self.top_action)),
            JumpToPlanItem(PerformGoal(self.buy_action))
        )
        self.assertEquals(expected_item, item)

    def test_create_if_then_else_resolvedness_no_else_from_string(self):
        string = "if resolved(?X.dest_city(X))" " then jumpto(perform(top))" " else "
        item = self.parser.parse(string)

        expected_item = IfThenElse(
            ResolvednessProposition(self.dest_city_question), JumpToPlanItem(PerformGoal(self.top_action)), None
        )
        self.assertEquals(expected_item, item)

    def test_create_if_then_else_resolvedness_no_then_from_string(self):
        string = "if resolved(?X.dest_city(X))" " then " " else jumpto(perform(top))"
        item = self.parser.parse(string)

        expected_item = IfThenElse(
            ResolvednessProposition(self.dest_city_question), None, JumpToPlanItem(PerformGoal(self.top_action))
        )
        self.assertEquals(expected_item, item)

    def test_create_forget_all_from_string(self):
        item = self.parser.parse("forget_all")
        self.assertTrue(item.is_forget_all_plan_item())

    def test_create_forget(self):
        fact = self.parser.parse("dest_city(paris)")
        item = self.parser.parse("forget(%s)" % fact)
        self.assertTrue(item.is_forget_plan_item())
        self.assertEqual(fact, item.getContent())

    def test_create_forget_predicate(self):
        predicate = self.parser.parse("dest_city")
        item = self.parser.parse("forget(%s)" % predicate)
        self.assertTrue(item.is_forget_plan_item())
        self.assertEqual(predicate, item.getContent())

    def test_create_forget_issue(self):
        issue = self.parser.parse("?X.dest_city(X)")
        item = self.parser.parse("forget_issue(%s)" % issue)
        self.assertTrue(item.is_forget_issue_plan_item())
        self.assertEqual(issue, item.getContent())

    def test_create_invoke_service_query_plan_item(self):
        issue = self.parser.parse("?X.dest_city(X)")
        item = self.parser.parse("invoke_service_query(%s)" % issue)
        self.assertTrue(item.is_invoke_service_query_plan_item())
        self.assertEqual(issue, item.getContent())
        self.assertEqual(1, item.get_min_results())
        self.assertEqual(1, item.get_max_results())

    def test_create_deprecated_dev_query_plan_item(self):
        issue = self.parser.parse("?X.dest_city(X)")
        item = self.parser.parse("dev_query(%s)" % issue)
        self.assertTrue(item.is_invoke_service_query_plan_item())
        self.assertEqual(issue, item.getContent())
        self.assertEqual(1, item.get_min_results())
        self.assertEqual(1, item.get_max_results())

    def test_invoke_service_action_no_params(self):
        service_action = "MakeReservation"
        item = self.parser.parse("invoke_service_action(%s, {})" % service_action)
        self.assertTrue(item.is_invoke_service_action_plan_item())
        self.assertEqual(service_action, item.get_service_action())

    def test_invoke_service_action_postconfirmed_and_preconfirmed_assertively(self):
        params_string = "{postconfirm=True, preconfirm=assertive}"
        service_action = "MakeReservation"
        item = self.parser.parse("invoke_service_action(%s, %s)" % (service_action, params_string))
        self.assertTrue(item.has_postconfirmation())
        self.assertTrue(item.has_assertive_preconfirmation())

    def test_invoke_service_action_preconfirmed_interrogatively(self):
        params_string = "{preconfirm=interrogative}"
        service_action = "MakeReservation"
        item = self.parser.parse("invoke_service_action(%s, %s)" % (service_action, params_string))
        self.assertTrue(item.has_interrogative_preconfirmation())

    def test_invoke_service_action_downdate_plan_true_by_default(self):
        params_string = "{}"
        service_action = "MakeReservation"
        item = self.parser.parse("invoke_service_action(%s, %s)" % (service_action, params_string))
        self.assertTrue(item.should_downdate_plan())

    def test_invoke_service_action_downdate_plan_overridable(self):
        params_string = "{downdate_plan=False}"
        service_action = "MakeReservation"
        item = self.parser.parse("invoke_service_action(%s, %s)" % (service_action, params_string))
        self.assertFalse(item.should_downdate_plan())

    def test_deprecated_dev_perform_no_params(self):
        service_action = "MakeReservation"
        item = self.parser.parse("dev_perform(%s, {})" % service_action)
        self.assertTrue(item.is_invoke_service_action_plan_item())
        self.assertEqual(service_action, item.get_service_action())

    def test_deprecated_dev_perform_postconfirmed_and_preconfirmed_assertively(self):
        params_string = "{postconfirm=True, preconfirm=assertive}"
        service_action = "MakeReservation"
        item = self.parser.parse("dev_perform(%s, %s)" % (service_action, params_string))
        self.assertTrue(item.has_postconfirmation())
        self.assertTrue(item.has_assertive_preconfirmation())

    def test_deprecated_dev_perform_preconfirmed_interrogatively(self):
        params_string = "{preconfirm=interrogative}"
        service_action = "MakeReservation"
        item = self.parser.parse("dev_perform(%s, %s)" % (service_action, params_string))
        self.assertTrue(item.has_interrogative_preconfirmation())

    def test_create_yesno_question(self):
        question = self.parser.parse("?dest_city(paris)")
        self.assertTrue(question.is_yes_no_question())

    def test_create_single_alt_question(self):
        alt_question_string = "?set([goal(perform(buy))])"
        question = self.parser.parse(alt_question_string)
        self.assertEquals(alt_question_string, unicode(question))

    def test_create_alt_question_with_predicate_propositions(self):
        alt_question_string = "?set([goal(perform(top)), goal(perform(buy))])"
        question = self.parser.parse(alt_question_string)
        self.assertEquals(alt_question_string, unicode(question))

    def test_create_alt_question_with_goal_propositions(self):
        alt_question_string = "?set([goal(perform(buy)), goal(perform(top))])"
        question = self.parser.parse(alt_question_string)
        self.assertEquals(alt_question_string, unicode(question))

    def test_create_single_alt_question_with_issue_proposition(self):
        alt_question_string = "?set([goal(resolve(?X.goal(X)))])"
        question = self.parser.parse(alt_question_string)
        self.assertEquals(alt_question_string, unicode(question))

    def test_create_single_neg_alt_question(self):
        alt_question_string = "?set([~goal(perform(buy))])"
        question = self.parser.parse(alt_question_string)
        self.assertEquals(alt_question_string, unicode(question))

    def test_is_alt_question_when_created(self):
        question_as_string = "?set([goal(perform(top)), goal(perform(buy))])"
        question = self.parser.parse(question_as_string)
        self.assertTrue(question.is_alt_question())

    def test_proposition_set_with_action_and_issue_propositions(self):
        string = "set([goal(perform(buy)), goal(resolve(?X.price(X)))])"
        object = self.parser.parse(string)
        expected_object = PropositionSet([
            GoalProposition(PerformGoal(self.buy_action)),
            GoalProposition(ResolveGoal(self.price_question, Speaker.SYS))
        ])
        self.assertEquals(expected_object, object)

    def test_negative_proposition_set_with_action_and_issue_propositions(self):
        string = "~set([goal(perform(buy)), goal(resolve(?X.price(X)))])"
        object = self.parser.parse(string)
        expected_object = PropositionSet([
            GoalProposition(PerformGoal(self.buy_action)),
            GoalProposition(ResolveGoal(self.price_question, Speaker.SYS))
        ],
                                         polarity=Polarity.NEG)
        self.assertEquals(expected_object, object)

    def test_greet_move(self):
        move = self.parser.parse("greet")
        self.assertEquals(GreetMove(), move)

    def test_user_greet_move_with_speaker_and_score(self):
        move = self.parser.parse("Move(greet, ddd_name='mockup_ddd', speaker=USR, understanding_confidence=0.47)")
        self.assertEquals(Speaker.USR, move.get_speaker())
        self.assertEquals(0.47, move.understanding_confidence)

    def test_mute_move(self):
        move = self.parser.parse("mute")
        self.assertEquals(MuteMove(), move)

    def test_sys_mute_move_with_score(self):
        move = self.parser.parse("Move(mute, speaker=SYS, understanding_confidence=1.0)")
        self.assertEquals(Speaker.SYS, move.get_speaker())
        self.assertEquals(1.0, move.understanding_confidence)

    def test_move_without_score(self):
        move = self.parser.parse("Move(greet, speaker=SYS)")
        self.assertEquals(Speaker.SYS, move.get_speaker())

    def test_unmute_move(self):
        move = self.parser.parse("unmute")
        self.assertEquals(Move.UNMUTE, move.get_type())

    def test_quit_move(self):
        move = self.parser.parse("quit")
        self.assertEquals(Move.QUIT, move.get_type())

    def test_contentful_reraise(self):
        move = self.parser.parse("icm:reraise:top")
        self.assertEquals(ICMMove.RERAISE, move.get_type())
        self.assertEquals(self.top_action, move.get_content())

    def test_contentless_reraise(self):
        move = self.parser.parse("icm:reraise")
        self.assertEquals(ICMMove.RERAISE, move.get_type())

    def test_reraise_with_speaker_and_score(self):
        speaker = Speaker.SYS
        score = 1.0
        move = self.parser.parse("ICMMove(icm:reraise:top, speaker=%s, understanding_confidence=%s)" % (speaker, score))
        expected_move = ICMMoveWithSemanticContent(
            ICMMove.RERAISE, self.top_action, understanding_confidence=score, speaker=speaker
        )
        self.assertEquals(expected_move, move)

    def test_resume(self):
        move = self.parser.parse("icm:resume:perform(buy)")
        self.assertEquals(ICMMove.RESUME, move.get_type())
        self.assertEquals(PerformGoal(self.buy_action), move.get_content())

    def test_contentful_accommodate(self):
        move = self.parser.parse("icm:accommodate:top")
        self.assertEquals(ICMMove.ACCOMMODATE, move.get_type())
        self.assertEquals(self.top_action, move.get_content())

    def test_contentless_accommodate(self):
        move = self.parser.parse("icm:accommodate")
        self.assertEquals(ICMMove.ACCOMMODATE, move.get_type())

    def test_loadplan(self):
        move = self.parser.parse("icm:loadplan")
        self.assertTrue(move.get_type() == ICMMove.LOADPLAN)

    def test_und_neg_without_content(self):
        icm = self.parser.parse("icm:und*neg")
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.NEG, icm.get_polarity())
        self.assertEquals(None, icm.get_content())

    def test_sem_neg(self):
        icm = self.parser.parse("icm:sem*neg")
        self.assertEquals(ICMMove.SEM, icm.get_type())
        self.assertEquals(ICMMove.NEG, icm.get_polarity())
        self.assertEquals(None, icm.get_content())

    def test_contentful_per_pos(self):
        icm = self.parser.parse('icm:per*pos:"a string"')
        self.assertEquals(ICMMove.PER, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())
        expected_content = 'a string'
        self.assertEquals(expected_content, icm.get_content())

    def test_contentful_per_pos_from_stringfyed_move(self):
        move = ICMMoveWithStringContent(ICMMove.PER, content="a string", polarity=ICMMove.POS)
        icm = self.parser.parse(unicode(move))
        self.assertEquals(ICMMove.PER, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())
        expected_content = "a string"
        self.assertEquals(expected_content, icm.get_content())

    def test_und_int_usr(self):
        icm = self.parser.parse("icm:und*int:USR*dest_city(paris)")
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.INT, icm.get_polarity())
        self.assertEquals("dest_city(paris)", unicode(icm.get_content()))

    def test_und_int_model(self):
        icm = self.parser.parse("icm:und*int:MODEL*dest_city(paris)")
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.INT, icm.get_polarity())
        self.assertEquals(Speaker.MODEL, icm.get_content_speaker())
        self.assertEquals("dest_city(paris)", unicode(icm.get_content()))

    def test_und_int_w_speaker_and_score(self):
        speaker = Speaker.SYS
        score = 1.0
        icm = self.parser.parse(
            "ICMMove(icm:und*int:USR*dest_city(paris), speaker=%s, understanding_confidence=%s)" % (speaker, score)
        )
        content = self.parser.parse("dest_city(paris)")
        expected_move = ICMMoveWithSemanticContent(
            ICMMove.UND,
            content,
            understanding_confidence=score,
            speaker=speaker,
            content_speaker=Speaker.USR,
            polarity=ICMMove.INT
        )
        self.assertEquals(expected_move, icm)

    def test_acc_pos_w_speaker_and_no_score(self):
        speaker = Speaker.SYS
        icm = self.parser.parse("ICMMove(icm:acc*pos, speaker=%s)" % speaker)
        expected_move = ICMMove(ICMMove.ACC, understanding_confidence=1.0, speaker=speaker, polarity=ICMMove.POS)
        self.assertEquals(expected_move, icm)

    def test_und_int_icm_fails_if_faulty_speaker(self):
        with self.assertRaises(Exception):
            self.parser.parse("icm:und*int:usr*dest_city(paris)")

    def test_und_pos_icm_for_issue_proposition(self):
        icm = self.parser.parse("icm:und*pos:USR*goal(resolve(?X.dest_city(X)))")
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())
        self.assertEquals("goal(resolve(?X.dest_city(X)))", unicode(icm.get_content()))

    def test_und_int_icm_without_speaker(self):
        score = 1.0
        speaker = Speaker.SYS
        icm = self.parser.parse(
            "ICMMove(icm:und*int:dest_city(paris), speaker=%s, understanding_confidence=%s)" % (speaker, score)
        )
        content = self.parser.parse("dest_city(paris)")
        expected_move = ICMMoveWithSemanticContent(
            ICMMove.UND,
            content,
            understanding_confidence=score,
            speaker=speaker,
            content_speaker=None,
            polarity=ICMMove.INT
        )
        self.assertEquals(expected_move, icm)

    def test_und_pos_icm_for_predicate_proposition(self):
        icm = self.parser.parse("icm:und*pos:USR*dest_city(paris)")
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())
        self.assertEquals("dest_city(paris)", unicode(icm.get_content()))

    def test_per_neg_icm(self):
        icm = self.parser.parse("icm:per*neg")
        self.assertEquals(ICMMove.PER, icm.get_type())
        self.assertEquals(ICMMove.NEG, icm.get_polarity())

    def test_per_neg_icm_w_speaker_and_score(self):
        speaker = Speaker.SYS
        score = 1.0
        icm = self.parser.parse("ICMMove(icm:per*neg, speaker=%s, understanding_confidence=%s)" % (speaker, score))
        expected_move = ICMMove(ICMMove.PER, understanding_confidence=score, speaker=speaker, polarity=ICMMove.NEG)
        self.assertEquals(expected_move, icm)

    def test_acc_pos_icm_no_content(self):
        icm = self.parser.parse("icm:acc*pos")
        self.assertEquals(ICMMove.ACC, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())

    def test_acc_neg_icm_for_issue(self):
        icm = self.parser.parse("icm:acc*neg:issue")
        self.assertEquals(ICMMove.ACC, icm.get_type())
        self.assertEquals(ICMMove.NEG, icm.get_polarity())
        self.assertEquals(str(icm), "ICMMove(icm:acc*neg:issue)")

    def test_unsupported_icm_content_unparseable(self):
        with self.assertRaises(ParseError):
            self.parser.parse("icm:acc*neg:unsupported")

    def test_acc_neg_issue_w_speaker_and_score(self):
        speaker = Speaker.SYS
        score = 1.0
        icm = self.parser.parse(
            "ICMMove(icm:acc*neg:issue, speaker=%s, understanding_confidence=%s)" % (speaker, score)
        )
        expected_move = IssueICMMove(ICMMove.ACC, understanding_confidence=score, speaker=speaker, polarity=ICMMove.NEG)
        self.assertEquals(expected_move, icm)

    def test_undecorated_icm_move_with_ICMMove_classname(self):
        string = 'ICMMove(icm:per*pos:"this is not understood")'
        actual_move = self.parser.parse(string)
        expected_move = ICMMoveWithStringContent(ICMMove.PER, "this is not understood", polarity=ICMMove.POS)
        self.assertEquals(expected_move, actual_move)

    def test_jumpto(self):
        item = self.parser.parse("jumpto(perform(buy))")
        expected_item = JumpToPlanItem(PerformGoal(self.buy_action))
        self.assertEquals(expected_item, item)

    def test_assume(self):
        item = self.parser.parse("assume(dest_city(paris))")
        expected_item = AssumePlanItem(self.proposition_dest_city_paris)
        self.assertEquals(expected_item, item)

    def test_assume_shared(self):
        item = self.parser.parse("assume_shared(dest_city(paris))")
        expected_item = AssumeSharedPlanItem(self.proposition_dest_city_paris)
        self.assertEquals(expected_item, item)

    def test_assume_issue(self):
        item = self.parser.parse("assume_issue(?X.dest_city(X))")
        expected_item = AssumeIssuePlanItem(self.dest_city_question)
        self.assertEquals(expected_item, item)

    def test_service_action_terminated_proposition(self):
        object = self.parser.parse("service_action_terminated(SomeServiceAction)")
        expected_object = ServiceActionTerminatedProposition(self.ontology_name, "SomeServiceAction")
        self.assertEquals(expected_object, object)

    def test_service_action_started_proposition(self):
        object = self.parser.parse("service_action_started(SomeServiceAction)")
        expected_object = ServiceActionStartedProposition(self.ontology_name, "SomeServiceAction")
        self.assertEquals(expected_object, object)

    def test_string_individual(self):
        object = self.parser.parse('"a string"')
        expected_object = Individual(self.ontology_name, 'a string', StringSort())
        self.assertEquals(expected_object, object)

    def test_string_individual_digits_only(self):
        object = self.parser.parse('"123"')
        expected_object = Individual(self.ontology_name, '123', StringSort())
        self.assertEquals(expected_object, object)

    def test_string_answer(self):
        move = self.parser.parse('answer("a string")')
        individual = Individual(self.ontology_name, 'a string', StringSort())
        expected_move = self._move_factory.createAnswerMove(individual)
        self.assertEquals(expected_move, move)

    def test_predicate_proposition_with_string_individual(self):
        object = self.parser.parse('number_to_call("070123456")')
        expected_object = PredicateProposition(
            self.predicate_number_to_call, self.ontology.create_individual('"070123456"')
        )
        self.assertEquals(expected_object, object)

    def test_unknown_term_unparseable(self):
        with self.assertRaises(ParseError):
            self.parser.parse("unknown_term")

    def test_parse_creates_new_instance(self):
        container_string = "{}"
        container = self.parser.parse(container_string)
        container.add("dummy_item")
        new_container = self.parser.parse(container_string)
        expected_new_container = Set()
        self.assertEquals(expected_new_container, new_container)

    def test_perform_goal(self):
        string = "perform(top)"
        expected_object = PerformGoal(self.top_action)
        self.assertEquals(expected_object, self.parser.parse(string))

    def test_resolve_goal(self):
        string = "resolve(?X.price(X))"
        expected_object = ResolveGoal(self.price_question, Speaker.SYS)
        self.assertEquals(expected_object, self.parser.parse(string))

    def test_resolve_user_goal(self):
        object = self.parser.parse("resolve_user(?X.dest_city(X))")
        expected_object = ResolveGoal(self.dest_city_question, Speaker.USR)
        self.assertEquals(expected_object, object)

    def test_handle_goal(self):
        string = "handle(ReservationConfirmed)"
        expected_object = HandleGoal(self.ontology_name, "ReservationConfirmed")
        self.assertEquals(expected_object, self.parser.parse(string))

    def test_deprecated_action_question_gives_helpful_error(self):
        string = "?X.action(X)"
        with self.assertRaises(ParseError) as cm:
            self.parser.parse(string)
        self.assertEquals(
            "'?X.action(X)' is not a valid question. Perhaps you mean '?X.goal(X)'.", unicode(cm.exception)
        )

    def test_deprecated_action_proposition_gives_helpful_error(self):
        string = "set([action(make_domestic_reservation), action(make_international_reservation)])"
        with self.assertRaises(ParseError) as cm:
            self.parser.parse(string)
        self.assertEquals(
            "'action(make_domestic_reservation)' is not a valid proposition. Perhaps you mean 'goal(perform(make_domestic_reservation))'.",
            unicode(cm.exception)
        )

    def test_deprecated_issue_proposition_gives_helpful_error(self):
        string = "set([issue(?X.price(X))])"
        with self.assertRaises(ParseError) as cm:
            self.parser.parse(string)
        self.assertEquals(
            "'issue(?X.price(X))' is not a valid proposition. Perhaps you mean 'goal(resolve(?X.price(X)))'.",
            unicode(cm.exception)
        )

    def test_predicate(self):
        string = "dest_city"
        expected_object = self.predicate_dest_city
        self.assertEquals(expected_object, self.parser.parse(string))

    def test_successful_perform_result(self):
        string = "SuccessfulServiceAction()"
        expected_object = SuccessfulServiceAction()
        self.assertEquals(expected_object, self.parser.parse(string))

    def test_failed_perform_result(self):
        string = "FailedServiceAction(mock_failure_reason)"
        expected_object = FailedServiceAction("mock_failure_reason")
        self.assertEquals(expected_object, self.parser.parse(string))
