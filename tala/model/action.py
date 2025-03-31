import warnings

from tala.model.semantic_object import OntologySpecificSemanticObject
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin

TOP = "top"
UP = "up"
HOW = "how"


class Action(OntologySpecificSemanticObject, AsSemanticExpressionMixin):
    @classmethod
    def create_from_json_api_data(cls, action_data, included):
        return cls(action_data["attributes"]["name"], action_data["attributes"]["ontology_name"])

    def __init__(self, value, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self.value = value

    def is_action(self):
        return True

    @property
    def name(self):
        return self.value

    def get_value(self):
        warnings.warn("Action.get_value() is deprecated. Use Action.value instead.", DeprecationWarning, stacklevel=2)
        return self.value

    def is_top_action(self):
        return self.value == TOP

    def is_up_action(self):
        return self.value == UP

    def is_how_action(self):
        return self.value == HOW

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash((self.ontology_name, self.value))

    def __eq__(self, other):
        try:
            return other.is_action() and other.value == self.value and other.ontology_name == self.ontology_name
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def as_json_api_dict(self):
        return {
            "data": {
                "type": "tala.model.action",
                "id": f"{self.ontology_name}:{self.name}",
                "attributes": {
                    "ontology_name": self.ontology_name,
                    "name": self.name
                }
            },
            "included": []
        }


class TopAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, TOP, ontology_name)


class UpAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, UP, ontology_name)


class HowAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, HOW, ontology_name)
