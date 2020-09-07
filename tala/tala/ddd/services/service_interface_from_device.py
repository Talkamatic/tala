from jinja2 import Template

from tala.ddd.services.service_interface import ServiceInterface, ServiceActionInterface, ServiceParameter, DeviceModuleTarget, ActionFailureReason, ServiceQueryInterface, FrontendTarget, PlayAudioActionInterface, AudioURLServiceParameter, ServiceEntityRecognizerInterface, ServiceValidatorInterface
from tala.model.device import DeviceAction


class ServiceInterfaceFromDevice(object):
    @classmethod
    def from_device_handler(cls, device_handler):
        play_audio_actions = list(cls._convert_play_audio_actions(device_handler))
        custom_actions = list(cls._convert_actions(device_handler))
        actions = play_audio_actions + custom_actions
        queries = list(cls._convert_queries(device_handler))
        validators = list(cls._convert_validators(device_handler))
        entity_recognizers = list(cls._convert_entity_recognizers(device_handler))
        service_interface = ServiceInterface(actions, queries, entity_recognizers, validators)
        return service_interface

    @classmethod
    def _convert_play_audio_actions(cls, device_handler):
        actions = device_handler.get_actions()
        for name, action in list(actions.items()):
            if hasattr(action, "TYPE") and action.TYPE == DeviceAction.PLAY_AUDIO:
                audio_url_predicate = action.AUDIO_URL_PARAMETER
                audio_url_parameter = AudioURLServiceParameter(audio_url_predicate)
                all_parameters = list(cls.convert_parameters(action.parameters))
                parameters = [parameter for parameter in all_parameters if parameter.name != audio_url_predicate]
                yield PlayAudioActionInterface(name, FrontendTarget(), parameters, audio_url_parameter)

    @classmethod
    def _convert_actions(cls, device_handler):
        actions = device_handler.get_actions()
        for name, action in list(actions.items()):
            if not hasattr(action, "TYPE") or action.TYPE != DeviceAction.PLAY_AUDIO:
                target = DeviceModuleTarget(device_handler.get_name())
                parameters = list(cls.convert_parameters(action.parameters))
                device_failure_reasons = action.FAILURE_REASONS if hasattr(action, "FAILURE_REASONS") else []
                failure_reasons = list(cls._convert_failure_reasons(device_failure_reasons))
                yield ServiceActionInterface(name, target, parameters, failure_reasons)

    @classmethod
    def _convert_queries(cls, device_handler):
        queries = device_handler.get_queries()
        device_name = device_handler.get_name()
        for name, query in list(queries.items()):
            parameters = list(cls.convert_parameters(query.parameters))
            yield ServiceQueryInterface(name, DeviceModuleTarget(device_name), parameters)

    @classmethod
    def _convert_validators(cls, device_handler):
        validities = device_handler.get_validities()
        device_name = device_handler.get_name()
        for name, validity in list(validities.items()):
            parameters = list(cls.convert_parameters(validity.parameters))
            yield ServiceValidatorInterface(name, DeviceModuleTarget(device_name), parameters)

    @classmethod
    def _convert_entity_recognizers(cls, device_handler):
        entity_recognizers = device_handler.get_entity_recognizers()
        device_name = device_handler.get_name()
        for name, entity_recognizer in list(entity_recognizers.items()):
            yield ServiceEntityRecognizerInterface(name, DeviceModuleTarget(device_name))

    @classmethod
    def convert_parameters(cls, device_parameters):
        for parameter in device_parameters:
            name = parameter["name"]
            format = parameter["field"]
            is_optional = parameter["default_value"] is not None
            yield ServiceParameter(name, format, is_optional)

    @classmethod
    def _convert_failure_reasons(cls, device_failure_reasons):
        for reason in device_failure_reasons:
            yield ActionFailureReason(reason)

    @staticmethod
    def to_xml(service_interface):
        template = Template(
            """{%- macro parameters(parameters) %}
{%- if parameters -%}
    <parameters>
{%- for parameter in parameters %}
      <parameter predicate="{{ parameter.name }}" format="{{ parameter.format }}" optional="{% if parameter.is_optional %}true{% else %}false{% endif %}"/>
{%- endfor %}
    </parameters>
{%- else -%}
    <parameters/>
{%- endif -%}
{%- endmacro -%}
{%- macro failure_reasons(failure_reasons) %}
{%- if failure_reasons -%}
    <failure_reasons>
{%- for failure_reason in failure_reasons %}
      <failure_reason name="{{ failure_reason.name }}"/>
{%- endfor %}
    </failure_reasons>
{%- else -%}
    <failure_reasons/>
{%- endif %}
{%- endmacro %}
{%- macro target(target) -%}
    <target>
{%- if target.is_device_module %}
      <device_module device="{{ target.device }}"/>
{%- else %}
      <frontend/>
{%- endif %}
    </target>
{%- endmacro -%}
<?xml version="1.0" encoding="utf-8"?>
<service_interface>
{%- for action in service_interface.actions %}
  <action name="{{ action.name }}">
    {{ parameters(action.parameters) }}
    {{ failure_reasons(action.failure_reasons) }}
    {{ target(action.target) }}
  </action>
{%- endfor %}
{%- for query in service_interface.queries %}
  <query name="{{ query.name }}">
    {{ parameters(query.parameters) }}
    {{ target(query.target) }}
  </query>
{%- endfor %}
{%- for validator in service_interface.validators %}
  <validator name="{{ validator.name }}">
    {{ parameters(validator.parameters) }}
    {{ target(validator.target) }}
  </validator>
{%- endfor %}
{%- for entity_recognizer in service_interface.entity_recognizers %}
  <entity_recognizer name="{{ entity_recognizer.name }}">
    {{ target(entity_recognizer.target) }}
  </entity_recognizer>
{%- endfor %}
</service_interface>
"""
        )
        written_interface = template.render(service_interface=service_interface)
        return written_interface
