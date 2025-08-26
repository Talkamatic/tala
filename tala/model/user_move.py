from typing import Text  # noqa: F401
import re

from tala.utils.equality import EqualityMixin


class MalformedMoveStringException(BaseException):
    pass


def create(user_move_as_dict):
    try:
        return DDDSpecificUserMove.from_dict(user_move_as_dict)
    except KeyError:
        return UserMove.from_dict(user_move_as_dict)


class UserMove(EqualityMixin):
    @classmethod
    def from_dict(cls, move_as_json):
        perception_confidence = move_as_json["perception_confidence"]
        understanding_confidence = move_as_json["understanding_confidence"]
        semantic_expression = move_as_json["semantic_expression"]

        return cls(semantic_expression, perception_confidence, understanding_confidence)

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
    @classmethod
    def from_dict(cls, move_as_json):
        ddd = move_as_json["ddd"]
        perception_confidence = move_as_json["perception_confidence"]
        understanding_confidence = move_as_json["understanding_confidence"]
        semantic_expression = move_as_json["semantic_expression"]

        return cls(ddd, semantic_expression, perception_confidence, understanding_confidence)

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


class ProperMove:
    def __init__(self, move_as_string):
        self._move_as_string = move_as_string
        self._move_type = None
        self._predicate = None
        self._individual = None
        self._action = None
        self._parse_move()

    def as_json(self):
        if self.move_type == "answer":
            return {"move_type": self.move_type, "predicate": self.predicate, "individual": self.individual}
        if self.move_type == "ask":
            return {"move_type": self.move_type, "predicate": self.predicate, "arity": self.arity}
        if self.move_type == "request":
            return {"move_type": self.move_type, "action": self.action}

    @property
    def move_type(self):
        if not self._move_type:
            self._parse_move()
        return self._move_type

    def _parse_move(self):
        if self._move_as_string.startswith("answer"):
            self._move_type = "answer"
            self._parse_answer()
        elif self._move_as_string.startswith("ask"):
            self._move_type = "ask"
            self._parse_ask()
        elif self._move_as_string.startswith("request"):
            self._move_type = "request"
            self._parse_request()
        else:
            raise MalformedMoveStringException(f'could not parse "{self._move_as_string}" as a move.')

    def _parse_answer(self):
        m = re.match(r"^answer\(([a-zA-Z0-9_\-\:]+)(\(([a-zA-Z0-9_\-\:\"]+)\))?\)$", self._move_as_string)
        if m:
            self._predicate = m[1]
            if len(m.groups()) > 2:
                self._individual = m[3]
        else:
            raise MalformedMoveStringException(f'could not parse "{self._move_as_string}" as a move.')

    def _parse_ask(self):
        m = re.match(r"^ask\(\?X.([a-zA-Z0-9_\-\:]+)\(X\)\)$", self._move_as_string)
        if m:
            print(m.groups())
            self._predicate = m[1]
            self._arity = 1
            return
        m = re.match(r"^ask\(\?([a-zA-Z0-9_\-\:]+)(\(\))?\)$", self._move_as_string)
        if m:
            print(m.groups())
            self._predicate = m[1]
            self._arity = 0
        else:
            raise MalformedMoveStringException(f'could not parse "{self._move_as_string}" as a move.')

    def _parse_request(self):
        m = re.match(r"^request\(([a-zA-Z0-9_\-\:]+)\)$", self._move_as_string)
        if m:
            self._action = m[1]
        else:
            raise MalformedMoveStringException(f'could not parse "{self._move_as_string}" as a move.')

    @property
    def predicate(self):
        if not self._predicate:
            self._parse_move()
        return self._predicate

    @property
    def individual(self):
        if not self._individual:
            self._parse_move()
        return self._individual

    @property
    def arity(self):
        if not self._arity:
            self._parse_move()
        return self._arity

    @property
    def action(self):
        if not self._action:
            self._parse_move()
        return self._action
