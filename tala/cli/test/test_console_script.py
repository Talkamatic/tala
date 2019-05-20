from mock import patch
from pathlib import Path

from integration_tests.test_console_scripts import ConsoleScriptTestCase
from tala.cli import console_script
from tala.config import BackendConfig


class TestGenerateRASA(ConsoleScriptTestCase):
    def setup(self):
        super(TestGenerateRASA, self).setup()
        self._MockRasaGenerator = None

    @patch('{}.RasaGenerator'.format(console_script.__name__), autospec=True)
    def test_ddd_is_generated_for_first_in_multi_ddd_backend(self, MockRasaGenerator):
        self._given_mock_rasa_generator(MockRasaGenerator)
        self._given_created_ddd_in_a_target_dir("another_ddd")
        self._given_created_ddd_in_a_target_dir("a_ddd")
        with self._given_changed_directory_to_target_dir():
            self._given_multi_ddd_backend()
            self._when_generating("a_ddd")
        self._then_rasa_generator_was_created_for("a_ddd")

    def _given_mock_rasa_generator(self, MockRasaGenerator):
        self._MockRasaGenerator = MockRasaGenerator

    def _given_multi_ddd_backend(self):
        self._replace_in_file(
            Path(BackendConfig.default_name()), '        "a_ddd"', '        "a_ddd",\n        "another_ddd"'
        )

    def _when_generating(self, ddd):
        self._run_tala_with(["generate", "rasa", ddd, "eng"])

    def _then_rasa_generator_was_created_for(self, name):
        args, kwargs = self._MockRasaGenerator.call_args_list[0]
        actual_ddd, actual_language = args
        assert name == actual_ddd.name, "Expected RASA Generator to have been created for DDD '{}' but got '{}'"\
            .format(name, actual_ddd.name)

    @patch('{}.RasaGenerator'.format(console_script.__name__), autospec=True)
    def test_ddd_is_generated_for_second_ddd_in_multi_ddd_backend(self, MockRasaGenerator):
        self._given_mock_rasa_generator(MockRasaGenerator)
        self._given_created_ddd_in_a_target_dir("another_ddd")
        self._given_created_ddd_in_a_target_dir("a_ddd")
        with self._given_changed_directory_to_target_dir():
            self._given_multi_ddd_backend()
            self._when_generating("another_ddd")
        self._then_rasa_generator_was_created_for("another_ddd")
