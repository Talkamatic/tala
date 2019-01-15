from tala.model.semantic_object import OntologySpecificSemanticObject


class Action(OntologySpecificSemanticObject):
    def __init__(self, value, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self.value = value

    def is_action(self):
        return True

    def isRespondPlanItem(self):
        return False

    def get_value(self):
        return self.value

    def is_top_action(self):
        return self.value == "top"

    def is_up_action(self):
        return self.value == "up"

    def __unicode__(self):
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
        Action.__init__(self, "top", ontology_name)


class UpAction(Action):
    def __init__(self, ontology_name):
        Action.__init__(self, "up", ontology_name)
