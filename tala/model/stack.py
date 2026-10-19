from tala.utils.as_json import AsJSONMixin
from tala.utils import json_api
from tala.utils.unicodify import unicodify


class StackError(Exception):
    pass


class Stack(AsJSONMixin):
    def __init__(self, content=None):
        if content is None:
            content = []
        super(Stack, self).__init__()
        self._content = list()
        for x in content:
            self.push(x)

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def as_dict(self):
        return {
            "stack": self._content,
        }

    def as_json_api_dict(self, id_=None, type_="tdm.tis.stack"):
        stack_obj = json_api.JSONAPIObject(type_, id_=id_)
        for item in self._content:
            stack_obj.append_relationship("content", json_api.as_json_api_entry(item))
        return stack_obj.as_dict

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
        return cls(list(reversed(content)))

    def __repr__(self):
        return "{name}(content={content})".format(name=self.__class__.__name__, content=self._content)

    def __str__(self):
        string = "Stack(" + unicodify(self._content) + ")"
        return string

    def __eq__(self, other):
        try:
            return self._content == other.content
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self._content)

    def __ne__(self, other):
        return not (self == other)

    def push(self, element):
        self._content.insert(0, element)

    def push_stack(self, other_stack):
        other_stack_elements = list(other_stack)
        other_stack_elements.reverse()
        for element in other_stack_elements:
            self.push(element)

    @property
    def top(self):
        if len(self) < 1:
            raise StackError("Cannot call 'top()' when stacksize <= 0")
        return self._content[0]

    def is_top(self, element):
        try:
            return element == self.top
        except StackError:
            return False

    def pop(self):
        if len(self) < 1:
            raise StackError("Cannot call 'pop()' when stacksize <= 0")
        return self._content.pop(0)

    def __len__(self):
        return len(self._content)

    def is_empty(self):
        return len(self) == 0

    def clear(self):
        self._content = list()

    def remove(self, element):
        self._content.remove(element)

    def __iter__(self):
        return self._content.__iter__()


class StackSet(Stack):
    def __init__(self, content=None):
        if content is None:
            content = []
        super().__init__(content)

    def as_dict(self):
        return {
            "stackset": self._content,
        }

    def as_json_api_dict(self, id_=None, type_="tdm.tis.stackset"):
        return super().as_json_api_dict(id_=id_, type_=type_)

    @classmethod
    def create_from_json_api_data(cls, data, included):
        return super(StackSet, cls).create_from_json_api_data(data, included)

    def __str__(self):
        string = "stackset(" + unicodify(self._content) + ")"
        return string

    def push(self, element):
        if element in self._content:
            self._content.remove(element)
        self._content.insert(0, element)

    def remove_if_exists(self, element):
        if element in self._content:
            self.remove(element)
