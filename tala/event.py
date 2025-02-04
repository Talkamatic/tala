from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin
from tala.utils.unicodify import unicodify


class InternalEvent(object):
    START = "START"
    STOP = "STOP"
    STOPPED = "STOPPED"


SEMANTIC_OBJECT_TYPE = "event"


class Event(InternalEvent, AsJSONMixin, EqualityMixin):
    PASSIVITY = "PASSIVITY"
    INTERPRETATION = "INTERPRETATION"
    SYSTEM_MOVES_SELECTED = "SYSTEM_MOVES_SELECTED"
    SERVICE_ACTION_STARTED = "SERVICE_ACTION_STARTED"
    SERVICE_ACTION_ENDED = "SERVICE_ACTION_ENDED"
    NEGATIVE_PERCEPTION = "NEGATIVE_PERCEPTION"
    EXPECTED_PASSIVITY_DURATION = "EXPECTED_PASSIVITY_DURATION"
    SELECTED_HYPOTHESIS = "SELECTED_HYPOTHESIS"
    SELECTED_INTERPRETATION = "SELECTED_INTERPRETATION"
    FACTS = "FACTS"
    AUDIO_PLAY = "AUDIO_PLAY"
    TO_FRONTEND_DEVICE = "TO_FRONTEND_DEVICE"
    SESSION_ID = "SESSION_ID"

    def __init__(self, type_, content=None, sender=None, reason=None):
        self._type = type_
        self._content = content
        self._sender = sender
        self._reason = reason

    @classmethod
    def create_from_json(cls, input):
        if input:
            type_ = input["type"]
            content = input.get("content")
            sender = input.get("sender")
            reason = input.get("reason")
            return Event(type_, content, sender, reason)
        return None

    @property
    def type_(self):
        return self._type

    @property
    def type(self):
        return self.type_

    @property
    def content(self):
        return self._content

    @property
    def sender(self):
        return self._sender

    @property
    def reason(self):
        return self._reason

    def get_type(self):
        return self.type_

    def get_sender(self):
        return self._sender

    def get_content(self):
        return self.content

    def get_reason(self):
        return self._reason

    def set_sender(self, sender):
        if self._sender:
            raise Exception("cannot change sender (from %s to %s)" % (self._sender, sender))
        self._sender = sender

    def __repr__(self):
        return "Event(%s, %s, sender=%s, reason=%s)" % (self.type, unicodify(self.content), self._sender, self._reason)

    def is_internal(self):
        return hasattr(InternalEvent, self.type)

    def as_dict(self):
        return {
            "semantic_object_type": SEMANTIC_OBJECT_TYPE,
            "type": self.type_,
            "content": self.content,
            "sender": self.sender,
            "reason": self.reason,
        }
