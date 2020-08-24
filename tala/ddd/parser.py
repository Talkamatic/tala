import copy
import re

from tala.ddd.utils import CacheMethod
from tala.model.action_status import Done
from tala.model.goal import HandleGoal, PerformGoal, ResolveGoal
from tala.model.individual import Yes, No
from tala.model.lambda_abstraction import LambdaAbstractedGoalProposition
from tala.model.speaker import Speaker
from tala.model.set import Set
from tala.model.move import ICMMove, IssueICMMove, ICMMoveWithSemanticContent, ReportMove, PrereportMove, GreetMove, QuitMove, MuteMove, UnmuteMove, AskMove, RequestMove, AnswerMove, ICMMoveWithStringContent
from tala.model.ontology import OntologyError
from tala.model.plan_item import AssumePlanItem, AssumeSharedPlanItem, AssumeIssuePlanItem, RespondPlanItem, DoPlanItem, BindPlanItem, ConsultDBPlanItem, JumpToPlanItem, IfThenElse, ForgetAllPlanItem, ForgetPlanItem, ForgetIssuePlanItem, InvokeServiceQueryPlanItem, InvokeServiceActionPlanItem, LogPlanItem
from tala.model.polarity import Polarity
from tala.model.proposition import GoalProposition, PropositionSet, ServiceActionStartedProposition, ServiceActionTerminatedProposition, ServiceResultProposition, ResolvednessProposition, PreconfirmationProposition, UnderstandingProposition, RejectedPropositions, PrereportProposition, PredicateProposition, KnowledgePreconditionProposition
from tala.model.question import AltQuestion, YesNoQuestion, WhQuestion, KnowledgePreconditionQuestion
from tala.model.question_raising_plan_item import QuestionRaisingPlanItem, FindoutPlanItem, RaisePlanItem
from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction
from tala.model.person_name import PersonName
from tala.model.date_time import DateTime


class ParseError(Exception):
    pass


class ParseFailure(Exception):
    pass


class Parser:
    def __init__(self, ddd_name, ontology, domain_name=None):
        self._ddd_name = ddd_name
        self.ontology = ontology
        self.ontology_name = ontology.get_name()
        self.domain_name = domain_name
        self._cache_method = CacheMethod(self, self._cacheable_parse)
        self._clauses = [
            self._parse_set,
            self._parse_decorated_non_icm_move,
            self._parse_non_icm_move,
            self._parse_findout_plan_item,
            self._parse_do_plan_item,
            self._parse_raise_plan_item,
            self._parse_bind_plan_item,
            self._parse_respond_plan_item,
            self._parse_consultDB_plan_item,
            self._parse_if_then_else_plan_item,
            self._parse_jumpto_plan_item,
            self._parse_forget_all_plan_item,
            self._parse_forget_plan_item,
            self._parse_assume_plan_item,
            self._parse_assume_shared_plan_item,
            self._parse_goal,
            self._parse_assume_issue_item,
            self._parse_log_item,
            self._parse_forget_issue_plan_item,
            self._parse_invoke_service_query_plan_item,
            self._parse_deprecated_dev_query_plan_item,
            self._parse_invoke_service_action_plan_item,
            self._parse_deprecated_dev_perform_plan_item,
            self._parse_question,
            self._parse_lambda_abstracted_goal_proposition,
            self._parse_lambda_abstracted_predicate_proposition,
            self._parse_service_result_proposition,
            self._parse_successful_service_action,
            self._parse_failed_service_action,
            self._parse_action_status,
            self._parse_decorated_icm_move,
            self._parse_icm_move,
            self._parse_proposition,
            self._parse_negative_individual,
            self._parse_yes_or_no,
            self._parse_prop_set,
            self._parse_action,
            self._parse_individual,
            self._parse_predicate,
            self._parse_string,
        ]

    def clear(self):
        self._cache_method.clear()

    def parse(self, string):
        object = self._cacheable_parse(string)
        new_instance = copy.deepcopy(object)
        return new_instance

    def _cacheable_parse(self, string):
        try:
            return self._parse(string)
        except OntologyError as exception:
            raise ParseError("failed to parse '%s': %s" % (string, exception))

    def parse_parameters(self, string):
        params = {}
        string = self._strip_curly_brackets(string)
        while self._more_data_to_read(string):
            (key, value, rest) = self._get_next_question_param(string)
            params[key] = value
            string = rest
        return params

    def _parse(self, string):
        for parse_method in self._clauses:
            try:
                return parse_method(string)
            except ParseFailure:
                pass
        raise ParseError("failed to parse '" + string + "' (ontology=" + str(self.ontology) + ")")

    def _parse_incrementally(self, string):
        for n in range(1, len(string) + 1):
            try:
                result = self._parse(string[0:n])
                if result:
                    return result, string[n:]
            except ParseError:
                pass

    def _parse_goal(self, string):
        try:
            return self._parse_resolve_goal(string)
        except ParseFailure:
            pass
        try:
            return self._parse_resolve_user_goal(string)
        except ParseFailure:
            pass
        try:
            return self._parse_perform_goal(string)
        except ParseFailure:
            pass
        try:
            return self._parse_handle_goal(string)
        except ParseFailure:
            pass
        raise ParseFailure()

    def _parse_decorated_non_icm_move(self, string):
        m = re.search(r'^Move\((.*)\)$', string)
        if m:
            move_and_maybe_realization_data_string = m.group(1)
            move, rest = self._parse_incrementally(move_and_maybe_realization_data_string)
            if rest:
                m = re.search(r'^, (.*)$', rest)
                if m:
                    realization_data_string = m.group(1)
                    realization_data = self._parse_realization_data(realization_data_string)
                    move.set_realization_data(**realization_data)
            return move
        else:
            raise ParseFailure()

    def _parse_non_icm_move(self, string):
        try:
            return self._parse_basic_move(string)
        except ParseFailure:
            pass
        try:
            return self._parse_request_move(string)
        except ParseFailure:
            pass
        try:
            return self._parse_ask_move(string)
        except ParseFailure:
            pass
        try:
            return self._parse_answer_move(string)
        except ParseFailure:
            pass
        try:
            return self._parse_report_move(string)
        except ParseFailure:
            pass
        try:
            return self._parse_prereport_move(string)
        except ParseFailure:
            pass
        raise ParseFailure()

    def _parse_basic_move(self, string):
        matcher = re.search(r'^(greet|mute|unmute|quit)$', string)
        if matcher:
            move_type_string = matcher.group(1)
            if move_type_string == "greet":
                return GreetMove()
            elif move_type_string == "mute":
                return MuteMove()
            elif move_type_string == "unmute":
                return UnmuteMove()
            elif move_type_string == "quit":
                return QuitMove()

        raise ParseFailure()

    def _parse_set(self, string):
        m = re.search(r'^\{(.*)\}$', string)
        if m:
            if m.group(1) == "":
                return Set()
            else:
                content_as_strings = m.group(1).split(", ")
                s = Set()
                for content_as_string in content_as_strings:
                    s.add(self.parse(content_as_string))
                return s
        else:
            raise ParseFailure()

    def _parse_string(self, string):
        m = re.search(r'^(["\'])(?P<string>[^\1]*)\1$', string)
        if m:
            return m.group("string")
        else:
            raise ParseFailure()

    def _parse_proposition(self, string):
        try:
            return self._parse_deprecated_service_action_terminated_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_deprecated_service_action_started_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_preconfirmation_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_prereport_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_goal_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_rejected_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_predicate_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_understanding_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_resolvedness_proposition(string)
        except ParseFailure:
            pass
        try:
            return self._parse_knowledge_precondition_proposition(string)
        except ParseFailure:
            pass
        self._check_if_deprecated_action_proposition(string)
        self._check_if_deprecated_issue_proposition(string)
        raise ParseFailure()

    def _check_if_deprecated_action_proposition(self, string):
        m = re.search(r'^action\((\w+)\)$', string)
        if m:
            action_name = m.group(1)
            raise ParseError(
                "'action(%s)' is not a valid proposition. Perhaps you mean 'goal(perform(%s))'." %
                (action_name, action_name)
            )

    def _check_if_deprecated_issue_proposition(self, string):
        m = re.search(r'^issue\((.+)\)$', string)
        if m:
            issue_name = m.group(1)
            raise ParseError(
                "'issue(%s)' is not a valid proposition. Perhaps you mean 'goal(resolve(%s))'." %
                (issue_name, issue_name)
            )

    def _parse_preconfirmation_proposition(self, string):
        m = re.search(r'^(~?)preconfirmed\((?P<action>\w+), (\[[^\]]*\])\)$', string)
        if m:
            (polarity_str, action_value, parameter_string) = (m.group(1), m.group("action"), m.group(3))
            polarity = self._parse_polarity(polarity_str)
            parameter_list = self._parse_proposition_list(parameter_string)
            return PreconfirmationProposition(self.ontology_name, action_value, parameter_list, polarity)
        raise ParseFailure()

    def _parse_prereport_proposition(self, string):
        m = re.search(r'^prereported\((?P<action>\w+), (\[[^\]]*\])\)$', string)
        if m:
            (action_value, parameter_string) = (m.group("action"), m.group(2))
            parameter_list = self._parse_proposition_list(parameter_string)
            return PrereportProposition(self.ontology_name, action_value, parameter_list)
        raise ParseFailure()

    def _parse_report_move(self, string):
        m = re.search(r'^report\((.*)\)$', string)
        if m:
            content_string = m.group(1)
            content = self._parse(content_string)
            return ReportMove(content)
        raise ParseFailure()

    def _parse_service_result_proposition(self, string):
        m = re.search(r'^ServiceResultProposition\((\w+), (\[[^\]]*\]), (.+)\)$', string)
        if m:
            (action_value, parameter_string, action_outcome_string) = m.groups()
            parameter_list = self._parse_proposition_list(parameter_string)
            action_outcome = self._parse(action_outcome_string)
            return ServiceResultProposition(self.ontology_name, action_value, parameter_list, action_outcome)
        raise ParseFailure()

    def _parse_successful_service_action(self, string):
        if string == "SuccessfulServiceAction()":
            return SuccessfulServiceAction()
        raise ParseFailure()

    def _parse_failed_service_action(self, string):
        m = re.search(r'^FailedServiceAction\((\w+)\)$', string)
        if m:
            (failure_reason, ) = m.groups()
            return FailedServiceAction(failure_reason)
        raise ParseFailure()

    def _parse_action_status(self, string):
        if string == "done":
            return Done()
        raise ParseFailure()

    def _parse_prereport_move(self, string):
        m = re.search(r'^prereport\((\w+), (\[[^\]]*\])\)$', string)
        if m:
            (action_value, arguments_string) = m.groups()
            arguments_list = self._parse_proposition_list(arguments_string)
            return PrereportMove(self.ontology_name, action_value, arguments_list)
        raise ParseFailure()

    def _parse_ask_move(self, string):
        m = re.search(r'^ask\((.+)\)', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return AskMove(question)
        else:
            raise ParseFailure()

    def _parse_question(self, string):
        m = re.search(r'^\?(.*)$', string)
        if m:
            question_content_string = m.group(1)
            question_content = self.parse(question_content_string)

            try:
                if question_content.is_knowledge_precondition_proposition():
                    return KnowledgePreconditionQuestion(question_content.embedded_question)
            except AttributeError:
                pass
            try:
                if question_content.is_lambda_abstracted_predicate_proposition():
                    return WhQuestion(question_content)
            except AttributeError:
                pass
            try:
                if question_content.is_lambda_abstracted_goal_proposition():
                    return WhQuestion(question_content)
            except AttributeError:
                pass
            try:
                if question_content.is_proposition_set():
                    return AltQuestion(question_content)
            except AttributeError:
                pass
            try:
                if question_content.is_proposition():
                    return YesNoQuestion(question_content)
            except AttributeError:
                pass
            if question_content.is_predicate():
                predicate = question_content
                if predicate.getSort().is_boolean_sort():
                    return YesNoQuestion(PredicateProposition(predicate))
        raise ParseFailure()

    def _parse_list_of_questions(self, string):
        string_without_brackets = self._strip_brackets(string)
        question_strings = [str.strip() for str in string_without_brackets.split(",")]
        return [self._parse_question(question_string) for question_string in question_strings]

    def _parse_lambda_abstracted_goal_proposition(self, string):
        if string == "X.goal(X)":
            return LambdaAbstractedGoalProposition()
        else:
            raise ParseFailure()

    def _parse_lambda_abstracted_predicate_proposition(self, string):
        m = re.search(r'^X\.(.+)\(X\)$', string)
        if m:
            predicate_name = m.group(1)
            if predicate_name == "action":
                raise ParseError("'?X.action(X)' is not a valid question. Perhaps you mean '?X.goal(X)'.")
            predicate = self.ontology.get_predicate(predicate_name)
            return self.ontology.create_lambda_abstracted_predicate_proposition(predicate)
        else:
            raise ParseFailure()

    def _parse_answer_move(self, string):
        m = re.search(r'^answer\((.+)\)', string)
        if m:
            answer_string = m.group(1)
            answer = self.parse(answer_string)
            answer_move = AnswerMove(answer)
            return answer_move
        else:
            raise ParseFailure()

    def _parse_decorated_icm_move(self, string):
        m = re.search(r'^ICMMove\(([^,]+)((, *)(.+))?\)$', string)
        if m:
            icm_string = m.group(1)
            realization_data_string = m.group(4)
            icm = self._parse_icm_move(icm_string)
            if realization_data_string:
                realization_data = self._parse_realization_data(realization_data_string)
                icm.set_realization_data(**realization_data)
            return icm
        else:
            raise ParseFailure()

    def _parse_realization_data(self, string):
        realization_data = dict()
        while self._more_data_to_read(string):
            (key, value, rest) = self._get_next_realization_data(string)
            realization_data[key] = value
            string = rest

        return realization_data

    def _get_next_realization_data(self, string):
        m = re.search(r'^(?P<key>[^=]+)=(?P<value>[^=]+) *\, *(?P<rest>[^=]+=.*)$', string)
        if m:
            rest = m.group('rest')
        else:
            m = re.search(r'^(?P<key>[^=]+)=(?P<value>.+)$', string)
            rest = ""
        if m:
            key = m.group('key')
            value_as_string = m.group('value')
            if key == "speaker":
                value = value_as_string
            elif key == "perception_confidence":
                value = float(value_as_string)
            elif key == "understanding_confidence":
                value = float(value_as_string)
            elif key == "utterance" or key == "ddd_name":
                value = self._strip_quotes(value_as_string)
            else:
                raise ParseFailure("unsupported realization attribute '%s'" % key)
            return (key, value, rest)
        else:
            raise ParseFailure()

    def _strip_quotes(self, string):
        m = re.search(r'^"([^"]*)"$', string)
        if m:
            return m.group(1)
        else:
            m = re.search("^'([^']*)'$", string)
            if m:
                return m.group(1)
            else:
                raise ParseFailure()

    def _parse_icm_move(self, string):
        m = re.search(r'^icm:', string)
        if m:
            try:
                return self._parse_reraise_or_accommodate_or_resume_icm(string)
            except ParseFailure:
                pass
            try:
                return self._parse_loadplan_icm(string)
            except ParseFailure:
                pass
            try:
                return self._parse_perception_or_acceptance_icm(string)
            except ParseFailure:
                pass
            try:
                return self._parse_understanding_icm(string)
            except ParseFailure:
                pass
        raise ParseFailure()

    def _parse_reraise_or_accommodate_or_resume_icm(self, string):
        matcher = re.search(
            '^icm:(%s|%s|%s)(:([^:]+))?$' % (ICMMove.RERAISE, ICMMove.ACCOMMODATE, ICMMove.RESUME), string
        )
        if matcher:
            (icm_type, content_string) = (matcher.group(1), matcher.group(3))
            if content_string:
                content = self.parse(content_string)
                return ICMMoveWithSemanticContent(icm_type, content)
            return ICMMove(icm_type)
        else:
            raise ParseFailure()

    def _parse_loadplan_icm(self, string):
        matcher = re.search(r'^icm:loadplan', string)
        if matcher:
            return ICMMove(ICMMove.LOADPLAN)
        else:
            raise ParseFailure()

    def _parse_perception_or_acceptance_icm(self, string):
        try:
            return self._parse_contentless_perception_or_acceptance_icm(string)
        except ParseFailure:
            pass
        try:
            return self._parse_contentful_perception_icm(string)
        except ParseFailure:
            pass
        try:
            return self._parse_contentful_acceptance_icm(string)
        except ParseFailure:
            pass
        raise ParseFailure()

    def _parse_contentless_perception_or_acceptance_icm(self, string):
        m = re.search(r'^icm:(per|acc)\*(pos|neg|int)$', string)
        if m:
            icm_type = m.group(1)
            polarity = m.group(2)
            return ICMMove(icm_type, polarity=polarity)
        raise ParseFailure()

    def _parse_contentful_perception_icm(self, string):
        m = re.search(r'^icm:per\*(pos|neg|int):"([^"]*)"$', string)
        if m:
            (polarity, content_string) = m.groups()
            return ICMMoveWithStringContent(ICMMove.PER, content_string, polarity=polarity)
        raise ParseFailure()

    def _parse_contentful_acceptance_icm(self, string):
        m = re.search(r'^icm:(per|acc)\*(pos|neg|int)(:([^:]*))?$', string)
        if m:
            (icm_type, polarity, junk, content_string) = m.groups()
            if content_string == "issue":
                return IssueICMMove(icm_type, polarity=polarity)
            else:
                content = self.parse(content_string)
            return ICMMoveWithSemanticContent(type=icm_type, content=content, polarity=polarity)
        raise ParseFailure()

    def _parse_understanding_icm(self, string):
        m = re.search(r'^icm:(sem|und)\*(int|pos|neg)(:((.+)\*)?([^:]+))?$', string)
        if m:
            (type, polarity, foo, foo, content_speaker, content_string) = m.groups()
            if content_string:
                content = self.parse(content_string)
            else:
                content = None
            return ICMMoveWithSemanticContent(type, content, content_speaker=content_speaker, polarity=polarity)
        else:
            raise ParseFailure()

    def _parse_resolvedness_proposition(self, string):
        m = re.search(r'^resolved\((.+)\)$', string)
        if m:
            issue_string = m.group(1)
            issue = self.parse(issue_string)
            return ResolvednessProposition(issue)
        else:
            raise ParseFailure()

    def _parse_knowledge_precondition_proposition(self, string):
        m = re.search(r'^(~?)know_answer\((.+)\)$', string)
        if m:
            polarity_string, issue_string = m.group(1), m.group(2)
            issue = self.parse(issue_string)
            polarity = self._parse_polarity(polarity_string)
            return KnowledgePreconditionProposition(issue, polarity)
        else:
            raise ParseFailure()

    def _parse_request_move(self, string):
        matcher = re.search(r'^request\(([^\{\}]+)\)(.*)', string)
        if matcher:
            action_string = matcher.group(1)
            action = self.parse(action_string)
            return RequestMove(action)
        else:
            raise ParseFailure()

    def _parse_findout_plan_item(self, string):
        m = re.search(r'^findout\((.*)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return FindoutPlanItem(self.domain_name, question)
        else:
            raise ParseFailure()

    def _parse_do_plan_item(self, string):
        m = re.search(r'^do\((\w+)\)$', string)
        if m:
            action_string = m.group(1)
            action = self.parse(action_string)
            return DoPlanItem(action)
        else:
            raise ParseFailure()

    def _parse_bind_plan_item(self, string):
        m = re.search(r'^bind\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return BindPlanItem(question)
        else:
            raise ParseFailure()

    def _parse_forget_all_plan_item(self, string):
        if string == "forget_all":
            return ForgetAllPlanItem()
        else:
            raise ParseFailure()

    def _parse_forget_plan_item(self, string):
        m = re.search(r'^forget\((.+)\)$', string)
        if m:
            proposition_string = m.group(1)
            proposition = self.parse(proposition_string)
            return ForgetPlanItem(proposition)
        else:
            raise ParseFailure()

    def _parse_assume_plan_item(self, string):
        m = re.search(r'^assume\((.+)\)$', string)
        if m:
            proposition_string = m.group(1)
            proposition = self._parse_proposition(proposition_string)
            return AssumePlanItem(proposition)
        else:
            raise ParseFailure()

    def _parse_assume_shared_plan_item(self, string):
        m = re.search(r'^assume_shared\((.+)\)$', string)
        if m:
            proposition_string = m.group(1)
            proposition = self._parse_proposition(proposition_string)
            return AssumeSharedPlanItem(proposition)
        else:
            raise ParseFailure()

    def _parse_assume_issue_item(self, string):
        m = re.search(r'^assume_issue\((.+)\)$', string)
        if m:
            issue_string = m.group(1)
            issue = self.parse(issue_string)
            return AssumeIssuePlanItem(issue)
        else:
            raise ParseFailure()

    def _parse_log_item(self, string):
        m = re.search(r'^log\("(.+)"\)$', string)
        if m:
            log_message = m.group(1)
            return LogPlanItem(log_message)
        else:
            raise ParseFailure()

    def _parse_forget_issue_plan_item(self, string):
        m = re.search(r'^forget_issue\((.+)\)$', string)
        if m:
            issue_string = m.group(1)
            issue = self.parse(issue_string)
            return ForgetIssuePlanItem(issue)
        else:
            raise ParseFailure()

    def _parse_invoke_service_query_plan_item(self, string):
        m = re.search(r'^invoke_service_query\(([^,]+)\)$', string)
        if m:
            (issue_string, ) = m.groups()
            issue = self.parse(issue_string)
            return InvokeServiceQueryPlanItem(issue, min_results=1, max_results=1)
        else:
            raise ParseFailure()

    def _parse_deprecated_dev_query_plan_item(self, string):
        m = re.search(r'^dev_query\(([^,]+)\)$', string)
        if m:
            (issue_string, ) = m.groups()
            issue = self.parse(issue_string)
            return InvokeServiceQueryPlanItem(issue, min_results=1, max_results=1)
        else:
            raise ParseFailure()

    def _parse_invoke_service_action_plan_item(self, string):
        m = re.search(r'^invoke_service_action\(([^,]+), *(\{.*\})\)$', string)
        if m:
            (service_action, params_string) = m.groups()
            params = self._parse_invoke_service_action_params(params_string)
            return InvokeServiceActionPlanItem(self.ontology.name, service_action, **params)
        else:
            raise ParseFailure()

    def _parse_deprecated_dev_perform_plan_item(self, string):
        m = re.search(r'^dev_perform\(([^,]+), *(\{.*\})\)$', string)
        if m:
            (service_action, params_string) = m.groups()
            params = self._parse_invoke_service_action_params(params_string)
            return InvokeServiceActionPlanItem(self.ontology.name, service_action, **params)
        else:
            raise ParseFailure()

    def _parse_raise_plan_item(self, string):
        m = re.search(r'^raise\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return RaisePlanItem(self.domain_name, question)
        else:
            raise ParseFailure()

    def _parse_respond_plan_item(self, string):
        m = re.search(r'^respond\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return RespondPlanItem(question)
        else:
            raise ParseFailure()

    def _parse_resolve_goal(self, string):
        m = re.search(r'^resolve\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return ResolveGoal(question, Speaker.SYS)
        else:
            raise ParseFailure()

    def _parse_resolve_user_goal(self, string):
        m = re.search(r'^resolve_user\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return ResolveGoal(question, Speaker.USR)
        else:
            raise ParseFailure()

    def _parse_perform_goal(self, string):
        m = re.search(r'^perform\((.+)\)$', string)
        if m:
            action_string = m.group(1)
            action = self._parse_action(action_string)
            return PerformGoal(action)
        else:
            raise ParseFailure()

    def _parse_handle_goal(self, string):
        m = re.search(r'^handle\((.+)\)$', string)
        if m:
            service_action = m.group(1)
            return HandleGoal(self.ontology_name, service_action)
        else:
            raise ParseFailure()

    def _parse_consultDB_plan_item(self, string):
        m = re.search(r'^consultDB\((.+)\)$', string)
        if m:
            question_string = m.group(1)
            question = self._parse_question(question_string)
            return ConsultDBPlanItem(question)
        else:
            raise ParseFailure()

    def _parse_if_then_else_plan_item(self, string):
        m = re.search(r'^if (.+) then (.*) else (.*)$', string)
        if m:
            (condition_string, consequent_string, alternative_string) = m.groups()
            condition = self._parse_proposition(condition_string)
            if consequent_string != "":
                consequent = self.parse(consequent_string)
            else:
                consequent = None
            if alternative_string != "":
                alternative = self.parse(alternative_string)
            else:
                alternative = None
            return IfThenElse(condition, consequent, alternative)
        else:
            raise ParseFailure()

    def _parse_jumpto_plan_item(self, string):
        m = re.search(r'^jumpto\((.+)\)$', string)
        if m:
            goal_string = m.group(1)
            goal = self._parse_goal(goal_string)
            return JumpToPlanItem(goal)
        else:
            raise ParseFailure()

    def _parse_goal_proposition(self, string):
        m = re.search(r'^(~?)goal\((.+)\)$', string)
        if m:
            (polarity_str, goal_string) = (m.group(1), m.group(2))
            polarity = self._parse_polarity(polarity_str)
            goal = self._parse_goal(goal_string)
            return GoalProposition(goal, polarity)
        raise ParseFailure()

    def _parse_rejected_proposition(self, string):
        m = re.search(r'^rejected\(([^,]+)(, *(.+))?\)$', string)
        if m:
            (content_string, dummy, reason_string) = m.groups()
            rejected = self.parse(content_string)
            return RejectedPropositions(rejected, reason=reason_string)
        raise ParseFailure()

    def _parse_deprecated_service_action_terminated_proposition(self, string):
        m = re.search(r'^service_action_terminated\((.+)\)$', string)
        if m:
            service_action = m.group(1)
            return ServiceActionTerminatedProposition(self.ontology_name, service_action)
        raise ParseFailure()

    def _parse_deprecated_service_action_started_proposition(self, string):
        m = re.search(r'^service_action_started\((.+)\)$', string)
        if m:
            service_action = m.group(1)
            return ServiceActionStartedProposition(self.ontology_name, service_action)
        raise ParseFailure()

    def _parse_predicate_proposition(self, string):
        m = re.search(r'^(~?)(\w+)(\((.*)\))$', string)
        if m:
            (polarity_str, predicate_name, individual_string) = (m.group(1), m.group(2), m.group(4))

            if self.ontology.has_predicate(predicate_name):
                predicate = self.ontology.get_predicate(predicate_name)
                if individual_string is None or individual_string == "":
                    if not predicate.getSort().is_boolean_sort():
                        raise ParseFailure()
                    individual = None
                else:
                    individual = self._parse_individual(individual_string)
                polarity = self._parse_polarity(polarity_str)
                return PredicateProposition(predicate, individual, polarity)
        raise ParseFailure()

    def _parse_negative_individual(self, string):
        m = re.search(r'^~(\w+)$', string)
        if m:
            individual_value = m.group(1)
            return self.ontology.create_negative_individual(individual_value)
        raise ParseFailure()

    def _parse_individual(self, string):
        try:
            return self._parse_real_individual(string)
        except ParseFailure:
            pass
        try:
            return self._parse_integer_individual(string)
        except ParseFailure:
            pass
        try:
            return self._parse_string_individual(string)
        except ParseFailure:
            pass
        try:
            return self._parse_individual_of_enumerated_sort(string)
        except ParseFailure:
            pass
        try:
            return self._parse_individual_of_person_name_sort(string)
        except ParseFailure:
            pass
        try:
            return self._parse_individual_of_datetime_sort(string)
        except ParseFailure:
            pass
        raise ParseFailure()

    def _parse_individual_of_enumerated_sort(self, string):
        m = re.search(r'^(.+)$', string)
        if m:
            individual_value = m.group(1)
            try:
                sort = self.ontology.individual_sort(individual_value)
            except OntologyError:
                raise ParseFailure()
            if not sort.is_string_sort() and not sort.is_real_sort():
                return self.ontology.create_individual(individual_value)
        raise ParseFailure()

    def _parse_real_individual(self, string):
        m = re.search(r'^[0-9]*\.[0-9]+$', string)
        if m:
            individual_value = float(string)
            return self.ontology.create_individual(individual_value)
        else:
            raise ParseFailure()

    def _parse_integer_individual(self, string):
        m = re.search(r'^[0-9]+$', string)
        if m:
            individual_value = int(string)
            return self.ontology.create_individual(individual_value)
        else:
            raise ParseFailure()

    def _parse_individual_of_person_name_sort(self, string):
        m = re.search(r'^person_name\((.+)\)$', string)
        if m:
            individual_value_string = m.group(1)
            individual_value = PersonName(individual_value_string)
            return self.ontology.create_individual(individual_value)
        else:
            raise ParseFailure()

    def _parse_individual_of_datetime_sort(self, string):
        m = re.search(r'^datetime\((.+)\)$', string)
        if m:
            individual_value_string = m.group(1)
            individual_value = DateTime(individual_value_string)
            return self.ontology.create_individual(individual_value)
        else:
            raise ParseFailure()

    def _parse_string_individual(self, string):
        string_content = self._parse_string(string)
        individual = self.ontology.create_individual(f'"{string_content}"')
        return individual

    def _parse_understanding_proposition(self, string):
        m = re.search(r'^(\~?)und\((USR|SYS|MODEL|None),[ ]*(.+)\)$', string)
        if m:
            negation = m.group(1)
            if negation == "":
                polarity = Polarity.POS
            else:
                polarity = Polarity.NEG
            speaker = self._parse_speaker(m.group(2))
            proposition_str = m.group(3)
            proposition = self.parse(proposition_str)
            und = UnderstandingProposition(speaker, proposition, polarity)
            return und
        else:
            raise ParseFailure()

    def _parse_speaker(self, string):
        if string == Speaker.USR:
            return Speaker.USR
        elif string == Speaker.SYS:
            return Speaker.SYS
        elif string == Speaker.MODEL:
            return Speaker.MODEL
        elif string == "None":
            return None

    def _parse_yes_no_question(self, string):
        m = re.search(r'^\?(\w+\(\w+\))$', string)
        if m:
            proposition_string = m.group(1)
            proposition = self._parse_predicate_proposition(proposition_string)
            return YesNoQuestion(proposition)
        else:
            raise ParseFailure()

    def _parse_yes_or_no(self, string):
        m = re.search(r'^(yes|no)$', string)
        if m:
            yes_no_string = m.group(1)
            if yes_no_string == "yes":
                return Yes()
            return No()
        else:
            raise ParseFailure()

    def _parse_action(self, string):
        m = re.search(r'^(\w+)$', string)
        try:
            if m:
                action_value = m.group(1)
                return self.ontology.create_action(action_value)
        except OntologyError:
            pass
        raise ParseFailure()

    def _parse_predicate(self, string):
        m = re.search(r'^(\w+)$', string)
        if m:
            predicate_value = m.group(1)
            try:
                return self.ontology.get_predicate(predicate_value)
            except OntologyError:
                pass
        raise ParseFailure()

    def _parse_prop_set(self, string):
        m = re.search(r'^(~?)set\((.+)\)$', string)
        if m:
            (polarity_str, alts_as_string) = m.groups()
            propositions = self._parse_proposition_list(alts_as_string)
            polarity = self._parse_polarity(polarity_str)
            return PropositionSet(propositions, polarity)
        raise ParseFailure()

    def _parse_proposition_list(self, string):
        propositions = []
        string = self._strip_brackets(string)
        while self._more_data_to_read(string):
            (proposition, rest) = self._get_next_proposition(string)
            propositions.append(proposition)
            string = rest
        return propositions

    def _get_next_proposition(self, string):
        m = re.search(r'^(?P<prop_group>([^,]+)) *\,? *(?P<rest>.*)', string)
        if m:
            proposition = self._parse_proposition(m.group('prop_group'))
            rest = m.group('rest')
            return (proposition, rest)
        else:
            raise ParseFailure()

    def _get_next_question_param(self, string):
        m = re.search(r'^(?P<key>[^=]+)=(?P<value>[^=]+) *\, *(?P<rest>[^=]+=.*)$', string)
        if m:
            rest = m.group('rest')
        else:
            m = re.search(r'^(?P<key>[^=]+)=(?P<value>.+)$', string)
            rest = ""
        if m:
            key = m.group('key')
            value_as_string = m.group('value')
            value = self.parse_parameter(key, value_as_string)
            return (key, value, rest)
        else:
            raise ParseFailure()

    def parse_parameter(self, key, string):
        try:
            if key == "graphical_type":
                return self._parse_findout_type(string)
            elif key == "source":
                return self._parse_findout_source(string)
            elif key == "incremental":
                return self._parse_boolean(string)
            elif key == "alts":
                return self._parse_prop_set(string)
            elif key == "service_query":
                return self._parse_question(string)
            elif key == "device":
                return string
            elif key == "verbalize":
                return self._parse_boolean(string)
            elif key == "default":
                return self._parse_question(string)
            elif key == "format":
                return string
            elif key == "label_questions":
                return self._parse_list_of_questions(string)
            elif key == "sort_order":
                return self._parse_findout_sort_order(string)
            elif key == "background":
                return self._parse_predicate_list(string)
            elif key == "ask_features":
                return self._parse_predicate_list(string)
            elif key == "related_information":
                return self._parse_list_of_questions(string)
            elif key == "allow_goal_accommodation":
                return self._parse_boolean(string)
            elif key == "max_spoken_alts":
                return self._parse_integer(string)
            else:
                raise ParseError("unsupported question parameter '%s'" % key)
        except ParseFailure:
            raise ParseError("failed to parse parameter %s=%s" % (key, string))

    def _parse_predicate_list(self, string):
        string_without_brackets = self._strip_brackets(string)
        predicate_strings = [str.strip() for str in string_without_brackets.split(",")]
        return [self._parse_predicate(predicate_string) for predicate_string in predicate_strings]

    def _parse_findout_type(self, string):
        if string in [QuestionRaisingPlanItem.GRAPHICAL_TYPE_LIST, QuestionRaisingPlanItem.GRAPHICAL_TYPE_TEXT]:
            return string
        else:
            raise ParseFailure()

    def _parse_findout_source(self, string):
        if string in [QuestionRaisingPlanItem.SOURCE_SERVICE, QuestionRaisingPlanItem.SOURCE_DOMAIN]:
            return string
        else:
            raise ParseFailure()

    def _parse_findout_sort_order(self, string):
        if string in [QuestionRaisingPlanItem.ALPHABETIC]:
            return string
        else:
            raise ParseFailure()

    def _parse_boolean(self, string):
        if string.lower() == "true":
            return True
        elif string.lower() == "false":
            return False
        else:
            raise ParseFailure()

    def _parse_integer(self, string):
        m = re.search(r'^[0-9]+$', string)
        if m:
            individual_value = int(string)
            return individual_value
        else:
            raise ParseFailure()

    def _parse_invoke_service_action_params(self, string):
        params = {}
        string = self._strip_curly_brackets(string)
        while self._more_data_to_read(string):
            (key, value, rest) = self._get_next_invoke_service_action_param(string)
            params[key] = value
            string = rest
        return params

    def _get_next_invoke_service_action_param(self, string):
        m = re.search(r'^(?P<key>[^=]+)=(?P<value>[^, ]+) *\,? *(?P<rest>.*)', string)
        if m:
            key = m.group('key')
            value_as_string = m.group('value')
            if key == "postconfirm":
                value = self._parse_boolean(value_as_string)
            elif key == "preconfirm":
                value = self.parse_preconfirm_value(value_as_string)
            elif key == "downdate_plan":
                value = self._parse_boolean(value_as_string)
            else:
                raise ParseFailure()
            rest = m.group('rest')
            return (key, value, rest)
        else:
            raise ParseFailure()

    def parse_preconfirm_value(self, string):
        if string == "interrogative":
            return InvokeServiceActionPlanItem.INTERROGATIVE
        elif string == "assertive":
            return InvokeServiceActionPlanItem.ASSERTIVE
        else:
            raise ParseFailure()

    def _strip_brackets(self, bracketed_string):
        matcher = re.search(r'^\[(.*)\]$', bracketed_string)
        if matcher:
            return matcher.group(1)
        else:
            raise ParseError("_strip_brackets failed for '%s'" % bracketed_string)

    def _strip_curly_brackets(self, bracketed_string):
        matcher = re.search(r'^{(.*)}$', bracketed_string)
        if matcher:
            return matcher.group(1)

    def _more_data_to_read(self, string):
        return string != ""

    def _parse_polarity(self, string):
        if string == "":
            return Polarity.POS
        elif string == "~":
            return Polarity.NEG
        else:
            raise Exception("expected polarity string but got '%s'" % string)
