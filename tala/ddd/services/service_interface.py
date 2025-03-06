from tala.utils.as_json import AsJSONMixin


class UnexpectedParameterFieldException(Exception):
    pass


class UnexpectedActionException(Exception):
    pass


class UnexpectedQueryException(Exception):
    pass


class UnexpectedValidatorException(Exception):
    pass


class DuplicateNameException(Exception):
    pass


class FailureReasonsNotAllowedException(Exception):
    pass


class UnsupportedServiceInterfaceTarget(Exception):
    pass


class ParameterNotFoundException(Exception):
    pass


class ParameterField:
    VALUE = "value"
    GRAMMAR_ENTRY = "grammar_entry"


SEMANTIC_OBJECT_TYPE = "service_interface"

DEVICE_MODULE_TARGET = "device_module_target"
FRONTEND_TARGET = "frontend_target"
HTTP_TARGET = "http_target"


class ServiceInterface(AsJSONMixin):
    def __init__(self, actions, queries, validators):
        self._validate(actions)
        self._actions = {action.name: action for action in actions}
        self._validate(queries)
        self._queries = {query.name: query for query in queries}
        self._validate(validators)
        self._validators = {validator.name: validator for validator in validators}

    def _validate(self, specific_interfaces):
        names = [interface.name for interface in specific_interfaces]
        if not self._all_unique(names):
            raise DuplicateNameException(
                "Expected all names to be unique among %s but they weren't" % specific_interfaces
            )

    def _all_unique(self, all_names):
        unique_names = set(all_names)
        return len(all_names) == len(unique_names)

    @property
    def actions(self):
        return list(self._actions.values())

    def get_action(self, name):
        if not self.has_action(name):
            raise UnexpectedActionException(
                "Expected one of the known actions %s but got '%s'" % (list(self._actions.keys()), name)
            )
        return self._actions[name]

    def has_action(self, name):
        return name in self._actions

    def get_query(self, name):
        if not self.has_query(name):
            raise UnexpectedQueryException(
                "Expected one of the known queries %s but got '%s'" % (list(self._queries.keys()), name)
            )
        return self._queries[name]

    def has_query(self, name):
        return name in self._queries

    def get_validator(self, name):
        if not self.has_validator(name):
            raise UnexpectedValidatorException(
                "Expected one of the known validators %s but got '%s'" % (list(self._validators.keys()), name)
            )
        return self._validators[name]

    def has_validator(self, name):
        return name in self._validators

    @property
    def queries(self):
        return list(self._queries.values())

    @property
    def validators(self):
        return list(self._validators.values())

    def __repr__(self):
        return "%s(actions=%s, queries=%s, validators=%s)" % (
            self.__class__.__name__, self.actions, self.queries, self.validators
        )

    def __eq__(self, other):
        def has_all(these, those):
            return all(this in those for this in these) and all(that in these for that in those)

        return bool(
            isinstance(other, self.__class__) and has_all(self.actions, other.actions)
            and has_all(self.queries, other.queries) and has_all(self.validators, other.validators)
        )

    def as_dict(self):
        json = super(ServiceInterface, self).as_dict()
        json["semantic_object_type"] = SEMANTIC_OBJECT_TYPE
        json["actions"] = [value.as_json() for value in self._actions.values()]
        json["queries"] = [value.as_json() for value in self._queries.values()]
        json["validators"] = [value.as_json() for value in self._validators.values()]
        return json


class SpecificServiceInterface(AsJSONMixin):
    def __init__(self, interface_type, name, target):
        super(SpecificServiceInterface, self).__init__()
        self._interface_type = interface_type
        self._name = name
        self._target = target

    @property
    def interface_type(self):
        return self._interface_type

    @property
    def name(self):
        return self._name

    @property
    def target(self):
        return self._target

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.interface_type, self.name, self.target)

    def __eq__(self, other):
        return bool(
            isinstance(other, self.__class__) and self.interface_type == other.interface_type
            and self.name == other.name and self.target == other.target
        )

    def ensure_target_is_not_frontend(self):
        if self.target.is_frontend:
            raise UnsupportedServiceInterfaceTarget(
                "Expected a non-frontend target for service interface '%s' but got a frontend target." % self.name
            )


class ParameterizedSpecificServiceInterface(SpecificServiceInterface):
    def __init__(self, interface_type, name, target, parameters):
        super(ParameterizedSpecificServiceInterface, self).__init__(interface_type, name, target)
        self._parameters = parameters

    @property
    def parameters(self):
        return self._parameters

    def __repr__(self):
        return "%s(%r, %r, parameters=%s)" % (self.__class__.__name__, self.name, self.target, self.parameters)

    def __eq__(self, other):
        return bool(
            isinstance(other, self.__class__) and self.name == other.name and self.target == other.target
            and self.parameters == other.parameters
        )


class BaseActionInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, name, target, parameters, failure_reasons):
        super(BaseActionInterface, self).__init__("action", name, target, parameters)
        self._failure_reasons = failure_reasons
        self._validate_target_and_failure_reasons()

    def _validate_target_and_failure_reasons(self):
        if self.target.is_frontend:
            if self.failure_reasons:
                failure_reason_names = [reason.name for reason in self.failure_reasons]
                raise FailureReasonsNotAllowedException(
                    "Expected no failure reasons for action '%s' with target 'frontend', but got %s" %
                    (self.name, failure_reason_names)
                )

    @property
    def failure_reasons(self):
        return self._failure_reasons

    def __repr__(self):
        return "%s(%r, %r, parameters=%s, failure_reasons=%s)" % (
            self.__class__.__name__, self.name, self.target, self.parameters, self.failure_reasons
        )

    def __eq__(self, other):
        return bool(
            isinstance(other, self.__class__) and self.name == other.name and self.target == other.target
            and self.parameters == other.parameters and self.failure_reasons == other.failure_reasons
        )


class ServiceActionInterface(BaseActionInterface):
    pass


class ServiceQueryInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceQueryInterface, self).__init__("query", *args, **kwargs)
        self.ensure_target_is_not_frontend()


class ServiceValidatorInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceValidatorInterface, self).__init__("validator", *args, **kwargs)
        self.ensure_target_is_not_frontend()


class ServiceImplicationInterface(SpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceImplicationInterface, self).__init__("implication", *args, **kwargs)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.target)


class AbstractServiceParameter(AsJSONMixin):
    def __init__(self, name, format):
        self._name = name
        self._format = format

    @property
    def name(self):
        return self._name

    @property
    def format(self):
        return self._format

    @property
    def is_optional(self):
        raise NotImplementedError("Needs to be implemented")


class ServiceParameter(AbstractServiceParameter):
    VALID_FORMATS = [ParameterField.VALUE, ParameterField.GRAMMAR_ENTRY]

    def __init__(self, name, format=None, is_optional=None):
        is_optional = is_optional or False
        format = format or ParameterField.VALUE
        if format not in self.VALID_FORMATS:
            raise UnexpectedParameterFieldException(
                "Expected format as one of %s but got '%s' for parameter '%s'" % (self.VALID_FORMATS, format, name)
            )
        super(ServiceParameter, self).__init__(name, format)
        self._is_optional = is_optional

    @property
    def is_optional(self):
        return self._is_optional

    def __repr__(self):
        return "%s(%r, format=%r, is_optional=%r)" % (self.__class__.__name__, self.name, self.format, self.is_optional)

    def __eq__(self, other):
        return bool(
            isinstance(other, self.__class__) and self.name == other.name and self.format == other.format
            and self.is_optional == other.is_optional
        )


class ActionFailureReason(AsJSONMixin):
    def __init__(self, name):
        super(ActionFailureReason, self).__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def __eq__(self, other):
        return bool(isinstance(other, self.__class__) and self.name == other.name)


class ServiceTarget(AsJSONMixin):
    def __init__(self, target_type):
        self.target_type = target_type

    @property
    def is_device_module(self):
        return self.target_type == DEVICE_MODULE_TARGET

    @property
    def is_frontend(self):
        return self.target_type == FRONTEND_TARGET

    @property
    def is_http(self):
        return self.target_type == HTTP_TARGET

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not (self == other)


class DeviceModuleTarget(ServiceTarget):
    def __init__(self, device):
        super(DeviceModuleTarget, self).__init__(DEVICE_MODULE_TARGET)
        self._device = device

    @property
    def device(self):
        return self._device

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.device)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.device == other.device


class FrontendTarget(ServiceTarget):
    def __init__(self):
        super(FrontendTarget, self).__init__(FRONTEND_TARGET)


class HttpTarget(ServiceTarget):
    def __init__(self, endpoint):
        super(HttpTarget, self).__init__(HTTP_TARGET)
        self._endpoint = endpoint

    @property
    def endpoint(self):
        return self._endpoint

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.endpoint)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.endpoint == other.endpoint
