class UserMove(object):
    def __init__(self, semantic_expression, perception_confidence, understanding_confidence):
        self._semantic_expression = semantic_expression
        self._perception_confidence = perception_confidence
        self._understanding_confidence = understanding_confidence

    @property
    def is_ddd_specific(self):
        return False

    @property
    def semantic_expression(self):
        return self._semantic_expression

    @property
    def perception_confidence(self):
        return self._perception_confidence

    @property
    def understanding_confidence(self):
        return self._understanding_confidence

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (other == self)

    def __unicode__(self):
        return "{}({}, perception_confidence={}, understanding_confidence={})"\
            .format(self.__class__.__name__, self._semantic_expression, self._perception_confidence,
                    self._understanding_confidence)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return str(self)


class DDDSpecificUserMove(UserMove):
    def __init__(self, ddd, semantic_expression, perception_confidence, understanding_confidence):
        super(DDDSpecificUserMove, self).__init__(semantic_expression, perception_confidence, understanding_confidence)
        self._ddd = ddd

    @property
    def is_ddd_specific(self):
        return True

    @property
    def ddd(self):
        return self._ddd

    def __unicode__(self):
        return "{}({}, perception_confidence={}, understanding_confidence={})"\
            .format(self.__class__.__name__, self._ddd, self._semantic_expression, self._perception_confidence,
                    self._understanding_confidence)
