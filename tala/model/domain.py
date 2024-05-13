import copy

from tala.model.action import Action
from tala.model.error import DomainError
from tala.model.goal import PerformGoal, ResolveGoal, PERFORM
from tala.model.question import KnowledgePreconditionQuestion
from tala.model import speaker
from tala.model.plan import Plan, InvalidPlansException
from tala.model import plan_item
from tala.model.proposition import PredicateProposition, ServiceActionTerminatedProposition
from tala.utils.as_json import AsJSONMixin, convert_to_json
from tala.utils.unique import unique

SEMANTIC_OBJECT_TYPE = "domain"


class DddDomain:
    pass


def dict_as_key_value_list(dict_):
    return [create_json_dict(key, value) for key, value in dict_.items()]


def create_json_dict(key, value):
    return {"key": convert_to_json(key), "value": convert_to_json(value)}


def queries_dict_as_list(dict_):
    def is_iterator(query_content):
        return "limit" in query_content

    queries_list = []
    for _question, content_dict in dict_.items():
        result_dict = {}
        if is_iterator(content_dict):
            result_dict = serialize_iterator(content_dict)
        else:
            for entry in content_dict:
                result_dict[entry] = convert_to_json(content_dict[entry])
        queries_list.append(result_dict)
    return queries_list


def serialize_iterator(iterator):
    serialized_iterator = {}
    for key, value in iterator.items():
        if key in ["for_enumeration", "for_random_enumeration"]:
            serialized_iterator[key] = [convert_to_json(item) for item in value]
        else:
            serialized_iterator[key] = value
    return serialized_iterator


class Domain(AsJSONMixin):

    def __init__(
            self, ddd_name, name, ontology, plans=None, default_questions=None, parameters=None,
            validators=None, dependencies=None, queries=None
    ):  # yapf: disable
        if plans is None:
            plans = []
        if default_questions is None:
            default_questions = []
        if parameters is None:
            parameters = {}
        if validators is None:
            validators = {}
        if dependencies is None:
            dependencies = {}
        if queries is None:
            queries = []

        self.ddd_name = ddd_name
        self.name = name
        self.ontology = ontology
        self.default_questions = default_questions
        self.parameters = parameters
        self.dependencies = dependencies
        self.plans = self._plan_list_to_dict_indexed_by_goal(plans)
        self.queries = self._query_list_to_dict_indexed_by_question(queries)
        self.validators = validators
        self._goals_in_defined_order = [plan["goal"] for plan in plans]
        self._add_top_plan_if_missing()
        self._add_up_plan()

    def as_dict(self):
        json = super(Domain, self).as_dict()
        json["ontology"] = "<skipped>"
        json["semantic_object_type"] = SEMANTIC_OBJECT_TYPE
        json["parameters"] = dict_as_key_value_list(self.parameters)
        json["dependencies"] = dict_as_key_value_list(self.dependencies)
        json["queries"] = queries_dict_as_list(self.queries)
        return json

    @property
    def goals(self):
        return list(self.plans.keys())

    def _has_top_plan(self):
        return any([
            plan for plan in list(self.plans.values()) if (
                plan["goal"].is_goal() and plan["goal"].type == PERFORM
                and plan["goal"].get_action().get_value() == "top"
            )
        ])  # noqa: E127

    def get_ontology(self):
        return self.ontology

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.ddd_name == other.ddd_name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.name) * hash(self.ddd_name)

    def get_name(self):
        return self.name

    def action(self, action_name):
        return Action(action_name, self.ontology.get_name())

    def is_depending_on(self, dependent_issue, other):
        if dependent_issue in self.dependencies:
            if other in self.dependencies[dependent_issue]:
                return True
        if self._goal_issue_depends_on_question(dependent_issue, other):
            return True
        if self.is_feature_of(other, dependent_issue):
            return True
        return False

    def is_feature_of(self, feature_question, question):
        try:
            feature_question_predicate = feature_question.content.predicate
            question_predicate = question.content.predicate
        except AttributeError:
            return False
        return feature_question_predicate.is_feature_of(question_predicate)

    def _goal_issue_depends_on_question(self, goal_issue, question):
        resolve_goal = ResolveGoal(goal_issue, speaker.SYS)
        if self.has_goal(resolve_goal):
            plan = self.get_plan(resolve_goal)
            for item in plan:
                if item.type_ in plan_item.QUESTION_TYPES:
                    if question == item.content:
                        return True
        return False

    def get_dependent_question(self, question):
        for other_question in self.get_plan_questions():
            if self.is_depending_on(other_question, question):
                return other_question
        return None

    def has_goal(self, goal):
        return goal in self.plans

    def get_plan(self, goal):
        plan_info = self._get_plan_info(goal)
        return plan_info["plan"]

    def _get_plan_info(self, goal):
        if goal in self.plans:
            return self.plans[goal]
        else:
            raise DomainError("no plan for goal '%s' in domain '%s'" % (goal, self.get_name()))

    def dominates(self, supergoal, subgoal):
        if self.has_goal(supergoal):
            plan = self.get_plan(supergoal)
            for item in plan:
                if item.type_ in plan_item.QUESTION_TYPES:
                    question = item.content
                    if question.is_alt_question():
                        for proposition in question.content:
                            if proposition.is_goal_proposition():
                                goal = proposition.get_goal()
                                if goal == subgoal:
                                    return True
                                elif self.dominates(goal, subgoal):
                                    return True
        return False

    def _is_action_goal(self, goal):
        try:
            return goal.is_action()
        except AttributeError:
            return False

    def goal_is_preferred(self, goal):
        return self.goal_is_conditionally_preferred(goal, [])

    def goal_is_conditionally_preferred(self, goal, facts):
        condition = self.get_preferred(goal)
        if condition is True or condition in facts:
            return True

    def is_default_question(self, question):
        return question in self.default_questions

    def get_plan_questions(self):
        already_found = set()
        for goal in self.plans:
            plan = self.get_plan(goal)
            for question in self.get_questions_in_plan(plan):
                if question not in already_found:
                    already_found.add(question)
                    yield question

    def get_plan_goal_iterator(self):
        for goal in self.plans:
            yield goal

    def get_all_goals(self):
        return list(self.plans.keys())

    def get_all_goals_in_defined_order(self):
        return self._goals_in_defined_order

    def get_all_resolve_goals(self):
        return [x for x in self.plans if x.is_resolve_goal()]

    def get_downdate_conditions(self, goal):
        if self.has_goal(goal):
            for downdate_condition in self.get_goal_attribute(goal, 'postconds'):
                yield downdate_condition
            for downdate_condition in self._implicit_downdate_conditions_for_service_action_invocations(goal):
                yield downdate_condition
            for downdate_condition in self._implicit_downdate_conditions_for_handle_goal(goal):
                yield downdate_condition

    def _implicit_downdate_conditions_for_service_action_invocations(self, goal):
        plan = self.get_plan(goal)
        for item in plan:
            if item.type_ == plan_item.TYPE_INVOKE_SERVICE_ACTION and item.should_downdate_plan():
                yield ServiceActionTerminatedProposition(self.ontology.name, item.get_service_action())

    def _implicit_downdate_conditions_for_handle_goal(self, goal):
        if goal.is_handle_goal():
            yield ServiceActionTerminatedProposition(self.ontology.name, goal.get_device_event())

    def get_goal_attribute(self, goal, attribute):
        plan_info = self._get_plan_info(goal)
        try:
            return plan_info[attribute]
        except KeyError:
            return []

    def get_postplan(self, goal):
        if self.has_goal(goal):
            return self.get_goal_attribute(goal, 'postplan')
        else:
            return []

    def get_superactions(self, goal):
        if self.has_goal(goal):
            return self.get_goal_attribute(goal, 'superactions')
        else:
            return []

    def restart_on_completion(self, goal):
        return self.get_goal_attribute(goal, 'restart_on_completion')

    def get_reraise_on_resume(self, goal):
        reraise_on_resume = self.get_goal_attribute(goal, "reraise_on_resume")
        if reraise_on_resume == []:
            reraise_on_resume = True
        return reraise_on_resume

    def is_silently_accommodatable(self, goal):
        return self.get_goal_attribute(goal, 'unrestricted_accommodation')

    def get_preferred(self, goal):
        if self.has_goal(goal):
            return self.get_goal_attribute(goal, 'preferred')
        else:
            return []

    def goal_allows_accommodation_without_feedback(self, goal):
        return self.get_goal_attribute(goal, "accommodate_without_feedback")

    def get_resolving_answers(self, question):
        def all_answers(question):
            for individual in self.ontology.individuals_as_objects:
                if individual.sort == question.predicate.sort:
                    yield PredicateProposition(question.predicate, individual)

        return unique(all_answers(question))

    def _query_list_to_dict_indexed_by_question(self, query_list):
        plans = {}
        for query_info in query_list:
            query = query_info["query"]
            if query in plans:
                raise InvalidPlansException(f"multiple definitions for query {query}")
            plans[query] = query_info
        return plans

    def _plan_list_to_dict_indexed_by_goal(self, plan_list):
        plans = {}
        for plan_info in plan_list:
            goal = plan_info["goal"]
            if not goal.is_goal():
                raise Exception("expected goal but found %s" % goal)
            if goal in plans:
                raise InvalidPlansException("multiple plans for goal %s" % goal)
            plans[goal] = plan_info
        return plans

    def _add_up_plan(self):
        up_action = self.action("up")
        goal = PerformGoal(up_action)
        self.plans[goal] = {"goal": goal, "plan": Plan()}

    def _add_top_plan_if_missing(self):
        top_goal = PerformGoal(self.action("top"))
        if top_goal not in self.plans:
            self.plans[top_goal] = {"goal": top_goal, "plan": Plan()}

    def get_incremental(self, semantic_object):
        return self._get_parameter(semantic_object, "incremental")

    def get_alternatives(self, semantic_object):
        return self._get_parameter(semantic_object, "alts")

    def get_source(self, semantic_object):
        return self._get_parameter(semantic_object, "source")

    def get_format(self, semantic_object):
        return self._get_parameter(semantic_object, "format")

    def get_service_query(self, semantic_object):
        return self._get_parameter(semantic_object, "service_query")

    def get_on_zero_hits_action(self, semantic_object):
        return self._get_parameter(semantic_object, "on_zero_hits_action")

    def get_on_too_many_hits_action(self, semantic_object):
        return self._get_parameter(semantic_object, "on_too_many_hits_action")

    def get_label_questions(self, semantic_object):
        return self._get_parameter(semantic_object, "label_questions")

    def get_sort_order(self, semantic_object):
        return self._get_parameter(semantic_object, "sort_order")

    def get_max_spoken_alts(self, question):
        return self._get_parameter(question, "max_spoken_alts")

    def get_background(self, semantic_object):
        return self._get_parameter(semantic_object, "background")

    def get_ask_features(self, semantic_object):
        return self._get_parameter(semantic_object, "ask_features")

    def get_hints(self, semantic_object):
        return self._get_parameter(semantic_object, "hints")

    def get_related_information(self, semantic_object):
        return self._get_parameter(semantic_object, "related_information")

    def get_max_reported_hit_count(self, semantic_object):
        return self._get_parameter(semantic_object, "max_reported_hit_count")

    def get_alternatives_predicate(self, goal):
        return self._get_plan_attribute(goal, "alternatives_predicate")

    def get_always_ground(self, semantic_object):
        return self._get_parameter(semantic_object, "always_ground")

    def get_is_always_relevant(self, semantic_object):
        return self._get_parameter(semantic_object, "always_relevant")

    def _get_plan_attribute(self, goal, attribute):
        if goal in self.plans:
            plan_info = self._get_plan_info(goal)
            if attribute in plan_info:
                return plan_info[attribute]

    def get_max_answers(self, goal):
        return self._get_plan_attribute(goal, "max_answers")

    def get_verbalize(self, semantic_object):
        if self._get_parameter(semantic_object, "verbalize") is False:
            return False
        else:
            return True

    def allows_goal_accommodation(self, question):
        if self._get_parameter(question, "allow_goal_accommodation") is False:
            return False
        else:
            return True

    def _get_parameter(self, question, parameter):
        try:
            return self.parameters[question][parameter]
        except KeyError:
            return None

    def get_questions_in_plan(self, plan):
        for item in plan:
            if item.type_ in plan_item.QUESTION_TYPES:
                question = item.content
                for feature_question in self.get_feature_questions_for_plan_item(question, item):
                    yield feature_question
                ask_features = self.get_ask_features(question)
                if ask_features:
                    for ask_feature in ask_features:
                        feature_question = self.ontology.create_wh_question(ask_feature.name)
                        yield feature_question
                        if ask_feature.kpq:
                            yield KnowledgePreconditionQuestion(feature_question)
                yield question

    def get_feature_questions_for_plan_item(self, question, plan_item):
        feature_questions = []
        if question.content.is_lambda_abstracted_predicate_proposition():
            for predicate in list(self.ontology.get_predicates().values()):
                if predicate.is_feature_of(question.content.predicate):
                    feature_question = self.ontology.create_wh_question(predicate.get_name())
                    feature_questions.append(feature_question)
        return feature_questions

    def is_question_in_plan(self, question, plan):
        return question in self.get_questions_in_plan(plan)

    def get_invoke_service_action_items_for_action(self, action_name):
        for goal in self.get_all_goals():
            plan = self.get_plan(goal)
            for item in plan:
                if item.type_ == plan_item.TYPE_INVOKE_SERVICE_ACTION and item.get_service_action() == action_name:
                    yield item

    def get_names_of_user_targeted_actions(self):
        actions = []
        for goal in self.get_all_goals():
            plan = self.get_plan(goal)
            for item in plan:
                if item.type_ == plan_item.TYPE_GET_DONE:
                    actions.append(item.content.value)
        return actions

    def get_implications_for_domain_query(self, query):
        return self.queries[query]["implications"]

    def get_propositions_for_random_selection(self, query):
        return self.queries[query]["for_random_selection"]

    def get_propositions_for_enumeration(self, query):
        return copy.copy(self.queries[query].get("for_enumeration", []))

    def get_propositions_for_random_enumeration(self, query):
        return copy.copy(self.queries[query].get("for_random_enumeration", []))

    def get_limit_for_iterator(self, query):
        limit = self.queries[query].get("limit", -1)
        return int(limit)
