class ValidationResult(object):
    @property
    def is_successful(self):
        raise NotImplementedError("This property needs to be implemented in a subclass.")

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return NotImplemented
        return True

    def __ne__(self, other):
        are_equal = self.__eq__(other)
        if are_equal is NotImplemented:
            return NotImplemented
        return not are_equal

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


class ValidationSuccess(ValidationResult):
    @property
    def is_successful(self):
        return True


class ValidationFailure(ValidationResult):
    def __init__(self, invalidity_reason, invalid_parameters):
        self._invalidity_reason = invalidity_reason
        self._invalid_parameters = invalid_parameters

    @property
    def is_successful(self):
        return False

    @property
    def invalidity_reason(self):
        return self._invalidity_reason

    @property
    def invalid_parameters(self):
        return self._invalid_parameters

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.invalidity_reason, self.invalid_parameters)

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return NotImplemented
        return self.invalidity_reason == other.invalidity_reason and self.invalid_parameters == other.invalid_parameters
