from tala.utils.equality import EqualityMixin
from tala.utils.as_json import AsJSONMixin


class UnexpectedModalityException(Exception):
    pass


class Entity(EqualityMixin, AsJSONMixin):
    def __init__(self, name: str, sort: str, natural_language_form: str, ddd_name: str = None) -> None:
        self._name = name
        self._sort = sort
        self._natural_language_form = natural_language_form
        self._ddd_name = ddd_name

    @classmethod
    def create_from_json(cls, input):
        name = input["name"]
        sort = input["sort"]
        natural_language_form = input["natural_language_form"]
        ddd_name = input.get("ddd")
        return Entity(name, sort, natural_language_form, ddd_name)

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
        return "{}({}, {}, {}, {})".format(
            self.__class__.__name__, self._name, self._sort, self._natural_language_form, self._ddd_name
        )

    def __repr__(self):
        return str(self)

    def as_dict(self):
        if self.ddd_name:
            return {
                "name": self.name,
                "sort": self.sort,
                "natural_language_form": self.natural_language_form,
                "ddd": self.ddd_name,
            }
        else:
            return {
                "name": self.name,
                "sort": self.sort,
                "natural_language_form": self.natural_language_form,
            }
