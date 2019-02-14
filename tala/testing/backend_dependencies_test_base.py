from mock import Mock

from tala.config import BackendConfig, RasaConfig
from tala.model.ontology import Ontology


class BackendDependenciesTestBase(object):
    def setUp(self):
        self._mock_args = Mock()
        self._result = None
        self._mock_ddds = []
        self._mocked_rasa_component_builder = None

    def given_mock_backend_config(self, MockBackendConfig):
        self._config = BackendConfig.default_config()
        mock_backend_config = MockBackendConfig.return_value
        mock_backend_config.read.return_value = self._config

    def given_mock_ddd_set_loader(self, MockDddSetLoader):
        def mock_ddds_as_list(ddd_names, path=".", *args, **kwargs):
            return [self._get_ddd(name) for name in ddd_names]

        mock_ddd_set_loader = MockDddSetLoader.return_value
        mock_ddd_set_loader.ddds_as_list.side_effect = mock_ddds_as_list

    def _create_mock_ddd(self, name):
        mock_ddd = Mock(name=name)
        mock_ddd.name = name
        return mock_ddd

    def given_ddds(self, ddds):
        self._mock_ddds = [self._create_mock_ddd(name) for name in ddds]
        self._config["ddds"] = ddds

    def given_active_ddd_in_config(self, active_ddd):
        self._config["active_ddd"] = active_ddd

    def given_mock_rasa_config(self, MockRasaConfig):
        self._rasa_config = RasaConfig.default_config()
        mock_rasa_config = MockRasaConfig.return_value
        mock_rasa_config.read.return_value = self._rasa_config

    def given_rasa_enabled_in(self, ddd):
        self._get_ddd(ddd).is_rasa_enabled = True

    def given_mocked_ontology_in(self, ddd):
        self._get_ddd(ddd).ontology = Mock(spec=Ontology)

    def given_mocked_ontology_has_predicates_of_sort(self, ddd, expected_sort):
        def return_true_for_expected_sort(actual_sort):
            return actual_sort == expected_sort

        self._get_ddd(ddd).ontology.predicates_contain_sort.side_effect = return_true_for_expected_sort

    def _create_backend_dependencies(self):
        raise NotImplementedError()

    def _get_ddd(self, name):
        for ddd in self._mock_ddds:
            if ddd.name == name:
                return ddd
        return self._create_mock_ddd(name)

    def given_mock_rasa_loader(self, MockRasaLoader):
        self._mock_rasa_interpreter = MockRasaLoader.create_interpreter.return_value
        self._mock_rasa_loader = MockRasaLoader

    def when_creating_backend_dependencies(self):
        self._create_backend_dependencies()

    def given_rasa_disabled_in(self, ddd):
        self._get_ddd(ddd).is_rasa_enabled = False
