class CommonExample(object):
    def __init__(self, intent, text, entities=None):
        super(CommonExample, self).__init__()
        self._intent = intent
        self._text = text
        self._entities = entities or []

    @property
    def text(self):
        return self._text

    @property
    def intent(self):
        return self._intent

    @property
    def entities(self):
        return self._entities

    def generate(self):
        return {
            "text": self._text,
            "intent": self._intent,
            "entities": [entity.generate() for entity in self._entities],
        }
