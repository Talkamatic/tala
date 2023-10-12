from tala.model.semantic_object import OntologySpecificSemanticObject
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin

TOP = "top"
UP = "up"
HOW = "how"


class Action(OntologySpecificSemanticObject, AsSemanticExpressionMixin):
    def __init__(self, value, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self.value = value

    def is_action(self):
        return True

    def get_value(self):
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
            return other.is_action() and other.get_value() == self.get_value(
            ) and other.ontology_name == self.ontology_name
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)


class TopAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, TOP, ontology_name)


class UpAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, UP, ontology_name)


class HowAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, HOW, ontology_name)
