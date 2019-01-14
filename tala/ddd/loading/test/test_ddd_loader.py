from mock import patch

from tala.config import BackendConfig
from tala.ddd.loading import ddd_loader
from tala.ddd.loading.ddd_loader import DDDLoader
from tala.testing.ddd_mocker import DddMockingTestCase


class TestDDDLoader(DddMockingTestCase):
    def setUp(self):
        self._backend_config = BackendConfig.default_config()
        DddMockingTestCase.setUp(self)

    def tearDown(self):
        DddMockingTestCase.tearDown(self)

    def _when_load_is_called(self, ddd_name, languages=None):
        with patch('%s.warnings' % ddd_loader.__name__) as mock_warnings:
            self._mock_warnings = mock_warnings
            languages = languages or ["eng"]
            mock_ddd_loader = DDDLoader(ddd_name, self._mock_ddd_config, languages)
            self._result = mock_ddd_loader.load()

    def test_loading_with_rasa_posts_warning_message(self):
        self._given_ontology_py_file("mockup_app/ontology.py")
        self._given_domain_py_file("mockup_app/domain.py")
        self._given_service_interface_xml_file("mockup_app/service_interface.xml")
        self._given_device_py_file("mockup_app/device.py")
        self._given_mocked_ddd_config(enable_rasa_nlu=True)
        self._when_load_is_called("mockup_app")
        self._then_warning_message_is_posted(
            "The support for RASA NLU is still in BETA. Talk gently. "
            "It is currently enabled in DDD 'mockup_app'."
        )

    def _then_warning_message_is_posted(self, expected_warning):
        self._mock_warnings.warn.assert_any_call(expected_warning)
