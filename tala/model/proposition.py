import warnings
import copy

from tala.model.error import OntologyError
from tala.model.move import AnswerMove
from tala.model.polarity import Polarity
from tala.model.semantic_object import SemanticObject, OntologySpecificSemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify


class PropositionsFromDifferentOntologiesException(Exception):
    pass


class UnexpectedGoalException(Exception):
    pass


class MissingIndividualException(Exception):
    pass


class Proposition(SemanticObject, AsSemanticExpressionMixin):
    UNDERSTANDING = "UNDERSTANDING"
    GOAL = "GOAL"
    PREDICATE = "PREDICATE"
    PRECONFIRMATION = "PRECONFIRMATION"
    PREREPORT = "PREREPORT"
    MUTE = "MUTE"
    UNMUTE = "UNMUTE"
    QUIT = "QUIT"
    PREDICTED = "PREDICTED"
    REJECTED = "REJECTED"
    RESOLVEDNESS = "RESOLVEDNESS"
    SERVICE_RESULT = "SERVICE_RESULT"
    SERVICE_ACTION_STARTED = "SERVICE_ACTION_STARTED"
    SERVICE_ACTION_TERMINATED = "SERVICE_ACTION_TERMINATED"
    PROPOSITION_SET = "PROPOSITION_SET"
    KNOWLEDGE_PRECONDITION = "KNOWLEDGE_PRECONDITION"
    ACTION_STATUS = "ACTION_STATUS"
    QUESTION_STATUS = "QUESTION_STATUS"
    IMPLICATION = "IMPLICATION"
    NUMBER_OF_ALTERNATIVES = "NUMBER_OF_ALTERNATIVES"

    TYPES = [
        UNDERSTANDING,
        GOAL,
        PREDICATE,
        PRECONFIRMATION,
        PREREPORT,
        MUTE,
        UNMUTE,
        QUIT,
        PREDICTED,
        REJECTED,
        RESOLVEDNESS,
        SERVICE_RESULT,
        SERVICE_ACTION_STARTED,
        SERVICE_ACTION_TERMINATED,
        PROPOSITION_SET,
        KNOWLEDGE_PRECONDITION,
        ACTION_STATUS,
        QUESTION_STATUS,
        IMPLICATION,
        NUMBER_OF_ALTERNATIVES
    ]  # yapf: disable

    def __init__(self, type, polarity=None):
        SemanticObject.__init__(self)
        self._type = type
        if polarity is None:
            polarity = Polarity.POS
        self._polarity = polarity
        self._predicted = False
        self._confidence_estimates = None

    def __eq__(self, other):
        try:
            return other.is_proposition() and self.type_ == other.type_ and self.polarity == other.polarity
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.type_, self.polarity))

    @property
    def confidence_estimates(self):
        return self._confidence_estimates

    @confidence_estimates.setter
    def confidence_estimates(self, confidence):
        self._confidence_estimates = confidence

    @property
    def polarity_prefix(self):
        if self._polarity == Polarity.NEG:
            return "~"
        else:
            return ""

    def get_type(self):
        return self.type_

    @property
    def type_(self):
        return self._type

    def is_proposition(self):
        return True

    def is_understanding_proposition(self):
        return self._type == Proposition.UNDERSTANDING

    def is_predicate_proposition(self):
        return self._type == Proposition.PREDICATE

    def is_preconfirmation_proposition(self):
        return self._type == Proposition.PRECONFIRMATION

    def is_prereport_proposition(self):
        return self._type == Proposition.PREREPORT

    def is_service_result_proposition(self):
        return self._type == Proposition.SERVICE_RESULT

    def is_mute_proposition(self):
        return self._type == Proposition.MUTE

    def is_unmute_proposition(self):
        return self._type == Proposition.UNMUTE

    def is_quit_proposition(self):
        return self._type == Proposition.QUIT

    def is_goal_proposition(self):
        return self._type == Proposition.GOAL

    def is_rejected_proposition(self):
        return self._type == Proposition.REJECTED

    def is_resolvedness_proposition(self):
        return self._type == Proposition.RESOLVEDNESS

    def is_service_action_started_proposition(self):
        return self._type == Proposition.SERVICE_ACTION_STARTED

    def is_service_action_terminated_proposition(self):
        return self._type == Proposition.SERVICE_ACTION_TERMINATED

    def is_predicted_proposition(self):
        return self._type == Proposition.PREDICTED

    def is_knowledge_precondition_proposition(self):
        return self._type == Proposition.KNOWLEDGE_PRECONDITION

    def is_implication_proposition(self):
        return self._type == Proposition.IMPLICATION

    def is_number_of_alternatives_proposition(self):
        return self._type == Proposition.NUMBER_OF_ALTERNATIVES

    def get_polarity(self):
        return self.polarity

    @property
    def polarity(self):
        return self._polarity

    def is_positive(self):
        return self.polarity == Polarity.POS

    def is_predicted(self):
        return self._predicted

    def negate(self):
        proposition_copy = copy.copy(self)
        if proposition_copy.is_positive():
            proposition_copy._polarity = Polarity.NEG
        else:
            proposition_copy._polarity = Polarity.POS
        return proposition_copy

    def is_incompatible_with(self, other):
        return False

    def is_true_given_proposition_set(self, facts):
        return self in facts

    def __repr__(self):
        return "%s%s" % (Proposition.__name__, (self._type, self._polarity))


class PropositionWithSemanticContent(Proposition, SemanticObjectWithContent):
    def __init__(self, type_, content, polarity=None):
        Proposition.__init__(self, type_, polarity)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    @property
    def content(self):
        return self._content

    def __eq__(self, other):
        try:
            return other.is_proposition() and \
                other.has_semantic_content() and \
                self.content == other.content and \
                self.type_ == other.type_ \
                and self.polarity == other.polarity
        except AttributeError:
            return False

    def __repr__(self):
        return "%s%s" % (PropositionWithSemanticContent.__name__, (self._type, self.content, self._polarity))


class ControlProposition(Proposition):
    def __init__(self, type, polarity=None):
        Proposition.__init__(self, type, polarity)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self._type

    def __hash__(self):
        return self._type.__hash__()


class MuteProposition(ControlProposition):
    def __init__(self=None):
        Proposition.__init__(self, Proposition.MUTE)


class UnmuteProposition(ControlProposition):
    def __init__(self=None):
        Proposition.__init__(self, Proposition.UNMUTE)


class QuitProposition(ControlProposition):
    def __init__(self=None):
        Proposition.__init__(self, Proposition.QUIT)


class PredicateProposition(PropositionWithSemanticContent):
    def __init__(self, predicate, individual=None, polarity=None, predicted=False):
        if polarity is None:
            polarity = Polarity.POS
        PropositionWithSemanticContent.__init__(self, Proposition.PREDICATE, predicate, polarity=polarity)
        self.predicate = predicate
        self.individual = individual
        self._predicted = predicted
        if individual is not None and individual.sort != predicate.sort:
            raise OntologyError(("Sortal mismatch between predicate %s " + "(sort %s) and individual %s (sort %s)") %
                                (predicate, predicate.sort, individual, individual.sort))

    def as_move(self):
        if self.individual is None:
            raise MissingIndividualException(f"Expected an individual but got none for {self!r}")
        return AnswerMove(self)

    def get_predicate(self):
        warnings.warn(
            "Proposition.get_predicate() is deprecated. Use Proposition.predicate instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.predicate

    def getPredicate(self):
        warnings.warn(
            "Proposition.getPredicate() is deprecated. Use Proposition.predicate instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_predicate()

    def getArgument(self):
        warnings.warn(
            "Proposition.getArgument() is deprecated. Use Proposition.individual instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.individual

    def is_incompatible_with(self, other):
        if self.negate() == other:
            return True

        if self._proposes_other_individual_of_same_predicate(other) and not self.predicate.allows_multiple_instances():
            return True

        if self._is_feature_of_the_following_negative_proposition(other):
            return True

        if self._polarity == Polarity.NEG and self._is_feature(other):
            return True

        return False

    def _proposes_other_individual_of_same_predicate(self, other):
        return other.is_predicate_proposition() \
            and self.predicate == other.predicate \
            and self.is_positive() \
            and other.is_positive() \
            and self.individual != other.individual

    def _is_feature_of_the_following_negative_proposition(self, other):
        return (
            other.is_predicate_proposition() and self.predicate.is_feature_of(other.predicate)
            and other.polarity == Polarity.NEG
        )

    def _is_feature(self, answer):
        return (answer.is_predicate_proposition() and answer.predicate.is_feature_of(self.predicate))

    def __eq__(self, other):
        try:
            return other is not None and other.is_proposition() and other.is_predicate_proposition(
            ) and self.predicate == other.predicate and self.individual == other.individual and self.polarity == other.polarity
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        if self.individual is None:
            return f"{self.polarity_prefix}{self.predicate}"
        else:
            return f"{self.polarity_prefix}{self.predicate}({self.individual})"

    def __hash__(self):
        return hash((self.predicate, self.individual, self.polarity))

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.predicate, self.individual, self._polarity, self._predicted))


class GoalProposition(PropositionWithSemanticContent):
    def __init__(self, goal, polarity=None):
        PropositionWithSemanticContent.__init__(self, Proposition.GOAL, goal, polarity=polarity)
        self._goal = goal

    def as_move(self):
        if self._goal.is_goal_with_semantic_content():
            return self._goal.as_move()
        raise UnexpectedGoalException(f"Expected goal with semantic content, but got {self._goal!r}")

    def get_goal(self):
        return self._goal

    def __eq__(self, other):
        try:
            return other.is_proposition() and other.is_goal_proposition() and self._goal == other.get_goal(
            ) and self._polarity == other.polarity
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "%sgoal(%s)" % (self.polarity_prefix, self._goal)

    def __hash__(self):
        return hash((self._goal, self._polarity))


class PreconfirmationProposition(Proposition, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, arguments, polarity=None):
        self.service_action = service_action
        self._arguments = arguments
        Proposition.__init__(self, Proposition.PRECONFIRMATION, polarity)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def get_service_action(self):
        return self.service_action

    def get_arguments(self):
        argument_list = []
        for param in self._arguments:
            argument_list.append(param)
        return argument_list

    @property
    def arguments(self):
        return self.get_arguments()

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_preconfirmation_proposition()
                and other.ontology_name == self.ontology_name and other.type_ == self.type_
                and other.get_service_action() == self.get_service_action() and other.polarity == self.polarity
                and other.get_arguments() == self.get_arguments()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "%spreconfirmed(%s, %s)" % (self.polarity_prefix, str(self.service_action), unicodify(self._arguments))

    def __hash__(self):
        return hash((self.service_action, frozenset(self.arguments)))

    def as_dict(self):
        result = {
            "arguments": [proposition for proposition in self.arguments],
            "service_action": self.service_action,
            "polarity": self.polarity
        }
        ontology_specific_dict = OntologySpecificSemanticObject.as_dict(self)
        return ontology_specific_dict | result


class PrereportProposition(Proposition, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, argument_list):
        self.service_action = service_action
        self.argument_set = frozenset(argument_list)
        Proposition.__init__(self, Proposition.PREREPORT)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def get_service_action(self):
        return self.service_action

    def get_arguments(self):
        argument_list = []
        for param in self.argument_set:
            argument_list.append(param)
        return argument_list

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_prereport_proposition()
                and other.ontology_name == self.ontology_name
                and other.get_service_action() == self.get_service_action() and other.polarity == self.polarity
                and other.argument_set == self.argument_set
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.ontology_name, self.service_action, self.argument_set))

    def __str__(self):
        return "prereported(%s, %s)" % (str(self.service_action), str(self.get_arguments()))

    def as_dict(self):
        result = {
            "argument_set": [proposition for proposition in self.argument_set],
        }
        return super().as_dict() | result


class ServiceActionTerminatedProposition(Proposition, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, polarity=None):
        self.service_action = service_action
        Proposition.__init__(self, Proposition.SERVICE_ACTION_TERMINATED, polarity)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def get_service_action(self):
        return self.service_action

    def __str__(self):
        return "%sservice_action_terminated(%s)" % (self.polarity_prefix, str(self.service_action))

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_service_action_terminated_proposition()
                and other.ontology_name == self.ontology_name
                and other.get_service_action() == self.get_service_action() and other.polarity == self.polarity
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.service_action)

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.ontology_name, self.service_action, self.polarity)


class PredictedProposition(PropositionWithSemanticContent):
    def __init__(self, prediction, polarity=None):
        PropositionWithSemanticContent.__init__(self, Proposition.PREDICTED, prediction, polarity)

    def __str__(self):
        return "%spredicted(%s)" % (self.polarity_prefix, self.prediction)

    def __eq__(self, other):
        try:
            return other.is_proposition() \
                and other.is_predicted_proposition() \
                and other.prediction == self.prediction \
                and other.polarity == self.polarity
        except AttributeError:
            return False

    @property
    def prediction(self):
        return self.content

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.type_, self.prediction))


class ServiceResultProposition(Proposition, OntologySpecificSemanticObject):
    STARTED = "STARTED"
    ENDED = "ENDED"

    def __init__(self, ontology_name, service_action, arguments, result, status=None):
        self.service_action = service_action
        self.arguments = arguments
        self.result = result
        self._manage_status(status)
        Proposition.__init__(self, Proposition.SERVICE_RESULT)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def _manage_status(self, status):
        if not status:
            self.status = ServiceResultProposition.ENDED
        else:
            self.status = status

    def get_service_action(self):
        return self.service_action

    def get_arguments(self):
        return self.arguments

    def get_result(self):
        return self.result

    def get_status(self):
        return self.status

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_service_result_proposition()
                and other.get_service_action() == self.get_service_action()
                and other.get_arguments() == self.get_arguments() and other.get_result() == self.get_result()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "ServiceResultProposition(%s, %s, %s)" % (self.service_action, unicodify(self.arguments), self.result)

    def __hash__(self):
        return hash((self.get_service_action(), self.get_result()))

    def as_dict(self):
        result = {"result": self.result.as_json(), "ontology_name": self.ontology_name}
        return super().as_dict() | result


class ServiceActionStartedProposition(Proposition, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, parameters=None):
        if parameters is None:
            parameters = []
        self.service_action = service_action
        self.parameters = parameters
        Proposition.__init__(self, Proposition.SERVICE_ACTION_STARTED)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_service_action_started_proposition()
                and other.ontology_name == self.ontology_name and other.service_action == self.service_action
                and other.polarity == self.polarity
            )
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.ontology_name, self.service_action, self.polarity))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "ServiceActionStartedProposition(%s, %s)" % (self.service_action, unicodify(self.parameters))

    def as_dict(self):
        result = {
            "service_action": self.service_action,
            "parameters": self.parameters,
            "ontology_name": self.ontology_name
        }
        return super().as_dict() | result


class RejectedPropositions(PropositionWithSemanticContent):
    def __init__(self, rejected_combination, polarity=None, reason=None):
        self.rejected_combination = rejected_combination
        self.reason_for_rejection = reason
        PropositionWithSemanticContent.__init__(self, Proposition.REJECTED, rejected_combination, polarity)

    def get_rejected_combination(self):
        return self.rejected_combination

    def get_reason(self):
        return self.reason_for_rejection

    def __str__(self):
        if self.reason_for_rejection:
            return "%srejected(%s, %s)" % (self.polarity_prefix, self.rejected_combination, self.reason_for_rejection)
        else:
            return "%srejected(%s)" % (self.polarity_prefix, str(self.rejected_combination))

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_rejected_proposition()
                and other.get_rejected_combination() == self.get_rejected_combination()
                and other.get_reason() == self.get_reason() and other.polarity == self.polarity
            )
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.rejected_combination, self.reason_for_rejection, self.polarity))

    def __ne__(self, other):
        return not (self == other)


class PropositionSet(Proposition):
    def __init__(self, propositions, polarity=Polarity.POS):
        self._propositions = propositions
        self._hash = hash(frozenset(propositions))
        Proposition.__init__(self, Proposition.PROPOSITION_SET, polarity)

    def is_proposition_set(self):
        return True

    def __iter__(self):
        return self._propositions.__iter__()

    def __hash__(self):
        return self._hash

    def get_propositions(self):
        return self._propositions

    def unicode_propositions(self):
        return "[%s]" % ", ".join([str(proposition) for proposition in self._propositions])

    def is_single_alt(self):
        return len(self._propositions) == 1

    def is_multi_alt(self):
        return len(self._propositions) > 1

    def get_single_alt(self):
        for proposition in self._propositions:
            return proposition

    def is_goal_alts(self):
        for proposition in self._propositions:
            if proposition.is_goal_proposition():
                return True
        return False

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_proposition_set() and self.polarity == other.polarity
                and self.get_propositions() == other.get_propositions()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "%sset(%s)" % (self.polarity_prefix, self.unicode_propositions())

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self._propositions, self._polarity)

    @property
    def predicate(self):
        predicates = {proposition.predicate for proposition in self._propositions}
        if len(predicates) == 1:
            return list(predicates)[0]
        else:
            raise Exception("cannot get predicate for proposition set with zero or mixed predicates")

    def getPredicate(self):
        warnings.warn(
            "PropositionSet.getPredicate() is deprecated. Use PropositionSet.predicate instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.predicate

    def is_ontology_specific(self):
        if not all([proposition.is_ontology_specific() for proposition in self._propositions]):
            return False
        if not any([proposition.is_ontology_specific() for proposition in self._propositions]):
            return False
        return self._all_propositions_from_same_ontology()

    def _all_propositions_from_same_ontology(self):
        first_ontology_name = self._ontology_names[0]
        return all([name == first_ontology_name for name in self._ontology_names])

    @property
    def ontology_name(self):
        if self.is_ontology_specific() and self._all_propositions_from_same_ontology:
            return self._propositions[0].ontology_name

        message = "Expected all propositions %s\n\nin ontology %s\n\nbut they're from %s" % (
            self._propositions, self._propositions[0].ontology_name, self._ontology_names
        )
        raise PropositionsFromDifferentOntologiesException(message)

    @property
    def _ontology_names(self):
        ontology_names = [proposition.ontology_name for proposition in self._propositions]
        return ontology_names

    def has_semantic_content(self):
        return True


class UnderstandingProposition(PropositionWithSemanticContent):
    def __init__(self, speaker, content, polarity=Polarity.POS):
        PropositionWithSemanticContent.__init__(self, Proposition.UNDERSTANDING, content, polarity=polarity)
        self._speaker = speaker
        self._content = content

    def get_speaker(self):
        return self._speaker

    def get_content(self):
        return self._content

    @property
    def speaker(self):
        return self._speaker

    def __str__(self):
        return "und(%s, %s)" % (str(self._speaker), str(self._content))

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_understanding_proposition()
                and self.get_speaker() == other.get_speaker() and self.get_content() == other.get_content()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self._content, self._speaker))


class ResolvednessProposition(PropositionWithSemanticContent):
    def __init__(self, issue):
        self.issue = issue
        PropositionWithSemanticContent.__init__(self, Proposition.RESOLVEDNESS, issue)

    def get_issue(self):
        return self.issue

    def __str__(self):
        return "resolved(%s)" % self.issue

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_resolvedness_proposition() and other.get_issue() == self.get_issue()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.get_issue())


class KnowledgePreconditionProposition(PropositionWithSemanticContent):
    def __init__(self, question, polarity):
        PropositionWithSemanticContent.__init__(self, Proposition.KNOWLEDGE_PRECONDITION, question, polarity)

    @property
    def embedded_question(self):
        return self.content

    def __eq__(self, other):
        try:
            return (
                other.is_proposition() and other.is_knowledge_precondition_proposition()
                and other.embedded_question == self.embedded_question and other.polarity == self.polarity
            )
        except AttributeError:
            return False

    def __str__(self):
        return f"{self.polarity_prefix}know_answer({self.embedded_question})"

    def __hash__(self):
        return hash(self.embedded_question)


class ActionStatusProposition(PropositionWithSemanticContent):
    def __init__(self, action, status):
        PropositionWithSemanticContent.__init__(self, Proposition.ACTION_STATUS, action)
        self._status = status

    @property
    def status(self):
        return self._status

    @property
    def action(self):
        return self.content

    def __eq__(self, other):
        try:
            return (other.content == self.content and other.status == self.status and self.type_ == other.type_)
        except AttributeError:
            return False

    def __str__(self):
        return f"action_status({self.content}, {self.status})"

    def __hash__(self):
        return hash((self.content, self.status))


class QuestionStatusProposition(PropositionWithSemanticContent):
    def __init__(self, question, status):
        PropositionWithSemanticContent.__init__(self, Proposition.QUESTION_STATUS, question)
        self._status = status

    @property
    def status(self):
        return self._status

    def __eq__(self, other):
        try:
            return (other.content == self.content and other.status == self.status and self.type_ == other.type_)
        except AttributeError:
            return False

    def __str__(self):
        return f"question_status({self.content}, {self.status})"

    def __hash__(self):
        return hash((self.content, self.status))


class ImplicationProposition(PropositionWithSemanticContent):
    def __init__(self, antecedent, consequent):
        self._antecedent = antecedent
        self._consequent = consequent
        PropositionWithSemanticContent.__init__(self, Proposition.IMPLICATION, (antecedent, consequent))

    @property
    def antecedent(self):
        return self._antecedent

    @property
    def consequent(self):
        return self._consequent

    def is_ontology_specific(self):
        return True

    @property
    def ontology_name(self):
        return self._antecedent.ontology_name

    def __eq__(self, other):
        try:
            return (other.antecedent == self.antecedent and other.consequent == self.consequent)
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(tuple(self.__dict__.items()))

    def __repr__(self):
        return "implies(%s, %s)" % (self.antecedent, self.consequent)

    def __str__(self):
        return repr(self)


class NumberOfAlternativesProposition(PropositionWithSemanticContent):
    def __init__(self, content):
        PropositionWithSemanticContent.__init__(self, Proposition.NUMBER_OF_ALTERNATIVES, content)

    def __repr__(self):
        return f"{self.polarity_prefix}number_of_alternatives({self._content})"

    def __str__(self):
        return repr(self)
