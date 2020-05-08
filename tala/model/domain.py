from tala.model.action import Action
from tala.model.error import DomainError
from tala.model.goal import PerformGoal, ResolveGoal
from tala.model.speaker import Speaker
from tala.model.plan import Plan, InvalidPlansException
from tala.model.proposition import PredicateProposition, ServiceActionTerminatedProposition
from tala.model.question_raising_plan_item import QuestionRaisingPlanItem
from tala.utils.as_json import AsJSONMixin
from tala.utils.unique import unique


class DddDomain:
    pass


class Domain(AsJSONMixin):
    DEFAULT_IO_STATUS = "default"
    EXCLUDED_IO_STATUS = "excluded"
    HIDDEN_IO_STATUS = "hidden"
    SILENT_IO_STATUS = "silent"
    DISABLED_IO_STATUS = "disabled"

    def __init__(self, ddd_name, name, ontology, plans=[], default_questions=[], parameters={}, dependencies={}):
        self.ddd_name = ddd_name
        self.name = name
        self.ontology = ontology
        self.default_questions = default_questions
        self.parameters = parameters
        self.dependencies = dependencies
        self.plans = self._plan_list_to_dict_indexed_by_goal(plans)
        self._goals_in_defined_order = [plan["goal"] for plan in plans]
        self._add_top_plan_if_missing()
        self._add_up_plan()

    def as_dict(self):
        json = super(Domain, self).as_dict()
        json["ontology"] = "<skipped>"
        return json

    @property
    def goals(self):
        return list(self.plans.keys())

    def _has_top_plan(self):
        return any([
            plan for plan in list(self.plans.values()) if (
                plan["goal"].is_goal() and plan["goal"].get_goal_type() == PerformGoal.PERFORM_GOAL
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
            feature_question_predicate = feature_question.get_content().getPredicate()
            question_predicate = question.get_content().getPredicate()
        except AttributeError:
            return False
        return feature_question_predicate.is_feature_of(question_predicate)

    def _goal_issue_depends_on_question(self, goal_issue, question):
        resolve_goal = ResolveGoal(goal_issue, Speaker.SYS)
        if self.has_goal(resolve_goal):
            plan = self.get_plan(resolve_goal)
            for item in plan:
                if item.is_question_plan_item():
                    if question == item.getContent():
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

    def get_io_status(self, goal):
        if self.has_goal(goal):
            plan_info = self._get_plan_info(goal)
            if "io_status" in plan_info:
                return plan_info["io_status"]
        return Domain.DEFAULT_IO_STATUS

    def dominates(self, supergoal, subgoal):
        if self.has_goal(supergoal):
            plan = self.get_plan(supergoal)
            for item in plan:
                if item.is_question_plan_item():
                    question = item.getContent()
                    if question.is_alt_question():
                        for proposition in question.get_content():
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
            if item.is_invoke_service_action_plan_item() and item.should_downdate_plan():
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

    def get_gui_context(self, goal):
        return self.get_goal_attribute(goal, 'gui_context')

    def restart_on_completion(self, goal):
        return self.get_goal_attribute(goal, 'restart_on_completion')

    def has_dynamic_title(self, goal):
        return self.get_goal_attribute(goal, 'dynamic_title')

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
        def answers(individuals, predicate, sort):
            for individual_value in individuals:
                individual_sort = self.ontology.individual_sort(individual_value)
                if individual_sort == sort:
                    individual = self.ontology.create_individual(individual_value)
                    yield PredicateProposition(predicate, individual)

        predicate = question.get_predicate()
        question_sort = predicate.getSort()
        all_answers = answers(self.ontology.get_individuals(), predicate, question_sort)
        return unique(all_answers)

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

    def get_graphical_type(self, semantic_object):
        return self._get_parameter(semantic_object, "graphical_type")

    def get_incremental(self, semantic_object):
        return self._get_parameter(semantic_object, "incremental")

    def get_alternatives(self, semantic_object):
        return self._get_parameter(semantic_object, "alts")

    def get_source(self, semantic_object):
        return self._get_parameter(semantic_object, "source")

    def get_format(self, semantic_object):
        return self._get_parameter(semantic_object, "format")

    def get_default(self, semantic_object):
        return self._get_parameter(semantic_object, "default")

    def get_service_query(self, semantic_object):
        return self._get_parameter(semantic_object, "service_query")

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

    def get_related_information(self, semantic_object):
        return self._get_parameter(semantic_object, "related_information")

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

    def question_forces_graphical_choice(self, question):
        return self.get_graphical_type(question) in [
            QuestionRaisingPlanItem.GRAPHICAL_TYPE_LIST, QuestionRaisingPlanItem.GRAPHICAL_TYPE_TEXT
        ] and not self.get_incremental(question)

    def _get_parameter(self, question, parameter):
        try:
            return self.parameters[question][parameter]
        except KeyError:
            return None

    def get_questions_in_plan(self, plan):
        for plan_item in plan:
            if plan_item.is_question_plan_item():
                question = plan_item.getContent()
                for feature_question in self.get_feature_questions_for_plan_item(question, plan_item):
                    yield feature_question
                yield question

    def get_feature_questions_for_plan_item(self, question, plan_item):
        feature_questions = []
        if question.get_content().is_lambda_abstracted_predicate_proposition():
            for predicate in list(self.ontology.get_predicates().values()):
                if predicate.is_feature_of(question.get_content().getPredicate()):
                    feature_question = self.ontology.create_wh_question(predicate.get_name())
                    feature_questions.append(feature_question)
        return feature_questions

    def get_invoke_service_action_items_for_action(self, action_name):
        for goal in self.get_all_goals():
            plan = self.get_plan(goal)
            for item in plan:
                if item.is_invoke_service_action_plan_item() and item.get_service_action() == action_name:
                    yield item
