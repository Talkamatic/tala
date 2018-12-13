from tala.model.sort import STRING


class Entity(object):
    def __init__(self, identifier, text, start, end):
        self._identifier = identifier
        self._text = text
        self._start = start
        self._end = end

    def generate(self):
        return {
            "start": self._start,
            "end": self._end,
            "value": self._text,
            "entity": self._identifier,
        }

    @property
    def text(self):
        return self._text


class SortalEntity(Entity):
    def __init__(self, sort, text, start, end):
        identifier = STRING if sort == STRING else "sort:%s" % sort
        super(SortalEntity, self).__init__(identifier, text, start, end)


class PropositionalEntity(Entity):
    def __init__(self, predicate, text, start, end):
        identifier = "predicate:%s" % predicate
        super(PropositionalEntity, self).__init__(identifier, text, start, end)
