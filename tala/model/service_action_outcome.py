class ServiceActionOutcome():
    @property
    def is_successful(self):
        raise NotImplementedError("This property needs to be implemented in a subclass")

    def __eq__(self, other):
        try:
            return other.is_successful == self.is_successful
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def as_json(self):
        return {"service_action_outcome": None}


class Success(ServiceActionOutcome):
    @property
    def is_successful(self):
        return True

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def as_json(self):
        return {"service_action_outcome": True}


class SuccessfulServiceAction(Success):
    pass


class Failure(ServiceActionOutcome):
    def __init__(self, failure_reason):
        super().__init__()
        self._failure_reason = failure_reason

    @property
    def is_successful(self):
        return False

    @property
    def failure_reason(self):
        return self._failure_reason

    def as_json(self):
        return {"service_action_outcome": False, "failure_reason": self.failure_reason}

    def __eq__(self, other):
        return super().__eq__(other) and other.failure_reason == self.failure_reason

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.failure_reason)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.failure_reason)


class FailedServiceAction(Failure):
    def __init__(self, failure_reason):
        super().__init__(failure_reason)
