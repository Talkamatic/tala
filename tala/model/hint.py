from tala.model.plan_item import PlanItem
from tala.model.semantic_object import SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify
from tala.utils.json_api import JSONAPIObject


class Hint(SemanticObjectWithContent, AsSemanticExpressionMixin, JSONAPIObject):
    @classmethod
    def create_from_json_api_data(cls, plan_data, included):
        def generate_plan_items():
            for plan_item_key in plan_data["relationships"]["content"]["data"]:
                plan_item_data = included.get_object_from_relationship(plan_item_key)
                item = PlanItem.create_from_json_api_data(plan_item_data, included)
                if item is None:
                    raise BaseException("item is None", item)
                yield item

        return cls(list(generate_plan_items()))

    def __init__(self, plan):
        SemanticObjectWithContent.__init__(self, plan)
        self._plan = plan

    def __eq__(self, other):
        try:
            equality = self.plan == other.plan
            return equality
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self._plan)

    @property
    def plan(self):
        return self._plan

    def __str__(self):
        return "Hint" + unicodify(self.plan)

    def as_json_api_dict(self):
        obj = JSONAPIObject("tala.model.hint.Hint")
        for plan_item in self.plan:
            obj.append_relationship("content", plan_item.as_json_api_dict())
        return obj.as_dict
