from tala.model.semantic_object import SemanticObject

HAS_VALUE = "HasValue"
IS_TRUE = "IsTrue"
HAS_SHARED_VALUE = "HasSharedValue"
HAS_PRIVATE_VALUE = "HasPrivateValue"
HAS_SHARED_OR_PRIVATE_VALUE = "HasSharedOrPrivateValue"
IS_SHARED_COMMITMENT = "IsSharedCommitment"
IS_PRIVATE_BELIEF = "IsPrivateBelief"
IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT = "IsPrivateBeliefOrSharedCommitment"
QUERY_HAS_MORE_ITEMS = "QueryHasMoreItems"

SEMANTIC_OBJECT_TYPE = "condition"


def create_condition(type_, parameter):
    if type_ == HAS_SHARED_VALUE:
        return HasSharedValue(parameter)
    if type_ == HAS_PRIVATE_VALUE:
        return HasPrivateValue(parameter)
    if type_ == HAS_SHARED_OR_PRIVATE_VALUE:
        return HasSharedOrPrivateValue(parameter)
    if type_ == IS_SHARED_COMMITMENT:
        return IsSharedCommitment(parameter)
    if type_ == IS_PRIVATE_BELIEF:
        return IsPrivateBelief(parameter)
    if type_ == IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT:
        return IsPrivateBeliefOrSharedCommitment(parameter)
    if type_ == QUERY_HAS_MORE_ITEMS:
        return QueryHasMoreItems(parameter)
    if type_ == HAS_VALUE:
        return HasValue(parameter)
    if type_ == IS_TRUE:
        return IsTrue(parameter)


class Condition(SemanticObject):
    def __init__(self, type_):
        self._type = type_

    @property
    def condition_type(self):
        return self._type

    def is_has_value_condition(self):
        return self.condition_type in [HAS_VALUE, HAS_SHARED_VALUE, HAS_PRIVATE_VALUE, HAS_SHARED_OR_PRIVATE_VALUE]

    def is_is_true_condition(self):
        return self.condition_type in [
            IS_TRUE, IS_SHARED_COMMITMENT, IS_PRIVATE_BELIEF, IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT
        ]

    def is_true_given_proposition_set(self, _):
        return False

    def __eq__(self, other):
        try:
            return self.condition_type == other.condition_type
        except AttributeError:
            return False

    def __repr__(self):
        return "Condition()"

    def as_dict(self):
        result = {"semantic_object_type": SEMANTIC_OBJECT_TYPE, "type": self.condition_type}
        return super().as_dict() | result


class HasValue(Condition):
    def __init__(self, predicate, type_=HAS_VALUE):
        super().__init__(type_)
        self._predicate = predicate

    @property
    def predicate(self):
        return self._predicate

    def is_true_given_proposition_set(self, proposition_set):
        for proposition in proposition_set:
            try:
                if proposition.get_predicate() == self.predicate:
                    return True
            except AttributeError:
                pass
        return False

    def __eq__(self, other):
        try:
            equality = super().__eq__(other) and self.predicate == other.predicate
            return equality
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.predicate)


class HasSharedValue(HasValue):
    def __init__(self, predicate):
        super().__init__(predicate, HAS_SHARED_VALUE)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.shared.com)


class HasPrivateValue(HasValue):
    def __init__(self, predicate):
        super().__init__(predicate, HAS_PRIVATE_VALUE)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel)


class HasSharedOrPrivateValue(HasValue):
    def __init__(self, predicate):
        super().__init__(predicate, HAS_SHARED_OR_PRIVATE_VALUE)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel
                                                     ) or super().is_true_given_proposition_set(tis.shared.com)


class IsTrue(Condition):
    def __init__(self, proposition, type_=IS_TRUE):
        super().__init__(type_)
        self._proposition = proposition

    @property
    def proposition(self):
        return self._proposition

    def is_true_given_proposition_set(self, proposition_set):
        return self.proposition in proposition_set

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.proposition == other.proposition
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.proposition)


class IsSharedCommitment(IsTrue):
    def __init__(self, proposition):
        super().__init__(proposition, IS_SHARED_COMMITMENT)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.shared.com)


class IsPrivateBelief(IsTrue):
    def __init__(self, proposition):
        super().__init__(proposition, IS_PRIVATE_BELIEF)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel)


class IsPrivateBeliefOrSharedCommitment(IsTrue):
    def __init__(self, proposition):
        super().__init__(proposition, IS_PRIVATE_BELIEF_OR_SHARED_COMMITMENT)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel
                                                     ) or super().is_true_given_proposition_set(tis.shared.com)


class QueryHasMoreItems(Condition):
    def __init__(self, query, type_=QUERY_HAS_MORE_ITEMS):
        super().__init__(type_)
        self._query = query

    @property
    def query(self):
        return self._query

    def is_true_given_tis(self, tis):
        no_more_elements = tis.iterator_has_no_more_elements(self.query)
        reached_limit = tis.iterator_has_reached_limit(self.query)
        result = not (no_more_elements or reached_limit)
        return result

    def __eq__(self, other):
        try:
            equality = super().__eq__(other) and self.query == other.query
            return equality
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.query)
