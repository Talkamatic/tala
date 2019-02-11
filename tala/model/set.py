from tala.utils.as_json import convert_to_json, JSONLoggable


class Set(JSONLoggable):
    def __init__(self, content_or_contentclass=None):
        super(Set, self).__init__()
        if content_or_contentclass is None:
            contentclass = None
            initial_content = []
        elif hasattr(content_or_contentclass, '__iter__'):
            contentclass = None
            initial_content = content_or_contentclass
        else:
            contentclass = content_or_contentclass
            initial_content = []
        self.contentclass = contentclass
        self.content = []
        for x in initial_content:
            self.add(x)

    def __unicode__(self):
        return "{" + ", ".join(map(unicode, self.content)) + "}"

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.content or self.contentclass or [])

    def as_json(self):
        return {
            "set": list(convert_to_json(object_) for object_ in self.content),
        }

    def __eq__(self, other):
        try:
            return self.is_subset_of(other) and other.is_subset_of(self)
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self.content)

    def __ne__(self, other):
        return not (self == other)

    def add(self, element):
        if element not in self.content:
            self._typecheck(element)
            self.content.append(element)

    def remove(self, element):
        self.content.remove(element)

    def remove_if_exists(self, element):
        if element in self.content:
            self.remove(element)

    def is_subset_of(self, other):
        for item in self.content:
            if item not in other.content:
                return False
        return True

    def _typecheck(self, element):
        if self.contentclass:
            if not isinstance(element, self.contentclass):
                raise TypeError(
                    "object " + unicode(element) + " of type " + element.__class__.__name__ + " is not of type " +
                    unicode(self.contentclass)
                )

    def __len__(self):
        return len(self.content)

    def isEmpty(self):
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
