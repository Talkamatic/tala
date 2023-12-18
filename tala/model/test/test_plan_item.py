# flake8: noqa

from tala.model.move import ICMMove, ICMMoveWithSemanticContent
from tala.model import plan_item
from tala.model.proposition import ServiceResultProposition
from tala.testing.lib_test_case import LibTestCase
from tala.utils.unicodify import unicodify


class PlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.question = self.dest_city_question
        self.respond_plan_item = plan_item.Respond(self.question)
        self.findout_plan_item = plan_item.Findout(self.domain_name, self.question)
        self.raise_plan_item = plan_item.Raise(self.domain_name, self.question)
        self.bind_plan_item = plan_item.Bind(self.question)
        self.if_condition = self.proposition_dest_city_paris
        self.if_consequent = [self.findout_plan_item]
        self.if_alternative = [self.raise_plan_item]
        self.if_then_else_plan_item = plan_item.IfThenElse(self.if_condition, self.if_consequent, self.if_alternative)
        self.service_result_proposition = ServiceResultProposition(
            self.ontology_name, "mockup_service_action", [], "mock_perform_result"
        )
        self.service_report_item = plan_item.ServiceReport(self.service_result_proposition)

    def test_equality_with_none(self):
        self.assertNotEqual(self.respond_plan_item, None)

    def test_create_DoPlanItem(self):
        do_item = plan_item.Do(self.buy_action)
        self.assertEqual(self.buy_action, do_item.content)

    def test_DoPlanItem_type(self):
        do_item = plan_item.Do(self.buy_action)
        self.assertEqual(plan_item.TYPE_DO, do_item.type_)

    def test_isRespondPlanItem(self):
        self.assertTrue(self.respond_plan_item.type_ == plan_item.TYPE_RESPOND)

    def test_isFindoutPlanItem(self):
        self.assertTrue(self.findout_plan_item.type_ == plan_item.TYPE_FINDOUT)

    def test_FindoutPlanItem_content(self):
        self.assertEqual(self.question, self.findout_plan_item.content)

    def test_isRaisePlanItem(self):
        self.assertTrue(self.raise_plan_item.type_ == plan_item.TYPE_RAISE)

    def test_RaisePlanItem_content(self):
        self.assertEqual(self.question, self.raise_plan_item.content)

    def test_FindoutPlanItem_to_string(self):
        expected_string = "findout(?X.dest_city(X))"
        self.assertEqual(expected_string, str(self.findout_plan_item))

    def test_PlanItem_unicode(self):
        quitPlanItem = plan_item.Quit()
        self.assertEqual(str(quitPlanItem), "quit")

    def test_GreetPlanItem_unicode(self):
        greetPlanItem = plan_item.Greet()
        self.assertEqual(str(greetPlanItem), "greet")

    def test_findout_is_question_plan_item(self):
        self.assertTrue(self.findout_plan_item.type_ in plan_item.QUESTION_TYPES)

    def test_raise_is_question_plan_item(self):
        self.assertTrue(self.raise_plan_item.type_ in plan_item.QUESTION_TYPES)

    def test_bind_is_question_plan_item(self):
        self.assertTrue(self.bind_plan_item.type_ in plan_item.QUESTION_TYPES)

    def test_respond_is_not_question_plan_item(self):
        self.assertFalse(self.respond_plan_item.type_ in plan_item.QUESTION_TYPES)

    def test_findout_is_question_raising_item(self):
        self.assertTrue(self.findout_plan_item.is_question_raising_item())

    def test_raise_is_question_raising_item(self):
        self.assertTrue(self.raise_plan_item.is_question_raising_item())

    def test_bind_is_not_question_raising_item(self):
        self.assertFalse(self.bind_plan_item.is_question_raising_item())

    def test_respond_is_not_question_raising_item(self):
        self.assertFalse(self.respond_plan_item.is_question_raising_item())

    def test_emit_item_for_icm_und_non_pos_is_question_raising_item(self):
        icm_und = ICMMove(ICMMove.UND, polarity=ICMMove.NEG)
        emit_item = plan_item.EmitIcm(icm_und)
        self.assertTrue(emit_item.is_question_raising_item())

    def test_emit_item_for_icm_und_pos_for_positive_content_is_question_raising_item(self):
        positive_content = self.proposition_dest_city_paris
        icm = ICMMoveWithSemanticContent(ICMMove.UND, positive_content, polarity=ICMMove.POS)
        emit_item = plan_item.EmitIcm(icm)
        self.assertTrue(emit_item.is_question_raising_item())

    def test_emit_item_for_icm_und_pos_for_negated_content_is_not_question_raising_item(self):
        negation = self.proposition_not_dest_city_paris
        icm = ICMMoveWithSemanticContent(ICMMove.UND, negation, polarity=ICMMove.POS)
        emit_item = plan_item.EmitIcm(icm)
        self.assertFalse(emit_item.is_question_raising_item())

    def test_report_item_is_turn_yielding(self):
        self.assertTrue(self.service_report_item.is_turn_yielding())

    def test_respond_item_is_turn_yielding(self):
        self.assertTrue(self.respond_plan_item.is_turn_yielding())

    def test_emit_item_for_acc_neg_is_turn_yielding(self):
        icm_acc_neg = ICMMove(ICMMove.ACC, polarity=ICMMove.NEG)
        emit_item = plan_item.EmitIcm(icm_acc_neg)
        self.assertTrue(emit_item.is_turn_yielding())

    def test_emit_item_for_acc_pos_is_not_turn_yielding(self):
        icm_acc_pos = ICMMove(ICMMove.ACC, polarity=ICMMove.POS)
        emit_item = plan_item.EmitIcm(icm_acc_pos)
        self.assertFalse(emit_item.is_turn_yielding())

    def test_if_then_else_getters(self):
        self.assertEqual(plan_item.TYPE_IF_THEN_ELSE, self.if_then_else_plan_item.type_)
        self.assertEqual(self.if_condition, self.if_then_else_plan_item.get_condition())
        self.assertEqual(self.if_consequent, self.if_then_else_plan_item.get_consequent())
        self.assertEqual(self.if_alternative, self.if_then_else_plan_item.get_alternative())

    def test_if_then_else_to_string(self):
        expected_string = "if_then_else{}".format(
            unicodify((self.if_condition, self.if_consequent, self.if_alternative))
        )
        self.assertEqual(expected_string, str(self.if_then_else_plan_item))

    def test_create_forget_all(self):
        item = plan_item.ForgetAll()
        self.assertTrue(item.type_ == plan_item.TYPE_FORGET_ALL)

    def test_create_forget_plan_item_proposition(self):
        fact = self.proposition_dest_city_paris
        item = plan_item.Forget(fact)
        self.assertEqual(item.type_, plan_item.TYPE_FORGET)
        self.assertEqual(fact, item.content)

    def test_create_forget_plan_item_predicate(self):
        predicate = self.predicate_dept_city
        item = plan_item.Forget(predicate)
        self.assertTrue(item.type_ == plan_item.TYPE_FORGET)
        self.assertEqual(predicate, item.content)

    def test_create_forget_issue_plan_item(self):
        issue = self.price_question
        item = plan_item.ForgetIssue(issue)
        self.assertTrue(item.type_ == plan_item.TYPE_FORGET_ISSUE)
        self.assertEqual(issue, item.content)

    def test_service_report_plan_item(self):
        self.assertTrue(self.service_report_item.type_ == plan_item.TYPE_SERVICE_REPORT)
        self.assertTrue(self.service_result_proposition, self.service_report_item.content)

    def test_findout_equality(self):  #/// Should allow_answer_from_pcom change equality?
        item = plan_item.Findout(self.domain_name, self.question)
        identical_item = plan_item.Findout(self.domain_name, self.question)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(identical_item, item)

    def test_inequality_due_to_question(self):
        item1 = plan_item.Findout(self.domain_name, self.dest_city_question)
        item2 = plan_item.Findout(self.domain_name, self.price_question)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(item1, item2)

    def test_clone_findout_into_raise_plan_item(self):
        findout_plan_item = plan_item.Findout(self.domain_name, self.question)
        raise_plan_item = findout_plan_item.clone_as_type(plan_item.TYPE_RAISE)
        self.assertTrue(raise_plan_item.type_ == plan_item.TYPE_RAISE)
        self.assertEqual(self.question, raise_plan_item.question)

    def test_findout_defaults_to_disallow_answer_from_pcom(self):
        findout_plan_item = plan_item.Findout(self.domain_name, self.question)
        self.assertFalse(findout_plan_item.allow_answer_from_pcom)

    def test_findout_supports_allow_answer_from_pcom(self):
        findout_plan_item = plan_item.Findout(self.domain_name, self.question, allow_answer_from_pcom=True)
        self.assertTrue(findout_plan_item.allow_answer_from_pcom)

    #/// FindoutPlanItem is not used by ddd_xml_compiler. Only
    # QuestionRaisingPlanItem is.
    # 1. Tests?
    # 2. Remove FindoutPlanItem?


class InvokeServiceActionPlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_invoke_service_action_plan_item(self):
        self.given_created_service_action_plan_item()
        self._actual_result = self._plan_item.type_
        self.then_result_is(plan_item.TYPE_INVOKE_SERVICE_ACTION)

    def given_created_service_action_plan_item(self, service_action="mock_service_action", **kwargs):
        self._plan_item = plan_item.InvokeServiceAction(self.ontology.name, service_action, **kwargs)

    def test_get_service_action(self):
        self.given_created_service_action_plan_item(service_action="mock_service_action")
        self.when_call(self._plan_item.get_service_action)
        self.then_result_is("mock_service_action")

    def test_has_interrogative_preconfirmation_false_by_default(self):
        self.given_created_service_action_plan_item()
        self.when_call(self._plan_item.has_interrogative_preconfirmation)
        self.then_result_is(False)

    def test_interrogative_preconfirmation_true(self):
        self.given_created_service_action_plan_item(preconfirm=plan_item.InvokeServiceAction.INTERROGATIVE)
        self.when_call(self._plan_item.has_interrogative_preconfirmation)
        self.then_result_is(True)

    def test_has_assertive_preconfirmation_false_by_default(self):
        self.given_created_service_action_plan_item()
        self.when_call(self._plan_item.has_assertive_preconfirmation)
        self.then_result_is(False)

    def test_assertive_preconfirmation_true(self):
        self.given_created_service_action_plan_item(preconfirm=plan_item.InvokeServiceAction.ASSERTIVE)
        self.when_call(self._plan_item.has_assertive_preconfirmation)
        self.then_result_is(True)

    def test_has_postconfirmation_false_by_default(self):
        self.given_created_service_action_plan_item()
        self.when_call(self._plan_item.has_postconfirmation)
        self.then_result_is(False)

    def test_has_postconfirmation_true(self):
        self.given_created_service_action_plan_item(postconfirm=True)
        self.when_call(self._plan_item.has_postconfirmation)
        self.then_result_is(True)

    def test_should_downdate_plan_true_by_default(self):
        self.given_created_service_action_plan_item()
        self.when_call(self._plan_item.should_downdate_plan)
        self.then_result_is(True)

    def test_should_downdate_plan_false(self):
        self.given_created_service_action_plan_item(downdate_plan=False)
        self.when_call(self._plan_item.should_downdate_plan)
        self.then_result_is(False)

    def test_unicode(self):
        self.given_created_service_action_plan_item(
            service_action="mock_service_action", preconfirm=None, postconfirm=False, downdate_plan=True
        )
        self.when_get_unicode()
        self.then_result_is(
            "invoke_service_action(mock_service_action, {preconfirm=None, postconfirm=False, downdate_plan=True})"
        )

    def when_get_unicode(self):
        self._actual_result = str(self._plan_item)


class InvokeServiceQueryPlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_invoke_service_query_plan_item(self):
        self.given_created_invoke_service_query_plan_item()
        self._actual_result = self._plan_item.type_
        self.then_result_is(plan_item.TYPE_INVOKE_SERVICE_QUERY)

    def given_created_invoke_service_query_plan_item(self, *args, **kwargs):
        self._create_invoke_service_query_plan_item(*args, **kwargs)

    def _create_invoke_service_query_plan_item(self, issue="mock_issue", min_results=None, max_results=None):
        self._plan_item = plan_item.InvokeServiceQuery(issue, min_results, max_results)

    def test_min_results_is_0_by_default(self):
        self.given_created_invoke_service_query_plan_item()
        self.when_getting_value(self._plan_item.min_results)
        self.then_result_is(0)

    def test_min_results_overridden(self):
        self.given_created_invoke_service_query_plan_item(min_results=1)
        self.when_getting_value(self._plan_item.min_results)
        self.then_result_is(1)

    def test_max_results_is_none_by_default(self):
        self.given_created_invoke_service_query_plan_item()
        self.when_getting_value(self._plan_item.max_results)
        self.then_result_is(None)

    def test_max_results_overridden(self):
        self.given_created_invoke_service_query_plan_item(max_results=1)
        self.when_getting_value(self._plan_item.max_results)
        self.then_result_is(1)

    def test_exception_raised_for_min_results_below_0(self):
        self.when_created_invoke_service_query_plan_item_then_exception_is_raised(
            min_results=-1,
            max_results=None,
            expected_exception=plan_item.MinResultsNotSupportedException,
            expected_message="Expected 'min_results' to be 0 or above but got -1."
        )

    def test_exception_raised_for_max_results_below_1(self):
        self.when_created_invoke_service_query_plan_item_then_exception_is_raised(
            min_results=0,
            max_results=0,
            expected_exception=plan_item.MaxResultsNotSupportedException,
            expected_message="Expected 'max_results' to be None or above 0 but got 0."
        )

    def when_created_invoke_service_query_plan_item_then_exception_is_raised(
        self, min_results, max_results, expected_exception, expected_message
    ):
        with self.assertRaises(expected_exception) as context_manager:
            self._create_invoke_service_query_plan_item(min_results=min_results, max_results=max_results)
        self.assertEqual(expected_message, str(context_manager.exception))

    def test_get_content(self):
        self.given_created_invoke_service_query_plan_item(issue="mock_issue")
        self._actual_result = self._plan_item.content
        self.then_result_is("mock_issue")

    def test_unicode(self):
        self.given_created_invoke_service_query_plan_item(issue="mock_issue", min_results=0, max_results=1)
        self.when_get_unicode()
        self.then_result_is("invoke_service_query(mock_issue, min_results=0, max_results=1)")

    def when_get_unicode(self):
        self._actual_result = str(self._plan_item)


class JumpToPlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.action = self.buy_action
        self.item = plan_item.JumpTo(self.action)

    def test_unicode(self):
        self.assertEqual("jumpto(buy)", str(self.item))

    def test_equality(self):
        identical_item = plan_item.JumpTo(self.action)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.item, identical_item)

    def test_inequality(self):
        non_identical_item = plan_item.JumpTo(self.top_action)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.item, non_identical_item)


class AssumePlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.assume_price = plan_item.Assume(self.price_proposition)

    def test_unicode(self):
        self.assertEqual("assume(price(1234.0))", str(self.assume_price))

    def test_is_assume_item(self):
        self.assertEqual(self.assume_price.type_, plan_item.TYPE_ASSUME)


class AssumeSharedPlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.assume_shared_price = plan_item.AssumeShared(self.price_proposition)

    def test_unicode(self):
        self.assertEqual("assume_shared(price(1234.0))", str(self.assume_shared_price))

    def test_is_assume_shared_item(self):
        self.assertEqual(self.assume_shared_price.type_, plan_item.TYPE_ASSUME_SHARED)


class AssumeSharedIssuePlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.assume_price_issue = plan_item.AssumeIssue(self.price_question)

    def test_unicode(self):
        self.assertEqual("assume_issue(?X.price(X))", str(self.assume_price_issue))

    def test_is_assume_shared_issue(self):
        self.assertEqual(self.assume_price_issue.type_, plan_item.TYPE_ASSUME_ISSUE)


class LogPlanItemTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.message = "log message"
        self.log_plan_item = plan_item.Log(self.message)

    def test_string(self):
        self.assertEqual("log_plan_item('debug', 'log message')", str(self.log_plan_item))

    def test_is_log_plan_item(self):
        self.assertEqual(self.log_plan_item.type_, plan_item.TYPE_LOG)
