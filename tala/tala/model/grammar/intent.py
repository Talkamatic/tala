class TooFewTextChunksException(Exception):
    pass


class InvalidTextChunkEntityCombinationException(Exception):
    pass


class Intent(object):
    def __init__(self, intent, text_chunks, required_entities):
        self._intent = intent
        self._text_chunks = text_chunks
        self._required_entities = required_entities

        if len(text_chunks) < 1:
            raise TooFewTextChunksException("Expected at least one text chunk but got %s" % text_chunks)

        if len(text_chunks) != len(required_entities) + 1:
            raise InvalidTextChunkEntityCombinationException(
                "Expected %d text chunks for the %d entities, to achieve [chunk, entity, chunk, [...], entity, chunk] "
                "but got %d chunks" % (len(required_entities) + 1, len(required_entities), len(text_chunks))
            )

    @property
    def intent(self):
        return self._intent

    @property
    def text_chunks(self):
        return self._text_chunks

    @property
    def required_entities(self):
        return self._required_entities

    def __eq__(self, other):
        return bool(
            isinstance(other, self.__class__) and self._intent == other.intent
            and self._text_chunks == other.text_chunks and self._required_entities == other.required_entities
        )

    def __repr__(self):
        return "%s(%r, text_chunks=%s, required_entities=%s)" % (
            self.__class__.__name__, self._intent, self._text_chunks, self._required_entities
        )


class Request(Intent):
    def __init__(self, action, text_chunks, required_entities):
        super(Request, self).__init__(action, text_chunks, required_entities)

    @property
    def action(self):
        return self._intent


class Question(Intent):
    def __init__(self, predicate, text_chunks, required_entities):
        super(Question, self).__init__(predicate, text_chunks, required_entities)

    @property
    def predicate(self):
        return self._intent


class Answer(Intent):
    def __init__(self, text_chunks, required_entities):
        super(Answer, self).__init__("answer", text_chunks, required_entities)


class AnswerNegation(Intent):
    def __init__(self, text_chunks, required_entities):
        super(AnswerNegation, self).__init__("answer_negation", text_chunks, required_entities)
