import json
import os
import tempfile

from unittest.mock import patch
import pytest

from tala.config import Config, DddConfig, BackendConfig, DeploymentsConfig, \
    UnexpectedConfigEntriesException, BackendConfigNotFoundException, DddConfigNotFoundException, \
    DeploymentsConfigNotFoundException, OptionalConfigField, \
    MandatoryConfigField, MissingMandatoryConfigEntryException


class ConfigTester(object):
    def setup_configs(self):
        self.configs = {}
        self._working_dir = os.getcwd()
        temp_dir = tempfile.mkdtemp(prefix="TestConfig")
        os.chdir(temp_dir)

    def teardown_configs(self):
        os.chdir(self._working_dir)

    def given_config_file_exists(self, *args, **kwargs):
        self._create_config_file(*args, **kwargs)

    def _create_config_file(self, ConfigClass, config, name=None):
        if name is None:
            name = ConfigClass.default_name()
        self._write_config(name, config)

    def _write_config(self, name, config):
        with open(name, 'w') as f:
            json.dump(config, f)

    def given_created_config_object(self, ConfigClass, path=None):
        self._config = ConfigClass(path)

    def given_fields(self, mock_fields, return_value):
        mock_fields.return_value = return_value

    def given_default_name(self, mock_default_name, value):
        mock_default_name.return_value = value

    def when_trying_to_read(self):
        try:
            self.when_reading()
        except UnexpectedConfigEntriesException:
            pass

    def when_reading_then_exception_is_raised_with_message_that_matches_regex(self, exception_class, expected_regex):
        with pytest.raises(exception_class, match=expected_regex):
            self.when_reading()

    def when_reading(self):
        self._result = self._config.read()

    def when_calling_default_config(self, **kwargs):
        self._result = self._config.default_config(**kwargs)

    def when_calling_default_config_then_exception_is_raised_with_message_matching_regex(
        self, exception_class, expected_regex, **kwargs
    ):
        with pytest.raises(exception_class, match=expected_regex):
            self._config.default_config(**kwargs)

    def then_result_is(self, expected):
        assert self._result == expected

    def then_config_is(self, filename, expected_config):
        with open(filename) as f:
            actual_config = json.load(f)
        assert actual_config == expected_config

    def then_wrote(self, filename, expected_config):
        with open(filename) as f:
            actual_config = json.load(f)
        assert actual_config == expected_config

    def then_result_has_key_value_pair(self, key, expected_value):
        assert self._result[key] == expected_value


class TestConfig(ConfigTester):
    def setup_method(self):
        self.setup_configs()

    def teardown_method(self):
        self.teardown_configs()

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"mock_key": OptionalConfigField(default_value="mock_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_key": "mock_value"})
        self.given_created_config_object(Config)
        self.when_reading()
        self.then_result_is({"mock_key": "mock_value"})

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read_with_unexpected_entry_raises_exception(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"mock_key": OptionalConfigField(default_value="mock_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_key": "mock_value", "mock_unexpected_key": ""})
        self.given_created_config_object(Config)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, r"Parameters \['mock_unexpected_key'\] are unexpected in.*"
            r"The config was updated and the previous config was backed up in 'mock\.config\.json\.backup'\."
        )

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read_with_missing_optional_entries_does_not_modify_file(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"mock_key": OptionalConfigField(default_value="mock_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {})
        self.given_created_config_object(Config)
        self.when_trying_to_read()
        self.then_config_is("mock.config.json", {})

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read_returns_default_value_for_missing_optional_entry(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"mock_key": OptionalConfigField(default_value="mock_default_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {})
        self.given_created_config_object(Config)
        self.when_trying_to_read()
        self.then_result_is({"mock_key": "mock_default_value"})

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_default_config_returns_default_value_if_not_overridden(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"key": OptionalConfigField(default_value="default_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_created_config_object(Config)
        self.when_calling_default_config()
        self.then_result_has_key_value_pair("key", "default_value")

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_default_config_returns_overridden_value_if_overridden(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"key": OptionalConfigField(default_value="default_value")})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_created_config_object(Config)
        self.when_calling_default_config(key="overridden_value")
        self.then_result_has_key_value_pair("key", "overridden_value")

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_default_config_raises_exception_if_required_field_is_missing(self, mock_default_name, mock_fields):
        self.given_fields(
            mock_fields, {
                "mandatory_key": MandatoryConfigField(),
                "optional_key": OptionalConfigField(default_value="default_value")
            }
        )
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_created_config_object(Config)
        self.when_calling_default_config_then_exception_is_raised_with_message_matching_regex(
            MissingMandatoryConfigEntryException,
            r"Expected mandatory entry 'mandatory_key' but it is missing among entries \['optional_key'\]\.",
            optional_key="mock_value"
        )

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_write_default_config(self, mock_default_name, mock_fields):
        self.given_fields(
            mock_fields, {
                "optional_key": OptionalConfigField(default_value="default_value"),
                "mandatory_key": MandatoryConfigField()
            }
        )
        self.given_default_name(mock_default_name, "mock.config.json")
        self.when_writing_default_config(Config, mandatory_key="value_for_mandatory_field")
        self.then_wrote(
            "mock.config.json", {
                "optional_key": "default_value",
                "mandatory_key": "value_for_mandatory_field"
            }
        )

    def when_writing_default_config(self, Config, **kwargs):
        Config.write_default_config(**kwargs)

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read_with_missing_mandatory_field_raises_exception(self, mock_default_name, mock_fields):
        self.given_fields(
            mock_fields, {
                "mandatory_key": MandatoryConfigField(),
                "optional_key": OptionalConfigField(default_value="default_value"),
            }
        )
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"optional_key": "mock_value"})
        self.given_created_config_object(Config)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            MissingMandatoryConfigEntryException,
            r"Expected mandatory entry 'mandatory_key' in 'mock\.config\.json' but it is missing among "
            r"entries \['optional_key'\]\."
        )


class TestInheritance(ConfigTester):
    def setup_method(self):
        self.setup_configs()

    def teardown_method(self):
        self.teardown_configs()

    @patch.object(Config, "fields")
    def test_override_value_from_parent(self, mock_fields):
        self.given_fields(mock_fields, {"key_to_override": OptionalConfigField(default_value="mock_default_value")})
        self.given_config_file_exists(
            Config, {
                "key_to_override": "parent_value",
                "overrides": None
            }, name="parent.config.json"
        )
        self.given_config_file_exists(
            Config, {
                "overrides": "parent.config.json",
                "key_to_override": "child_value"
            }, name="child.config.json"
        )
        self.given_created_config_object(Config, "child.config.json")
        self.when_reading()
        self.then_result_is({"key_to_override": "child_value", "overrides": "parent.config.json"})

    @patch.object(Config, "fields")
    def test_keep_value_from_parent(self, mock_fields):
        self.given_fields(mock_fields, {"key_to_override": OptionalConfigField(default_value="mock_default_value")})
        self.given_config_file_exists(
            Config, {
                "key_to_override": "parent_value",
                "overrides": None
            }, name="parent.config.json"
        )
        self.given_config_file_exists(Config, {"overrides": "parent.config.json"}, name="child.config.json")
        self.given_created_config_object(Config, "child.config.json")
        self.when_reading()
        self.then_result_is({"key_to_override": "parent_value", "overrides": "parent.config.json"})

    @patch.object(Config, "fields")
    def test_read_with_missing_parent_raises_exception(self, mock_fields):
        self.given_fields(mock_fields, {})
        self.given_config_file_exists(
            BackendConfig, {"overrides": "non_existing_parent.config.json"}, name="child.config.json"
        )
        self.given_created_config_object(BackendConfig, "child.config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            BackendConfigNotFoundException,
            r"Expected backend config '.*non_existing_parent\.config\.json' to exist but it was not found\."
        )

    @patch.object(Config, "fields")
    @patch.object(Config, "default_name")
    def test_read_does_not_yield_exception_if_mandatory_field_is_inherited(self, mock_default_name, mock_fields):
        self.given_fields(mock_fields, {"mock_key": MandatoryConfigField()})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(
            Config, {
                "mock_key": "parent_value",
                "overrides": None
            }, name="parent.config.json"
        )
        self.given_config_file_exists(Config, {"overrides": "parent.config.json"})
        self.given_created_config_object(Config)
        self.when_reading()
        self.then_no_exception_is_raised()

    def then_no_exception_is_raised(self):
        pass


class TestDddConfig(ConfigTester):
    def setup_method(self):
        self.setup_configs()

    def teardown_method(self):
        self.teardown_configs()

    def test_default_name(self):
        assert DddConfig.default_name() == "ddd.config.json"

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(DddConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            DddConfigNotFoundException,
            r"Expected DDD config '.*non_existing_config\.json' to exist but it was not found\."
        )


class TestDeploymentsConfig(ConfigTester):
    def setup_method(self):
        self.setup_configs()

    def teardown_method(self):
        self.teardown_configs()

    def test_default_name(self):
        assert DeploymentsConfig.default_name() == "deployments.config.json"

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(DeploymentsConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            DeploymentsConfigNotFoundException,
            r"Expected deployments config '.*non_existing_config\.json' to exist but it was not found\."
        )

    def test_several_environments_allowed(self):
        self.given_config_file_exists(DeploymentsConfig, {"dev": "dev-url", "prod": "prod-url"})
        self.given_created_config_object(DeploymentsConfig)
        self.when_reading()
        self.then_result_is({"dev": "dev-url", "prod": "prod-url"})

    def test_get_url_when_deployment_exists_in_deployment_config(self):
        self.given_config_file_exists(DeploymentsConfig, {"dev": "dev-url", "prod": "prod-url"})
        self.given_created_config_object(DeploymentsConfig)
        self.when_getting_url_for("dev")
        self.then_url_was("dev-url")

    def when_getting_url_for(self, deployment):
        self._url = self._config.get_url(deployment)

    def then_url_was(self, expected_url):
        assert self._url == expected_url

    def test_get_url_when_deployment_is_missing_in_deployment_config(self):
        self.given_config_file_exists(DeploymentsConfig, {"dev": "dev-url", "prod": "prod-url"})
        self.given_created_config_object(DeploymentsConfig)
        self.when_getting_url_for("my.ddd.tala.cloud")
        self.then_url_was("my.ddd.tala.cloud")

    def test_get_url_when_deployment_config_is_missing(self):
        self.given_created_config_object(DeploymentsConfig)
        self.when_getting_url_for("my.ddd.tala.cloud")
        self.then_url_was("my.ddd.tala.cloud")


class TestBackendConfig(ConfigTester):
    def setup_method(self):
        self.setup_configs()

    def teardown_method(self):
        self.teardown_configs()

    def test_default_name(self):
        assert BackendConfig.default_name() == "backend.config.json"

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(BackendConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            BackendConfigNotFoundException,
            r"Expected backend config '.*non_existing_config\.json' to exist but it was not found\."
        )

    def test_write_default_config_with_ddd(self):
        self.when_writing_default_config_with_ddd_name("my-ddd")
        self.then_wrote(
            BackendConfig.default_name(),
            BackendConfig.default_config(ddds=["my-ddd"], active_ddd="my-ddd", supported_languages="none")
        )

    def when_writing_default_config_with_ddd_name(self, ddd_name):
        BackendConfig.write_default_config(ddd_name=ddd_name)
