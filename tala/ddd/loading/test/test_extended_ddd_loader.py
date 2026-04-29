import os
import warnings
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

    def test_load_json(self):
        self._given_ontology_json_file("mockup_app/ontology.json")
        self._given_domain_json_file("mockup_app/domain.json")
        self._given_service_interface_json_file("mockup_app/service_interface.json")
        self._given_mocked_ddd_config(
            ddd_files={
                "ontology": "ontology.json",
                "domain": "domain.json",
                "service_interface": "service_interface.json",
            }
        )
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_load_json_bundle(self):
        self._given_ddd_bundle_json_file("mockup_app/ddd.json")
        self._given_mocked_ddd_config(ddd_bundle="ddd.json")
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_load_json_bundle_with_goal_children(self):
        self._given_ddd_bundle_with_goal_children("mockup_app/ddd.json")
        self._given_mocked_ddd_config(ddd_bundle="ddd.json")
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_load_json_bundle_with_wrapper(self):
        self._given_ddd_bundle_with_wrapper("mockup_app/ddd.json")
        self._given_mocked_ddd_config(ddd_bundle="ddd.json")
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_load_json_bundle_with_attrs_and_items(self):
        self._given_ddd_bundle_with_attrs_and_items("mockup_app/ddd.json")
        self._given_mocked_ddd_config(ddd_bundle="ddd.json")
        self._when_load_is_called("mockup_app")
        self._then_result_contains_ddd("mockup_app")

    def test_xml_warns_when_json_alternative_exists(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._given_ontology_json_file("mockup_app/ontology.json")
        self._given_domain_json_file("mockup_app/domain.json")
        self._given_service_interface_json_file("mockup_app/service_interface.json")
        original_value = os.environ.get("TALA_XML_WARN")
        os.environ["TALA_XML_WARN"] = "1"

        try:
            with warnings.catch_warnings(record=True) as recorded:
                warnings.simplefilter("always", DeprecationWarning)
                self._when_load_is_called("mockup_app")
        finally:
            if original_value is None:
                os.environ.pop("TALA_XML_WARN", None)
            else:
                os.environ["TALA_XML_WARN"] = original_value

        assert any(issubclass(item.category, DeprecationWarning) for item in recorded)

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
        self.assertEqual(name, self._result.domain.name)

    def test_ontology_field(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_ontology("MockupOntology")

    def _then_loaded_ddd_has_ontology(self, name):
        self.assertEqual(name, self._result.ontology.name)

    def test_service_interface_is_loaded(self):
        self._given_ontology_xml_file("mockup_app/ontology.xml")
        self._given_domain_xml_file("mockup_app/domain.xml")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._when_load_is_called("mockup_app")
        self._then_loaded_ddd_has_service_interface()

    def _then_loaded_ddd_has_service_interface(self):
        self.assertTrue(isinstance(self._result.service_interface, ServiceInterface))

    def _given_ontology_json_file(self, path):
        content = '{"ontology": {"@": {"name": "MockupOntology"}}}'
        self.create_mockup_file(path, content)

    def _given_domain_json_file(self, path):
        content = '{"domain": {"@": {"name": "MockupDomain"}}}'
        self.create_mockup_file(path, content)

    def _given_service_interface_json_file(self, path):
        content = '{"service_interface": {}}'
        self.create_mockup_file(path, content)

    def _given_ddd_bundle_json_file(self, path):
        content = (
            '{"ontology": {"@": {"name": "MockupOntology"}}, '
            '"domain": {"@": {"name": "MockupDomain"}}, '
            '"service_interface": {}}'
        )
        self.create_mockup_file(path, "".join(content))

    def _given_ddd_bundle_with_goal_children(self, path):
        content = (
            '{"ontology": {"@": {"name": "MockupOntology"}}, '
            '"domain": {"@": {"name": "MockupDomain"}, "goal": {"perform": {"@": {"action": "top"}}}}, '
            '"service_interface": {}}'
        )
        self.create_mockup_file(path, "".join(content))

    def _given_ddd_bundle_with_wrapper(self, path):
        content = (
            '{"ddd": {'
            '"schema_version": "1.0", '
            '"ontology": {"@": {"name": "MockupOntology"}}, '
            '"domain": {"@": {"name": "MockupDomain"}}, '
            '"service_interface": {}}'
            '}'
        )
        self.create_mockup_file(path, "".join(content))

    def _given_ddd_bundle_with_attrs_and_items(self, path):
        content = (
            '{"ontology": {"attrs": {"name": "MockupOntology"}}, '
            '"domain": {"attrs": {"name": "MockupDomain"}, '
            '"items": [{"goal": {"perform": {"attrs": {"action": "top"}}}}]}, '
            '"service_interface": {}}'
        )
        self.create_mockup_file(path, "".join(content))

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
