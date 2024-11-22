from tala.model.common import Modality
from tala.model.user_move import UserMove, create  # noqa: F401
from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin
from tala.utils.unicodify import unicodify


class UnexpectedModalityException(Exception):
    pass


class Interpretation(EqualityMixin, AsJSONMixin):
    @classmethod
    def from_dict(cls, json_data):
        moves = [create(move) for move in json_data.get("moves", [])]
        modality = json_data.get("modality", Modality.OTHER)
        utterance = json_data.get("utterance")
        perception_confidence = json_data.get("perception_confidence")
        return cls(moves, modality, utterance, perception_confidence)

    def __init__(self, moves, modality, utterance=None, perception_confidence=None):
        # type: ([UserMove], str, str) -> None
        self._moves = moves
        if modality not in Modality.SUPPORTED_MODALITIES:
            raise UnexpectedModalityException(
                f"Expected one of the supported modalities {Modality.SUPPORTED_MODALITIES} but got '{modality}'"
            )
        if utterance:
            if modality not in Modality.ALLOWS_UTTERANCE:
                raise UnexpectedModalityException(
                    f"Expected no utterance for modality '{modality}' but got '{utterance}'"
                )
        if not utterance:
            if modality in Modality.REQUIRES_UTTERANCE:
                raise UnexpectedModalityException(f"Expected an utterance for modality '{modality}' but it was missing")
        self._modality = modality
        self._utterance = utterance
        self._perception_confidence = perception_confidence

    @property
    def moves(self):
        # type: () -> [UserMove]
        return self._moves

    @property
    def modality(self):
        # type: () -> str
        return self._modality

    @property
    def utterance(self):
        # type: () -> str
        return self._utterance

    @property
    def perception_confidence(self):
        return self._perception_confidence

    def as_dict(self):
        d = {
            "modality": self.modality,
            "moves": [move.as_dict() for move in self.moves],
            "utterance": self.utterance,
        }
        if self.perception_confidence:
            d["perception_confidence"] = self.perception_confidence
        return d

    def __repr__(self):
        return f"{self.__class__.__name__}({unicodify(self._moves)}, {self._modality}, {self._utterance}, {self._perception_confidence})"


class InterpretationWithoutUtterance(Interpretation):
    def __init__(self, moves, modality):
        # type: ([UserMove], str) -> None
        super(InterpretationWithoutUtterance, self).__init__(moves, modality)
        self._moves = moves
        self._modality = modality

    def as_dict(self):
        return {"modality": self.modality, "moves": [move.as_dict() for move in self.moves]}

    def __repr__(self):
        return f"{self.__class__.__name__}({unicodify(self._moves)}, {self._modality})"
