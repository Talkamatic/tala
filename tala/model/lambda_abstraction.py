from tala.model.semantic_object import OntologySpecificSemanticObject, SemanticObject
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class LambdaAbstractedPredicateProposition(OntologySpecificSemanticObject, AsSemanticExpressionMixin):
    def __init__(self, predicate, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self.predicate = predicate

    def is_lambda_abstracted_predicate_proposition(self):
        return True

    def __str__(self):
        variable = "X"
        return variable + "." + self.getPredicate().get_name() + "(" + variable + ")"

    def __eq__(self, other):
        if (isinstance(other, LambdaAbstractedPredicateProposition)):
            return self.getPredicate() == other.getPredicate()
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def getPredicate(self):
        return self.predicate

    def getSort(self):
        return self.predicate.getSort()

    def __hash__(self):
        return hash((self.__class__.__name__, self.predicate))


class LambdaAbstractedImplicationPropositionForConsequent(OntologySpecificSemanticObject):
    def __init__(self, antecedent, consequent_predicate, ontology_name):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
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


class LambdaAbstractedGoalProposition(SemanticObject, AsSemanticExpressionMixin):
    def __init__(self):
        SemanticObject.__init__(self)

    def is_lambda_abstracted_goal_proposition(self):
        return True

    def __eq__(self, other):
        return isinstance(other, LambdaAbstractedGoalProposition)

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "X.goal(X)"

    def __hash__(self):
        return hash(self.__class__.__name__)
