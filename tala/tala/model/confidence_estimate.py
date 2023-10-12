from tala.utils.equality import EqualityMixin


class ConfidenceEstimates(EqualityMixin):
    def __init__(
        self, perception_confidence=None, understanding_confidence=None, weighted_understanding_confidence=None
    ):
        self._perception_confidence = None
        self._understanding_confidence = None
        self._weighted_understanding_confidence = None
        if understanding_confidence is not None or perception_confidence is not None:
            self.set_realization_data(
                perception_confidence=perception_confidence, understanding_confidence=understanding_confidence
            )
            if weighted_understanding_confidence is not None:
                self.weighted_understanding_confidence = weighted_understanding_confidence

    @property
    def perception_confidence(self):
        return self._perception_confidence

    @property
    def understanding_confidence(self):
        return self._understanding_confidence

    @property
    def weighted_understanding_confidence(self):
        return self._weighted_understanding_confidence

    @weighted_understanding_confidence.setter
    def weighted_understanding_confidence(self, confidence):
        self._weighted_understanding_confidence = confidence

    @property
    def confidence(self):
        confidence_sources = [self.perception_confidence, self.understanding_confidence]
        if None in confidence_sources:
            return None
        return self.perception_confidence * self.understanding_confidence

    @property
    def weighted_confidence(self):
        confidence_sources = [self.perception_confidence, self.weighted_understanding_confidence]
        if None in confidence_sources:
            return None
        return self.perception_confidence * self.weighted_understanding_confidence

    def set_realization_data(self, perception_confidence=None, understanding_confidence=None):
        self._perception_confidence = perception_confidence
        if self._perception_confidence is None:
            self._perception_confidence = 1.0
        self._understanding_confidence = understanding_confidence
        if self._understanding_confidence is None:
            self._understanding_confidence = 1.0
        self._weighted_understanding_confidence = self._understanding_confidence

    def uprank(self, amount):
        self._weighted_understanding_confidence *= (1 + amount)

    def downrank(self, amount):
        self._weighted_understanding_confidence *= (1 - amount)

    def build_string_from_attributes(self):
        string = ""
        if self.understanding_confidence is not None:
            string += ", understanding_confidence=%s" % self.understanding_confidence
        if self.weighted_understanding_confidence is not None:
            string += ", weighted_understanding_confidence=%s" % self.weighted_understanding_confidence
        if self.perception_confidence is not None:
            string += ", perception_confidence=%s" % self.perception_confidence
        return string
