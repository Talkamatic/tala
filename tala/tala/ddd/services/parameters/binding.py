from collections import namedtuple


class SingleInstanceParameterBinding(
    namedtuple("SingleInstanceParameterBinding", ["parameter", "value", "proposition"])
):
    @property
    def propositions(self):
        return [self.proposition]

    @property
    def is_multiple_instance_binding(self):
        return False


class MultiInstanceParameterBinding(
    namedtuple("MultiInstanceParameterBinding", ["parameter", "values", "propositions"])
):
    @property
    def value(self):
        return self.values

    @property
    def is_multiple_instance_binding(self):
        return True
