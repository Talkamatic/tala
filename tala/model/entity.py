from tala.utils.equality import EqualityMixin


class UnexpectedModalityException(Exception):
    pass


class Entity(EqualityMixin):
    def __init__(self, name: str, sort: str, natural_language_form: str, ddd_name: str = None) -> None:
        self._name = name
        self._sort = sort
        self._natural_language_form = natural_language_form
        self._ddd_name = ddd_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def sort(self) -> str:
        return self._sort

    @property
    def natural_language_form(self) -> str:
        return self._natural_language_form

    @property
    def ddd_name(self) -> str:
        return self._ddd_name

    def __str__(self):
        return "{}({}, {}, {}, {})".format(self.__class__.__name__, self._name, self._sort,
                                           self._natural_language_form, self._ddd_name)

    def __repr__(self):
        return str(self)
