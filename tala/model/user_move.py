from typing import Text  # noqa: F401

from tala.utils.equality import EqualityMixin


class UserMove(EqualityMixin):
    def __init__(self, semantic_expression, perception_confidence, understanding_confidence):
        # type: (Text, float, float) -> None
        self._semantic_expression = semantic_expression
        self._perception_confidence = perception_confidence
        self._understanding_confidence = understanding_confidence

    @property
    def is_ddd_specific(self):
        # type: () -> bool
        return False

    @property
    def semantic_expression(self):
        # type: () -> Text
        return self._semantic_expression

    @property
    def perception_confidence(self):
        # type: () -> float
        return self._perception_confidence

    @property
    def understanding_confidence(self):
        # type: () -> float
        return self._understanding_confidence

    def as_dict(self):
        return {
            "perception_confidence": self.perception_confidence,
            "understanding_confidence": self.understanding_confidence,
            "semantic_expression": self.semantic_expression,
        }

    def __str__(self):
        return f"{self.__class__.__name__}({self._semantic_expression}, " \
               f"perception_confidence={self._perception_confidence}, " \
               f"understanding_confidence={self._understanding_confidence})"

    def __repr__(self):
        return str(self)


class DDDSpecificUserMove(UserMove):
    def __init__(self, ddd, semantic_expression, perception_confidence, understanding_confidence):
        # type: (Text, Text, float, float) -> None
        super(DDDSpecificUserMove, self).__init__(semantic_expression, perception_confidence, understanding_confidence)
        self._ddd = ddd

    @property
    def is_ddd_specific(self):
        # type: () -> bool
        return True

    @property
    def ddd(self):
        # type: () -> Text
        return self._ddd

    def as_dict(self):
        return {
            "ddd": self.ddd,
            "perception_confidence": self.perception_confidence,
            "understanding_confidence": self.understanding_confidence,
            "semantic_expression": self.semantic_expression,
        }

    def __str__(self):
        return f"{self.__class__.__name__}({self._ddd}, semantic_expression={self._semantic_expression}, " \
               f"perception_confidence={self._perception_confidence}, " \
               f"understanding_confidence={self._understanding_confidence})"
