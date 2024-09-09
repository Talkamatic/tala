from unittest.mock import Mock

from tala.config import BackendConfig
from tala.ddd.ddd_manager import DDDManager
from tala.ddd.loading.ddd_loader import DDDLoaderException
from tala.ddd.services.service_interface import ServiceInterface
from tala.testing.ddd_mocker import DddMockingTestCase
from tala.log import logger

from tala.ddd.loading.extended_ddd_loader import ExtendedDDDLoader


class TestExtendedDDDLoader(DddMockingTestCase):
    def setUp(self):
        self.test_logger = logger.configure_and_get_test_logger()
        self._backend_config = BackendConfig.default_config(active_ddd="mockup_app", ddds=["mockup_app"])
        self._mocked_rasa_component_builder = None
        DddMockingTestCase.setUp(self)
        self._mock_warnings = None
        self._MockRasaDDDInterpreter = None
        self._mocked_gf_ddd_interpreter = None
        self._mocked_ontology = None
        self._mocked_grammar = None

    def tearDown(self):
        DddMockingTestCase.tearDown(self)

    def test_load_xml(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def _then_result_contains_ddd(self, ddd_name):
        ddd = self._result
        self.assertEqual(ddd_name, ddd.name)
        ddd.ontology
        ddd.domain

    def test_name_field(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_name("mockup_app")

    def _then_loaded_ddd_has_name(self, name):
        self.assertEqual(name, self._result.name)

    def test_domain_field(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_domain("MockupDomain")

    def _then_loaded_ddd_has_domain(self, name):
        self.assertEqual(name, self._result.domain.get_name())

    def test_ontology_field(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_ontology("MockupOntology")

    def _then_loaded_ddd_has_ontology(self, name):
        self.assertEqual(name, self._result.ontology.get_name())

    def test_service_interface_is_loaded(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_service_interface()

    def _then_loaded_ddd_has_service_interface(self):
        self.assertTrue(isinstance(self._result.service_interface, ServiceInterface))

    def test_missing_service_interface_raises_exception(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._when_load_is_called_then_exception_is_raised_matching(
            "mockup_app", DDDLoaderException, "Expected 'service_interface.xml' to exist but it does not"
        )

    def _when_load_is_called_then_exception_is_raised_matching(self, ddd, expected_exception, expected_pattern):
        with self.assertRaisesRegex(expected_exception, expected_pattern):
            self._when_load_is_called(ddd)

    def _when_load_is_called(self, *args, **kwargs):
        self._load(*args, **kwargs)

    def _load(self, ddd_name):
        mock_ddd_manager = Mock(spec=DDDManager)
        mock_ddd_loader = MockExtendedDDDLoader(
            ddd_manager=mock_ddd_manager,
            name=ddd_name,
            ddd_config=self._mock_ddd_config,
            rerank_amount=self._backend_config["rerank_amount"]
        )
        self._result = mock_ddd_loader.load()

    def test_load_without_device_module(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._given_mocked_ddd_config(device_module=None)
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_path_field(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_path("%s/mockup_app" % self._temp_dir)

    def _then_loaded_ddd_has_path(self, path):
        self.assertEqual(path, self._result.path)


class MockExtendedDDDLoader(ExtendedDDDLoader):
    def _load_ddds_as_dict(self):
        return self.ddds_as_dict
