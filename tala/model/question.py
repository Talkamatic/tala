import warnings

from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.semantic_object import SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify
from tala.model.goal import PERFORM


class Question(SemanticObjectWithContent, AsSemanticExpressionMixin):
    TYPE_WH = "WHQ"
    TYPE_YESNO = "YNQ"
    TYPE_ALT = "ALTQ"
    TYPE_KPQ = "KPQ"
    TYPE_CONSEQUENT = "CONSEQUENT"

    TYPES = [TYPE_WH, TYPE_YESNO, TYPE_ALT, TYPE_KPQ, TYPE_CONSEQUENT]

    def __init__(self, type, content):
        SemanticObjectWithContent.__init__(self, content)
        self._type = type
        self._content = content

    def __eq__(self, other):
        try:
            equality = self.type_ == other.type_ and self.content == other.content
            return equality
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

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
                if (alt.is_goal_proposition() and alt.get_goal().type_ == PERFORM):
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

    def get_sort(self):
        warnings.warn("Question.get_sort() is deprecated. Use Question.sort instead.", DeprecationWarning, stacklevel=2)
        return self.sort

    @property
    def content(self):
        return self._content

    def get_content(self):
        warnings.warn(
            "Question.get_content() is deprecated. Use Question.content instead.", DeprecationWarning, stacklevel=2
        )
        return self.content

    @property
    def type_(self):
        return self._type

    def get_type(self):
        warnings.warn(
            "Question.get_predicate() is deprecated. Use Question.predicate instead.", DeprecationWarning, stacklevel=2
        )
        return self.type_

    @property
    def predicate(self):
        return self.content.predicate

    def get_predicate(self):
        warnings.warn(
            "Question.get_predicate() is deprecated. Use Question.predicate instead.", DeprecationWarning, stacklevel=2
        )
        return self.predicate

    def __str__(self):
        return "?" + unicodify(self._content)


class WhQuestion(Question):
    def __init__(self, lambda_abstraction):
        Question.__init__(self, Question.TYPE_WH, lambda_abstraction)

    def __repr__(self):
        return "WhQuestion(%r)" % self._content


class AltQuestion(Question):
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
