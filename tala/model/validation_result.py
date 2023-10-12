from tala.utils.equality import EqualityMixin


class ValidationResult(EqualityMixin):
    @property
    def is_successful(self):
        raise NotImplementedError("This property needs to be implemented in a subclass.")

    def __repr__(self):
        return "%s()" % self.__class__.__name__


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

    def __hash__(self):
        return 17 * hash(str(self)) + 7 * hash(self.__class__.__name__)
