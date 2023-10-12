from tala.model.semantic_object import SemanticObject


class ActionStatus(SemanticObject):
    DONE = "done"
    ABORTED = "aborted"


class Done(ActionStatus):
    def __eq__(self, other):
        return isinstance(other, Done)

    def as_semantic_expression(self):
        return self.DONE

    def __str__(self):
        return self.DONE

    def __repr__(self):
        return "Done()"

    def __hash__(self):
        return hash(self.DONE)

    def as_dict(self):
        return {"action_status": self.DONE}


class Aborted(ActionStatus):
    def __init__(self, reason):
        self._reason = reason

    @property
    def reason(self):
        return self._reason

    def __eq__(self, other):
        return isinstance(other, Aborted) and self.reason == other.reason

    def as_semantic_expression(self):
        return f"{self.ABORTED}({self.reason})"

    def __str__(self):
        return f"{self.ABORTED}({self.reason})"

    def __repr__(self):
        return f"Aborted({self.reason})"

    def __hash__(self):
        return hash((self.ABORTED, self.reason))

    def as_dict(self):
        return {"action_status": self.ABORTED, "reason": self.reason}
