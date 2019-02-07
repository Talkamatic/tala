from tala.utils.as_json import can_convert_to_json
from tala.utils.unicodify import unicodify


class StackError(Exception):
    pass


class Stack:
    def __init__(self, content=set(), contentclass=None):
        self.contentclass = contentclass
        self.content = list()
        for x in content:
            self.push(x)

    def as_json(self):
        def json_result():
            for object_ in self.content:
                if can_convert_to_json(object_):
                    yield object_.as_json()
                else:
                    yield object_

        return {
            "type": "stack",
            "content": list(json_result()),
        }

    def __repr__(self):
        return "{name}(content={content})".format(name=self.__class__.__name__, content=self.content)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        string = "Stack(" + unicodify(self.content) + ")"
        return string

    def __eq__(self, other):
        try:
            return self.content == other.content
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def push(self, element):
        self._typecheck(element)
        self.content.insert(0, element)

    def push_stack(self, other_stack):
        other_stack_elements = list(other_stack)
        other_stack_elements.reverse()
        for element in other_stack_elements:
            self.push(element)

    def _typecheck(self, element):
        if self.contentclass:
            if not isinstance(element, self.contentclass):
                raise TypeError(
                    "object " + unicode(element) + " of type " + element.__class__.__name__ + " is not of type " +
                    unicode(self.contentclass)
                )

    def top(self):
        if len(self) < 1:
            raise StackError("Cannot call 'top()' when stacksize <= 0")
        return self.content[0]

    def isTop(self, element):
        try:
            return element == self.top()
        except StackError:
            return False

    def pop(self):
        if len(self) < 1:
            raise StackError("Cannot call 'pop()' when stacksize <= 0")
        return self.content.pop(0)

    def __len__(self):
        return len(self.content)

    def isEmpty(self):
        return len(self) == 0

    def clear(self):
        self.content = list()

    def remove(self, element):
        self.content.remove(element)

    def __iter__(self):
        return self.content.__iter__()


class StackSet(Stack):
    def __unicode__(self):
        string = "stackset(" + unicodify(self.content) + ")"
        return string

    def push(self, element):
        self._typecheck(element)
        if element in self.content:
            self.content.remove(element)
        self.content.insert(0, element)

    def remove_if_exists(self, element):
        if element in self.content:
            self.remove(element)

    def create_view(self, philter):
        return StackSetView(self, philter)


class StackSetView:
    def __init__(self, source_object, philter):
        self.source_object = source_object
        self.philter = philter

    def __unicode__(self):
        string = "stacksetview(" + unicode(list(self)) + ")"
        return string

    def __str__(self):
        return unicode(self).encode("utf-8")

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
