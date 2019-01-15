class InputHypothesis(object):
    def __init__(self, utterance, confidence):
        self._utterance = utterance
        self._confidence = confidence

    @property
    def utterance(self):
        return self._utterance

    @property
    def confidence(self):
        return self._confidence

    def __eq__(self, other):
        return self.utterance == other.utterance and self.confidence == other.confidence

    def __ne__(self, other):
        return not (self == other)

    def __unicode__(self):
        return "InputHypothesis(%r, %r)" % (self._utterance, self._confidence)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return str(self)
