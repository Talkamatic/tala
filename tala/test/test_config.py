import json
import os
import unittest
import tempfile

from mock import patch

from tala.config import Config, DddConfig, BackendConfig, DeploymentsConfig, \
    UnexpectedConfigEntriesException, BackendConfigNotFoundException, DddConfigNotFoundException, \
    DeploymentsConfigNotFoundException, UnexpectedRASALanguageException, DEFAULT_INACTIVE_SECONDS_ALLOWED


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

    def given_default_config(self, mock_default_config, value):
        mock_default_config.return_value = value

    def given_default_name(self, mock_default_name, value):
        mock_default_name.return_value = value

    def when_trying_to_read(self):
        try:
            self.when_reading()
        except UnexpectedConfigEntriesException:
            pass

    def when_reading_then_exception_is_raised_with_message_that_matches_regex(self, exception_class, expected_regex):
        with self.assertRaisesRegexp(exception_class, expected_regex):
            self.when_reading()

    def when_reading(self):
        self._read_config = self._config.read()

    def then_read_config_was(self, config):
        self.assertDictEqual(self._read_config, config)

    def then_config_is(self, filename, expected_config):
        with open(filename) as f:
            actual_config = json.load(f)
        self.assertDictEqual(actual_config, expected_config)

    def then_wrote(self, filename, expected_config):
        with open(filename) as f:
            actual_config = json.load(f)
        self.assertDictEqual(expected_config, actual_config)


class TestConfig(unittest.TestCase, ConfigTester):
    def setUp(self):
        self.setup_configs()

    def tearDown(self):
        self.teardown_configs()

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_key": "mock_value"})
        self.given_created_config_object(Config)
        self.when_reading()
        self.then_read_config_was({"mock_key": "mock_value"})

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read_with_unexpected_and_missing_entry_raises_exception(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_unexpected_key": ""})
        self.given_created_config_object(Config)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException,
            "Parameter mock_unexpected_key is unexpected while mock_key is missing from.*"
            "The config was updated and the previous config was backed up in 'mock\.config\.json\.backup'\."
        )

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read_with_unexpected_entry_raises_exception(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_key": "mock_value", "mock_unexpected_key": ""})
        self.given_created_config_object(Config)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, "Parameter mock_unexpected_key is unexpected in.*"
            "The config was updated and the previous config was backed up in 'mock\.config\.json\.backup'\."
        )

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read_with_missing_entries_raises_exception(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key_1": "mock_value", "mock_key_2": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {})
        self.given_created_config_object(Config)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, "Parameter mock_key_1 and mock_key_2 is missing from.*"
            "The config was updated and the previous config was backed up in 'mock\.config\.json\.backup'\."
        )

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read_with_missing_entries_saves_old_config(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(Config, {"mock_unexpected_key": "mock_unexpected_value"})
        self.given_created_config_object(Config)
        self.when_trying_to_read()
        self.then_config_is(self._config.back_up_name(), {"mock_unexpected_key": "mock_unexpected_value"})

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_read_with_missing_entries_writes_updated_config(self, mock_default_name, mock_default_config):
        self.given_default_config(
            mock_default_config, {
                "mock_key_1": "mock_default_value_1",
                "mock_key_2": "mock_default_value_2"
            }
        )
        self.given_default_name(mock_default_name, "mock.config.json")
        self.given_config_file_exists(
            Config, {
                "mock_unexpected_key": "mock_unexpected_value",
                "mock_key_2": "mock_updated_value_2"
            }
        )
        self.given_created_config_object(Config)
        self.when_trying_to_read()
        self.then_config_is(
            Config.default_name(), {
                "mock_key_1": "mock_default_value_1",
                "mock_key_2": "mock_updated_value_2"
            }
        )

    @patch.object(Config, "default_config")
    @patch.object(Config, "default_name")
    def test_write_default_config(self, mock_default_name, mock_default_config):
        self.given_default_config(mock_default_config, {"mock_key": "mock_value"})
        self.given_default_name(mock_default_name, "mock.config.json")
        self.when_writing_default_config(Config)
        self.then_wrote("mock.config.json", {"mock_key": "mock_value"})

    def when_writing_default_config(self, Config):
        Config.write_default_config()


class TestInheritance(unittest.TestCase, ConfigTester):
    def setUp(self):
        self.setup_configs()

    def tearDown(self):
        self.teardown_configs()

    @patch.object(Config, "default_config")
    def test_override_value_from_parent(self, mock_default_config):
        self.given_default_config(mock_default_config, {"key_to_override": "mock_default_value", "overrides": None})
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
        self.then_read_config_was({"key_to_override": "child_value", "overrides": "parent.config.json"})

    @patch.object(Config, "default_config")
    def test_keep_value_from_parent(self, mock_default_config):
        self.given_default_config(mock_default_config, {"key_to_override": "mock_default_value", "overrides": None})
        self.given_config_file_exists(
            Config, {
                "key_to_override": "parent_value",
                "overrides": None
            }, name="parent.config.json"
        )
        self.given_config_file_exists(Config, {"overrides": "parent.config.json"}, name="child.config.json")
        self.given_created_config_object(Config, "child.config.json")
        self.when_reading()
        self.then_read_config_was({"key_to_override": "parent_value", "overrides": "parent.config.json"})

    def test_read_with_missing_parent_raises_exception(self):
        self.given_config_file_exists(
            BackendConfig, {"overrides": "non_existing_parent.config.json"}, name="child.config.json"
        )
        self.given_created_config_object(BackendConfig, "child.config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            BackendConfigNotFoundException,
            "Expected backend config '.*non_existing_parent\.config\.json' to exist but it was not found\."
        )


class TestDddConfig(unittest.TestCase, ConfigTester):
    def setUp(self):
        self.setup_configs()

    def tearDown(self):
        self.teardown_configs()

    def test_default_name(self):
        self.assertEqual(DddConfig.default_name(), "ddd.config.json")

    def test_default_config(self):
        self.assertEqual(
            DddConfig.default_config(), {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {},
                "overrides": None,
            }
        )

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(DddConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            DddConfigNotFoundException,
            "Expected DDD config '.*non_existing_config\.json' to exist but it was not found\."
        )

    def test_invalid_rasa_nlu_language(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "unsupported-language": {},
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedRASALanguageException,
            "Expected one of the supported RASA languages \['eng'.+\] in DDD config '.+' but got 'unsupported-language'"
        )

    def test_expected_rasa_nlu(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "eng": {
                        "url": "mock-url",
                        "config": {
                            "project": "my-project",
                            "model": "my-model",
                        }
                    },
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading()
        self.then_read_config_was({
            "use_rgl": True,
            "use_third_party_parser": False,
            "device_module": None,
            "word_list": "word_list.txt",
            "rasa_nlu": {
                "eng": {
                    "url": "mock-url",
                    "config": {
                        "project": "my-project",
                        "model": "my-model",
                    }
                },
            },
            "overrides": None,
        })

    def test_unexpected_rasa_nlu_key(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "eng": {
                        "url": "my-url",
                        "config": {},
                        "unexpected-key": "mock-value",
                    },
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException,
            "Parameters \[u'unexpected-key'\] are unexpected in 'rasa_nlu.eng' of DDD config '.+'\."
        )

    def test_missing_url_in_rasa_nlu(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "eng": {
                        "config": {},
                    },
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, "Parameter 'url' is missing from 'rasa_nlu.eng' in DDD config '.+'\."
        )

    def test_missing_config_in_rasa_nlu(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "eng": {
                        "url": "my-url",
                    },
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, "Parameter 'config' is missing from 'rasa_nlu.eng' in DDD config '.+'\."
        )

    def test_missing_keys_in_rasa_nlu(self):
        self.given_config_file_exists(
            DddConfig, {
                "use_rgl": True,
                "use_third_party_parser": False,
                "device_module": None,
                "word_list": "word_list.txt",
                "rasa_nlu": {
                    "eng": {},
                },
                "overrides": None,
            }
        )
        self.given_created_config_object(DddConfig)
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            UnexpectedConfigEntriesException, "Parameter 'url' is missing from 'rasa_nlu.eng' in DDD config '.+'\."
        )


class TestDeploymentsConfig(unittest.TestCase, ConfigTester):
    def setUp(self):
        self.setup_configs()

    def tearDown(self):
        self.teardown_configs()

    def test_default_name(self):
        self.assertEqual(DeploymentsConfig.default_name(), "deployments.config.json")

    def test_default_config(self):
        self.assertEqual(DeploymentsConfig.default_config(), {
            "dev": "https://127.0.0.1:9090/interact",
        })

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(DeploymentsConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            DeploymentsConfigNotFoundException,
            "Expected deployments config '.*non_existing_config\.json' to exist but it was not found\."
        )

    def test_several_environments_allowed(self):
        self.given_config_file_exists(DeploymentsConfig, {"dev": "dev-url", "prod": "prod-url"})
        self.given_created_config_object(DeploymentsConfig)
        self.when_reading()
        self.then_read_config_was({"dev": "dev-url", "prod": "prod-url"})


class TestBackendConfig(unittest.TestCase, ConfigTester):
    def setUp(self):
        self.setup_configs()

    def tearDown(self):
        self.teardown_configs()

    def test_default_name(self):
        self.assertEqual(BackendConfig.default_name(), "backend.config.json")

    def test_default_config(self):
        self.assertEqual(
            BackendConfig.default_config(), {
                "asr": "none",
                "supported_languages": ["eng"],
                "ddds": [""],
                "active_ddd": "",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "use_word_list_correction": False,
                "overrides": None,
                "rerank_amount": 0.2,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )

    def test_default_config_with_ddd_name(self):
        self.assertEqual(
            BackendConfig.default_config(ddd_name="my-ddd"), {
                "asr": "none",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "use_word_list_correction": False,
                "overrides": None,
                "rerank_amount": 0.2,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )

    def test_read_with_missing_config_file_raises_exception(self):
        self.given_created_config_object(BackendConfig, "non_existing_config.json")
        self.when_reading_then_exception_is_raised_with_message_that_matches_regex(
            BackendConfigNotFoundException,
            "Expected backend config '.*non_existing_config\.json' to exist but it was not found\."
        )

    def test_read_with_android_asr_and_missing_use_word_list_correction_sets_it_to_true(self):
        self.given_config_file_exists(
            BackendConfig, {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "overrides": None,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )
        self.given_created_config_object(BackendConfig)
        self.when_trying_to_read()
        self.then_config_is(
            BackendConfig.default_name(), {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "use_word_list_correction": True,
                "overrides": None,
                "rerank_amount": 0.2,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )

    def test_read_with_android_asr_and_something_missing_keeps_use_word_list_correction_if_false(self):
        self.given_config_file_exists(
            BackendConfig, {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "use_word_list_correction": False,
                "overrides": None,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )
        self.given_created_config_object(BackendConfig)
        self.when_trying_to_read()
        self.then_config_is(
            BackendConfig.default_name(), {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "use_word_list_correction": False,
                "overrides": None,
                "rerank_amount": 0.2,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )

    def test_read_with_android_asr_and_something_missing_keeps_use_word_list_correction_if_true(self):
        self.given_config_file_exists(
            BackendConfig, {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "use_word_list_correction": True,
                "overrides": None,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )
        self.given_created_config_object(BackendConfig)
        self.when_trying_to_read()
        self.then_config_is(
            BackendConfig.default_name(), {
                "asr": "android",
                "supported_languages": ["eng"],
                "ddds": ["my-ddd"],
                "active_ddd": "my-ddd",
                "use_recognition_profile": False,
                "repeat_questions": True,
                "use_word_list_correction": True,
                "overrides": None,
                "rerank_amount": 0.2,
                "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
            }
        )

    def test_write_default_config_with_ddd(self):
        self.when_writing_default_config_with_ddd_name("my-ddd")
        self.then_wrote(BackendConfig.default_name(), BackendConfig.default_config(ddd_name="my-ddd"))

    def when_writing_default_config_with_ddd_name(self, ddd_name):
        BackendConfig.write_default_config(ddd_name=ddd_name)
