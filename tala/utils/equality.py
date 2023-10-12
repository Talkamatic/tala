class EqualityMixin(object):
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        x = self.__eq__(other)
        if x is not NotImplemented:
            return not x
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(items(self))))


def items(object_):
    if isinstance(object_, (list, tuple, set)):
        return (items(element) for element in object_)
    if isinstance(object_, dict):
        return tuple({key: items(value) for key, value in list(object_.items())})
    if hasattr(object_, "__class__"):
        if not isinstance(object_, EqualityMixin):
            if hasattr(object_, "__hash__"):
                return hash(object_)
    if hasattr(object_, "__dict__"):
        return items(object_.__dict__)
    return object_
