import copy
import warnings

from tala.model.error import DomainError
from tala.model.move import ICMMove
from tala.model.proposition import Proposition
from tala.model.semantic_object import SemanticObject, OntologySpecificSemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify

TYPE_RESPOND = "respond"
TYPE_GREET = "greet"
TYPE_RESPOND_TO_INSULT = "respond_to_insult"
TYPE_RESPOND_TO_THANK_YOU = "respond_to_thank_you"
TYPE_QUIT = "quit"
TYPE_MUTE = "mute"
TYPE_UNMUTE = "unmute"
TYPE_FINDOUT = "findout"
TYPE_RAISE = "raise"
TYPE_BIND = "bind"
TYPE_DO = "do"
TYPE_EMIT_ICM = "emit_icm"
TYPE_JUMPTO = "jumpto"
TYPE_IF_THEN_ELSE = "if_then_else"
TYPE_FORGET_ALL = "forget_all"
TYPE_FORGET = "forget"
TYPE_FORGET_SHARED = "forget_shared"
TYPE_FORGET_ISSUE = "forget_issue"
TYPE_INVOKE_SERVICE_QUERY = "invoke_service_query"
TYPE_INVOKE_DOMAIN_QUERY = "invoke_domain_query"
TYPE_INVOKE_SERVICE_ACTION = "invoke_service_action"
TYPE_SERVICE_REPORT = "service_report"
TYPE_ACTION_REPORT = "action_report"
TYPE_QUESTION_REPORT = "question_report"
TYPE_ASSUME = "assume"
TYPE_ASSUME_SHARED = "assume_shared"
TYPE_ASSUME_ISSUE = "assume_issue"
TYPE_EMIT_MOVE = "emit_move"
TYPE_HANDLE = "handle"
TYPE_LOG = "log"
TYPE_GET_DONE = "get_done"
TYPE_ACTION_PERFORMED = "signal_action_completion"
TYPE_ACTION_ABORTED = "signal_action_failure"
TYPE_END_TURN = "end_turn"
TYPE_RESET_DOMAIN_QUERY = "reset_domain_query"
TYPE_ITERATE = "iterate"
TYPE_CHANGE_DDD = "change_ddd"

QUESTION_TYPES = [TYPE_FINDOUT, TYPE_RAISE, TYPE_BIND]

ALL_PLAN_ITEM_TYPES = [
    TYPE_RESPOND,
    TYPE_GREET,
    TYPE_RESPOND_TO_INSULT,
    TYPE_RESPOND_TO_THANK_YOU,
    TYPE_QUIT,
    TYPE_MUTE,
    TYPE_UNMUTE,
    TYPE_FINDOUT,
    TYPE_RAISE,
    TYPE_BIND,
    TYPE_DO,
    TYPE_EMIT_ICM,
    TYPE_JUMPTO,
    TYPE_IF_THEN_ELSE,
    TYPE_FORGET_ALL,
    TYPE_FORGET,
    TYPE_FORGET_SHARED,
    TYPE_FORGET_ISSUE,
    TYPE_INVOKE_SERVICE_QUERY,
    TYPE_INVOKE_DOMAIN_QUERY,
    TYPE_INVOKE_SERVICE_ACTION,
    TYPE_SERVICE_REPORT,
    TYPE_ACTION_REPORT,
    TYPE_QUESTION_REPORT,
    TYPE_ASSUME,
    TYPE_ASSUME_SHARED,
    TYPE_ASSUME_ISSUE,
    TYPE_EMIT_MOVE,
    TYPE_HANDLE,
    TYPE_LOG,
    TYPE_GET_DONE,
    TYPE_ACTION_PERFORMED,
    TYPE_ACTION_ABORTED,
    TYPE_END_TURN,
    TYPE_RESET_DOMAIN_QUERY,
    TYPE_ITERATE,
    TYPE_CHANGE_DDD
]  # yapf: disable


class PlanItem(SemanticObject, AsSemanticExpressionMixin):
    def __init__(self, type):
        SemanticObject.__init__(self)
        self._type = type

    def __repr__(self):
        return "%s%s" % (PlanItem.__class__.__name__, (self._type, ))

    def __str__(self):
        return str(self._type)

    def __eq__(self, other):
        return other.is_plan_item() and self.type_ == other.type_

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.__class__.__name__, self._type))

    @property
    def type_(self):
        return self._type

    def get_type(self):
        warnings.warn(
            "PlanItem.get_type() is deprecated. Use PlanItem.type_ instead.", DeprecationWarning, stacklevel=2
        )
        return self.type_

    def is_plan_item(self):
        return True

    def getType(self):
        warnings.warn("PlanItem.getType() is deprecated. Use PlanItem.type_ instead.", DeprecationWarning, stacklevel=2)
        return self._type

    def is_question_raising_item(self):
        return False

    def is_turn_yielding(self):
        return False

    def as_dict(self):
        return {
            self.type_: None,
        }


class PlanItemWithContent(PlanItem):
    def __init__(self, type, content):
        PlanItem.__init__(self, type)
        self._content = content

    def __repr__(self):
        return "%s%s" % (PlanItemWithContent.__name__, (self._type, self._content))

    def __str__(self):
        return "%s(%s)" % (str(self._type), str(self._content))

    def __eq__(self, other):
        try:
            return other is not None \
                and other.is_plan_item() \
                and self.type_ == other.type_ \
                and self.content == other.content
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.__class__.__name__, self._type, self._content))

    @property
    def content(self):
        return self._content

    def as_dict(self):
        return {self.type_: self._content}


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
        return other is not None and other.is_plan_item() and other.has_semantic_content(
        ) and self.type_ == other.type_ and self.content == other.content

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.__class__.__name__, self._type, self._content))

    def get_type(self):
        warnings.warn(
            "PlanItemWithSemanticContent.get_type() is deprecated. Use PlanItemWithSemanticContent.type_ instead.",
            DeprecationWarning,
            stacklevel=2
        )

        return self._type

    @property
    def content(self):
        return self._content

    def get_content(self):
        warnings.warn(
            "PlanItemWithSemanticContent.get_content() is deprecated. Use PlanItemWithSemanticContent.content instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._content

    def getContent(self):
        warnings.warn(
            "PlanItemWithSemanticContent.getContent() is deprecated. Use PlanItemWithSemanticContent.content instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.content

    def as_dict(self):
        return {self.type_: self._content}


class Assume(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, TYPE_ASSUME, content=content)


class AssumePlanItem(Assume):
    pass


class AssumeShared(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, TYPE_ASSUME_SHARED, content=content)


class AssumeSharedPlanItem(AssumeShared):
    pass


class AssumeIssue(PlanItemWithSemanticContent):
    def __init__(self, content, insist=False):
        PlanItemWithSemanticContent.__init__(self, TYPE_ASSUME_ISSUE, content=content)
        self._should_insist = insist

    @property
    def should_insist(self):
        return self._should_insist

    def as_dict(self):
        return {"insist": self.should_insist} | super().as_dict()


class AssumeIssuePlanItem(AssumeIssue):
    pass


class Respond(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, TYPE_RESPOND, content=content)

    def is_turn_yielding(self):
        return True


class RespondPlanItem(Respond):
    pass


class Do(PlanItemWithSemanticContent):
    def __init__(self, action):
        assert action.is_action()
        PlanItemWithSemanticContent.__init__(self, TYPE_DO, content=action)


class DoPlanItem(Do):
    pass


class Quit(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_QUIT)


class QuitPlanItem(Quit):
    pass


class Mute(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_MUTE)


class MutePlanItem(Mute):
    pass


class Unmute(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_UNMUTE)


class UnmutePlanItem(Unmute):
    pass


class Greet(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_GREET)

    def is_turn_yielding(self):
        return True


class GreetPlanItem(Greet):
    pass


class RespondToInsult(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_RESPOND_TO_INSULT)


class RespondToInsultPlanItem(RespondToInsult):
    pass


class RespondToThankYou(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_RESPOND_TO_THANK_YOU)


class RespondToThankYouPlanItem(RespondToThankYou):
    pass


class EmitICM(PlanItemWithSemanticContent):
    def __init__(self, icm_move):
        PlanItemWithSemanticContent.__init__(self, TYPE_EMIT_ICM, content=icm_move)

    def is_question_raising_item(self):
        icm = self.content
        return (icm.type_ == ICMMove.UND and not (icm.get_polarity() == ICMMove.POS and not icm.content.is_positive()))

    def is_turn_yielding(self):
        return self.content.type_ == ICMMove.ACC and self.content.get_polarity() == ICMMove.NEG


class EmitIcmPlanItem(EmitICM):
    pass


class EmitIcm(EmitICM):
    pass


class Bind(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, TYPE_BIND, content)

    @property
    def question(self):
        return self.content

    def get_question(self):
        warnings.warn("Bind.get_question() is deprecated. Use Bind.question instead.", DeprecationWarning, stacklevel=2)
        return self.question


class BindPlanItem(Bind):
    pass


class JumpTo(PlanItemWithSemanticContent):
    def __init__(self, content):
        PlanItemWithSemanticContent.__init__(self, TYPE_JUMPTO, content=content)

    @property
    def goal(self):
        return self.content


class JumpToPlanItem(JumpTo):
    pass


class IfThenElse(PlanItem):
    def __init__(self, condition, consequent, alternative):
        self.condition = condition
        self.consequent = consequent
        self.alternative = alternative
        self._check_integrity_of_data()
        PlanItem.__init__(self, TYPE_IF_THEN_ELSE)

    def _check_integrity_of_data(self):
        self._assert_one_alternative_is_non_empty_list()
        self._assert_ontology_integrity()

    def _assert_one_alternative_is_non_empty_list(self):
        assert self.consequent is not [] or self.alternative is not [], \
            "One of consequent (%s) and alternative (%s) must not be []" % (self.consequent, self.alternative)

    def _assert_ontology_integrity(self):
        if self.consequent is not [] or self.alternative is not []:
            items = self.consequent + self.alternative
            ontology_specific_plan_items = [item for item in items if item.is_ontology_specific()]
            if len(ontology_specific_plan_items) > 0:
                ontology_name = ontology_specific_plan_items[0].ontology_name
                for item in ontology_specific_plan_items:
                    assert ontology_name == item.ontology_name, "Expected identical ontologies in all consequents (%s) and alternatives (%s) but got %r and %r (plan item: %r)" % (
                        self.consequent, self.alternative, ontology_name, item.ontology_name, item
                    )

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
        result = "if_then_else{}".format(unicodify((self.condition, self.consequent, self.alternative)))
        return result

    def __repr__(self):
        result = "if_then_else{}".format(unicodify((self.condition, self.consequent, self.alternative)))
        return result

    def __eq__(self, other):
        try:
            equality = (self.condition == other.condition) \
                and (self.consequent == other.consequent) \
                and (self.alternative == other.alternative)
            return equality
        except AttributeError:
            pass
        return False

    def as_dict(self):
        return {
            self.type_: {
                "condition": self.condition,
                "consequent": self.consequent,
                "alternative": self.alternative,
            }
        }


class ForgetAll(PlanItem):
    def __init__(self):
        PlanItem.__init__(self, TYPE_FORGET_ALL)


class ForgetAllPlanItem(ForgetAll):
    pass


class Forget(PlanItemWithSemanticContent):
    def __init__(self, predicate_or_proposition):
        PlanItemWithSemanticContent.__init__(self, TYPE_FORGET, predicate_or_proposition)


class ForgetPlanItem(Forget):
    pass


class ForgetShared(PlanItemWithSemanticContent):
    def __init__(self, predicate_or_proposition):
        PlanItemWithSemanticContent.__init__(self, TYPE_FORGET_SHARED, predicate_or_proposition)


class ForgetSharedPlanItem(ForgetShared):
    pass


class ForgetIssue(PlanItemWithSemanticContent):
    def __init__(self, issue):
        PlanItemWithSemanticContent.__init__(self, TYPE_FORGET_ISSUE, issue)


class ForgetIssuePlanItem(ForgetIssue):
    pass


class MinResultsNotSupportedException(Exception):
    pass


class MaxResultsNotSupportedException(Exception):
    pass


class InvokeQuery(PlanItemWithSemanticContent):
    @property
    def min_results(self):
        return self._min_results

    @property
    def max_results(self):
        return self._max_results

    @property
    def question(self):
        return self._content

    def get_min_results(self):
        warnings.warn(
            "InvokeQuery.get_min_results() is deprecated. Use InvokeQuery.min_results instead.",
            DeprecationWarning,
            stacklevel=2
        )

        return self.min_results

    def get_max_results(self):
        warnings.warn(
            "InvokeQuery.get_max_results() is deprecated. Use InvokeQuery.max_results instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.max_results

    def __str__(self):
        return "invoke_service_query(%s, min_results=%s, max_results=%s)" % (
            str(self._content), self._min_results, self._max_results
        )

    def __repr__(self):
        return "%s(%r, min_results=%r, max_results=%r)" % (
            self.__class__.__name__, self._content, self._min_results, self._max_results
        )

    def __eq__(self, other):
        return super(PlanItemWithSemanticContent, self).__eq__(other) \
            and other.min_results == self.min_results \
            and other.max_results == self.max_results

    def as_dict(self):
        return {
            self.type_: {
                "issue": self._content,
                "min_results": self._min_results,
                "max_results": self._max_results,
            }
        }


class InvokeQueryPlanItem(InvokeQuery):
    pass


class InvokeServiceQuery(InvokeQueryPlanItem):
    def __init__(self, issue, min_results=None, max_results=None):
        min_results = min_results or 0
        if min_results < 0:
            raise MinResultsNotSupportedException("Expected 'min_results' to be 0 or above but got %r." % min_results)
        if max_results is not None and max_results < 1:
            raise MaxResultsNotSupportedException(
                "Expected 'max_results' to be None or above 0 but got %r." % max_results
            )
        PlanItemWithSemanticContent.__init__(self, TYPE_INVOKE_SERVICE_QUERY, issue)
        self._min_results = min_results
        self._max_results = max_results


class InvokeServiceQueryPlanItem(InvokeServiceQuery):
    pass


class InvokeDomainQuery(InvokeQueryPlanItem):
    def __init__(self, issue, min_results=None, max_results=None):
        min_results = min_results or 0
        if min_results < 0:
            raise MinResultsNotSupportedException("Expected 'min_results' to be 0 or above but got %r." % min_results)
        if max_results is not None and max_results < 1:
            raise MaxResultsNotSupportedException(
                "Expected 'max_results' to be None or above 0 but got %r." % max_results
            )
        PlanItemWithSemanticContent.__init__(self, TYPE_INVOKE_DOMAIN_QUERY, issue)
        self._min_results = min_results
        self._max_results = max_results


class InvokeDomainQueryPlanItem(InvokeDomainQuery):
    pass


class InvokeServiceAction(PlanItem, OntologySpecificSemanticObject):
    INTERROGATIVE = "INTERROGATIVE"
    ASSERTIVE = "ASSERTIVE"

    def __init__(self, ontology_name, service_action, preconfirm=None, postconfirm=False, downdate_plan=True):
        self.service_action = service_action
        self.preconfirm = preconfirm
        self.postconfirm = postconfirm
        self._downdate_plan = downdate_plan
        PlanItem.__init__(self, TYPE_INVOKE_SERVICE_ACTION)
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
        return super(InvokeServiceAction, self).__eq__(other) and other.get_service_action() == self.get_service_action(
        ) and other.has_interrogative_preconfirmation() == self.has_interrogative_preconfirmation(
        ) and other.has_assertive_preconfirmation() == self.has_assertive_preconfirmation(
        ) and other.has_postconfirmation() == self.has_postconfirmation() and other.should_downdate_plan(
        ) == self.should_downdate_plan()

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
            self.type_: {
                "service_action": self.service_action,
                "ontology": self.ontology_name,
                "preconfirm": self.preconfirm,
                "postconfirm": self.postconfirm,
                "downdate_plan": self._downdate_plan,
            }
        }


class InvokeServiceActionPlanItem(InvokeServiceAction):
    pass


class ServiceReport(PlanItemWithSemanticContent):
    def __init__(self, result_proposition):
        PlanItemWithSemanticContent.__init__(self, TYPE_SERVICE_REPORT, result_proposition)

    def is_turn_yielding(self):
        return self._content.type_ == Proposition.SERVICE_RESULT


class ServiceReportPlanItem(ServiceReport):
    pass


class ActionReport(PlanItemWithSemanticContent):
    def __init__(self, result_proposition):
        PlanItemWithSemanticContent.__init__(self, TYPE_ACTION_REPORT, result_proposition)

    def is_turn_yielding(self):
        return self._content.type_ in [Proposition.SERVICE_RESULT, Proposition.ACTION_STATUS]


class ActionReportPlanItem(ActionReport):
    pass


class QuestionReport(PlanItemWithSemanticContent):
    def __init__(self, result_proposition):
        PlanItemWithSemanticContent.__init__(self, TYPE_QUESTION_REPORT, result_proposition)

    def is_turn_yielding(self):
        return self._content.type_ == Proposition.QUESTION_STATUS


class QuestionReportPlanItem(QuestionReport):
    pass


class EmitMove(PlanItemWithSemanticContent):
    def __init__(self, move):
        PlanItemWithSemanticContent.__init__(self, TYPE_EMIT_MOVE, move)


class EmitMovePlanItem(EmitMove):
    pass


class Handle(PlanItem, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action):
        PlanItem.__init__(self, TYPE_HANDLE)
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self._service_action = service_action

    @property
    def service_action(self):
        return self._service_action

    def __str__(self):
        return "invoke_service_action(%s)" % (str(self.service_action))

    def as_dict(self):
        return {
            self.type_: {
                "service_action": self._service_action,
                "ontology": self.ontology_name,
            }
        }


class HandlePlanItem(Handle):
    pass


class UnexpectedLogLevelException(Exception):
    pass


class Log(PlanItem):
    LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]

    def __init__(self, message, log_level="debug"):
        if log_level not in self.LOG_LEVELS:
            raise UnexpectedLogLevelException(
                f"Log plan item creation attempted with log level '{log_level}'. Expected one of '{self.LOG_LEVELS}'"
            )

        PlanItem.__init__(self, TYPE_LOG)
        self._message = message
        self._level = log_level

    @property
    def message(self):
        return self._message

    @property
    def level(self):
        return self._level

    def __str__(self):
        return f"log_plan_item('{self._level}', '{self.message}')"

    def __repr__(self):
        return str(self)

    def as_dict(self):
        return {self.type_: {"message": self.message, "level": self.level}}


class LogPlanItem(Log):
    pass


class GetDone(PlanItemWithSemanticContent):
    def __init__(self, action, step=None):
        PlanItemWithSemanticContent.__init__(self, TYPE_GET_DONE, action)
        self._step = step

    @property
    def step(self):
        return self._step

    @property
    def action(self):
        return self.content

    def as_dict(self):
        return {"step": self._step} | super().as_dict()


class GetDonePlanItem(GetDone):
    pass


class GoalPerformed(PlanItem):
    def __init__(self, postconfirm):
        PlanItem.__init__(self, TYPE_ACTION_PERFORMED)
        self._postconfirm = postconfirm

    @property
    def postconfirm(self):
        return self._postconfirm

    def as_dict(self):
        return {self.type_: self._postconfirm}


class GoalPerformedPlanItem(GoalPerformed):
    pass


class GoalAborted(PlanItem):
    def __init__(self, reason):
        PlanItem.__init__(self, TYPE_ACTION_ABORTED)
        self._reason = reason

    @property
    def reason(self):
        return self._reason

    def __str__(self):
        return f"signal_action_failure('{self.reason}')"

    def __repr__(self):
        return f"GoalAbortedPlanItem('{self.reason}')"

    def as_dict(self):
        return {self.type_: self._reason}


class GoalAbortedPlanItem(GoalAborted):
    pass


class EndTurn(PlanItem):
    def __init__(self, timeout):
        PlanItem.__init__(self, TYPE_END_TURN)
        self._timeout = timeout

    @property
    def timeout(self):
        return self._timeout

    def __str__(self):
        return f"end_turn('{self.timeout}')"

    def __repr__(self):
        return f"EndTurnPlanItem('{self.timeout}')"

    def as_dict(self):
        return {self.type_: self._timeout}


class EndTurnPlanItem(EndTurn):
    pass


class ResetDomainQuery(PlanItem):
    def __init__(self, query):
        PlanItem.__init__(self, TYPE_RESET_DOMAIN_QUERY)
        self._query = query

    @property
    def query(self):
        return self._query

    def __str__(self):
        return f"reset_domain_query('{self.query}')"

    def __repr__(self):
        return f"ResetDomainQueryPlanItem('{self.query}')"

    def as_dict(self):
        return {self.type_: self._query}


class ResetDomainQueryPlanItem(ResetDomainQuery):
    pass


class Iterate(PlanItemWithContent):
    def __init__(self, iterator):
        PlanItemWithContent.__init__(self, TYPE_ITERATE, iterator)

    @property
    def iterator(self):
        return self._content

    def __str__(self):
        return f"iterate('{self.iterator}')"

    def __repr__(self):
        return f"IteratePlanItem('{self.iterator}')"


class IteratePlanItem(Iterate):
    pass


class ChangeDDD(PlanItem):
    def __init__(self, ddd):
        PlanItem.__init__(self, TYPE_CHANGE_DDD)
        self._ddd = ddd

    @property
    def ddd(self):
        return self._ddd

    def __str__(self):
        return f"change_ddd('{self.ddd}')"

    def __repr__(self):
        return f"ChangeDDD('{self.ddd}')"

    def as_dict(self):
        return {self.type_: self._ddd}


class ChangeDDDPlanItem(ChangeDDD):
    pass


class QuestionRaisingPlanItem(PlanItemWithSemanticContent):
    SOURCE_SERVICE = "service"
    SOURCE_DOMAIN = "domain"
    ALPHABETIC = "alphabetic"

    def __init__(self, domain_name, type, content, allow_pcom_answer=False):
        if not content.is_question():
            raise DomainError("cannot create QuestionRaisingPlanItem " + "from non-question %s" % content)
        self._domain_name = domain_name
        self._allow_answer_from_pcom = allow_pcom_answer
        PlanItemWithSemanticContent.__init__(self, type, content)

    @property
    def domain_name(self):
        return self._domain_name

    @property
    def allow_answer_from_pcom(self):
        return self._allow_answer_from_pcom

    def is_question_raising_item(self):
        return True

    def get_question(self):
        warnings.warn(
            "QuestionRaisingPlanItem.get_question() is deprecated. Use QuestionRaisingPlanItem.question instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.question

    @property
    def question(self):
        return self.content

    def clone_as_type(self, type_):
        clone = copy.deepcopy(self)
        clone._type = type_
        return clone

    def __str__(self):
        if self._content is None:
            content_string = ""
        else:
            content_string = str(self._content)
        return "%s(%s)" % (str(self._type), content_string)

    def as_dict(self):
        return {
            self.type_: self._content,
            "domain_name": self._domain_name,
            "allow_answer_from_pcom": self._allow_answer_from_pcom
        }


class Findout(QuestionRaisingPlanItem):
    def __init__(self, domain_name, content, allow_answer_from_pcom=False):
        QuestionRaisingPlanItem.__init__(self, domain_name, TYPE_FINDOUT, content, allow_answer_from_pcom)


class FindoutPlanItem(Findout):
    pass


class Raise(QuestionRaisingPlanItem):
    def __init__(self, domain_name, content):
        QuestionRaisingPlanItem.__init__(self, domain_name, TYPE_RAISE, content)


class RaisePlanItem(Raise):
    pass


class UnexpectedDomainException(Exception):
    pass


class QuestionRaisingPlanItemOfDomain(object):
    def __init__(self, domain, plan_item):
        if domain.name != plan_item.domain_name:
            raise UnexpectedDomainException(
                "Expected domain '%s' to match domain of plan item %s but it was '%s'" %
                (plan_item.domain_name, plan_item, domain)
            )
        self._domain = domain
        self._plan_item = plan_item

    def get_alternatives(self):
        return self._domain.get_alternatives(self._plan_item.question)

    def get_incremental(self):
        return self._domain.get_incremental(self._plan_item.question)

    def get_source(self):
        return self._domain.get_source(self._plan_item.question)

    def get_format(self):
        return self._domain.get_format(self._plan_item.question)

    def get_service_query(self):
        return self._domain.get_service_query(self._plan_item.question)

    def get_label_questions(self):
        return self._domain.get_label_questions(self._plan_item.question)

    def has_parameters(self):
        return self.get_alternatives() \
            or self.get_incremental() \
            or self.get_source() \
            or self.get_format() \
            or self.get_service_query() \
            or self.get_label_questions()
