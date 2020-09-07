from tala.model.move import ICMMove
from tala.model.proposition import Proposition
from tala.model.semantic_object import SemanticObject, OntologySpecificSemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify


class PlanItem(SemanticObject, AsSemanticExpressionMixin):
    TYPE_RESPOND = "respond"
    TYPE_GREET = "greet"
    TYPE_QUIT = "quit"
    TYPE_MUTE = "mute"
    TYPE_UNMUTE = "unmute"
    TYPE_FINDOUT = "findout"
    TYPE_CONSULTDB = "consultDB"
    TYPE_RAISE = "raise"
    TYPE_BIND = "bind"
    TYPE_DO = "do"
    TYPE_EMIT_ICM = "emit_icm"
    TYPE_JUMPTO = "jumpto"
    TYPE_IF_THEN_ELSE = "if_then_else"
    TYPE_FORGET_ALL = "forget_all"
    TYPE_FORGET = "forget"
    TYPE_FORGET_ISSUE = "forget_issue"
    TYPE_INVOKE_SERVICE_QUERY = "invoke_service_query"
    TYPE_INVOKE_SERVICE_ACTION = "invoke_service_action"
    TYPE_SERVICE_REPORT = "service_report"
    TYPE_ASSUME = "assume"
    TYPE_ASSUME_SHARED = "assume_shared"
    TYPE_ASSUME_ISSUE = "assume_issue"
    TYPE_EMIT_MOVE = "emit_move"
    TYPE_HANDLE = "handle"
    TYPE_LOG = "log"
    TYPE_GET_DONE = "get_done"

    def __init__(self, type):
        SemanticObject.__init__(self)
        self._type = type

    def __repr__(self):
        return "%s%s" % (PlanItem.__class__.__name__, (self._type, ))

    def __str__(self):
        return str(self._type)

    def __eq__(self, other):
        return other.is_plan_item() and self.get_type() == other.get_type()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.__class__.__name__, self._type))

    def get_type(self):
        return self._type

    def is_plan_item(self):
        return True

    def isRespondPlanItem(self):
        return self._type == self.TYPE_RESPOND

    def isQuitPlanItem(self):
        return self._type == self.TYPE_QUIT

    def is_mute_plan_item(self):
        return self._type == self.TYPE_MUTE

    def is_unmute_plan_item(self):
        return self._type == self.TYPE_UNMUTE

    def isGreetPlanItem(self):
        return self._type == self.TYPE_GREET

    def isFindoutPlanItem(self):
        return self._type == self.TYPE_FINDOUT

    def isConsultDBPlanItem(self):
        return self._type == self.TYPE_CONSULTDB

    def isRaisePlanItem(self):
        return self._type == self.TYPE_RAISE

    def isBindPlanItem(self):
        return self._type == self.TYPE_BIND

    def isDoPlanItem(self):
        return self._type == self.TYPE_DO

    def isEmitIcmPlanItem(self):
        return self._type == self.TYPE_EMIT_ICM

    def is_question_plan_item(self):
        return self._type in [self.TYPE_FINDOUT, self.TYPE_RAISE, self.TYPE_BIND]

    def is_forget_all_plan_item(self):
        return self._type == self.TYPE_FORGET_ALL

    def is_forget_plan_item(self):
        return self._type == self.TYPE_FORGET

    def is_forget_issue_plan_item(self):
        return self._type == self.TYPE_FORGET_ISSUE

    def is_invoke_service_query_plan_item(self):
        return self._type == self.TYPE_INVOKE_SERVICE_QUERY

    def is_invoke_service_action_plan_item(self):
        return self._type == self.TYPE_INVOKE_SERVICE_ACTION

    def is_service_report_plan_item(self):
        return self._type == self.TYPE_SERVICE_REPORT

    def is_jumpto_plan_item(self):
        return self._type == self.TYPE_JUMPTO

    def is_assume_plan_item(self):
        return self._type == self.TYPE_ASSUME

    def is_assume_shared_plan_item(self):
        return self._type == self.TYPE_ASSUME_SHARED

    def is_assume_issue_plan_item(self):
        return self._type == self.TYPE_ASSUME_ISSUE

    def is_emit_move_plan_item(self):
        return self._type == self.TYPE_EMIT_MOVE

    def is_handle_plan_item(self):
        return self._type == self.TYPE_HANDLE

    def is_log_plan_item(self):
        return self._type == self.TYPE_LOG

    def getType(self):
        return self._type

    def is_question_raising_item(self):
        return False

    def is_turn_yielding(self):
        return False

    def as_dict(self):
        return {
            self.get_type(): None,
        }


class PlanItemWithSemanticContent(PlanItem, SemanticObjectWithContent):
    def __init__(self, type, content):
        PlanItem.__init__(self, type)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    def __repr__(self):
        return "%s%s" % (PlanItemWithSemanticContent.__name__, (self._type, self._content))

    def __str__(self):
        return "%s(%s)" % (str(self._type), str(self._content))

    def __eq__(self, other):
        return other is not None and other.is_plan_item() and other.has_semantic_content() and self.get_type(
        ) == other.get_type() and self.get_content() == other.get_content()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.__class__.__name__, self._type, self._content))

    def get_type(self):
        return self._type

    def get_content(self):
        return self._content

    def getContent(self):
        return self.get_content()

    def as_dict(self):
        return {self.get_type(): self._content}


class AssumePlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_ASSUME, content=content)


class AssumeSharedPlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_ASSUME_SHARED, content=content)


class AssumeIssuePlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_ASSUME_ISSUE, content=content)


class RespondPlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_RESPOND, content=content)

    def is_turn_yielding(self):
        return True


class DoPlanItem(PlanItemWithSemanticContent):
    def __init__(self, action):
        assert action.is_action()
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_DO, content=action)


class QuitPlanItem(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, PlanItem.TYPE_QUIT)


class MutePlanItem(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, PlanItem.TYPE_MUTE)


class UnmutePlanItem(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, PlanItem.TYPE_UNMUTE)


class GreetPlanItem(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, PlanItem.TYPE_GREET)


class EmitIcmPlanItem(PlanItemWithSemanticContent):
    def __init__(self, icm_move):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_EMIT_ICM, content=icm_move)

    def is_question_raising_item(self):
        icm = self.getContent()
        return (
            icm.get_type() == ICMMove.UND
            and not (icm.get_polarity() == ICMMove.POS and not icm.get_content().is_positive())
        )

    def is_turn_yielding(self):
        icm = self.getContent()
        return (icm.get_type() == ICMMove.ACC and icm.get_polarity() == ICMMove.NEG)


class BindPlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_BIND, content)

    def get_question(self):
        return self.getContent()


class ConsultDBPlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_CONSULTDB, content=content)


class JumpToPlanItem(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_JUMPTO, content=content)


class IfThenElse(PlanItem):
    def __init__(self, condition, consequent, alternative):
        self.condition = condition
        self.consequent = consequent
        self.alternative = alternative
        assert consequent is not None or alternative is not None, "One of consequent (%s) and alternative (%s) must not be None" % (
            consequent, alternative
        )
        if consequent is not None and alternative is not None:
            assert consequent.ontology_name == alternative.ontology_name, "Expected identical ontologies in both consequent (%s) and alternative (%s) but got %r and %r" % (
                consequent, alternative, consequent.ontology_name, alternative.ontology_name
            )
        PlanItem.__init__(self, PlanItem.TYPE_IF_THEN_ELSE)

    def get_condition(self):
        return self.condition

    def get_consequent(self):
        return self.consequent

    def get_alternative(self):
        return self.alternative

    def remove_consequent(self):
        self.consequent = None

    def remove_alternative(self):
        self.alternative = None

    def __str__(self):
        return "if_then_else{}".format(unicodify((self.condition, self.consequent, self.alternative)))

    def as_dict(self):
        return {
            self.get_type(): {
                "condition": self.condition,
                "consequent": self.consequent,
                "alternative": self.alternative,
            }
        }


class ForgetAllPlanItem(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, PlanItem.TYPE_FORGET_ALL)


class ForgetPlanItem(PlanItemWithSemanticContent):
    def __init__(self, predicate_or_proposition):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_FORGET, predicate_or_proposition)


class ForgetIssuePlanItem(PlanItemWithSemanticContent):
    def __init__(self, issue):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_FORGET_ISSUE, issue)


class MinResultsNotSupportedException(Exception):
    pass


class MaxResultsNotSupportedException(Exception):
    pass


class InvokeServiceQueryPlanItem(PlanItemWithSemanticContent):
    def __init__(self, issue, min_results=None, max_results=None):
        min_results = min_results or 0
        if min_results < 0:
            raise MinResultsNotSupportedException("Expected 'min_results' to be 0 or above but got %r." % min_results)
        if max_results is not None and max_results < 1:
            raise MaxResultsNotSupportedException(
                "Expected 'max_results' to be None or above 0 but got %r." % max_results
            )
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_INVOKE_SERVICE_QUERY, issue)
        self._min_results = min_results
        self._max_results = max_results

    def get_min_results(self):
        return self._min_results

    def get_max_results(self):
        return self._max_results

    def __str__(self):
        return "invoke_service_query(%s, min_results=%s, max_results=%s)" % (
            str(self._content), self._min_results, self._max_results
        )

    def __repr__(self):
        return "%s(%r, min_results=%r, max_results=%r)" % (
            self.__class__.__name__, self._content, self._min_results, self._max_results
        )

    def __eq__(self, other):
        return super(PlanItemWithSemanticContent, self).__eq__(other) and other.get_min_results(
        ) == self.get_min_results() and other.get_max_results() == self.get_max_results()

    def as_dict(self):
        return {
            self.get_type(): {
                "issue": self._content,
                "min_results": self._min_results,
                "max_results": self._max_results,
            }
        }


class InvokeServiceActionPlanItem(PlanItem, OntologySpecificSemanticObject):
    INTERROGATIVE = "INTERROGATIVE"
    ASSERTIVE = "ASSERTIVE"

    def __init__(self, ontology_name, service_action, preconfirm=None, postconfirm=False, downdate_plan=True):
        self.service_action = service_action
        self.preconfirm = preconfirm
        self.postconfirm = postconfirm
        self._downdate_plan = downdate_plan
        PlanItem.__init__(self, PlanItem.TYPE_INVOKE_SERVICE_ACTION)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def get_service_action(self):
        return self.service_action

    def has_interrogative_preconfirmation(self):
        return self.preconfirm == self.INTERROGATIVE

    def has_assertive_preconfirmation(self):
        return self.preconfirm == self.ASSERTIVE

    def has_postconfirmation(self):
        return self.postconfirm

    def should_downdate_plan(self):
        return self._downdate_plan

    def __eq__(self, other):
        return super(InvokeServiceActionPlanItem, self).__eq__(other) and other.get_service_action(
        ) == self.get_service_action() and other.has_interrogative_preconfirmation(
        ) == self.has_interrogative_preconfirmation() and other.has_assertive_preconfirmation(
        ) == self.has_assertive_preconfirmation() and other.has_postconfirmation() == self.has_postconfirmation(
        ) and other.should_downdate_plan() == self.should_downdate_plan()

    def __str__(self):
        return "invoke_service_action(%s, {preconfirm=%s, postconfirm=%s, downdate_plan=%s})" % (
            str(self.service_action), self.preconfirm, self.postconfirm, self._downdate_plan
        )

    def __repr__(self):
        return "%s(%r, %r, preconfirm=%r, postconfirm=%r, downdate_plan=%r)" % (
            self.__class__.__name__, self.ontology_name, self.service_action, self.preconfirm, self.postconfirm,
            self._downdate_plan
        )

    def as_dict(self):
        return {
            self.get_type(): {
                "service_action": self.service_action,
                "ontology": self.ontology_name,
                "preconfirm": self.preconfirm,
                "postconfirm": self.postconfirm,
                "downdate_plan": self._downdate_plan,
            }
        }


class ServiceReportPlanItem(PlanItemWithSemanticContent):
    def __init__(self, result_proposition):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_SERVICE_REPORT, result_proposition)

    def is_turn_yielding(self):
        return self._content.get_type() == Proposition.SERVICE_RESULT


class EmitMovePlanItem(PlanItemWithSemanticContent):
    def __init__(self, move):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_EMIT_MOVE, move)


class HandlePlanItem(PlanItem, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action):
        PlanItem.__init__(self, PlanItem.TYPE_HANDLE)
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self._service_action = service_action

    @property
    def service_action(self):
        return self._service_action

    def __str__(self):
        return "invoke_service_action(%s)" % (str(self.service_action))

    def as_dict(self):
        return {
            self.get_type(): {
                "service_action": self._service_action,
                "ontology": self.ontology_name,
            }
        }


class LogPlanItem(PlanItem):
    def __init__(self, message):
        PlanItem.__init__(self, PlanItem.TYPE_LOG)
        self._message = message

    @property
    def message(self):
        return self._message

    def __str__(self):
        return f"log_plan_item('{self.message}')"


class GetDonePlanItem(PlanItemWithSemanticContent):
    def __init__(self, action):
        PlanItemWithSemanticContent.__init__(self, PlanItem.TYPE_GET_DONE, action)
