import json
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tala.ddd.ddd_manager import DDDManager
from tala.ddd.services.service_interface import ServiceInterface
from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.ontology import Ontology


class TestDDDManagerJSONFormat:
    def test_accepts_legacy_ddd_json_with_warning(self):
        self.given_ddd_manager()
        self.given_legacy_ddd_json()

        self.when_loading_ddd_expecting_warning()

        self.then_legacy_format_is_loaded()

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

    def when_loading_ddd_expecting_warning(self):
        with patch("tala.ddd.ddd_manager.JSONDDDParser.parse") as parse_mock:
            parse_mock.return_value = self._create_legacy_ddd()
            with pytest.warns(DeprecationWarning):
                self._ddd_manager.get_ddd("legacy_ddd")

    def when_loading_json_api_ddd_without_warning(self):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            self._json_api_name = self._json_api_ddd["data"]["attributes"]["name"]
            self._ddd_manager.get_ddd(self._json_api_name)
            self._warnings = recorded

    def then_legacy_format_is_loaded(self):
        assert "legacy_ddd" in self._ddd_manager._ddds

    def then_json_api_format_is_loaded(self):
        assert self._json_api_name in self._ddd_manager._ddds
        assert not any(issubclass(warning.category, DeprecationWarning) for warning in self._warnings)

    def _create_legacy_ddd(self):
        ontology = Ontology("legacy_ontology", set(), set(), {}, set())
        domain = Domain("legacy_ddd", "legacy_domain", ontology)
        service_interface = Mock(spec=ServiceInterface)
        return DDD("legacy_ddd", ontology, domain, service_interface=service_interface)
