from tala.utils.as_json import AsJSONMixin
from tala.utils.json_api import JSONAPIMixin, JSONAPIObject


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

FRONTEND_TARGET = "frontend_target"
HTTP_TARGET = "http_target"


class ServiceInterface(AsJSONMixin, JSONAPIMixin):
    @classmethod
    def create_from_json_api_data(cls, json_dict, _included):

        actions = [
            ServiceActionInterface.create_from_json_api_dict(action)
            for action in json_dict["attributes"].get("actions", [])
        ]

        queries = [
            ServiceQueryInterface.create_from_json_api_dict(query)
            for query in json_dict["attributes"].get("queries", [])
        ]

        validators = [
            ServiceValidatorInterface.create_from_json_api_dict(validator)
            for validator in json_dict["attributes"].get("validators", [])
        ]

        return cls(actions, queries, validators)

    def __init__(self, actions, queries, validators):
        self._validate(actions)
        self._actions = {action.name: action for action in actions}
        self._validate(queries)
        self._queries = {query.name: query for query in queries}
        self._validate(validators)
        self._validators = {validator.name: validator for validator in validators}

    def as_json_api_dict(self):

        service_interface = JSONAPIObject("tala.ddd.services.ServiceInterface", "ServiceInterface")

        for _name, action in self._actions.items():
            action_dict = action.as_json_api_dict()
            service_interface.append_attribute("actions", action_dict)

        for _name, query in self._queries.items():
            query_dict = query.as_json_api_dict()
            service_interface.append_attribute("queries", query_dict)

        for _name, validator in self._validators.items():
            validator_dict = validator.as_json_api_dict()
            service_interface.append_attribute("validators", validator_dict)

        return service_interface.as_dict

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


class SpecificServiceInterface(AsJSONMixin, JSONAPIMixin):
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

    @classmethod
    def create_parameters_from_json_api_dict(cls, data):
        name = data["id"]
        attributes = data["attributes"]
        if attributes["target"]["target_type"] == HTTP_TARGET:
            target = HttpTarget(attributes["target"]["endpoint"])
        elif attributes["target"]["target_type"] == FRONTEND_TARGET:
            target = FrontendTarget()
        parameters = [ServiceParameter.create_from_json_api_dict(parameter) for parameter in attributes["parameters"]]

        return name, target, parameters

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


class ServiceActionInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, name, target, parameters, failure_reasons):
        super(ServiceActionInterface, self).__init__("action", name, target, parameters)
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

    @classmethod
    def create_from_json_api_dict(cls, data):
        parameters = super().create_parameters_from_json_api_dict(data)
        failure_reasons = [ActionFailureReason(reason) for reason in data["attributes"]["failure_reasons"]]
        parameters += (failure_reasons, )
        return cls(*parameters)

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

    def as_json_api_dict(self):
        return {
            "type": "tala.ddd.services.service_interface.ServiceActionInterface",
            "id": self.name,
            "attributes": {
                "target": self.target.as_json_api_attribute(),
                "parameters": [parameter.as_json_api_attribute() for parameter in self.parameters],
                "failure_reasons": [reason.name for reason in self.failure_reasons]
            }
        }


class ServiceQueryInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceQueryInterface, self).__init__("query", *args, **kwargs)
        self.ensure_target_is_not_frontend()

    @classmethod
    def create_from_json_api_dict(cls, data):
        parameters = super().create_parameters_from_json_api_dict(data)
        return cls(*parameters)

    def as_json_api_dict(self):
        return {
            "type": "tala.ddd.services.service_interface.ServiceQueryInterface",
            "id": self.name,
            "attributes": {
                "target": self.target.as_json_api_attribute(),
                "parameters": [parameter.as_json_api_attribute() for parameter in self.parameters],
            }
        }


class ServiceValidatorInterface(ParameterizedSpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceValidatorInterface, self).__init__("validator", *args, **kwargs)
        self.ensure_target_is_not_frontend()

    def as_json_api_dict(self):
        return {
            "type": "tala.ddd.services.service_interface.ServiceValidatorInterface",
            "id": self.name,
            "attributes": {
                "target": self.target.as_json_api_attribute(),
                "parameters": [parameter.as_json_api_attribute() for parameter in self.parameters],
            }
        }

    @classmethod
    def create_from_json_api_dict(cls, data):
        parameters = super().create_parameters_from_json_api_dict(data)
        return cls(*parameters)


class ServiceImplicationInterface(SpecificServiceInterface):
    def __init__(self, *args, **kwargs):
        super(ServiceImplicationInterface, self).__init__("implication", *args, **kwargs)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.target)


class ServiceParameter(AsJSONMixin):
    VALID_FORMATS = [ParameterField.VALUE, ParameterField.GRAMMAR_ENTRY]

    @classmethod
    def create_from_json_api_dict(cls, data):
        return cls(data["name"], data["format"], data["optional"])

    def __init__(self, name, format=None, is_optional=None):
        self._name = name
        is_optional = is_optional or False
        format = format or ParameterField.VALUE
        if format not in self.VALID_FORMATS:
            raise UnexpectedParameterFieldException(
                "Expected format as one of %s but got '%s' for parameter '%s'" % (self.VALID_FORMATS, format, name)
            )
        self._format = format
        self._is_optional = is_optional

    @property
    def name(self):
        return self._name

    @property
    def format(self):
        return self._format

    def as_json_api_attribute(self):
        return {"name": self.name, "format": self.format, "optional": self.is_optional}

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


class FrontendTarget(ServiceTarget):
    def __init__(self):
        super(FrontendTarget, self).__init__(FRONTEND_TARGET)

    def as_json_api_attribute(self):
        return {"target_type": FRONTEND_TARGET}


class HttpTarget(ServiceTarget):
    def __init__(self, endpoint):
        super(HttpTarget, self).__init__(HTTP_TARGET)
        self._endpoint = endpoint

    @property
    def endpoint(self):
        return self._endpoint

    def as_json_api_attribute(self):
        return {"target_type": HTTP_TARGET, "endpoint": self.endpoint}

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.endpoint)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.endpoint == other.endpoint
