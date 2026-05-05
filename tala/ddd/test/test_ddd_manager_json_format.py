import json
from pathlib import Path
import pytest

from tala.ddd.ddd_manager import DDDManager, DddJsonFormatException


class TestDDDManagerJSONFormat:
    def test_rejects_legacy_ddd_json(self):
        self.given_ddd_manager()
        self.given_legacy_ddd_json()

        self.when_loading_ddd_expecting_error()

    def test_accepts_json_api_ddd_json_without_warning(self):
        self.given_ddd_manager()
        self.given_json_api_ddd_json()

        self.when_loading_json_api_ddd_without_warning()

        self.then_json_api_format_is_loaded()

    def given_ddd_manager(self):
        self._ddd_manager = DDDManager()

    def given_legacy_ddd_json(self):
        self._legacy_ddd = {"ddd_name": "legacy_ddd"}
        self._ddd_manager.add_ddds_as_json(["legacy_ddd"], [self._legacy_ddd])

    def given_json_api_ddd_json(self):
        fixture_path = Path(__file__).parent / "fixtures" / "hello_world_ddd.json"
        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            self._json_api_ddd = json.load(fixture_file)
        self._ddd_manager.add_ddds_as_json([self._json_api_ddd["data"]["attributes"]["name"]], [self._json_api_ddd])

    def when_loading_ddd_expecting_error(self):
        with pytest.raises(DddJsonFormatException):
            self._ddd_manager.get_ddd("legacy_ddd")

    def when_loading_json_api_ddd_without_warning(self):
        self._json_api_name = self._json_api_ddd["data"]["attributes"]["name"]
        self._ddd_manager.get_ddd(self._json_api_name)

    def then_json_api_format_is_loaded(self):
        assert self._json_api_name in self._ddd_manager._ddds
