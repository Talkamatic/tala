from tala.utils.as_json import AsJSONMixin
from tala.utils import json_api
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class Set(AsSemanticExpressionMixin, AsJSONMixin):
    def __init__(self, content=None):
        if content is None:
            content = []
        super(Set, self).__init__()
        self.content = []
        for x in content:
            self.add(x)

    def __str__(self):
        return "{" + ", ".join(map(str, self.content)) + "}"

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.content)

    def as_dict(self):
        return {
            "set": self.content,
        }

    def as_json_api_dict(self, id_=None, type_="tdm.tis.set"):
        set_obj = json_api.JSONAPIObject(type_, id_=id_)
        for item in self.content:
            set_obj.append_relationship("content", json_api.as_json_api_entry(item))
        return set_obj.as_dict

    @classmethod
    def create_from_json_api_data(cls, data, included):
        if data is None:
            return cls()
        try:
            items = included.get_data_for_relationship("content", data)
        except AttributeError:
            included = json_api.IncludedObject(included or [])
            items = included.get_data_for_relationship("content", data)
        if items is None:
            return cls()
        try:
            items[0]
        except (TypeError, KeyError, IndexError):
            items = [items]
        content = [json_api.create_from_json_api_data(item, included) for item in items if item is not None]
        return cls(content)

    def __eq__(self, other):
        try:
            equality = self.is_subset_of(other) and other.is_subset_of(self)
            return equality
        except AttributeError:
            return False
        except TypeError:
            return False

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self.content)

    def add(self, element):
        if element not in self.content:
            self.content.append(element)

    def remove(self, element):
        self.content.remove(element)

    def remove_if_exists(self, element):
        if element in self.content:
            self.remove(element)

    def is_subset_of(self, other):
        for item in self.content:
            if item not in other:
                return False
        return True

    def __len__(self):
        return len(self.content)

    def is_empty(self):
        return len(self) == 0

    def clear(self):
        self.content = []

    def __iter__(self):
        return self.content.__iter__()

    def union(self, other):
        union_set = Set()
        for item in self:
            union_set.add(item)
        for item in other:
            union_set.add(item)
        return union_set

    def extend(self, other):
        for item in other:
            self.add(item)

    def intersection(self, other):
        intersection_set = Set()
        for item in self:
            if item in other:
                intersection_set.add(item)
        return intersection_set
