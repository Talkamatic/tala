# -*- coding: utf-8 -*-

from mock import Mock

from tala.model.common import Modality
from tala.model.speaker import Speaker
from tala.model.move import Move, ICMMove, MoveException, ReportMove, ICMMoveWithSemanticContent
from tala.model.proposition import ServiceResultProposition, PredicateProposition
from tala.testing.lib_test_case import LibTestCase
from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction
from tala.testing.move_factory import MoveFactoryWithPredefinedBoilerplate


class ReportMoveTests(LibTestCase):
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
        self.assertEquals(Move.REPORT, self.success_move.get_type())
        self.assertEquals(self.success_result, self.success_move.report_proposition)

    def test_str_success_move(self):
        self.assertEquals(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction()))", unicode(self.success_move)
        )

    def test_str_failure_move(self):
        self.assertEquals(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], FailedServiceAction(no_itinerary_found)))",
            unicode(self.failure_move)
        )

    def test_str_with_ddd_name(self):
        self.success_move.set_ddd_name("mockup_ddd")
        self.assertEquals(
            "report(ServiceResultProposition("
            "BuyTrip, [dest_city(paris), dept_city(london)], SuccessfulServiceAction()), ddd_name='mockup_ddd')",
            unicode(self.success_move)
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
                self.ontology.get_predicate("comment_message"), self.ontology.create_individual(u"balkong önskas")
            )
        ]
        move = self.move_factory.create_report_move(
            ServiceResultProposition(self.ontology_name, "RegisterComment", parameters, SuccessfulServiceAction())
        )
        self.assertEquals(
            u'report(ServiceResultProposition('
            u'RegisterComment, [comment_message("balkong önskas")], SuccessfulServiceAction()))', unicode(move)
        )


class PrereportMoveTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name, ddd_name="mockup_ddd")
        self.service_action = "BuyTrip"
        self.arguments = [self.proposition_dest_city_paris, self.proposition_dept_city_london]
        self.move = self.move_factory.create_prereport_move(self.service_action, self.arguments)

    def test_getters(self):
        self.assertEquals(Move.PREREPORT, self.move.get_type())
        self.assertEquals(self.service_action, self.move.get_service_action())
        self.assertEquals(self.arguments, self.move.get_arguments())

    def test_to_string(self):
        self.assertEquals("prereport(BuyTrip, [dest_city(paris), dept_city(london)])", unicode(self.move))

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


class MoveTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name, ddd_name="mockup_ddd")
        self.icm_acc_neg = self.move_factory.createIcmMove(ICMMove.ACC, speaker=Speaker.SYS, polarity=ICMMove.NEG)
        self.icm_acc_neg_issue = self.move_factory.createIcmMove(
            ICMMove.ACC, speaker=Speaker.SYS, polarity=ICMMove.NEG, content="issue"
        )
        self.icm_per_neg = self.move_factory.createIcmMove(ICMMove.PER, speaker=Speaker.SYS, polarity=ICMMove.NEG)
        self.icm_per_pos = self.move_factory.createIcmMove(ICMMove.PER, speaker=Speaker.SYS, polarity=ICMMove.POS)
        self.icm_acc_pos = self.move_factory.createIcmMove(ICMMove.ACC, speaker=Speaker.SYS, polarity=ICMMove.POS)
        self.report_move = self.move_factory.create_report_move(
            ServiceResultProposition(self.ontology_name, "service_action", [], SuccessfulServiceAction())
        )
        self.answer_move = self.move_factory.createAnswerMove(speaker=Speaker.SYS, answer=self.individual_paris)
        self.request_move = self.move_factory.createRequestMove(action=self.buy_action)
        self.ask_move = self.move_factory.create_ask_move(speaker=Speaker.SYS, question=self.price_question)

    def testShortAnswerunicode(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        answer = move_factory.createAnswerMove(self.individual_paris)
        self.assertEquals("Move(answer(paris))", unicode(answer))

    def test_short_answer_is_answer_move(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(
            self.ontology_name, speaker="USR", understanding_confidence=1.0, ddd_name=""
        )
        answer = move_factory.createAnswerMove(self.individual_paris)
        self.assertEquals(Move.ANSWER, answer.get_type())

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
        answer_move = move_factory.createAnswerMove(proposition_string)
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
        move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        self.assertEquals(Move.GREET, move.get_type())

    def test_greet_move_to_string(self):
        move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        self.assertEquals(
            "Move(greet, ddd_name='mockup_ddd', speaker=SYS, understanding_confidence=1.0, "
            "weighted_understanding_confidence=1.0, perception_confidence=1.0, modality=speech)", unicode(move)
        )

    def test_greet_move_to_semantic_expression(self):
        move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        self.assertEquals("Move(greet)", move.get_semantic_expression())

    def test_string_representation_with_score_and_speaker(self):
        move = self.move_factory.createMove(
            Move.GREET, understanding_confidence=1.0, speaker=Speaker.SYS, perception_confidence=0.9
        )
        move_string = "Move(greet, ddd_name='mockup_ddd', speaker=SYS, understanding_confidence=1.0, " "weighted_understanding_confidence=1.0, perception_confidence=0.9, modality=speech)"
        self.assertEquals(move_string, unicode(move))

    def test_str_with_background(self):
        move = self.move_factory.create_ask_move(speaker=Speaker.SYS, question=self.dept_city_question)
        move.set_background([self.proposition_dest_city_paris])
        self.assertEquals(
            "Move(ask(?X.dept_city(X), [dest_city(paris)]), ddd_name='mockup_ddd', speaker=SYS, "
            "understanding_confidence=1.0, weighted_understanding_confidence=1.0, "
            "perception_confidence=1.0, modality=speech)", unicode(move)
        )

    def test_str_with_utterance(self):
        move = self.move_factory.createMove(
            Move.GREET, understanding_confidence=0.5, speaker=Speaker.USR, utterance="hello"
        )
        move_string = "Move(greet, ddd_name='mockup_ddd', speaker=USR, understanding_confidence=0.5, " "weighted_understanding_confidence=0.5, perception_confidence=1.0, modality=speech, " "utterance='hello')"
        self.assertEquals(move_string, unicode(move))

    def test_move_equality_basic(self):
        move1 = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, perception_confidence=0.8, understanding_confidence=0.6
        )
        move2 = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, perception_confidence=0.8, understanding_confidence=0.6
        )
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(move1, move2)

    def test_move_inequality_basic(self):
        move1 = self.move_factory.createMove(Move.QUIT, speaker=Speaker.SYS)
        move2 = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_speaker_inequality(self):
        user_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=1.0)
        sys_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS, understanding_confidence=1.0)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(user_move, sys_move)

    def test_understanding_confidence_inequality(self):
        hi_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.9)
        lo_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.8)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_weighted_understanding_confidence_inequality(self):
        hi_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.5)
        hi_move.weighted_understanding_confidence = 0.9
        lo_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.5)
        lo_move.weighted_understanding_confidence = 0.8
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_perception_confidence_inequality(self):
        hi_move = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, understanding_confidence=0.5, perception_confidence=0.5
        )
        lo_move = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, understanding_confidence=0.5, perception_confidence=0.6
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(lo_move, hi_move)

    def test_utterance_inequality(self):
        move1 = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, understanding_confidence=1.0, utterance="hello"
        )
        move2 = self.move_factory.createMove(
            Move.GREET, speaker=Speaker.USR, understanding_confidence=1.0, utterance="hi"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_move_content_equality_tolerates_score_diff(self):
        hi_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.9)
        lo_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.8)
        self.assertTrue(hi_move.move_content_equals(lo_move))
        self.assertTrue(lo_move.move_content_equals(hi_move))

    def test_move_content_equality_tolerates_speaker_diff(self):
        usr_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=1.0)
        sys_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS, understanding_confidence=1.0)
        self.assertTrue(sys_move.move_content_equals(usr_move))
        self.assertTrue(usr_move.move_content_equals(sys_move))

    def test_move_content_inequality_type_differs(self):
        quit_move = self.move_factory.createMove(Move.QUIT, speaker=Speaker.SYS)
        greet_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        self.assertFalse(quit_move.move_content_equals(greet_move))
        self.assertFalse(greet_move.move_content_equals(quit_move))

    def test_content_inequality_content_differs(self):
        paris_answer_move = self.move_factory.createAnswerMove(speaker=Speaker.SYS, answer=self.individual_paris)
        london_answer_move = self.move_factory.createAnswerMove(speaker=Speaker.SYS, answer=self.individual_london)
        self.assertFalse(paris_answer_move.move_content_equals(london_answer_move))

    def test_content_inequality(self):
        move1 = self.move_factory.createAnswerMove(speaker=Speaker.SYS, answer=self.individual_paris)
        move2 = self.move_factory.createAnswerMove(speaker=Speaker.SYS, answer=self.individual_london)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(move1, move2)

    def test_move_inequality_between_move_classes(self):
        icm = self.move_factory.createIcmMove(ICMMove.ACC, content=ICMMove.POS)
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
        turn_yielding_moves = [self.report_move, self.icm_acc_neg, self.answer_move]
        non_turn_yielding_moves = [self.icm_acc_pos, self.request_move, self.ask_move]
        for move in turn_yielding_moves:
            self.assertTrue(move.is_turn_yielding(), "%s should be turn yielding" % move)
        for move in non_turn_yielding_moves:
            self.assertFalse(move.is_turn_yielding(), "%s should not be turn yielding" % move)

    def test_upscore(self):
        move = self.move_factory.createMove(Move.GREET, speaker=Speaker.USR, understanding_confidence=0.5)
        move.uprank(0.2)
        self.assertEquals(0.5 * 1.2, move.weighted_understanding_confidence)


class ICMMoveTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)

    def test_create_reraise_icm_move(self):
        move = self.move_factory.createIcmMove(ICMMove.RERAISE, content=self.ontology.create_action("top"))
        self.assertTrue(move.get_type() == ICMMove.RERAISE)

    def test_reraise_to_string(self):
        move = self.move_factory.createIcmMove(ICMMove.RERAISE, content=self.ontology.create_action("top"))
        self.assertEquals("ICMMove(icm:reraise:top)", unicode(move))

    def test_loadplan_to_string(self):
        move = self.move_factory.createIcmMove(ICMMove.LOADPLAN)
        self.assertEquals("ICMMove(icm:loadplan)", unicode(move))

    def test_string_representation_with_score_and_speaker(self):
        move = self.move_factory.createIcmMove(
            ICMMove.ACC,
            polarity=ICMMove.POS,
            understanding_confidence=1.0,
            speaker=Speaker.SYS,
            perception_confidence=0.9
        )
        self.assertEquals(
            "ICMMove(icm:acc*pos, speaker=SYS, understanding_confidence=1.0, perception_confidence=0.9)", unicode(move)
        )

    def test_create_und_int(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.INT, speaker=Speaker.SYS)
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.INT, icm.get_polarity())

    def test_inequality_due_to_polarity_difference(self):
        icm_int = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.INT)
        icm_pos = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS)
        icm_neg = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.NEG)
        self.assertNotEquals(icm_pos, icm_int)
        self.assertNotEquals(icm_pos, icm_neg)
        self.assertNotEquals(icm_int, icm_neg)

    def test_inequality_due_to_type_difference(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS)
        non_identical_icm = self.move_factory.createIcmMove(ICMMove.ACC, polarity=ICMMove.POS)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_content_difference(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS, content="dummy_content")
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content="different_dummy_content"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_content_speaker_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=Speaker.USR
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=Speaker.SYS
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_speaker_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=Speaker.SYS
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.NEG, understanding_confidence=1.0, speaker=Speaker.SYS
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_inequality_due_to_score_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, speaker=Speaker.USR, understanding_confidence=0.9, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND,
            polarity=ICMMove.POS,
            speaker=Speaker.USR,
            understanding_confidence=0.77,
            ddd_name="mockup_ddd"
        )
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(icm, non_identical_icm)

    def test_content_inequality_due_to_polarity_difference(self):
        icm_int = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.INT)
        icm_pos = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS)
        self.assertFalse(icm_pos.move_content_equals(icm_int))

    def test_content_inequality_due_to_type_difference(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS)
        non_identical_icm = self.move_factory.createIcmMove(ICMMove.ACC, polarity=ICMMove.POS)
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_inequality_due_to_content_difference(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS, content="dummy_content")
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content="different_dummy_content"
        )
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_inequality_due_to_content_speaker_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=Speaker.USR
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content=Mock(), content_speaker=Speaker.SYS
        )
        self.assertFalse(icm.move_content_equals(non_identical_icm))

    def test_content_equality_tolerates_speaker_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=Speaker.USR, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, understanding_confidence=1.0, speaker=Speaker.SYS, ddd_name="mockup_ddd"
        )
        self.assertTrue(icm.move_content_equals(non_identical_icm))

    def test_content_equality_tolerates_score_difference(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, speaker=Speaker.USR, understanding_confidence=0.9, ddd_name="mockup_ddd"
        )
        non_identical_icm = self.move_factory.createIcmMove(
            ICMMove.UND,
            polarity=ICMMove.POS,
            speaker=Speaker.USR,
            understanding_confidence=0.77,
            ddd_name="mockup_ddd"
        )
        self.assertTrue(icm.move_content_equals(non_identical_icm))

    def test_und_neg_to_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.NEG)
        expected_string = "ICMMove(icm:und*neg)"
        self.assertEquals(expected_string, unicode(icm))

    def test_und_int_to_string(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.INT, content_speaker=Speaker.USR, content=self.proposition_dest_city_paris
        )
        expected_string = "ICMMove(icm:und*int:USR*dest_city(paris))"
        self.assertEquals(expected_string, unicode(icm))

    def test_create_und_pos(self):
        icm = self.move_factory.createIcmMove(ICMMove.UND, polarity=ICMMove.POS, speaker=Speaker.SYS)
        self.assertEquals(ICMMove.UND, icm.get_type())
        self.assertEquals(ICMMove.POS, icm.get_polarity())

    def test_und_pos_to_string(self):
        icm = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.POS, content_speaker=Speaker.USR, content=self.proposition_dest_city_paris
        )
        expected_string = "ICMMove(icm:und*pos:USR*dest_city(paris))"
        self.assertEquals(expected_string, unicode(icm))

    def test_per_neg_to_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.PER, polarity=ICMMove.NEG)
        self.assertEquals("ICMMove(icm:per*neg)", unicode(icm))

    def test_per_pos_to_string_with_content_as_double_quoted_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.PER, polarity=ICMMove.POS, content='a string')
        self.assertEquals('ICMMove(icm:per*pos:"a string")', unicode(icm))

    def test_acc_pos_to_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.ACC, polarity=ICMMove.POS)
        self.assertEquals("ICMMove(icm:acc*pos)", unicode(icm))

    def test_sem_neg_to_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.SEM, polarity=ICMMove.NEG)
        expected_string = "ICMMove(icm:sem*neg)"
        self.assertEquals(expected_string, unicode(icm))

    def test_acc_neg_issue_to_string(self):
        icm = self.move_factory.createIcmMove(ICMMove.ACC, polarity=ICMMove.NEG, content="issue")
        self.assertEquals("ICMMove(icm:acc*neg:issue)", unicode(icm))

    def test_icm_move_getters(self):
        move = self.move_factory.createIcmMove(
            ICMMove.UND, polarity=ICMMove.INT, content=self.price_question, content_speaker=Speaker.USR
        )
        self.assertTrue(move.is_icm())
        self.assertEquals(ICMMove.INT, move.get_polarity())
        self.assertEquals(self.price_question, move.get_content())
        self.assertEquals(Speaker.USR, move.get_content_speaker())

    def test_ddd_getter_and_setter(self):
        move = self.move_factory.createMove(Move.GREET)
        name = "mockup_ddd"
        move.set_ddd_name(name)
        self.assertEquals(name, move.get_ddd_name())


class MoveRealizationTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)

    def test_set_realization_data_for_haptic_input(self):
        move = self.move_factory.createMove(Move.GREET)
        understanding_confidence = 0.5
        speaker = Speaker.USR
        modality = Modality.HAPTIC
        move.set_realization_data(
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            modality=modality,
            ddd_name="mockup_ddd"
        )
        self.assertEquals(understanding_confidence, move.understanding_confidence)
        self.assertEquals(speaker, move.get_speaker())
        self.assertEquals(modality, move.get_modality())

    def test_set_realization_data_for_spoken_input(self):
        move = self.move_factory.createMove(Move.GREET)
        understanding_confidence = 0.5
        speaker = Speaker.USR
        modality = Modality.SPEECH
        utterance = "hello"
        move.set_realization_data(
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            modality=modality,
            utterance=utterance,
            ddd_name="mockup_ddd"
        )
        self.assertEquals(understanding_confidence, move.understanding_confidence)
        self.assertEquals(speaker, move.get_speaker())
        self.assertEquals(modality, move.get_modality())
        self.assertEquals(utterance, move.get_utterance())

    def test_set_realization_data_raises_exception_if_already_set(self):
        greet_move = self.move_factory.createMove(Move.GREET)
        icm_move = self.move_factory.createIcmMove(ICMMove.ACC, content=ICMMove.POS)
        for move in [greet_move, icm_move]:
            move.set_realization_data(speaker=Speaker.SYS, ddd_name="mockup_ddd")
            with self.assertRaisesRegexp(MoveException, "realization data already set"):
                move.set_realization_data(speaker=Speaker.SYS)

    def test_realization_with_speaker_usr_and_no_score_not_allowed(self):
        with self.assertRaisesRegexp(MoveException, "understanding confidence must be supplied for user moves"):
            self.move_factory.createMove(Move.GREET, speaker=Speaker.USR)
        with self.assertRaises(MoveException):
            self.move_factory.createIcmMove(ICMMove.ACC, ICMMove.POS, speaker=Speaker.USR)

    def test_realization_without_speaker_not_allowed(self):
        with self.assertRaisesRegexp(MoveException, "speaker must be supplied"):
            self.move_factory.createMove(Move.GREET, understanding_confidence=1.0)
        with self.assertRaises(MoveException):
            self.move_factory.createIcmMove(ICMMove.ACC, ICMMove.POS, understanding_confidence=1.0)

    def test_realization_without_ddd_name_not_allowed_for_user_moves(self):
        with self.assertRaisesRegexp(MoveException, "ddd_name must be supplied"):
            self.move_factory.createMove(Move.GREET, understanding_confidence=1.0, speaker=Speaker.USR)

    def test_realization_with_speaker_sys_and_score_below_one_not_allowed(self):
        with self.assertRaisesRegexp(MoveException, "understanding confidence below 1.0 not allowed for system moves"):
            self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS, understanding_confidence=0.5)
        with self.assertRaises(MoveException):
            self.move_factory.createIcmMove(
                ICMMove.ACC, content=ICMMove.POS, speaker=Speaker.SYS, understanding_confidence=0.5
            )

    def test_realization_with_speaker_sys_and_score_one_allowed(self):
        self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS, understanding_confidence=1.0)
        self.move_factory.createIcmMove(ICMMove.ACC, ICMMove.POS, speaker=Speaker.SYS, understanding_confidence=1.0)

    def test_get_score_returns_one_for_move_with_speaker_sys(self):
        greet_move = self.move_factory.createMove(Move.GREET, speaker=Speaker.SYS)
        icm_move = self.move_factory.createIcmMove(ICMMove.ACC, content=ICMMove.POS, speaker=Speaker.SYS)
        for sys_move in [greet_move, icm_move]:
            self.assertEquals(1.0, sys_move.understanding_confidence)

    def test_move_speech_modality_is_default(self):
        quit_move = self.move_factory.createMove(Move.QUIT, speaker=Speaker.SYS)
        icm_move = self.move_factory.createIcmMove(ICMMove.ACC, content=ICMMove.POS, speaker=Speaker.SYS)
        for move in [quit_move, icm_move]:
            self.assertEquals(Modality.SPEECH, move.get_modality())

    def test_move_haptic_modality_is_available(self):
        self.move_factory.createMove(Move.QUIT, speaker=Speaker.SYS, modality=Modality.HAPTIC)

    def test_move_text_modality_is_available(self):
        self.move_factory.createMove(Move.QUIT, speaker=Speaker.SYS, modality=Modality.TEXT)


class MoveTestsFromTdmLib(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def testPropositionalAnswerMoveEquality(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        destination_answer = self.proposition_dest_city_paris
        answerMove = move_factory.createAnswerMove(destination_answer)
        duplicateMove = move_factory.createAnswerMove(destination_answer)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(answerMove, duplicateMove)

    def testYesNoAskMoveunicode(self):
        question = self.ontology.create_yes_no_question("dest_city", "paris")
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        move = move_factory.create_ask_move(question)
        moveAsString = unicode(move)
        self.assertEquals("Move(ask(?dest_city(paris)))", moveAsString)

    def test_wh_ask_move_to_string(self):
        move_factory = MoveFactoryWithPredefinedBoilerplate(self.ontology_name)
        move = move_factory.create_ask_move(self.dest_city_question)
        moveAsString = unicode(move)
        self.assertEquals("Move(ask(?X.dest_city(X)))", moveAsString)
