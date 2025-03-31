import copy

import tala.model
from tala.model.proposition import PropositionSet, ImplicationProposition
from tala.model.action import Action
from tala.model.error import DomainError
from tala.model.goal import PerformGoal, ResolveGoal, PERFORM
from tala.model.question import KnowledgePreconditionQuestion, Question
from tala.model import speaker
from tala.model.plan import Plan, InvalidPlansException
from tala.model import plan_item
from tala.model.proposition import PredicateProposition, ServiceActionTerminatedProposition
from tala.utils.as_json import AsJSONMixin, convert_to_json
from tala.utils.json_api import (JSONAPIMixin, JSONAPIObject, get_attribute)
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


class Domain(AsJSONMixin, JSONAPIMixin):
    @classmethod
    def create_from_json_api_data(cls, data, included, ontology):
        def create_plans(plans, included):
            for (
                goal, plan, postplan, downdate_conditions, superactions, preferred, unrestricted_accommodation,
                reraise_on_resume, max_answers, alternatives_predicate, accommodate_without_feedback
            ) in create_plans_content(plans, included):
                yield {
                    "goal": goal,
                    "plan": plan,
                    "postplan": postplan,
                    "postconds": downdate_conditions,
                    "superactions": superactions,
                    "preferred": preferred,
                    "unrestricted_accommodation": unrestricted_accommodation,
                    "reraise_on_resume": reraise_on_resume,
                    "max_answers": max_answers,
                    "alternatives_predicate": alternatives_predicate,
                    "accommodate_without_feedback": accommodate_without_feedback
                }

        def create_plans_content(plans, included):
            for planref in plans:
                plan_data = included.get_object_from_relationship(planref)
                yield Plan.create_from_json_api_data(plan_data, included)

        def create_dependency(dependency_data, included):
            key_question_data = included.get_object_from_relationship(dependency_data["relationships"]["key"]["data"])
            values = set()
            for value_data_item in dependency_data["relationships"]["value"]["data"]:
                value_item = included.get_object_from_relationship(value_data_item)
                values.add(Question.create_from_json_api_data(value_item, included))
            return Question.create_from_json_api_data(key_question_data, included), values

        def create_parameters(parameter_data, included):
            BOOLEAN_PARAMETERS = [
                "always_ground",
                "always_relevant",
                "allow_goal_accommodation",
                "verbalize",
                "incremental",
            ]
            QUESTION_PARAMETERS = ["service_query", "default"]
            INT_PARAMETERS = ["max_spoken_alts", "max_reported_hit_count"]
            STRING_PARAMETERS = ["source"]
            ACTION_PARAMETERS = ["on_zero_hits_action", "on_too_many_hits_action"]

            parameters = {}
            key_question_data = included.get_object_from_relationship(parameter_data["relationships"]["key"]["data"])
            key_question = Question.create_from_json_api_data(key_question_data, included)
            for boolean_parameter in BOOLEAN_PARAMETERS:
                if boolean_parameter in parameter_data["attributes"]:
                    parameters[boolean_parameter] = bool(parameter_data["attributes"][boolean_parameter])
            for int_parameter in INT_PARAMETERS:
                if int_parameter in parameter_data["attributes"]:
                    parameters[int_parameter] = int(parameter_data["attributes"][int_parameter])
            for question_parameter in QUESTION_PARAMETERS:
                if question_parameter in parameter_data["relationships"]:
                    question_data = included.get_object_from_relationship(
                        parameter_data["relationships"][question_parameter]["data"]
                    )
                    question = Question.create_from_json_api_data(question_data, included)
                    parameters[question_parameter] = question
            for parameter in STRING_PARAMETERS:
                if parameter in parameter_data["attributes"]:
                    parameters[parameter] = parameter_data["attributes"][parameter]
            for action_parameter in ACTION_PARAMETERS:
                if action_parameter in parameter_data["relationships"]:
                    parameters[action_parameter] = create_on_action_parameter(
                        action_parameter, parameter_data, included
                    )

            if "alts_value" in parameter_data["relationships"]:
                parameters["alts_value"] = create_alternatives_parameter(parameter_data, included)
            if "ask_features" in parameter_data["relationships"]:
                parameters["ask_features"] = create_ask_features_parameter(parameter_data, included)
            if "hints" in parameter_data["relationships"]:
                parameters["hints"] = create_hints_parameter(parameter_data, included)
            if "background" in parameter_data["relationships"]:
                parameters["background"] = create_background_parameter(parameter_data, included)
            if "related_information" in parameter_data["relationships"]:
                parameters["related_information"] = create_related_information_parameter(parameter_data, included)

            return key_question, parameters

        def create_query(query_data, included):
            if query_data["type"] == "implication":
                return create_implication(query_data, included)
            if query_data["type"] == "enumeration_query":
                return create_enumeration_query(query_data, included)
            if query_data["type"] == "iterator":
                return create_iterator(query_data, included)
            raise Exception(f"Type of query is not recognized: {query_data['type']}")

        def create_implication(implication_data, included):
            query_data = included.get_data_for_relationship("query", implication_data)
            query = Question.create_from_json_api_data(query_data, included)

            implications = []
            for item in implication_data["relationships"]["content"]["data"]:
                implication_object = included.get_object_from_relationship(item)
                implications.append(ImplicationProposition.create_from_json_api_data(implication_object, included))

            return {"query": query, "implications": implications}

        def create_enumeration_query(query_data, included):
            query_json = included.get_data_for_relationship("query", query_data)
            query = Question.create_from_json_api_data(query_json, included)

            enumeration_type = get_attribute("enumeration_type", query_data)
            propositions = []
            for item in query_data["relationships"]["content"]["data"]:
                prop_object = included.get_object_from_relationship(item)
                propositions.append(PredicateProposition.create_from_json_api_data(prop_object, included))

            return {"query": query, enumeration_type: propositions}

        def create_iterator(iterator_data, included):
            query = get_attribute("query", iterator_data)
            limit = get_attribute("limit", iterator_data)
            enumeration_type = get_attribute("enumeration_type", iterator_data)
            propositions = []
            for item in iterator_data["relationships"]["content"]["data"]:
                prop_object = included.get_object_from_relationship(item)
                propositions.append(PredicateProposition.create_from_json_api_data(prop_object, included))

            return {"query": query, "limit": limit, enumeration_type: propositions}

        def create_alternatives_parameter(parameter_data, included):
            prop_set_entry = included.get_object_from_relationship(
                parameter_data["relationships"]["alts_value"]["data"]
            )
            return PropositionSet.create_from_json_api_data(prop_set_entry, included)

        def create_ask_features_parameter(parameter_data, included):
            features = []
            for feature_entry in parameter_data["relationships"]["ask_features"]["data"]:
                feature_data = included.get_object_from_relationship(feature_entry)
                features.append(tala.model.ask_feature.AskFeature.create_from_json_api_dict(feature_data, included))
            return features

        def create_hints_parameter(parameter_data, included):
            hints = []
            for relationship in parameter_data["relationships"]["hints"]["data"]:
                hint_data = included.get_object_from_relationship(relationship)
                hints.append(tala.model.hint.Hint.create_from_json_api_data(hint_data, included))
            return hints

        def create_background_parameter(parameter_data, included):
            predicate_entries = parameter_data["relationships"]["background"]["data"]
            predicates = []
            for predicate_entry in predicate_entries:
                predicate = tala.model.predicate.Predicate.create_from_json_api_data(
                    included.get_object_from_relationship(predicate_entry), included
                )
                predicates.append(predicate)

            return predicates

        def create_related_information_parameter(parameter_data, included):
            related_entries = parameter_data["relationships"]["related_information"]["data"]
            questions = []
            for related_entry in related_entries:
                question = Question.create_from_json_api_data(
                    included.get_object_from_relationship(related_entry), included
                )
                questions.append(question)

            return questions

        def create_on_action_parameter(name, parameter_data, included):
            action_entry = parameter_data["relationships"][name]["data"]
            action_data = included.get_object_from_relationship(action_entry)

            return Action.create_from_json_api_data(action_data, included)

        def create_validator(data, included):
            validator_name = get_attribute("validator", data)
            configurations = []
            for configuration_list_data in data["relationships"]["valid_configurations"]["data"]:
                configurations.append(create_configuraton(configuration_list_data, included))
            return {"validator": validator_name, "valid_configurations": configurations}

        def create_configuraton(configuration_data, included):
            configuration = included.get_object_from_relationship(configuration_data)

            propositions = []
            for proposition_data in configuration["relationships"]["content"]["data"]:
                proposition = included.get_object_from_relationship(proposition_data)
                propositions.append(PredicateProposition.create_from_json_api_data(proposition, included))
            return propositions

        ddd_name = data["id"]
        user_defined_name = data["attributes"]["tala.model.domain.Domain.user_defined_name"]

        plans = list(create_plans(data["relationships"]["plans"]["data"], included))

        default_questions = []
        if "default_questions" in data["relationships"]:
            for question_ref in data["relationships"]["default_questions"]["data"]:
                question_data = included.get_object_from_relationship(question_ref)
                default_questions.append(Question.create_from_json_api_data(question_data, included))

        parameters = {}
        if "parameters" in data["relationships"]:
            for parameters_ref in data["relationships"]["parameters"]["data"]:
                parameters_data = included.get_object_from_relationship(parameters_ref)
                k, v = create_parameters(parameters_data, included)
                parameters[k] = v

        dependencies = {}
        if "dependencies" in data["relationships"]:
            for dependency_ref in data["relationships"]["dependencies"]["data"]:
                dependency_data = included.get_object_from_relationship(dependency_ref)

                key, value = create_dependency(dependency_data, included)
                dependencies[key] = value

        queries = []
        if "queries" in data["relationships"]:
            for query_ref in data["relationships"]["queries"]["data"]:
                query_data = included.get_object_from_relationship(query_ref)
                queries.append(create_query(query_data, included))

        validators = []
        if "validators" in data["relationships"]:
            for validator_ref in data["relationships"]["validators"]["data"]:
                validator_data = included.get_object_from_relationship(validator_ref)
                validators.append(create_validator(validator_data, included))

        return cls(
            ddd_name,
            user_defined_name,
            ontology,
            plans,
            default_questions,
            parameters,
            validators=validators,
            dependencies=dependencies,
            queries=queries,
        )

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

        self.ddd_name = ddd_name  # identifier
        self.name = name  # defined in XML
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

    def as_json_api_dict(self):
        def parameters_as_json_api_dict(question, parameters):
            d = JSONAPIObject("parameter")
            d.add_relationship("key", question.as_json_api_dict())
            if "alts_value" in parameters:
                d.add_relationship("alts_value", parameters["alts_value"].as_json_api_dict())
            if "ask_features" in parameters:
                for feature in parameters["ask_features"]:
                    d.append_relationship("ask_features", feature.as_json_api_dict())
            if "hints" in parameters:
                for hint in parameters["hints"]:
                    d.append_relationship("hints", hint.as_json_api_dict())
            if "always_ground" in parameters:
                d.add_attribute("always_ground", parameters["always_ground"])
            if "always_relevant" in parameters:
                d.add_attribute("always_relevant", parameters["always_relevant"])
            if "allow_goal_accommodation" in parameters:
                d.add_attribute("allow_goal_accommodation", parameters["allow_goal_accommodation"])
            if "verbalize" in parameters:
                d.add_attribute("verbalize", parameters["verbalize"])
            if "incremental" in parameters:
                d.add_attribute("incremental", parameters["incremental"])
            if "max_spoken_alts" in parameters:
                d.add_attribute("max_spoken_alts", parameters["max_spoken_alts"])
            if "max_reported_hit_count" in parameters:
                d.add_attribute("max_reported_hit_count", parameters["max_reported_hit_count"])
            if "on_zero_hits_action" in parameters:
                d.add_relationship("on_zero_hits_action", parameters["on_zero_hits_action"].as_json_api_dict())
            if "on_too_many_hits_action" in parameters:
                d.add_relationship("on_too_many_hits_action", parameters["on_too_many_hits_action"].as_json_api_dict())
            if "source" in parameters:
                d.add_attribute("source", parameters["source"])
            if "service_query" in parameters:
                d.add_relationship("service_query", parameters["service_query"].as_json_api_dict())
            if "default" in parameters:
                d.add_relationship("default", parameters["default"].as_json_api_dict())
            if "background" in parameters:
                for background in parameters["background"]:
                    d.append_relationship("background", background.as_json_api_dict())
            if "related_information" in parameters:
                for related_information in parameters["related_information"]:
                    d.append_relationship("related_information", related_information.as_json_api_dict())
            return d.as_dict

        def dependency_as_json_api_dict(question, dependencies):
            d = JSONAPIObject("dependency")
            d.add_relationship("key", question.as_json_api_dict())
            for dependency in dependencies:
                d.append_relationship("value", dependency.as_json_api_dict())

            return d.as_dict

        def query_as_json_api_dict(query_data):
            if is_implication_query(query_data):
                return implication_as_json_api_dict(query_data)
            elif is_iterator(query_data):
                return iterator_as_json_api_dict(query_data)
            else:
                return enumeration_query_as_json_api_dict(query_data)

        def is_implication_query(query_data):
            return "implications" in query_data

        def is_iterator(query_data):
            return isinstance(query_data["query"], str)

        def implication_as_json_api_dict(query_data):
            implication_object = JSONAPIObject("implication")
            implication_object.add_relationship("query", query_data["query"].as_json_api_dict())
            for implication in query_data["implications"]:
                implication_object.append_relationship("content", implication.as_json_api_dict())
            return implication_object.as_dict

        def iterator_as_json_api_dict(query_data):
            iterator_object = JSONAPIObject("iterator")
            try:
                iterator_object.add_relationship("query", query_data["query"].as_json_api_dict())
            except AttributeError:
                iterator_object.add_attribute("query", query_data["query"])
            iterator_object.add_attribute("limit", query_data["limit"])
            for type_ in ["for_enumeration", "for_random_enumeration", "for_random_selection"]:
                if type_ in query_data:
                    iterator_object.add_attribute("enumeration_type", type_)
                    break
            for proposition in query_data[type_]:
                iterator_object.append_relationship("content", proposition.as_json_api_dict())
            return iterator_object.as_dict

        def enumeration_query_as_json_api_dict(query_data):
            enumerator_object = JSONAPIObject("enumeration_query")
            enumerator_object.add_relationship("query", query_data["query"].as_json_api_dict())
            for type_ in ["for_enumeration", "for_random_enumeration", "for_random_selection"]:
                if type_ in query_data:
                    enumerator_object.add_attribute("enumeration_type", type_)
                    break
            for proposition in query_data[type_]:
                enumerator_object.append_relationship("content", proposition.as_json_api_dict())
            return enumerator_object.as_dict

        def validator_as_json_api_dict(validator_data):
            validator_object = JSONAPIObject("validator")
            validator_object.add_attribute("validator", validator_data["validator"])
            for configuration in validator_data["valid_configurations"]:
                prop_list = [prop.as_json_api_dict() for prop in configuration]
                prop_list_object = configuration_as_json_api_dict(prop_list)
                validator_object.append_relationship("valid_configurations", prop_list_object)
            return validator_object.as_dict

        def configuration_as_json_api_dict(prop_list):
            configuration_object = JSONAPIObject("configuration")
            for prop in prop_list:
                configuration_object.append_relationship("content", prop)
            return configuration_object.as_dict

        attributes = {
            "tala.model.domain.Domain.user_defined_name": self.name,
        }

        domain_object = JSONAPIObject("tala.model.domain", self.ddd_name, attributes, {}, [])
        for question in self.default_questions:
            domain_object.append_relationship("default_questions", question.as_json_api_dict())

        for question, dependencies in self.dependencies.items():
            domain_object.append_relationship("dependencies", dependency_as_json_api_dict(question, dependencies))

        for question, parameters in self.parameters.items():
            domain_object.append_relationship("parameters", parameters_as_json_api_dict(question, parameters))

        for _query_id, query_data in self.queries.items():
            domain_object.append_relationship("queries", query_as_json_api_dict(query_data))

        for validator_data in self.validators:
            domain_object.append_relationship("validators", validator_as_json_api_dict(validator_data))

        for goal, plan in self.plans.items():
            actual_plan = plan["plan"]
            goal = plan["goal"]
            preferred = plan.get("preferred", None)
            accommodate_without_feedback = plan.get("accommodate_without_feedback", False)
            restart_on_completion = plan.get("restart_on_completion", False)
            reraise_on_resume = plan.get("reraise_on_resume", True)
            max_answers = int(plan.get("max_answers", 0))
            alternatives_predicate = plan.get("alternatives_predicate")
            postplan = plan.get("postplan", [])
            downdate_conditions = plan.get("postconds", [])
            superactions = plan.get("superactions", [])
            unrestricted_accommodation = plan.get("unrestricted_accommodation", False)
            domain_object.append_relationship(
                "plans",
                actual_plan.as_json_api_dict(
                    goal, preferred, accommodate_without_feedback, restart_on_completion, reraise_on_resume,
                    max_answers, alternatives_predicate, postplan, downdate_conditions, superactions,
                    unrestricted_accommodation
                )
            )

        return domain_object.as_dict

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

    def _implicit_downdate_conditions_for_service_action_invocations(self, goal):
        plan = self.get_plan(goal)
        for item in plan:
            if item.type_ == plan_item.TYPE_INVOKE_SERVICE_ACTION and item.should_downdate_plan():
                yield ServiceActionTerminatedProposition(self.ontology.name, item.get_service_action())

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
