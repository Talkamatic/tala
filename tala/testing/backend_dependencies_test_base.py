from mock import Mock

from tala.config import BackendConfig
from tala.model.ontology import Ontology
from tala.nl import languages


class BackendDependenciesTestBase(object):
    def setUp(self):
        self._mock_args = Mock()
        self._result = None
        self._mock_ddds = []

    def given_mock_backend_config(self, MockBackendConfig, active_ddd="mock_ddd", ddds=["mock_ddd"],
                                  supported_languages=[languages.ENGLISH]):
        self._config = BackendConfig.default_config(
            active_ddd=active_ddd, ddds=ddds, supported_languages=supported_languages)
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

    def given_mocked_ontology_in(self, ddd):
        self._get_ddd(ddd).ontology = Mock(spec=Ontology)

    def given_mocked_ontology_has_predicates_of_sort(self, ddd, expected_sorts):
        def return_true_for_expected_sort(actual_sort):
            return actual_sort in expected_sorts

        self._get_ddd(ddd).ontology.predicates_contain_sort.side_effect = return_true_for_expected_sort

    def _create_backend_dependencies(self):
        raise NotImplementedError()

    def _get_ddd(self, name):
        for ddd in self._mock_ddds:
            if ddd.name == name:
                return ddd
        return self._create_mock_ddd(name)

    def when_creating_backend_dependencies(self):
        self._create_backend_dependencies()
