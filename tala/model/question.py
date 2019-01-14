from tala.model.semantic_object import SemanticObjectWithContent
from tala.utils.unicodify import unicodify


class Question(SemanticObjectWithContent):
    TYPE_WH = "WHQ"
    TYPE_YESNO = "YNQ"
    TYPE_ALT = "ALTQ"

    def __init__(self, type, content):
        SemanticObjectWithContent.__init__(self, content)
        self._type = type
        self._content = content

    def __eq__(self, other):
        try:
            return self.get_type() == other.get_type() and self.get_content() == other.get_content()
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self._content, self._type))

    def is_question(self):
        return True

    def is_wh_question(self):
        return self._type == self.TYPE_WH

    def is_yes_no_question(self):
        return self._type == self.TYPE_YESNO

    def is_alt_question(self):
        return self._type == self.TYPE_ALT

    def is_understanding_question(self):
        return (self._type == self.TYPE_YESNO and self._content.is_understanding_proposition())

    def is_preconfirmation_question(self):
        return (self._type == self.TYPE_YESNO and self._content.is_preconfirmation_proposition())

    def get_sort(self):
        predicate = self.get_predicate()
        return predicate.getSort()

    def get_content(self):
        return self._content

    def get_type(self):
        return self._type

    def get_predicate(self):
        return self._content.getPredicate()

    def __unicode__(self):
        return "?" + unicodify(self._content)


class WhQuestion(Question):
    def __init__(self, lambda_abstraction):
        Question.__init__(self, Question.TYPE_WH, lambda_abstraction)


class AltQuestion(Question):
    def __init__(self, proposition_set):
        Question.__init__(self, Question.TYPE_ALT, proposition_set)

    def __unicode__(self):
        if self._contains_single_predicate():
            return "?X.%s(X), %s" % (self._predicate(), self._content)
        else:
            return Question.__unicode__(self)

    def _contains_single_predicate(self):
        predicates = set([alt.getPredicate() for alt in self._content if alt.is_predicate_proposition()])
        return len(predicates) == 1

    def _predicate(self):
        return list(self._content)[0].getPredicate()


class YesNoQuestion(Question):
    def __init__(self, proposition):
        Question.__init__(self, Question.TYPE_YESNO, proposition)
