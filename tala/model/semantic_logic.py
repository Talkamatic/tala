from tala.model.domain import DomainError
from tala.model.individual import Individual
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition, \
    LambdaAbstractedGoalProposition
from tala.model.ontology import OntologyError
from tala.model.polarity import Polarity
from tala.model.proposition import Proposition, PredicateProposition, GoalProposition, PropositionSet, \
    PreconfirmationProposition, UnderstandingProposition, KnowledgePreconditionProposition
from tala.model.question import KnowledgePreconditionQuestion, ConsequentQuestion


class UnknownObjectClassException(Exception):
    pass


class UnexpectedObjectClassException(Exception):
    pass


class InvalidSemanticObjectException(Exception):
    pass


class SemanticLogic:
    def __init__(self, ddd_manager):
        self._ddd_manager = ddd_manager

    def is_relevant(self, semantic_object, other_semantic_object):
        logic_object = self.from_semantic_object(semantic_object)
        return logic_object.relevant(other_semantic_object)

    def are_combinable(self, semantic_object, other_semantic_object):
        logic_object = self.from_semantic_object(semantic_object)
        return logic_object.is_combinable_with(other_semantic_object)

    def combine(self, semantic_object, other_semantic_object):
        logic_object = self.from_semantic_object(semantic_object)
        return logic_object.combine_with(other_semantic_object)

    def resolves(self, semantic_object, other_semantic_object):
        logic_object = self.from_semantic_object(semantic_object)
        return logic_object.is_resolved_by(other_semantic_object)

    def from_semantic_object(self, semantic_object):
        if semantic_object.is_lambda_abstracted_predicate_proposition():
            ontology = self._ontology_of_semantic_object(semantic_object)
            return LambdaAbstractedPredicatePropositionLogic(ontology, semantic_object)
        if semantic_object.is_lambda_abstracted_goal_proposition():
            return LambdaAbstractedGoalPropositionLogic(semantic_object)
        if semantic_object.is_question():
            if semantic_object.is_knowledge_precondition_question():
                return KnowledgePreconditionQuestionLogic(semantic_object, self)
            if semantic_object.is_consequent_question():
                ontology = self._ontology_of_semantic_object(semantic_object)
                return ConsequentQuestionLogic(ontology, semantic_object)
            return self.from_semantic_object(semantic_object.content)
        if semantic_object.is_proposition():
            if semantic_object.is_predicate_proposition():
                ontology = self._ontology_of_semantic_object(semantic_object)
                return PredicatePropositionLogic(ontology, semantic_object)
            if semantic_object.is_goal_proposition():
                return GoalPropositionLogic(semantic_object)
            if semantic_object.is_proposition_set():
                return PropositionSetLogic(self._ddd_manager, semantic_object, self)
            if semantic_object.is_preconfirmation_proposition():
                return PreconfirmationPropositionLogic(semantic_object)
            if semantic_object.is_understanding_proposition():
                return UnderstandingPropositionLogic(semantic_object)
        raise UnknownObjectClassException("Expected semantic object of known subclass but got %r" % semantic_object)

    def _ontology_of_semantic_object(self, semantic_object):
        if semantic_object.is_ontology_specific():
            ontology = self._ddd_manager.get_ontology(semantic_object.ontology_name)
            return ontology
        raise InvalidSemanticObjectException("Semantic object %s does not belong to an ontology" % semantic_object)


class SemanticObjectSpecificLogic(object):
    TARGET_CLASS = None

    def __init__(self, semantic_object):
        if not isinstance(semantic_object, self.TARGET_CLASS):
            raise UnexpectedObjectClassException(
                "Expected object of class %s but got %s" % (self.TARGET_CLASS, semantic_object)
            )
        self._semantic_object = semantic_object

    def relevant(self, answer):
        raise NotImplementedError("This method needs to be implemented in a subclass.")

    def is_combinable_with(self, answer):
        raise NotImplementedError("This method needs to be implemented in a subclass.")

    def combine_with(self, answer):
        raise NotImplementedError("This method needs to be implemented in a subclass.")

    def is_resolved_by(self, answer):
        raise NotImplementedError("This method needs to be implemented in a subclass.")


class SemanticObjectAndOntologySpecificLogic(SemanticObjectSpecificLogic):
    def __init__(self, ontology, semantic_object):
        SemanticObjectSpecificLogic.__init__(self, semantic_object)
        self._ontology = ontology


class LambdaAbstractedPredicatePropositionLogic(SemanticObjectAndOntologySpecificLogic):
    TARGET_CLASS = LambdaAbstractedPredicateProposition

    def relevant(self, answer):
        is_relevant_individual = answer.is_individual() \
            and self._relevant_feature_for_individual(answer)
        is_relevant_predicate_proposition = answer.is_predicate_proposition() \
            and answer.predicate.is_feature_of(self._semantic_object.predicate)
        return self.is_combinable_with(answer) or is_relevant_individual or is_relevant_predicate_proposition

    def _relevant_feature_for_individual(self, individual):
        for predicate in list(self._ontology.get_predicates().values()):
            if predicate.is_feature_of(self._semantic_object.predicate)\
               and predicate.sort == individual.sort:
                return predicate

    def is_combinable_with(self, answer):
        try:
            self.combine_with(answer)
            return True
        except (AttributeError, DomainError, OntologyError):
            return False

    def combine_with(self, answer):
        if (
            answer.is_proposition() and (
                answer.predicate == self._semantic_object.predicate
                or answer.predicate.is_feature_of(self._semantic_object.predicate)
            )
        ):
            return answer
        elif answer.is_individual():
            if answer.is_positive():
                polarity = Polarity.POS
                individual = answer
            else:
                polarity = Polarity.NEG
                individual = Individual(answer.ontology_name, answer.value, answer.sort)

            feature_predicate = self._relevant_feature_for_individual(individual)
            if feature_predicate:
                output_predicate = feature_predicate
            else:
                output_predicate = self._semantic_object.predicate

            return PredicateProposition(output_predicate, individual, polarity)
        else:
            raise DomainError("cannot combine '" + str(self) + "' with '" + str(answer) + "'")

    def is_resolved_by(self, answer):
        try:
            return (answer.predicate == self._semantic_object.predicate and answer.is_positive())
        except AttributeError:
            pass
        try:
            return answer.sort == self._semantic_object.sort and answer.is_positive()
        except AttributeError:
            return False


class LambdaAbstractedGoalPropositionLogic(SemanticObjectSpecificLogic):
    TARGET_CLASS = LambdaAbstractedGoalProposition

    def relevant(self, answer):
        try:
            return answer.is_goal_proposition()
        except AttributeError:
            return False

    def combine_with(self, answer):
        if answer.is_goal_proposition():
            return answer

    def is_combinable_with(self, answer):
        try:
            return answer.is_goal_proposition()
        except AttributeError:
            return False

    def is_resolved_by(self, answer):
        try:
            if answer.is_goal_proposition():
                return True
        except AttributeError:
            pass
        return False


class PropositionLogic(SemanticObjectSpecificLogic):
    TARGET_CLASS = Proposition

    def relevant(self, answer):
        return self.is_combinable_with(answer)

    def is_resolved_by(self, answer):
        return self.is_combinable_with(answer)

    def is_combinable_with(self, answer):
        raise NotImplementedError("Method is_combinable_with() needs to be implemented in a subclass.")

    def combine_with(self, answer):
        raise NotImplementedError("Method combine_with() needs to be implemented in a subclass.")


class OntologySpecificPropositionLogic(PropositionLogic, SemanticObjectAndOntologySpecificLogic):
    def __init__(self, ontology, semantic_object):
        SemanticObjectAndOntologySpecificLogic.__init__(self, ontology, semantic_object)


class PredicatePropositionLogic(PropositionLogic, SemanticObjectAndOntologySpecificLogic):
    TARGET_CLASS = PredicateProposition

    def relevant(self, answer):
        return (
            self.is_combinable_with(answer) or self._has_feature_combinable_with(answer)
            or self._semantic_object._is_feature(answer)
        )

    def _has_feature_combinable_with(self, answer):
        return (
            answer.is_individual() and any([
                predicate for predicate in list(self._ontology.get_predicates().values())
                if predicate.is_feature_of(self._semantic_object.predicate) and predicate.sort == answer.sort
            ])
        )

    def is_combinable_with(self, answer):
        if answer.is_yes() or answer.is_no():
            return True
        elif answer.is_predicate_proposition() and self._semantic_object.predicate == answer.predicate and \
                self._semantic_object.individual == answer.individual:
            return True
        elif answer.is_individual() and self._is_combinable_with_individual(answer):
            return True
        else:
            return False

    def combine_with(self, answer):
        if answer.is_yes():
            return self._semantic_object
        elif answer.is_no():
            return self._semantic_object.negate()
        elif answer.is_proposition():
            return self._combine_with_proposition(answer)
        elif answer.is_individual():
            return self._combine_with_individual(answer)

    def _is_combinable_with_individual(self, individual):
        if self._semantic_object.predicate.sort == individual.sort \
           and self._semantic_object.individual is not None \
           and self._semantic_object.individual.value == individual.value:
            return True
        else:
            return False

    def _combine_with_proposition(self, proposition):
        if self._semantic_object.predicate == proposition.predicate and \
                self._semantic_object.individual == proposition.individual:
            return proposition

    def _combine_with_individual(self, individual):
        argument = self._semantic_object.individual
        if argument == individual:
            return self._semantic_object
        if argument.value == individual.value \
                and argument.is_positive() != individual.is_positive():
            return self._semantic_object.negate()


class GoalPropositionLogic(SemanticObjectSpecificLogic):
    TARGET_CLASS = GoalProposition

    def is_resolved_by(self, answer):
        return self.is_combinable_with(answer)

    def relevant(self, answer):
        return self.is_combinable_with(answer)

    def is_combinable_with(self, answer):
        if answer.is_yes() or answer.is_no():
            return True
        elif answer.is_proposition() and answer.is_goal_proposition() and answer.get_goal(
        ) == self._semantic_object.get_goal():
            return True
        else:
            return False

    def combine_with(self, answer):
        if answer.is_yes():
            return self._semantic_object
        elif answer.is_no():
            return self._semantic_object.negate()
        elif answer.is_goal_proposition() and answer.get_goal() == self._semantic_object.get_goal():
            return answer
        else:
            return False


class PropositionSetLogic(SemanticObjectSpecificLogic):
    TARGET_CLASS = PropositionSet

    def __init__(self, ddd_manager, semantic_object, semantic_logic):
        SemanticObjectSpecificLogic.__init__(self, semantic_object)
        self._ddd_manager = ddd_manager
        self._semantic_logic = semantic_logic

    def is_combinable_with(self, answer):
        if self._semantic_object.is_single_alt():
            return self._semantic_logic.are_combinable(self._semantic_object.get_single_alt(), answer)
        elif answer.is_no():
            return True
        elif not answer.is_yes():
            for proposition in self._semantic_object.get_propositions():
                if self._semantic_logic.are_combinable(proposition, answer):
                    return True
        return False

    def is_resolved_by(self, answer):
        if self._semantic_object.is_goal_alts() and self._is_goal_proposition(answer):
            if self._some_goal_in_alts_dominates_goal(answer.get_goal()):
                return True
        if self._semantic_object.is_multi_alt():
            if answer.is_no():
                return True
            elif self._semantic_object.negate() == answer:
                return True
        if self._semantic_object.is_single_alt():
            return self._semantic_logic.resolves(self._semantic_object.get_single_alt(), answer)
        if (answer.is_proposition() or answer.is_individual()) \
           and answer.is_positive():
            return self.combine_with(answer) is not None
        return False

    def _is_goal_proposition(self, proposition):
        try:
            return proposition.is_goal_proposition()
        except AttributeError:
            pass
        return False

    def _some_goal_in_alts_dominates_goal(self, subgoal):
        for proposition in self._semantic_object._propositions:
            if proposition.is_goal_proposition():
                supergoal = proposition.get_goal()
                if self._has_domain() and self._domain.dominates(supergoal, subgoal):
                    return True
        return False

    def _has_domain(self):
        return self._semantic_object.is_ontology_specific()

    @property
    def _domain(self):
        ddd = self._ddd_manager.get_ddd_of_semantic_object(self._semantic_object)
        return ddd.domain

    def combine_with(self, answer):
        if self._semantic_object.is_single_alt():
            return self._semantic_logic.combine(self._semantic_object.get_single_alt(), answer)
        elif answer.is_no():
            return self._semantic_object.negate()
        elif not answer.is_yes():
            for proposition in self._semantic_object.get_propositions():
                if self._semantic_logic.are_combinable(proposition, answer):
                    return self._semantic_logic.combine(proposition, answer)

    def relevant(self, answer):
        if self._semantic_object.is_multi_alt() and answer.is_no():
            return True
        elif self._semantic_object.is_single_alt():
            return self._semantic_logic.is_relevant(self._semantic_object.get_single_alt(), answer)
        elif not answer.is_yes():
            for proposition in self._semantic_object.get_propositions():
                if self._semantic_logic.is_relevant(proposition, answer):
                    return True
        return False


class PreconfirmationPropositionLogic(PropositionLogic):
    TARGET_CLASS = PreconfirmationProposition

    def is_combinable_with(self, answer):
        if answer.is_yes() or answer.is_no():
            return True
        return False

    def combine_with(self, answer):
        if answer.is_yes():
            return self._semantic_object
        elif answer.is_no():
            return self._semantic_object.negate()


class UnderstandingPropositionLogic(PropositionLogic):
    TARGET_CLASS = UnderstandingProposition

    def is_combinable_with(self, answer):
        if answer.is_yes() or answer.is_no():
            return True
        else:
            return False

    def combine_with(self, answer):
        if answer.is_yes():
            return self._semantic_object
        if answer.is_no():
            return self._semantic_object.negate()


class KnowledgePreconditionQuestionLogic(PropositionLogic):
    TARGET_CLASS = KnowledgePreconditionQuestion

    def __init__(self, semantic_object, semantic_logic):
        SemanticObjectSpecificLogic.__init__(self, semantic_object)
        self._semantic_logic = semantic_logic

    def combine_with(self, answer):
        if answer.is_yes():
            return KnowledgePreconditionProposition(self._semantic_object.content, Polarity.POS)
        if answer.is_no():
            return KnowledgePreconditionProposition(self._semantic_object.content, Polarity.NEG)
        try:
            return self._semantic_logic.combine(self._semantic_object.content, answer)
        except (DomainError, OntologyError, AttributeError):
            pass

    def is_combinable_with(self, answer):
        if self.combine_with(answer):
            return True

    def relevant(self, answer):
        if self.combine_with(answer):
            return True


class ConsequentQuestionLogic(SemanticObjectAndOntologySpecificLogic):
    TARGET_CLASS = ConsequentQuestion

    def combine_with(self, answer):
        if answer.is_proposition() and answer.is_implication_proposition() and \
                answer.antecedent == self._semantic_object.content.antecedent and \
                answer.consequent.predicate == self._semantic_object.content.consequent_predicate:
            return answer

    def is_combinable_with(self, answer):
        if self.combine_with(answer):
            return True

    def relevant(self, answer):
        if self.combine_with(answer):
            return True

    def is_resolved_by(self, answer):
        if self.combine_with(answer):
            return True
