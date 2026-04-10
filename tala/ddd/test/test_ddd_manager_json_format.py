import pytest

from tala.ddd.ddd_manager import DDDManager, LegacyDddJsonFormatException


class TestDDDManagerJSONFormat:
    def test_rejects_legacy_ddd_json(self):
        self.given_ddd_manager()
        self.given_legacy_ddd_json()

        self.when_loading_ddd()

        self.then_legacy_format_error_is_raised()

    def given_ddd_manager(self):
        self._ddd_manager = DDDManager()

    def given_legacy_ddd_json(self):
        self._legacy_ddd = {"ddd_name": "legacy_ddd"}
        self._ddd_manager.add_ddds_as_json(["legacy_ddd"], [self._legacy_ddd])

    def when_loading_ddd(self):
        self._error = pytest.raises(
            LegacyDddJsonFormatException,
            self._ddd_manager.get_ddd,
            "legacy_ddd",
        )

    def then_legacy_format_error_is_raised(self):
        assert "Legacy DDD JSON format is no longer supported" in str(self._error.value)
