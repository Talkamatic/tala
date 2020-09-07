import re
import warnings


class DddDevice(object):
    """This method is invoked when a commitment is added or revised, e.g. when a user answer
    is integrated. The device can use this information to update its state.

    Return value: None."""

    def commitment_update(self, commitment):
        pass


class DeviceError(Exception):
    pass


class ParameterNotFoundException(Exception):
    pass


class ParameterField:
    VALUE = "value"
    GRAMMAR_ENTRY = "grammar_entry"


class DeviceMethod(object):
    def __init__(self, device, ontology):
        super(DeviceMethod, self).__init__()
        self.device = device
        self.ontology = ontology
        self.parameters = self._parse_parameters()
        self._check_parameters_sanity()
        self._current_invocation_id = None

    def _parse_parameters(self):
        if hasattr(self, "PARAMETERS"):
            return list(map(self._parse_parameter, self.PARAMETERS))
        return []

    def _parse_parameter(self, parameters_string):
        m = re.search("^([^=.]+)(\.(value|grammar_entry))?(='([^']*)')?$", parameters_string)
        if m:
            name, _, field, default_value_string, default_value = m.groups()

            if field is None:
                field = ParameterField.VALUE

            if default_value_string:
                optional = True
            else:
                optional = False
                default_value = None

            return {"name": name, "field": field, "optional": optional, "default_value": default_value}
        else:
            raise DeviceError(
                "failed to parse parameters for %s: invalid syntax %r" % (self.__class__.__name__, parameters_string)
            )

    def _check_parameters_sanity(self):
        for parameter in self.parameters:
            self._check_parameter_sanity(parameter)

    def _check_parameter_sanity(self, parameter):
        if not self.ontology.has_predicate(parameter["name"]):
            raise DeviceError(
                "illegal parameters for %s: no predicate %r found in the ontology %s" %
                (self.__class__.__name__, parameter["name"], self.ontology)
            )

    def current_invocation_id(self):
        return self._current_invocation_id

    def set_current_invocation_id(self, invocation_id):
        self._current_invocation_id = invocation_id


class EntityRecognizer(DeviceMethod):
    def recognize(self, string, language):
        if hasattr(self, "recognize_entity"):
            deprecation_message = "The 'recognize_entity' method does not distinguish between languages. " "Use the 'recognize' method instead. This happened in '%s' of '%s'." % (
                self.__class__.__name__, self.device.__class__.__name__
            )
            warnings.warn(deprecation_message, DeprecationWarning)
            return self.recognize_entity(string)
        raise NotImplementedError("This method must be implemented by a subclass if used.")

    def recognize_entity(self, string):
        pass


class DeviceAction(DeviceMethod):
    TYPE = None
    PLAY_AUDIO = "PLAY_AUDIO"


class DeviceWHQuery(DeviceMethod):
    pass


class Validity(DeviceMethod):
    pass


class DeviceImplication(DeviceMethod):
    def __init__(self, device, ontology):
        super(DeviceImplication, self).__init__(device, ontology)
        warnings.warn("%s methods are experimental and should be used with care" % DeviceImplication.__name__)
