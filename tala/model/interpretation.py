from tala.model.common import Modality
from tala.model.user_move import UserMove  # noqa: F401
from tala.utils.unicodify import unicodify


class UnexpectedModalityException(Exception):
    pass


class Interpretation(object):
    def __init__(self, moves, modality, utterance=None):
        # type: ([UserMove], basestring, basestring) -> None
        self._moves = moves
        if modality not in Modality.SUPPORTED_MODALITIES:
            raise UnexpectedModalityException(
                "Expected one of the supported modalities {} but got '{}'".format(
                    Modality.SUPPORTED_MODALITIES, modality
                )
            )
        if utterance:
            if modality not in Modality.ALLOWS_UTTERANCE:
                raise UnexpectedModalityException(
                    "Expected no utterance for modality '{}' but got '{}'".format(modality, utterance)
                )
        if not utterance:
            if modality in Modality.REQUIRES_UTTERANCE:
                raise UnexpectedModalityException(
                    "Expected an utterance for modality '{}' but it was missing".format(modality)
                )
        self._modality = modality
        self._utterance = utterance

    @property
    def moves(self):
        # type: () -> [UserMove]
        return self._moves

    @property
    def modality(self):
        # type: () -> basestring
        return self._modality

    @property
    def utterance(self):
        # type: () -> basestring
        return self._utterance

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (other == self)

    def __unicode__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, unicodify(self._moves), self._modality, self._utterance)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return str(self)
