from tala.model.semantic_object import SemanticObject


class UnknownActionStatusException(Exception):
    pass


class ActionStatus(SemanticObject):
    DONE = "done"
    ABORTED = "aborted"

    @property
    def json_api_attributes(self):
        return []

    @classmethod
    def create_from_json_api_data(cls, data, included):
        if cls is Done:
            return Done()
        if cls is Aborted:
            attributes = data.get("attributes", {})
            return Aborted(attributes.get("reason"))
        raise UnknownActionStatusException(f"Unsupported action status class {cls.__name__}")


class Done(ActionStatus):
    @property
    def json_api_attributes(self):
        return []

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

    @property
    def json_api_attributes(self):
        return ["reason"]

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
