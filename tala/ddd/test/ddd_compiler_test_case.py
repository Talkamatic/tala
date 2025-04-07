from unittest.mock import Mock

from tala.ddd.services.service_interface import (
    ServiceInterface, ServiceActionInterface, ServiceValidatorInterface, HttpTarget
)


class DddCompilerTestCase(object):
    DDD_NAME = "mockup_ddd_name"

    def setup_method(self):
        self._service_interface = None
        self.mock_service_target = self._create_mock_service_target()

    def _create_mock_service_target(self):
        mock_target = Mock(spec=HttpTarget)
        mock_target.is_frontend = False
        return mock_target

    def _given_service_interface_with_validity(self, validity_name):
        self._create_service_interface(
            validators=[ServiceValidatorInterface(validity_name, self.mock_service_target, parameters=[])]
        )

    def _create_service_interface(self, actions=None, queries=None, validators=None, entity_recognizers=None):
        def has_action(name):
            return any(name == action.name for action in self._service_interface.actions)

        self._service_interface = Mock(spec=ServiceInterface)
        self._service_interface.has_action.side_effect = has_action
        self._service_interface.actions = actions or []
        self._service_interface.queries = queries or []
        self._service_interface.validators = validators or []
        self._service_interface.entity_recognizers = entity_recognizers or []

    def _given_service_interface_without_actions(self):
        self._create_service_interface()

    def _given_service_interface_with_action(self, action_name):
        self._create_service_interface(
            actions=[ServiceActionInterface(action_name, self.mock_service_target, parameters=[], failure_reasons=[])]
        )
