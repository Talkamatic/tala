from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin
from tala.utils.unicodify import unicodify

SEMANTIC_OBJECT_TYPE = "event"

EXPECTED_PASSIVITY_DURATION = "EXPECTED_PASSIVITY_DURATION"
FACTS = "FACTS"
INTERPRETATION = "INTERPRETATION"
NEGATIVE_PERCEPTION = "NEGATIVE_PERCEPTION"
PASSIVITY = "PASSIVITY"
SELECTED_HYPOTHESIS = "SELECTED_HYPOTHESIS"
SELECTED_INTERPRETATION = "SELECTED_INTERPRETATION"
START = "START"
SYSTEM_MOVES_SELECTED = "SYSTEM_MOVES_SELECTED"
TO_FRONTEND_DEVICE = "TO_FRONTEND_DEVICE"


class Event(AsJSONMixin, EqualityMixin):
    def __init__(self, type_, content=None, sender=None, reason=None):
        self._type = type_
        self._content = content
        self._sender = sender
        self._reason = reason

    @classmethod
    def create_from_json(cls, json_dict):
        if json_dict:
            return Event(json_dict["type"], json_dict.get("content"), json_dict.get("sender"), json_dict.get("reason"))
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

    def __repr__(self):
        return f"Event({self.type}, {unicodify(self.content)}, sender={self._sender}, reason={self._reason})"

    def as_dict(self):
        return {
            "semantic_object_type": SEMANTIC_OBJECT_TYPE,
            "type": self.type_,
            "content": self.content,
            "sender": self.sender,
            "reason": self.reason,
        }
