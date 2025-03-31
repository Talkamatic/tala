from tala.model.stack import Stack
from tala import model
from tala.model import plan_item
from tala.model.semantic_object import SemanticObject
from tala.model.goal import Goal
from tala.utils.json_api import JSONAPIObject
from tala.model.action import Action
from tala.model.proposition import PredicateProposition


class UnableToDetermineOntologyException(Exception):
    pass


class Plan(Stack, SemanticObject):
    @classmethod
    def create_from_json_api_data(cls, plan_data, included):
        def generate_plan_items():
            if "plan_content" in plan_data["relationships"]:
                for plan_item_key in plan_data["relationships"]["plan_content"]["data"]:
                    plan_item_data = included.get_object_from_relationship(plan_item_key)
                    item = plan_item.PlanItem.create_from_json_api_data(plan_item_data, included)
                    if item is None:
                        raise BaseException("item is None", item)
                    yield item

        def generate_postplan_items():
            if "postplan_content" in plan_data["relationships"]:
                for plan_item_key in plan_data["relationships"]["postplan_content"]["data"]:
                    plan_item_data = included.get_object_from_relationship(plan_item_key)
                    item = plan_item.PlanItem.create_from_json_api_data(plan_item_data, included)
                    if item is None:
                        raise BaseException("item is None", item)
                    yield item

        goal_data = included.get_object_from_relationship(plan_data["relationships"]["goal"]["data"])
        goal = Goal.create_from_json_api_data(goal_data, included)
        preferred = False
        if "preferred" in plan_data["relationships"]:
            preference_data = included.get_object_from_relationship(plan_data["relationships"]["preferred"]["data"])
            preferred = PredicateProposition.create_from_json_api_data(preference_data, included)

        if not preferred and "preferred" in plan_data["attributes"]:
            preferred = True

        downdate_conditions = []
        if "downdate_conditions" in plan_data["relationships"]:
            for downdate_condition in plan_data["relationships"]["downdate_conditions"]["data"]:
                condition_data = included.get_object_from_relationship(downdate_condition)
                if downdate_condition["type"].endswith("PredicateProposition"):
                    downdate_conditions.append(PredicateProposition.create_from_json_api_data(condition_data, included))
                else:
                    downdate_conditions.append(model.condition.create_from_json_api_data(condition_data, included))
        superactions = []
        if "superactions" in plan_data["relationships"]:
            for action in plan_data["relationships"]["superactions"]["data"]:
                action_data = included.get_object_from_relationship(action)
                superactions.append(Action.create_from_json_api_data(action_data, included))

        accommodate_without_feedback = plan_data["attributes"].get("accommodate_without_feedback", False)

        unrestricted_accommodation = plan_data["attributes"].get("unrestricted_accommodation", False)
        reraise_on_resume = plan_data["attributes"].get("reraise_on_resume", True)
        max_answers = int(plan_data["attributes"].get("max_answers", -1))
        alternatives_predicate = plan_data["attributes"].get("alternatives_predicate", None)

        return (
            goal, Plan(list(generate_plan_items())), list(generate_postplan_items()), downdate_conditions, superactions,
            preferred, unrestricted_accommodation, reraise_on_resume, max_answers, alternatives_predicate,
            accommodate_without_feedback
        )

    def __init__(self, content=None):
        if content is None:
            content = set()
        Stack.__init__(self, content=content)
        SemanticObject.__init__(self)

    def is_ontology_specific(self):
        if not all([proposition.is_ontology_specific() for proposition in self.content]):
            return False
        if not self._ontology_names:
            return False
        return self._are_all_propositions_from_same_ontology()

    def _are_all_propositions_from_same_ontology(self):
        return len(self._ontology_names) < 2

    def as_json_api_dict(
        self, goal, preferred, accommodate_without_feedback, restart_on_completion, reraise_on_resume, max_answers,
        alternatives_predicate, postplan, downdate_conditions, superactions, unrestricted_accommodation
    ):
        def get_id():
            return f"{goal.ontology_name}:{goal.type_}:{goal.content}"

        dict_ = {
            "data": {
                "type": "tala.model.plan",
                "id": get_id(),
                "attributes": {
                    "version:id": "2",
                    "ontology_name": goal.ontology_name,
                    "accommodate_without_feedback": accommodate_without_feedback,
                    "restart_on_completion": restart_on_completion,
                    "reraise_on_resume": reraise_on_resume,
                    "max_answers": max_answers,
                    "alternatives_predicate": alternatives_predicate,
                    "unrestricted_accommodation": unrestricted_accommodation
                },
                "relationships": {}
            },
            "included": []
        }

        obj = JSONAPIObject.create_from_dict(dict_)
        if preferred is True:
            obj.add_attribute("preferred", True)
        elif preferred:
            obj.add_relationship("preferred", preferred.as_json_api_dict())
        obj.add_relationship("goal", goal.as_json_api_dict())

        for downdate_condition in downdate_conditions:
            obj.append_relationship("downdate_conditions", downdate_condition.as_json_api_dict())

        for item in reversed([plan_item_ for plan_item_ in self.iter_stack()]):
            obj.append_relationship("plan_content", item.as_json_api_dict())

        for plan_item_ in postplan:
            obj.append_relationship("postplan_content", plan_item_.as_json_api_dict())

        for superaction in superactions:
            obj.append_relationship("superactions", superaction.as_json_api_dict())

        return obj.as_dict

    @property
    def ontology_name(self):
        if not self._ontology_names:
            raise UnableToDetermineOntologyException("Expected semantic content but found none")

        if self.is_ontology_specific():
            return self._ontology_names.pop()

        message = "Expected all propositions %s\n\nin ontology %s\n\nbut they're from %s" % (
            self.content, self.content[0].ontology_name, self._ontology_names
        )
        raise UnableToDetermineOntologyException(message)

    @property
    def _ontology_names(self):
        ontology_names = set(proposition.ontology_name for proposition in self.content)
        return ontology_names

    def has_semantic_content(self):
        return True

    def iter_stack(self):
        return Stack.__iter__(self)

    def __iter__(self):
        flattened_items = self._flatten(self.content)
        return flattened_items.__iter__()

    def _flatten(self, items):
        result = []
        for item in items:
            if item.type_ == plan_item.TYPE_IF_THEN_ELSE:
                if item.consequent:
                    result.extend(self._flatten(item.get_consequent()))
                if item.alternative:
                    result.extend(self._flatten(item.get_alternative()))
            else:
                result.append(item)
        return result

    def remove(self, item_to_remove):
        items_to_remove = []
        for item in self.content:
            if item == item_to_remove:
                items_to_remove.append(item)
            elif item.type_ == plan_item.TYPE_IF_THEN_ELSE:
                self.remove_nested(item_to_remove, item)
        for item in items_to_remove:
            self.content.remove(item)

    def remove_nested(self, to_remove, item):
        if to_remove in item.consequent:
            item.consequent.remove(to_remove)
        if to_remove in item.alternative:
            item.alternative.remove(to_remove)
        for sub_item in item.alternative + item.consequent:
            if sub_item.type_ == plan_item.TYPE_IF_THEN_ELSE:
                self.remove_nested(to_remove, sub_item)

    def get_questions_in_plan_without_feature_question(self):
        for item in self:
            if item.type_ in plan_item.QUESTION_TYPES:
                question = item.content
                yield question

    def __str__(self):
        return "Plan(%s)" % self.content

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.content))


class InvalidPlansException(Exception):
    pass
