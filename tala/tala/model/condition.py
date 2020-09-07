class Condition():

    HAS_VALUE = "HAS_VALUE"
    IS_SHARED_FACT = "IS_SHARED_FACT"

    def __init__(self, type):
        self._type = type

    @property
    def condition_type(self):
        return self._type

    def is_true_given(self, _):
        return False

    def __eq__(self, other):
        try:
            return self.condition_type == other.condition_type
        except AttributeError:
            return False

    def __repr__(self):
        return "Condition()"


class HasValue(Condition):
    def __init__(self, predicate):
        super().__init__(Condition.HAS_VALUE)
        self._predicate = predicate

    @property
    def predicate(self):
        return self._predicate

    def is_true_given(self, proposition_set):
        for proposition in proposition_set:
            try:
                if proposition.get_predicate() == self.predicate:
                    return True
            except AttributeError:
                pass
        return False

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.predicate == other.predicate
        except AttributeError:
            return False

    def __repr__(self):
        return "HasValue({})".format(self.predicate)


class IsSharedFact(Condition):
    def __init__(self, proposition):
        super().__init__(Condition.IS_SHARED_FACT)
        self._proposition = proposition

    @property
    def proposition(self):
        return self._proposition

    def is_true_given(self, proposition_set):
        return self.proposition in proposition_set

    def __eq__(self, other):
        return super().__eq__(other) and self.proposition == other.proposition and super().__eq__(other)

    def __repr__(self):
        return "IsSharedFact({})".format(self.proposition)
