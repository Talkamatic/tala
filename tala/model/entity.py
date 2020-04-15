from tala.utils.equality import EqualityMixin


class UnexpectedModalityException(Exception):
    pass


class Entity(EqualityMixin):
    def __init__(self, semantic_name: str, sort: str, surface_form: str, ddd_name: str = None) -> None:
        self._semantic_name = semantic_name
        self._sort = sort
        self._surface_form = surface_form
        self._ddd_name = ddd_name

    @property
    def semantic_name(self) -> str:
        return self._semantic_name

    @property
    def sort(self) -> str:
        return self._sort

    @property
    def surface_form(self) -> str:
        return self._surface_form

    @property
    def ddd_name(self) -> str:
        return self._ddd_name

    def __str__(self):
        return "{}({}, {}, {}, {})".format(self.__class__.__name__, self._semantic_name, self._sort,
                                           self._surface_form, self._ddd_name)

    def __repr__(self):
        return str(self)
