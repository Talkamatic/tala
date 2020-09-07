class RequiredEntity(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def is_propositional(self):
        return False

    @property
    def is_sortal(self):
        return False

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._name)

    def __eq__(self, other):
        return bool(isinstance(other, self.__class__) and self._name == other.name)

    def __hash__(self):
        return 19 * hash(self._name) * hash(self.__class__)


class RequiredSortalEntity(RequiredEntity):
    @property
    def is_sortal(self):
        return True


class RequiredPropositionalEntity(RequiredEntity):
    @property
    def is_propositional(self):
        return True
