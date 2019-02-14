import unittest
import warnings

from mock import patch, call

from tala.backend import dependencies
from tala.backend.dependencies.for_generating import BackendDependenciesForGenerating
from tala.testing.backend_dependencies_test_base import BackendDependenciesTestBase
from tala.model.sort import DATETIME, INTEGER


class BackendDependenciesForGeneratingTestCase(BackendDependenciesTestBase, unittest.TestCase):
    def setUp(self):
        super(BackendDependenciesForGeneratingTestCase, self).setUp()
        self._config = None
        self._backend_dependencies = None
        self._rasa_config = None
        self._mock_rasa_interpreter = None
        self._mock_rasa_loader = None

    @patch("%s.for_generating.RasaConfig" % dependencies.__name__, autospec=True)
    @patch("%s.abstract_backend_dependencies.BackendConfig" % dependencies.__name__, autospec=True)
    @patch("%s.for_generating.DDDSetLoader" % dependencies.__name__, autospec=True)
    def test_duckling_disabled_with_datetime_predicates_in_ontology_issues_warning(
        self, DddSetLoader, BackendConfig, RasaConfig
    ):
        self.given_mock_backend_config(BackendConfig)
        self.given_mock_ddd_set_loader(DddSetLoader)
        self.given_mock_rasa_config(RasaConfig)
        self.given_ddds(["mock_ddd"])
        self.given_active_ddd_in_config("mock_ddd")
        self.given_rasa_enabled_in("mock_ddd")
        self.given_mocked_ontology_in("mock_ddd")
        self.given_mocked_ontology_has_predicates_of_sort("mock_ddd", DATETIME)
        self.given_duckling_disabled_in_rasa_config()
        self.when_create_backend_dependencies_then_warning_is_issued_matching(
            "DDD 'mock_ddd' contains predicates of the 'datetime' sort, but duckling is disabled. "
            "'datetime' entities won't be recognized in NLU."
        )

    def given_duckling_disabled_in_rasa_config(self):
        self._rasa_config["enable_duckling"] = False

    def when_create_backend_dependencies_then_warning_is_issued_matching(self, expected_warning):
        with patch("{}.for_generating.warnings".format(dependencies.__name__), spec=warnings) as mock_warnings:
            self._create_backend_dependencies()
            mock_warnings.warn.assert_has_calls([call(expected_warning)])

    @patch("%s.for_generating.RasaConfig" % dependencies.__name__, autospec=True)
    @patch("%s.abstract_backend_dependencies.BackendConfig" % dependencies.__name__, autospec=True)
    @patch("%s.for_generating.DDDSetLoader" % dependencies.__name__, autospec=True)
    def test_duckling_disabled_with_integer_predicates_in_ontology_issues_warning(
        self, DddSetLoader, BackendConfig, RasaConfig
    ):
        self.given_mock_backend_config(BackendConfig)
        self.given_mock_ddd_set_loader(DddSetLoader)
        self.given_mock_rasa_config(RasaConfig)
        self.given_ddds(["mock_ddd"])
        self.given_active_ddd_in_config("mock_ddd")
        self.given_rasa_enabled_in("mock_ddd")
        self.given_mocked_ontology_in("mock_ddd")
        self.given_mocked_ontology_has_predicates_of_sort("mock_ddd", INTEGER)
        self.given_duckling_disabled_in_rasa_config()
        self.when_create_backend_dependencies_then_warning_is_issued_matching(
            "DDD 'mock_ddd' contains predicates of the 'integer' sort, but duckling is disabled. "
            "Accuracy for 'integer' entities will be reduced in NLU."
        )

    @patch("%s.for_generating.RasaConfig" % dependencies.__name__, autospec=True)
    @patch("%s.abstract_backend_dependencies.BackendConfig" % dependencies.__name__, autospec=True)
    @patch("%s.for_generating.DDDSetLoader" % dependencies.__name__, autospec=True)
    def test_duckling_disabled_but_no_predicates_of_duckling_sorts_in_ontology_issues_no_warnings(
        self, DddSetLoader, BackendConfig, RasaConfig
    ):
        self.given_mock_backend_config(BackendConfig)
        self.given_mock_ddd_set_loader(DddSetLoader)
        self.given_mock_rasa_config(RasaConfig)
        self.given_ddds(["mock_ddd"])
        self.given_active_ddd_in_config("mock_ddd")
        self.given_rasa_enabled_in("mock_ddd")
        self.given_mocked_ontology_in("mock_ddd")
        self.given_mocked_ontology_has_no_predicates_of_any_sorts("mock_ddd")
        self.given_duckling_disabled_in_rasa_config()
        self.when_create_backend_dependencies_then_no_warnings_are_issued()

    def given_mocked_ontology_has_no_predicates_of_any_sorts(self, ddd):
        self._get_ddd(ddd).ontology.predicates_contain_sort.return_value = False

    def when_create_backend_dependencies_then_no_warnings_are_issued(self):
        with patch("{}.for_generating.warnings".format(dependencies.__name__), spec=warnings) as mock_warnings:
            self._create_backend_dependencies()
            mock_warnings.warn.assert_not_called()

    @patch("%s.for_generating.RasaConfig" % dependencies.__name__, autospec=True)
    @patch("%s.abstract_backend_dependencies.BackendConfig" % dependencies.__name__, autospec=True)
    @patch("%s.for_generating.DDDSetLoader" % dependencies.__name__, autospec=True)
    def test_rasa_disabled_with_datetime_predicates_in_ontology_issues_warning(
        self, DddSetLoader, BackendConfig, RasaConfig
    ):
        self.given_mock_backend_config(BackendConfig)
        self.given_mock_ddd_set_loader(DddSetLoader)
        self.given_mock_rasa_config(RasaConfig)
        self.given_ddds(["mock_ddd"])
        self.given_active_ddd_in_config("mock_ddd")
        self.given_rasa_disabled_in("mock_ddd")
        self.given_mocked_ontology_in("mock_ddd")
        self.given_mocked_ontology_has_predicates_of_sort("mock_ddd", DATETIME)
        self.when_create_backend_dependencies_then_warning_is_issued_matching(
            "DDD 'mock_ddd' contains predicates of the 'datetime' sort, but RASA NLU is disabled. "
            "'datetime' entities won't be recognized in NLU."
        )

    @patch("%s.for_generating.RasaConfig" % dependencies.__name__, autospec=True)
    @patch("%s.abstract_backend_dependencies.BackendConfig" % dependencies.__name__, autospec=True)
    @patch("%s.for_generating.DDDSetLoader" % dependencies.__name__, autospec=True)
    def test_rasa_disabled_but_no_predicates_of_datetime_sort_in_ontology_issues_no_warnings(
        self, DddSetLoader, BackendConfig, RasaConfig
    ):
        self.given_mock_backend_config(BackendConfig)
        self.given_mock_ddd_set_loader(DddSetLoader)
        self.given_mock_rasa_config(RasaConfig)
        self.given_ddds(["mock_ddd"])
        self.given_active_ddd_in_config("mock_ddd")
        self.given_rasa_disabled_in("mock_ddd")
        self.given_mocked_ontology_in("mock_ddd")
        self.given_mocked_ontology_has_no_predicates_of_any_sorts("mock_ddd")
        self.when_create_backend_dependencies_then_no_warnings_are_issued()

    def _create_backend_dependencies(self):
        self._backend_dependencies = BackendDependenciesForGenerating(self._mock_args)
