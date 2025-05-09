from tala.model.lambda_abstraction import (
    LambdaAbstractedPredicateProposition, LambdaAbstractedProposition, LambdaAbstractedGoalProposition
)
from tala.model.predicate import Predicate  # noqa
from tala.model.proposition import Proposition, PropositionSet
from tala.model.semantic_object import SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify


class Question(SemanticObjectWithContent, AsSemanticExpressionMixin):
    TYPE_WH = "WHQ"
    TYPE_YESNO = "YNQ"
    TYPE_ALT = "ALTQ"
    TYPE_KPQ = "KPQ"
    TYPE_CONSEQUENT = "CONSEQUENT"

    TYPES = [TYPE_WH, TYPE_YESNO, TYPE_ALT, TYPE_KPQ, TYPE_CONSEQUENT]

    @classmethod
    def create_from_json_api_data(cls, question_data, included):
        class_name = question_data["type"].rsplit(".", 1)[-1]
        target_cls = globals().get(class_name)

        if target_cls is not None:
            return target_cls.create_from_json_api_data(question_data, included)
        raise Exception(f"cannot instantiate object of class {class_name}")

    def __init__(self, type_, content):
        SemanticObjectWithContent.__init__(self, content)
        self._type = type_
        self._content = content

    def __eq__(self, other):
        try:
            equality = self.type_ == other.type_ and self.content == other.content
            return equality
        except AttributeError:
            return False

    @property
    def json_api_id(self):
        if self.is_ontology_specific():
            return f"{self.ontology_name}:{self.type_}:{self.content}"
        else:
            return f"{self.type_}:{self.content}"

    @property
    def json_api_attributes(self):
        if self.is_ontology_specific() and self.ontology_name:
            return ["ontology_name", "type_"]
        else:
            return ["type_"]

    @property
    def json_api_relationships(self):
        return ["content"]

    def __hash__(self):
        return hash((self._content, self._type))

    def is_question(self):
        return True

    def is_action_question(self):
        if self.is_wh_question():
            try:
                return self.content.is_lambda_abstracted_goal_proposition()
            except AttributeError:
                return False
        elif self.is_alt_question():
            for alt in self.content:
                if (alt.is_goal_proposition() and alt.get_goal().type_ == "PERFORM_GOAL"):
                    return True
        elif self.is_yes_no_question():
            return self.content.is_goal_proposition()

    def is_wh_question(self):
        return self._type == self.TYPE_WH

    def is_yes_no_question(self):
        return self._type == self.TYPE_YESNO

    def is_alt_question(self):
        return self._type == self.TYPE_ALT

    def is_knowledge_precondition_question(self):
        return self._type == self.TYPE_KPQ

    def is_consequent_question(self):
        return self._type == self.TYPE_CONSEQUENT

    def is_understanding_question(self):
        return (self._type == self.TYPE_YESNO and self._content.is_understanding_proposition())

    def is_preconfirmation_question(self):
        return (self._type == self.TYPE_YESNO and self._content.is_preconfirmation_proposition())

    @property
    def sort(self):
        return self.predicate.sort

    @property
    def content(self):
        return self._content

    @property
    def type_(self):
        return self._type

    @property
    def predicate(self):
        return self.content.predicate

    def __str__(self):
        return "?" + unicodify(self.content)


class WhQuestion(Question):
    @classmethod
    def create_from_json_api_data(cls, lambda_abstraction_data, included):
        lambda_abstraction_entry = included.get_object_from_relationship(
            lambda_abstraction_data["relationships"]["content"]["data"]
        )
        if lambda_abstraction_entry["type"].endswith(
            LambdaAbstractedProposition.LAMBDA_ABSTRACTED_PREDICATE_PROPOSITION
        ):
            lambda_abstraction = LambdaAbstractedPredicateProposition.create_from_json_api_data(
                lambda_abstraction_entry, included
            )
            return cls(lambda_abstraction)
        if lambda_abstraction_entry["type"].endswith(LambdaAbstractedProposition.LAMBDA_ABSTRACTED_GOAL_PROPOSITION):
            return cls(LambdaAbstractedGoalProposition())
        raise NotImplementedError(f'{lambda_abstraction_entry["type"]} is not implemented')

    def __init__(self, lambda_abstraction):
        Question.__init__(self, Question.TYPE_WH, lambda_abstraction)

    def __repr__(self):
        return "WhQuestion(%r)" % self._content


class AltQuestion(Question):
    @classmethod
    def create_from_json_api_data(cls, question_data, included):
        propositions = included.get_object_from_relationship(question_data["relationships"]["content"]["data"])
        proposition_set = PropositionSet.create_from_json_api_data(propositions, included)
        return cls(proposition_set)

    def __init__(self, proposition_set):
        Question.__init__(self, Question.TYPE_ALT, proposition_set)

    def __str__(self):
        if self._contains_single_predicate():
            return "?X.%s(X), %s" % (self._predicate(), self._content)
        else:
            return Question.__str__(self)

    def _contains_single_predicate(self):
        predicates = {alt.predicate for alt in self._content if alt.is_predicate_proposition()}
        return len(predicates) == 1

    def _predicate(self):
        return list(self._content)[0].predicate


class YesNoQuestion(Question):
    @classmethod
    def create_from_json_api_data(cls, question_data, included):
        proposition_entry = included.get_object_from_relationship(question_data["relationships"]["content"]["data"])
        proposition = Proposition.create_from_json_api_data(proposition_entry, included)
        return cls(proposition)

    def __init__(self, proposition):
        Question.__init__(self, Question.TYPE_YESNO, proposition)


class KnowledgePreconditionQuestion(Question):
    def __init__(self, question):
        Question.__init__(self, Question.TYPE_KPQ, question)

    def __str__(self):
        return f"?know_answer({self.content})"


class ConsequentQuestion(Question):
    def __init__(self, lambda_abstracted_implication_proposition):
        Question.__init__(self, Question.TYPE_CONSEQUENT, lambda_abstracted_implication_proposition)

    def get_embedded_consequent_question(self):
        consequent_predicate = self.content.consequent_predicate
        lambda_abstracted_consequent_proposition = LambdaAbstractedPredicateProposition(
            consequent_predicate, consequent_predicate.ontology_name
        )
        return WhQuestion(lambda_abstracted_consequent_proposition)
