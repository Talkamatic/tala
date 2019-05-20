import json
import datetime

from pathlib import Path

from tala.nl.languages import SUPPORTED_RASA_LANGUAGES
from tala.utils.text_formatting import readable_list

DEFAULT_INACTIVE_SECONDS_ALLOWED = datetime.timedelta(hours=2).seconds


class ConfigNotFoundException(Exception):
    def __init__(self, message, config_path):
        self._config_path = config_path
        super(ConfigNotFoundException, self).__init__(message)

    @property
    def config_path(self):
        return self._config_path


class BackendConfigNotFoundException(ConfigNotFoundException):
    pass


class DddConfigNotFoundException(ConfigNotFoundException):
    pass


class DeploymentsConfigNotFoundException(ConfigNotFoundException):
    pass


class UnexpectedConfigEntriesException(Exception):
    pass


class UnexpectedRASALanguageException(Exception):
    pass


class Config(object):
    def __init__(self, path=None):
        path = path or self.default_name()
        self._path = Path(path)

    @property
    def _absolute_path(self):
        return Path.cwd() / self._path

    def read(self):
        if not self._path.exists():
            self._handle_non_existing_config_file()
        self._potentially_update_and_backup_config()
        config = self._config_from_file()
        config = self._potentially_update_with_values_from_parent(config)
        return config

    def _handle_non_existing_config_file(self):
        self._raise_config_not_found_exception()

    def _write(self, config):
        self._write_to_file(config, self._path)

    @classmethod
    def write_default_config(cls, path=None):
        path = path or cls.default_name()
        cls._write_to_file(cls.default_config(), Path(path))

    def _write_backup(self, config):
        path = Path(self.back_up_name())
        self._write_to_file(config, path)

    @staticmethod
    def _write_to_file(config, path):
        with path.open(mode="w") as f:
            string = json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
            f.write(unicode(string))

    def _config_from_file(self):
        with self._path.open(mode="r") as f:
            return json.load(f)

    def _potentially_update_and_backup_config(self):
        config = self._config_from_file()
        config = self._potentially_update_with_values_from_parent(config)
        default_config = self.default_config()
        keys_different_from_default = set(default_config.keys()).symmetric_difference(config.keys())
        if keys_different_from_default:
            updated_config = self._update_config_keys(default_config, config)
            self._write_backup(config)
            self._write(updated_config)
            message = self._format_unexpected_entries_message(default_config.keys(), config.keys())
            raise UnexpectedConfigEntriesException(message)

    def _potentially_update_with_values_from_parent(self, config):
        parent_path = config.get("overrides")
        if parent_path:
            config = self._update_with_values_from_parent(config, parent_path)
        return config

    def _update_with_values_from_parent(self, config, parent_path):
        parent_config_object = self.__class__(parent_path)
        parent_config = parent_config_object.read()
        parent_config.update(config)
        return parent_config

    def _format_unexpected_entries_message(self, expected, actual):
        unexpected = list(set(actual).difference(expected))
        missing = list(set(expected).difference(actual))
        ending = "The config was updated and the previous config was backed up in {!r}.".format(self.back_up_name())
        if unexpected and missing:
            return "Parameter {} is unexpected while {} is missing from {!r}. {}".format(
                readable_list(unexpected), readable_list(missing), self._absolute_path, ending
            )
        if unexpected:
            return "Parameter {} is unexpected in {!r}. {}"\
                .format(readable_list(unexpected), self._absolute_path, ending)
        if missing:
            return "Parameter {} is missing from {!r}. {}"\
                .format(readable_list(missing), self._absolute_path, ending)

    @classmethod
    def _update_config_keys(cls, defaults, config):
        updated_config = {}
        for key, default_value in defaults.iteritems():
            if key in config:
                updated_config[key] = config[key]
            else:
                updated_config[key] = default_value
        return updated_config

    def back_up_name(self):
        return "{}.backup".format(self._path)

    @staticmethod
    def default_name():
        raise NotImplementedError()

    @staticmethod
    def default_config():
        raise NotImplementedError()

    def _raise_config_not_found_exception(self):
        raise NotImplementedError()


class BackendConfig(Config):
    @staticmethod
    def default_name():
        return "backend.config.json"

    @staticmethod
    def default_config(ddd_name=""):
        return {
            "supported_languages": ["eng"],
            "ddds": [ddd_name],
            "active_ddd": ddd_name,
            "asr": "none",
            "use_recognition_profile": False,
            "repeat_questions": True,
            "use_word_list_correction": False,
            "overrides": None,
            "rerank_amount": BackendConfig.default_rerank_amount(),
            "inactive_seconds_allowed": DEFAULT_INACTIVE_SECONDS_ALLOWED,
        }

    @staticmethod
    def default_rerank_amount():
        return 0.2

    @classmethod
    def _update_config_keys(cls, defaults, config):
        updated_config = super(BackendConfig, cls)._update_config_keys(defaults, config)
        if "use_word_list_correction" not in config and config.get("asr") == "android":
            updated_config["use_word_list_correction"] = True
        return updated_config

    @classmethod
    def write_default_config(cls, path=None, ddd_name=None):
        path = path or cls.default_name()
        ddd_name = ddd_name or ""
        cls._write_to_file(cls.default_config(ddd_name), Path(path))

    def _raise_config_not_found_exception(self):
        raise BackendConfigNotFoundException(
            "Expected backend config '{}' to exist but it was not found.".format(self._absolute_path),
            self._absolute_path
        )


class DddConfig(Config):
    @staticmethod
    def default_name():
        return "ddd.config.json"

    @staticmethod
    def default_config():
        return {
            "use_rgl": True,
            "use_third_party_parser": False,
            "device_module": None,
            "word_list": "word_list.txt",
            "overrides": None,
            "rasa_nlu": {},
        }

    def _raise_config_not_found_exception(self):
        raise DddConfigNotFoundException(
            "Expected DDD config '{}' to exist but it was not found.".format(self._absolute_path), self._absolute_path
        )

    def read(self):
        config = super(DddConfig, self).read()
        self._validate_rasa_nlu_language(config["rasa_nlu"])
        self._validate_rasa_nlu(config["rasa_nlu"])
        return config

    def _validate_rasa_nlu_language(self, config):
        for language in config.keys():
            if language not in SUPPORTED_RASA_LANGUAGES:
                raise UnexpectedRASALanguageException(
                    "Expected one of the supported RASA languages {} in DDD config '{}' but got '{}'.".format(
                        SUPPORTED_RASA_LANGUAGES, self._absolute_path, language
                    )
                )

    def _validate_rasa_nlu(self, config):
        def message_for_missing_entry(parameter, language):
            return "Parameter '{parameter}' is missing from 'rasa_nlu.{language}' in DDD config '{file}'." \
                .format(parameter=parameter, language=language, file=self._absolute_path)

        def message_for_unexpected_entries(parameters, language):
            return "Parameters {parameters} are unexpected in 'rasa_nlu.{language}' of DDD config '{file}'." \
                .format(parameters=parameters, language=language, file=self._absolute_path)

        for language, rasa_nlu in config.items():
            if "url" not in rasa_nlu:
                raise UnexpectedConfigEntriesException(message_for_missing_entry("url", language))
            if "config" not in rasa_nlu:
                raise UnexpectedConfigEntriesException(message_for_missing_entry("config", language))
            unexpecteds = set(rasa_nlu.keys()) - {"url", "config"}
            if any(unexpecteds):
                raise UnexpectedConfigEntriesException(message_for_unexpected_entries(list(unexpecteds), language))


class DeploymentsConfig(Config):
    @staticmethod
    def default_name():
        return "deployments.config.json"

    @staticmethod
    def default_config():
        return {
            "dev": "https://127.0.0.1:9090/interact",
        }

    def _raise_config_not_found_exception(self):
        message = "Expected deployments config '{}' to exist but it was not found.".format(self._absolute_path)
        raise DeploymentsConfigNotFoundException(message, self._absolute_path)

    def _potentially_update_and_backup_config(self):
        pass

    def get_url(self, candidate_deployment):
        if not self._path.exists():
            return candidate_deployment
        config = self.read()
        if candidate_deployment in config:
            return config[candidate_deployment]
        return candidate_deployment


class OverriddenDddConfig(object):
    def __init__(self, ddd_name, path):
        self._ddd_name = ddd_name
        self._path = path

    @property
    def ddd_name(self):
        return self._ddd_name

    @property
    def path(self):
        return self._path
