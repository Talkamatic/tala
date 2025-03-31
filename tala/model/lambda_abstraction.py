from tala.model.semantic_object import OntologySpecificSemanticObject, SemanticObject
from tala.model.predicate import Predicate
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class LambdaAbstractedProposition:
    LAMBDA_ABSTRACTED_PREDICATE_PROPOSITION = "LambdaAbstractedPredicateProposition"
    LAMBDA_ABSTRACTED_IMPLICATION_PROPOSITION_FOR_CONSEQUENT = "LambdaAbstractedImplicationPropositionForConsequent"
    LAMBDA_ABSTRACTED_GOAL_PROPOSITION = "LambdaAbstractedGoalProposition"

    def __init__(self, type_):
        self.type_ = type_

    def as_dict(self):
        result = {"semantic_object_type": "LambdaAbstractedProposition"}
        return super().as_dict() | result


class LambdaAbstractedPredicateProposition(
    LambdaAbstractedProposition, OntologySpecificSemanticObject, AsSemanticExpressionMixin
):
    @classmethod
    def create_from_json_api_data(cls, lambda_abstraction_data, included):
        predicate_entry = included.get_object_from_relationship(
            lambda_abstraction_data["relationships"]["predicate"]["data"]
        )
        predicate = Predicate.create_from_json_api_data(predicate_entry, included)
        ontology_name = lambda_abstraction_data["attributes"]["ontology_name"]
        return cls(predicate, ontology_name)

    def __init__(self, predicate, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        LambdaAbstractedProposition.__init__(self, self.LAMBDA_ABSTRACTED_PREDICATE_PROPOSITION)
        self.predicate = predicate

    def is_lambda_abstracted_predicate_proposition(self):
        return True

    def __str__(self):
        variable = "X"
        return variable + "." + self.predicate.get_name() + "(" + variable + ")"

    def __eq__(self, other):
        if (isinstance(other, LambdaAbstractedPredicateProposition)):
            return self.predicate == other.predicate
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    @property
    def sort(self):
        return self.predicate.sort

    def __hash__(self):
        return hash((self.__class__.__name__, self.predicate))

    @property
    def json_api_id(self):
        return f"{self}"

    @property
    def json_api_attributes(self):
        return ["ontology_name"]

    @property
    def json_api_relationships(self):
        return ["predicate"]


class LambdaAbstractedImplicationPropositionForConsequent(LambdaAbstractedProposition, OntologySpecificSemanticObject):
    def __init__(self, antecedent, consequent_predicate, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        LambdaAbstractedProposition.__init__(self, self.LAMBDA_ABSTRACTED_IMPLICATION_PROPOSITION_FOR_CONSEQUENT)
        self._antecedent = antecedent
        self._consequent_predicate = consequent_predicate

    @property
    def antecedent(self):
        return self._antecedent

    @property
    def consequent_predicate(self):
        return self._consequent_predicate

    def is_lambda_abstracted_implication_proposition_for_consequent(self):
        return True

    def __str__(self):
        return "X.implies(%s, %s(X))" % (self._antecedent, self._consequent_predicate)

    def __eq__(self, other):
        try:
            return other.antecedent == self.antecedent and other.consequent_predicate == self.consequent_predicate
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.__class__.__name__, self.antecedent, self.consequent_predicate))


class LambdaAbstractedGoalProposition(LambdaAbstractedProposition, SemanticObject, AsSemanticExpressionMixin):
    def __init__(self):
        SemanticObject.__init__(self)
        LambdaAbstractedProposition.__init__(self, self.LAMBDA_ABSTRACTED_GOAL_PROPOSITION)

    def is_lambda_abstracted_goal_proposition(self):
        return True

    def __eq__(self, other):
        try:
            return other.type_ == self.LAMBDA_ABSTRACTED_GOAL_PROPOSITION
        except Exception:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "X.goal(X)"

    def __hash__(self):
        return hash(self.__class__.__name__)
