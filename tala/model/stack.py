import warnings

from tala.utils.as_json import AsJSONMixin
from tala.utils.unicodify import unicodify


class StackError(Exception):
    pass


class Stack(AsJSONMixin):
    def __init__(self, content=None):
        if content is None:
            content = []
        super(Stack, self).__init__()
        self.content = list()
        for x in content:
            self.push(x)

    def as_dict(self):
        return {
            "stack": self.content,
        }

    def __repr__(self):
        return "{name}(content={content})".format(name=self.__class__.__name__, content=self.content)

    def __str__(self):
        string = "Stack(" + unicodify(self.content) + ")"
        return string

    def __eq__(self, other):
        try:
            return self.content == other.content
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self.content)

    def __ne__(self, other):
        return not (self == other)

    def push(self, element):
        self.content.insert(0, element)

    def push_stack(self, other_stack):
        other_stack_elements = list(other_stack)
        other_stack_elements.reverse()
        for element in other_stack_elements:
            self.push(element)

    def top(self):
        if len(self) < 1:
            raise StackError("Cannot call 'top()' when stacksize <= 0")
        return self.content[0]

    def is_top(self, element):
        try:
            return element == self.top()
        except StackError:
            return False

    def isTop(self, element):
        warnings.warn("Stack.isTop() is deprecated. Use Stack.is_top() instead.", DeprecationWarning, stacklevel=2)
        return self.is_top(element)

    def pop(self):
        if len(self) < 1:
            raise StackError("Cannot call 'pop()' when stacksize <= 0")
        return self.content.pop(0)

    def __len__(self):
        return len(self.content)

    def isEmpty(self):
        warnings.warn("Stack.isEmpty() is deprecated. Use Stack.is_empty() instead.", DeprecationWarning, stacklevel=2)
        return self.is_empty()

    def is_empty(self):
        return len(self) == 0

    def clear(self):
        self.content = list()

    def remove(self, element):
        self.content.remove(element)

    def __iter__(self):
        return self.content.__iter__()


class StackSet(Stack):
    def __init__(self, content=None):
        if content is None:
            content = []
        super().__init__(content)

    def as_dict(self):
        return {
            "stackset": self.content,
        }

    def __str__(self):
        string = "stackset(" + unicodify(self.content) + ")"
        return string

    def push(self, element):
        if element in self.content:
            self.content.remove(element)
        self.content.insert(0, element)

    def remove_if_exists(self, element):
        if element in self.content:
            self.remove(element)

    def create_view(self, philter):
        return StackSetView(self, philter)


class QUD(AsJSONMixin):
    def __init__(self, content=None, turn_information=None):
        if content is None:
            content = []
        if turn_information is None:
            turn_information = {}

        self._stack_set = StackSet(content)
        self._turn_information = {k: v for k, v in turn_information.items()}

    def as_dict(self):
        return {
            "qud": {
                "stackset": self._stack_set.content,
                "turn_information": [{
                    "key": k.as_dict(),
                    "value": v
                } for k, v in self._turn_information.items()]
            }
        }

    def __len__(self):
        return len(self._stack_set)

    def __str__(self):
        return str(self._stack_set)

    def push(self, element, lifespan=1):
        self._stack_set.push(element)
        self._turn_information[element] = lifespan

    def __iter__(self):
        return self._stack_set.__iter__()

    def top(self):
        return self._stack_set.top()

    def pop(self):
        element = self._stack_set.pop()
        del self._turn_information[element]
        return element

    def clear(self):
        self._stack_set.clear()
        self._turn_information = {}

    def is_top(self, element):
        return self._stack_set.is_top(element)

    def is_empty(self):
        return self._stack_set.is_empty()

    def update_turn_information(self):
        for question in self._turn_information:
            self._turn_information[question] = self._turn_information[question] - 1

    def purge_entries(self):
        to_remove = []
        for entry in self._stack_set:
            if self._turn_information[entry] < 1:
                to_remove.append(entry)
        for entry in to_remove:
            self.remove(entry)

    def remove(self, entry):
        self._stack_set.remove(entry)
        del self._turn_information[entry]

    def __eq__(self, other):
        try:
            return list(self) == list(other)
        except AttributeError:
            return False


class StackSetView:
    def __init__(self, source_object, philter):
        self.source_object = source_object
        self.philter = philter

    def __str__(self):
        string = "stacksetview(" + str(list(self)) + ")"
        return string

    def top(self):
        return self._filtered_top(self.philter)

    def _filtered_top(self, philter):
        for element in self.source_object:
            if philter(element):
                return element

    def push(self, element):
        if element != self.top():
            self.source_object.push(element)

    def pop(self):
        self.source_object.remove(self.top())

    def __iter__(self):
        for elem in self.source_object:
            if self.philter(elem):
                yield elem

    def __len__(self):
        return len(list(self.__iter__()))

    def is_empty(self):
        return len(self) == 0
