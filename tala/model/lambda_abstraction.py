import warnings

from tala.model.semantic_object import OntologySpecificSemanticObject, SemanticObject
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class LambdaAbstractedProposition():
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

    def getPredicate(self):
        warnings.warn(
            "LambdaAbstractedPredicateProposition.getPredicate() is deprecated. "
            "Use LambdaAbstractedPredicateProposition.predicate instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.predicate

    @property
    def sort(self):
        return self.predicate.sort

    def getSort(self):
        warnings.warn(
            "LambdaAbstractedPredicateProposition.getSort() is deprecated. "
            "Use LambdaAbstractedPredicateProposition.sort instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.sort

    def __hash__(self):
        return hash((self.__class__.__name__, self.predicate))


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
