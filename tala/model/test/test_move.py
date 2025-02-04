import pytest
from unittest.mock import Mock

from tala.model.common import Modality
from tala.model import speaker
from tala.model.move import Move, ICMMove, ReportMove, ICMMoveWithSemanticContent, AskMove, CardinalSequencingICM
from tala.model.proposition import ServiceResultProposition, PredicateProposition
from tala.testing.lib_test_case import LibTestCase
from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction
from tala.testing.move_factory import MoveFactoryWithPredefinedBoilerplate


class SemanticExpressionTestMixin(object):
    def given_move(self, move):
        self._move = move

    def when_generating_semantic_expression(self):
        self._actual_result = self._move.as_semantic_expression()

    def given_set_realization_data_was_called(self, **kwargs):
        self._move.set_realization_data(**kwargs)

    def when_get_semantic_expression_without_realization_data(self):
        self._actual_result = self._move.semantic_expression_without_realization_data()


class ReportMoveTests(LibTestCase, SemanticExpressionTestMixin):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name, ddd_name="mockup_ddd")
        self.service_action = "BuyTrip"
        self.parameters = [self.proposition_dest_city_paris, self.proposition_dept_city_london]
        self.success_result = ServiceResultProposition(
            self.ontology_name, self.service_action, self.parameters, SuccessfulServiceAction()
        )
        self.success_move = self.move_factory.create_report_move(self.success_result)
        self.failure_move = self.move_factory.create_report_move(
            ServiceResultProposition(
                self.ontology_name, self.service_action, self.parameters, FailedServiceAction("no_itinerary_found")
            )
        )

    def test_getters(self):
        self.assertEqual(Move.REPORT, self.success_move.type_)
        self.assertEqual(self.success_result, self.success_move.content)

    def test_str_success_move(self):
        self.assertEqual(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction()))", str(self.success_move)
        )

    def test_str_failure_move(self):
        self.assertEqual(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], FailedServiceAction(no_itinerary_found)))",
            str(self.failure_move)
        )

    def test_str_with_ddd_name(self):
        self.success_move.set_ddd_name("mockup_ddd")
        self.assertEqual(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction()), ddd_name='mockup_ddd')",
            str(self.success_move)
        )

    def test_equality(self):
        move = self.move_factory.create_report_move(
            ServiceResultProposition(
                self.ontology_name, self.service_action, self.parameters, SuccessfulServiceAction()
            )
        )
        identical_move = self.move_factory.create_report_move(
            ServiceResultProposition(
                self.ontology_name, self.service_action, self.parameters, SuccessfulServiceAction()
            )
        )
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(move, identical_move)

    def test_unicode_with_swedish_character(self):
        parameters = [
            PredicateProposition(
                self.ontology.get_predicate("comment_message"), self.ontology.create_individual("balkong önskas")
            )
        ]
        move = self.move_factory.create_report_move(
            ServiceResultProposition(self.ontology_name, "RegisterComment", parameters, SuccessfulServiceAction())
        )
        self.assertEqual(
            'report(ServiceResultProposition('
            'RegisterComment, [comment_message("balkong önskas")], SuccessfulServiceAction()))', str(move)
        )

    def test_as_semantic_expression(self):
        self.given_move(self.success_move)
        self.when_generating_semantic_expression()
        self.then_result_is(
            "report("
            "ServiceResultProposition(BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction())"
            ")"
        )

    def test_semantic_expression_without_realization_data(self):
        self.given_move(self.success_move)
        self.given_set_realization_data_was_called(speaker=speaker.SYS, ddd_name="mock_ddd")
        self.when_get_semantic_expression_without_realization_data()
        self.then_result_is(
            "report(ServiceResultProposition(BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction()))"
        )


class PrereportMoveTests(LibTestCase, SemanticExpressionTestMixin):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name, ddd_name="mockup_ddd")
        self.service_action = "BuyTrip"
        self.arguments = [self.proposition_dest_city_paris, self.proposition_dept_city_london]
        self.move = self.move_factory.create_prereport_move(self.service_action, self.arguments)

    def test_getters(self):
        self.assertEqual(Move.PREREPORT, self.move.type_)
        self.assertEqual(self.service_action, self.move.get_service_action())
        self.assertEqual(self.arguments, self.move.get_arguments())

    def test_to_string(self):
        self.assertEqual("prereport(BuyTrip, [dest_city(paris), dept_city(london)])", str(self.move))

    def test_equality(self):
        move = self.move_factory.create_prereport_move(self.service_action, self.arguments)
        identical_move = self.move_factory.create_prereport_move(self.service_action, self.arguments)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(move, identical_move)

    def test_inequality_due_to_arguments(self):
        move1 = self.move_factory.create_prereport_move(self.service_action, [])
        move2 = self.move_factory.create_prereport_move(self.service_action, [self.proposition_dest_city_paris])
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_inequality_due_to_service_action(self):
        move1 = self.move_factory.create_prereport_move("action1", [])
        move2 = self.move_factory.create_prereport_move("action2", [])
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_as_semantic_expression(self):
        self.given_move(self.move)
        self.when_generating_semantic_expression()
        self.then_result_is("prereport(BuyTrip, [dest_city(paris), dept_city(london)])")

    def test_semantic_expression_without_realization_data(self):
        self.given_move(self.move_factory.create_prereport_move(self.service_action, self.arguments))
        self.given_set_realization_data_was_called(speaker=speaker.SYS, ddd_name="mock_ddd")
        self.when_get_semantic_expression_without_realization_data()
        self.then_result_is("prereport(BuyTrip, [dest_city(paris), dept_city(london)])")


class MoveTests(LibTestCase, SemanticExpressionTestMixin):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name, ddd_name="mockup_ddd")
        self.icm_acc_neg = self.move_factory.create_icm_move(ICMMove.ACC, speaker=speaker.SYS, polarity=ICMMove.NEG)
        self.icm_acc_neg_issue = self.move_factory.create_icm_move(
            ICMMove.ACC, speaker=speaker.SYS, polarity=ICMMove.NEG, content="issue"
        )
        self.icm_per_neg = self.move_factory.create_icm_move(ICMMove.PER, speaker=speaker.SYS, polarity=ICMMove.NEG)
        self.icm_per_pos = self.move_factory.create_icm_move(ICMMove.PER, speaker=speaker.SYS, polarity=ICMMove.POS)
        self.icm_acc_pos = self.move_factory.create_icm_move(ICMMove.ACC, speaker=speaker.SYS, polarity=ICMMove.POS)
        self.report_move = self.move_factory.create_report_move(
            ServiceResultProposition(self.ontology_name, "service_action", [], SuccessfulServiceAction())
        )
        self.answer_move = self.move_factory.create_answer_move(speaker=speaker.SYS, answer=self.individual_paris)
        self.request_move = self.move_factory.create_request_move(action=self.buy_action)
        self.ask_move = self.move_factory.create_ask_move(speaker=speaker.SYS, question=self.price_question)

    def test_as_semantic_expression_for_answer(self):
        self.given_move(self.answer_move)
        self.when_generating_semantic_expression()
        self.then_result_is("answer(paris)")

    def test_as_semantic_expression_for_request(self):
        self.given_move(self.request_move)
        self.when_generating_semantic_expression()
        self.then_result_is("request(buy)")

    def test_as_semantic_expression_for_ask(self):
        self.given_move(self.ask_move)
        self.when_generating_semantic_expression()
        self.then_result_is("ask(?X.price(X))")

    def test_as_semantic_expression_for_icm_acc_neg(self):
        self.given_move(self.icm_acc_neg)
        self.when_generating_semantic_expression()
        self.then_result_is("icm:acc*neg")

    def test_as_semantic_expression_for_icm_acc_neg_issue(self):
        self.given_move(self.icm_acc_neg_issue)
        self.when_generating_semantic_expression()
        self.then_result_is("icm:acc*neg:issue")

    def test_as_semantic_expression_for_icm_with_propositional_content(self):
        self.given_move(
            self.move_factory.create_icm_move(
                ICMMove.SEM, speaker=speaker.SYS, polarity=ICMMove.NEG, content=self.proposition_dest_city_paris
            )
        )
        self.when_generating_semantic_expression()
        self.then_result_is("icm:sem*neg:dest_city(paris)")

    def test_as_semantic_expression_for_icm_per_neg(self):
        self.given_move(self.icm_per_neg)
        self.when_generating_semantic_expression()
        self.then_result_is("icm:per*neg")

    def test_as_semantic_expression_for_icm_per_pos(self):
        self.given_move(self.icm_per_pos)
        self.when_generating_semantic_expression()
        self.then_result_is("icm:per*pos")

    def test_as_semantic_expression_for_icm_acc_pos(self):
        self.given_move(self.icm_acc_pos)
        self.when_generating_semantic_expression()
        self.then_result_is("icm:acc*pos")

    def test_short_answer_unicode(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        answer = move_factory.create_answer_move(self.individual_paris)
        self.assertEqual("Move(answer(paris))", str(answer))

    def test_short_answer_is_answer_move(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(
            self.ontology_name, speaker="USR", understanding_confidence=1.0, ddd_name=""
        )
        answer = move_factory.create_answer_move(self.individual_paris)
        self.assertEqual(Move.ANSWER, answer.type_)

    def test_is_question_raising_true_for_ask_move(self):
        question_string = "?X.dest_city(X)"
        move_factory = MoveFactoryWithPredefinedBoilerplate(
            self.ontology_name, speaker="USR", understanding_confidence=1.0, ddd_name=""
        )
        ask_move = move_factory.create_ask_move(question_string)
        self.assertTrue(ask_move.is_question_raising())

    def test_is_question_raising_false_for_answer_move(self):
        proposition_string = "dest_city(paris)"
        move_factory = MoveFactoryWithPredefinedBoilerplate(
            self.ontology_name, speaker="USR", understanding_confidence=1.0, ddd_name=""
        )
        answer_move = move_factory.create_answer_move(proposition_string)
        self.assertFalse(answer_move.is_question_raising())

    def test_is_question_raising_true_for_contentful_icm_und_neg(self):
        propositional_content = self.proposition_dest_city_paris
        contentful_icm_und_neg = ICMMoveWithSemanticContent(ICMMove.UND, propositional_content, polarity=ICMMove.NEG)
        self.assertTrue(contentful_icm_und_neg.is_question_raising())

    def test_is_question_raising_false_for_contentless_icm_und_neg(self):
        contentless_icm_und_neg = ICMMove(ICMMove.UND, polarity=ICMMove.NEG)
        self.assertFalse(contentless_icm_und_neg.is_question_raising())

    def test_is_question_raising_true_for_icm_und_int(self):
        propositional_content = self.proposition_dest_city_paris
        icm_und_int = ICMMoveWithSemanticContent(ICMMove.UND, propositional_content, polarity=ICMMove.INT)
        self.assertTrue(icm_und_int.is_question_raising())

    def test_is_question_raising_true_for_icm_und_pos_for_positive_content(self):
        positive_content = self.proposition_dest_city_paris
        icm = ICMMoveWithSemanticContent(ICMMove.UND, positive_content, polarity=ICMMove.POS)
        self.assertTrue(icm.is_question_raising())

    def test_is_question_raising_false_for_icm_und_pos_for_negated_content(self):
        negation = self.proposition_not_dest_city_paris
        icm = ICMMoveWithSemanticContent(ICMMove.UND, negation, polarity=ICMMove.POS)
        self.assertFalse(icm.is_question_raising())

    def test_is_question_raising_false_for_icm_acc_neg(self):
        icm_acc_neg = ICMMove(ICMMove.ACC, polarity=ICMMove.NEG)
        self.assertFalse(icm_acc_neg.is_question_raising())

    def test_create_greet_move(self):
        move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        self.assertEqual(Move.GREET, move.type_)

    def test_greet_move_to_string(self):
        move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        self.assertEqual(
            "Move(greet, ddd_name='mockup_ddd', speaker=SYS, understanding_confidence=1.0, "
            "weighted_understanding_confidence=1.0, perception_confidence=1.0, modality=speech)", str(move)
        )

    def test_greet_move_to_semantic_expression(self):
        move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        self.assertEqual("greet", move.as_semantic_expression())

    def test_string_representation_with_score_and_speaker(self):
        move = self.move_factory.create_move(
            Move.GREET, understanding_confidence=1.0, speaker=speaker.SYS, perception_confidence=0.9
        )
        move_string = "Move(greet, ddd_name='mockup_ddd', speaker=SYS, understanding_confidence=1.0, " "weighted_understanding_confidence=1.0, perception_confidence=0.9, modality=speech)"
        self.assertEqual(move_string, str(move))

    def test_str_with_background(self):
        move = self.move_factory.create_ask_move(speaker=speaker.SYS, question=self.dept_city_question)
        move.set_background([self.proposition_dest_city_paris])
        self.assertEqual(
            "Move(ask(?X.dept_city(X), [dest_city(paris)]), ddd_name='mockup_ddd', speaker=SYS, "
            "understanding_confidence=1.0, weighted_understanding_confidence=1.0, "
            "perception_confidence=1.0, modality=speech)", str(move)
        )

    def test_str_with_utterance(self):
        move = self.move_factory.create_move(
            Move.GREET, understanding_confidence=0.5, speaker=speaker.USR, utterance="hello"
        )
        move_string = "Move(greet, ddd_name='mockup_ddd', speaker=USR, understanding_confidence=0.5, " "weighted_understanding_confidence=0.5, perception_confidence=1.0, modality=speech, " "utterance='hello')"
        self.assertEqual(move_string, str(move))

    def test_move_equality_basic(self):
        move1 = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, perception_confidence=0.8, understanding_confidence=0.6
        )
        move2 = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, perception_confidence=0.8, understanding_confidence=0.6
        )
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(move1, move2)

    def test_move_inequality_basic(self):
        move1 = self.move_factory.create_move(Move.QUIT, speaker=speaker.SYS)
        move2 = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_speaker_inequality(self):
        user_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=1.0)
        sys_move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS, understanding_confidence=1.0)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(user_move, sys_move)

    def test_understanding_confidence_inequality(self):
        hi_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.9)
        lo_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.8)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_weighted_understanding_confidence_inequality(self):
        hi_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.5)
        hi_move.weighted_understanding_confidence = 0.9
        lo_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.5)
        lo_move.weighted_understanding_confidence = 0.8
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_perception_confidence_inequality(self):
        hi_move = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, understanding_confidence=0.5, perception_confidence=0.5
        )
        lo_move = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, understanding_confidence=0.5, perception_confidence=0.6
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_utterance_inequality(self):
        move1 = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, understanding_confidence=1.0, utterance="hello"
        )
        move2 = self.move_factory.create_move(
            Move.GREET, speaker=speaker.USR, understanding_confidence=1.0, utterance="hi"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_move_content_equality_tolerates_score_diff(self):
        hi_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.9)
        lo_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.8)
        self.assertTrue(hi_move.move_content_equals(lo_move))
        self.assertTrue(lo_move.move_content_equals(hi_move))

    def test_move_content_equality_tolerates_speaker_diff(self):
        usr_move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=1.0)
        sys_move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS, understanding_confidence=1.0)
        self.assertTrue(sys_move.move_content_equals(usr_move))
        self.assertTrue(usr_move.move_content_equals(sys_move))

    def test_move_content_inequality_type_differs(self):
        quit_move = self.move_factory.create_move(Move.QUIT, speaker=speaker.SYS)
        greet_move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        self.assertFalse(quit_move.move_content_equals(greet_move))
        self.assertFalse(greet_move.move_content_equals(quit_move))

    def test_content_inequality_content_differs(self):
        paris_answer_move = self.move_factory.create_answer_move(speaker=speaker.SYS, answer=self.individual_paris)
        london_answer_move = self.move_factory.create_answer_move(speaker=speaker.SYS, answer=self.individual_london)
        self.assertFalse(paris_answer_move.move_content_equals(london_answer_move))

    def test_content_inequality(self):
        move1 = self.move_factory.create_answer_move(speaker=speaker.SYS, answer=self.individual_paris)
        move2 = self.move_factory.create_answer_move(speaker=speaker.SYS, answer=self.individual_london)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_move_inequality_between_move_classes(self):
        icm = self.move_factory.create_icm_move(ICMMove.ACC, content=ICMMove.POS)
        report = ReportMove(ServiceResultProposition(self.ontology_name, "action", [], SuccessfulServiceAction()))
        self.assertFalse(report.move_content_equals(icm))

    def test_is_negative_perception_icm(self):
        self.assertTrue(self.icm_per_neg.is_negative_perception_icm())
        self.assertFalse(self.icm_per_pos.is_negative_perception_icm())

    def test_is_positive_acceptance_icm(self):
        self.assertTrue(self.icm_acc_pos.is_positive_acceptance_icm())
        self.assertFalse(self.icm_per_pos.is_positive_acceptance_icm())

    def test_is_negative_acceptance_issue_icm(self):
        self.assertTrue(self.icm_acc_neg_issue.is_negative_acceptance_issue_icm())
        self.assertFalse(self.icm_per_neg.is_negative_acceptance_issue_icm())
        self.assertFalse(self.icm_acc_neg.is_negative_acceptance_issue_icm())

    def test_create_prereport_move(self):
        service_action = "BuyTrip"
        dest_city = self.proposition_dest_city_paris
        dept_city = self.proposition_dept_city_london
        parameters = [dept_city, dest_city]
        self.move_factory.create_prereport_move(service_action, parameters)

    def test_is_turn_yielding(self):
        turn_yielding_moves = [self.report_move, self.ask_move, self.request_move]
        non_turn_yielding_moves = [self.icm_acc_pos, self.icm_acc_neg, self.answer_move]
        for move in turn_yielding_moves:
            self.assertTrue(move.is_turn_yielding(), f"{move} should be turn yielding")
        for move in non_turn_yielding_moves:
            self.assertFalse(move.is_turn_yielding(), f"{move} should not be turn yielding")

    def test_upscore(self):
        move = self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.5)
        move.uprank(0.2)
        self.assertEqual(0.5 * 1.2, move.weighted_understanding_confidence)

    def test_set_and_get_weighted_understanding_confidence_without_setting_realization_data(self):
        self.given_move(self.move_factory.create_move(Move.GREET, speaker=speaker.USR, understanding_confidence=0.5))
        self.given_weighted_understanding_confidence_was_set(0.6)
        self.when_get_weighted_understanding_confidence()
        self.then_result_is(0.6)

    def given_weighted_understanding_confidence_was_set(self, score):
        self._move.weighted_understanding_confidence = score

    def when_get_weighted_understanding_confidence(self):
        self._actual_result = self._move.weighted_understanding_confidence

    def test_set_and_get_weighted_understanding_confidence_after_setting_realization_data(self):
        self.given_move(Move(Move.GREET))
        self.given_set_realization_data_was_called(
            speaker=speaker.USR, ddd_name="mock_ddd", understanding_confidence=0.5
        )
        self.given_weighted_understanding_confidence_was_set(0.6)
        self.when_get_weighted_understanding_confidence()
        self.then_result_is(0.6)

    def test_semantic_expression_without_realization_data_for_move_without_content(self):
        self.given_move(Move(Move.GREET))
        self.given_set_realization_data_was_called(
            speaker=speaker.USR, ddd_name="mock_ddd", understanding_confidence=0.5
        )
        self.when_get_semantic_expression_without_realization_data()
        self.then_result_is("Move(greet)")

    def test_semantic_expression_without_realization_data_for_move_with_content(self):
        self.given_move(AskMove(self.price_question))
        self.given_set_realization_data_was_called(speaker=speaker.SYS, ddd_name="mock_ddd")
        self.when_get_semantic_expression_without_realization_data()
        self.then_result_is("Move(ask(?X.price(X)))")


class ICMMoveTests(LibTestCase, SemanticExpressionTestMixin):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)

    def test_create_reraise_icm_move(self):
        move = self.move_factory.create_icm_move(ICMMove.RERAISE, content=self.ontology.create_action("top"))
        self.assertTrue(move.type_ == ICMMove.RERAISE)

    def test_reraise_to_string(self):
        move = self.move_factory.create_icm_move(ICMMove.RERAISE, content=self.ontology.create_action("top"))
        self.assertEqual("ICMMove(icm:reraise:top)", str(move))

    def test_loadplan_to_string(self):
        move = self.move_factory.create_icm_move(ICMMove.LOADPLAN)
        self.assertEqual("ICMMove(icm:loadplan)", str(move))

    def test_string_representation_with_score_and_speaker(self):
        move = self.move_factory.create_icm_move(
            ICMMove.ACC,
            polarity=ICMMove.POS,
            understanding_confidence=1.0,
            speaker=speaker.SYS,
            perception_confidence=0.9
        )
        self.assertEqual(
            "ICMMove(icm:acc*pos, speaker=SYS, understanding_confidence=1.0, perception_confidence=0.9)", str(move)
        )

    def test_create_und_int(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.INT, speaker=speaker.SYS)
        self.assertEqual(ICMMove.UND, icm.type_)
        self.assertEqual(ICMMove.INT, icm.get_polarity())

    def test_inequality_due_to_polarity_difference(self):
        icm_int = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.INT)
        icm_pos = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS)
        icm_neg = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.NEG)
        self.assertNotEqual(icm_pos, icm_int)
        self.assertNotEqual(icm_pos, icm_neg)
        self.assertNotEqual(icm_int, icm_neg)

    def test_inequality_due_to_type_difference(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS)
        non_identical_icm = self.move_factory.create_icm_move(ICMMove.ACC, polarity=ICMMove.POS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_content_difference(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS, content="dummy_content")
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content="different_dummy_content"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_content_speaker_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=speaker.USR
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=speaker.SYS
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_speaker_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=speaker.SYS
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.NEG, understanding_confidence=1.0, speaker=speaker.SYS
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_score_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, speaker=speaker.USR, understanding_confidence=0.9, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND,
            polarity=ICMMove.POS,
            speaker=speaker.USR,
            understanding_confidence=0.77,
            ddd_name="mockup_ddd"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_content_inequality_due_to_polarity_difference(self):
        icm_int = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.INT)
        icm_pos = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS)
        self.assertFalse(icm_pos.move_content_equals(icm_int))

    def test_content_inequality_due_to_type_difference(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS)
        non_identical_icm = self.move_factory.create_icm_move(ICMMove.ACC, polarity=ICMMove.POS)
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_inequality_due_to_content_difference(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS, content="dummy_content")
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content="different_dummy_content"
        )
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_inequality_due_to_content_speaker_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=speaker.USR
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=speaker.SYS
        )
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_equality_tolerates_speaker_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=speaker.USR, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=speaker.SYS, ddd_name="mockup_ddd"
        )
        self.assertTrue(icm.move_content_equals(non_identical_icm))

    def test_content_equality_tolerates_score_difference(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, speaker=speaker.USR, understanding_confidence=0.9, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.create_icm_move(
            ICMMove.UND,
            polarity=ICMMove.POS,
            speaker=speaker.USR,
            understanding_confidence=0.77,
            ddd_name="mockup_ddd"
        )
        self.assertTrue(icm.move_content_equals(non_identical_icm))

    def test_und_neg_to_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.NEG)
        expected_string = "ICMMove(icm:und*neg)"
        self.assertEqual(expected_string, str(icm))

    def test_und_int_to_string(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.INT, content_speaker=speaker.USR, content=self.proposition_dest_city_paris
        )
        expected_string = "ICMMove(icm:und*int:USR*dest_city(paris))"
        self.assertEqual(expected_string, str(icm))

    def test_create_und_pos(self):
        icm = self.move_factory.create_icm_move(ICMMove.UND, polarity=ICMMove.POS, speaker=speaker.SYS)
        self.assertEqual(ICMMove.UND, icm.type_)
        self.assertEqual(ICMMove.POS, icm.get_polarity())

    def test_und_pos_to_string(self):
        icm = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.POS, content_speaker=speaker.USR, content=self.proposition_dest_city_paris
        )
        expected_string = "ICMMove(icm:und*pos:USR*dest_city(paris))"
        self.assertEqual(expected_string, str(icm))

    def test_per_neg_to_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.PER, polarity=ICMMove.NEG)
        self.assertEqual("ICMMove(icm:per*neg)", str(icm))

    def test_per_pos_to_string_with_content_as_double_quoted_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.PER, polarity=ICMMove.POS, content='a string')
        self.assertEqual('ICMMove(icm:per*pos:"a string")', str(icm))

    def test_acc_pos_to_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.ACC, polarity=ICMMove.POS)
        self.assertEqual("ICMMove(icm:acc*pos)", str(icm))

    def test_sem_neg_to_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.SEM, polarity=ICMMove.NEG)
        expected_string = "ICMMove(icm:sem*neg)"
        self.assertEqual(expected_string, str(icm))

    def test_acc_neg_issue_to_string(self):
        icm = self.move_factory.create_icm_move(ICMMove.ACC, polarity=ICMMove.NEG, content="issue")
        self.assertEqual("ICMMove(icm:acc*neg:issue)", str(icm))

    def test_icm_move_getters(self):
        move = self.move_factory.create_icm_move(
            ICMMove.UND, polarity=ICMMove.INT, content=self.price_question, content_speaker=speaker.USR
        )
        self.assertTrue(move.is_icm())
        self.assertEqual(ICMMove.INT, move.get_polarity())
        self.assertEqual(self.price_question, move.content)
        self.assertEqual(speaker.USR, move.get_content_speaker())

    def test_semantic_expression_without_realization_data(self):
        self.given_move(self.move_factory.create_icm_move(ICMMove.SEM, polarity=ICMMove.NEG))
        self.given_set_realization_data_was_called(speaker=speaker.SYS, ddd_name="mock_ddd")
        self.when_get_semantic_expression_without_realization_data()
        self.then_result_is("ICMMove(icm:sem*neg)")

    def test_ddd_getter_and_setter(self):
        move = self.move_factory.create_move(Move.GREET)
        name = "mockup_ddd"
        move.set_ddd_name(name)
        self.assertEqual(name, move.get_ddd_name())


class MoveRealizationTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)

    def test_set_realization_data_for_haptic_input(self):
        move = self.move_factory.create_move(Move.GREET)
        understanding_confidence = 0.5
        speaker_ = speaker.USR
        modality = Modality.HAPTIC
        move.set_realization_data(
            understanding_confidence=understanding_confidence,
            speaker=speaker_,
            modality=modality,
            ddd_name="mockup_ddd"
        )
        self.assertEqual(understanding_confidence, move.understanding_confidence)
        self.assertEqual(speaker_, move.get_speaker())
        self.assertEqual(modality, move.get_modality())

    def test_set_realization_data_for_spoken_input(self):
        move = self.move_factory.create_move(Move.GREET)
        understanding_confidence = 0.5
        speaker_ = speaker.USR
        modality = Modality.SPEECH
        utterance = "hello"
        move.set_realization_data(
            understanding_confidence=understanding_confidence,
            speaker=speaker_,
            modality=modality,
            utterance=utterance,
            ddd_name="mockup_ddd"
        )
        self.assertEqual(understanding_confidence, move.understanding_confidence)
        self.assertEqual(speaker_, move.get_speaker())
        self.assertEqual(modality, move.get_modality())
        self.assertEqual(utterance, move.get_utterance())

    def test_get_score_returns_one_for_move_with_speaker_sys(self):
        greet_move = self.move_factory.create_move(Move.GREET, speaker=speaker.SYS)
        icm_move = self.move_factory.create_icm_move(ICMMove.ACC, content=ICMMove.POS, speaker=speaker.SYS)
        for sys_move in [greet_move, icm_move]:
            self.assertEqual(1.0, sys_move.understanding_confidence)

    def test_move_speech_modality_is_default(self):
        quit_move = self.move_factory.create_move(Move.QUIT, speaker=speaker.SYS)
        icm_move = self.move_factory.create_icm_move(ICMMove.ACC, content=ICMMove.POS, speaker=speaker.SYS)
        for move in [quit_move, icm_move]:
            self.assertEqual(Modality.SPEECH, move.get_modality())

    def test_move_haptic_modality_is_available(self):
        self.move_factory.create_move(Move.QUIT, speaker=speaker.SYS, modality=Modality.HAPTIC)

    def test_move_text_modality_is_available(self):
        self.move_factory.create_move(Move.QUIT, speaker=speaker.SYS, modality=Modality.TEXT)


class MoveTestsFromTdmLib(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_propositional_answer_move_equality(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        destination_answer = self.proposition_dest_city_paris
        answerMove = move_factory.create_answer_move(destination_answer)
        duplicateMove = move_factory.create_answer_move(destination_answer)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(answerMove, duplicateMove)

    def test_yes_no_ask_move_unicode(self):
        question = self.ontology.create_yes_no_question("dest_city", "paris")
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        move = move_factory.create_ask_move(question)
        moveAsString = str(move)
        self.assertEqual("Move(ask(?dest_city(paris)))", moveAsString)

    def test_wh_ask_move_to_string(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        move = move_factory.create_ask_move(self.dest_city_question)
        moveAsString = str(move)
        self.assertEqual("Move(ask(?X.dest_city(X)))", moveAsString)


class TestICMMoves(object):
    def setup_method(self):
        self._move = None
        self._actual_result = None

    @pytest.mark.parametrize("move,expected_result", [
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.INT), True),
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.POS), True),
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.NEG), False),
        (ICMMoveWithSemanticContent(ICMMove.SEM, content="content", polarity=ICMMove.POS), False),
        (ICMMoveWithSemanticContent(ICMMove.PER, content="content", polarity=ICMMove.POS), False),
        (ICMMove(ICMMove.UND, polarity=ICMMove.INT), False),
        (ICMMove(ICMMove.UND, polarity=ICMMove.POS), False),
        (CardinalSequencingICM(1), False)
    ])  # yapf: disable
    def test_is_grounding_move(self, move, expected_result):
        self.given_move(move)
        self.when_calling_is_grounding_move()
        self.then_result_is(expected_result)

    def given_move(self, move):
        self._move = move

    def when_calling_is_grounding_move(self):
        self._actual_result = self._move.is_grounding_proposition()

    def then_result_is(self, expected_result):
        assert self._actual_result == expected_result

    @pytest.mark.parametrize("move, expected_result", [
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.INT), False),
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.POS), False),
        (ICMMoveWithSemanticContent(ICMMove.UND, content="content", polarity=ICMMove.NEG), False),
        (ICMMoveWithSemanticContent(ICMMove.SEM, content="content", polarity=ICMMove.POS), False),
        (ICMMoveWithSemanticContent(ICMMove.PER, content="content", polarity=ICMMove.POS), False),
        (ICMMove(ICMMove.UND, polarity=ICMMove.INT), False),
        (ICMMove(ICMMove.UND, polarity=ICMMove.POS), False),
        (CardinalSequencingICM(1), False),
        (CardinalSequencingICM(99), True)
    ])  # yapf: disable
    def test_equality_with_other_move(self, move, expected_result):
        self.given_move(move)
        self.when_calling_is_equal_to(CardinalSequencingICM(99))
        self.then_result_is(expected_result)

    def when_calling_is_equal_to(self, other_move):
        self._actual_result = self._move == other_move
