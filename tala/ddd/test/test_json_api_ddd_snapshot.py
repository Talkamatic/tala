import json
from pathlib import Path

from tala.model.ddd import DDD


class TestJSONAPIDDDCompatibility:
    def test_parses_json_api_snapshot(self):
        self.given_json_api_snapshot()

        self.when_parsing_ddd()

        self.then_ddd_matches_snapshot()

    def test_parses_snapshot_without_version_id(self):
        self.given_json_api_snapshot()
        self.given_snapshot_without_version_id()

        self.when_parsing_ddd()

        self.then_ddd_matches_snapshot()

    def given_json_api_snapshot(self):
        fixture_path = Path(__file__).parent / "fixtures" / "hello_world_ddd.json"
        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            self._snapshot = json.load(fixture_file)
        self._snapshot_input = self._snapshot

    def given_snapshot_without_version_id(self):
        self._snapshot_input = self._remove_version_id(self._snapshot)

    def when_parsing_ddd(self):
        self._parsed_ddd = DDD.create_from_json_api_data(self._snapshot_input)

    def then_ddd_matches_snapshot(self):
        expected_name = self._snapshot_input["data"]["attributes"]["name"]
        expected_ontology = self._snapshot_input["data"]["relationships"]["ontology"]["data"]["id"]
        expected_domain = self._expected_domain_name()

        assert self._parsed_ddd.name == expected_name
        assert self._parsed_ddd.ontology.name == expected_ontology
        assert self._parsed_ddd.domain.get_name() == expected_domain
        assert self._parsed_ddd.service_interface is not None

    def _expected_domain_name(self):
        domain_id = self._snapshot_input["data"]["relationships"]["domain"]["data"]["id"]
        for included in self._snapshot_input.get("included", []):
            if included.get("type") == "tala.model.domain" and included.get("id") == domain_id:
                attributes = included.get("attributes", {})
                return attributes.get("tala.model.domain.Domain.user_defined_name", domain_id)
        return domain_id

    def _remove_version_id(self, payload):
        if isinstance(payload, dict):
            cleaned = {}
            for key, value in payload.items():
                if key == "version:id":
                    continue
                cleaned[key] = self._remove_version_id(value)
            return cleaned
        if isinstance(payload, list):
            return [self._remove_version_id(item) for item in payload]
        return payload
