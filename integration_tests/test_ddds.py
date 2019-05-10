from pathlib import Path
import pytest

from tala.cli import console_script
from tala.utils.chdir import chdir


class TestDDDs(object):
    @pytest.mark.parametrize(
        "backend_config", [
            "hello_world.json",
            "http_service.config.json",
            "incremental_search.config.json",
            "literals_grammar.json",
            "mockup_travel.json",
            "partial_parsing.json",
            "rasa_answers.config.json",
            "rasa_for_dynamic_entities.config.json",
            "rasa_for_rgl.config.json",
            "rasa_for_static_entities.config.json",
            "rasa_numbers.config.json",
            "rasa_strings.config.json",
            "datetime.config.json",
            "send_to_frontend.config.json",
            "small_grammar.json",
            "tidePooler.json",
        ]
    )
    def test_verify_on_ddd(self, backend_config):
        with self._given_changed_to_ddd_directory():
            self._when_verifying_with(backend_config)
            self._then_no_errors_occured()

    def _given_changed_to_ddd_directory(self):
        directory = Path("tala") / "ddds"
        return chdir(directory)

    def _when_verifying_with(self, backend_config):
        console_script.main(["verify", "--config", backend_config])

    def _then_no_errors_occured(self):
        pass

    def test_verify_on_multiple_ddds(self):
        with self._given_changed_to_multi_ddd_directory():
            self._when_verifying()
            self._then_no_errors_occured()

    def _given_changed_to_multi_ddd_directory(self):
        directory = Path("tala") / "ddds" / "multi_ddd"
        return chdir(directory)

    def _when_verifying(self):
        console_script.main(["verify"])
