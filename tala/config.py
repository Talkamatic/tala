import json
import os
import datetime

from tala.utils.text_formatting import readable_list


DEFAULT_INACTIVE_SECONDS_ALLOWED = datetime.timedelta(hours=2).seconds


class ConfigNotFoundException(Exception):
    def __init__(self, message, config_path):
        self._config_path = config_path
        super(ConfigNotFoundException, self).__init__(message)

    @property
    def config_path(self):
        return self._config_path


class BackendConfigNotFoundException(ConfigNotFoundException): pass
class DddConfigNotFoundException(ConfigNotFoundException): pass
class RasaConfigNotFoundException(ConfigNotFoundException): pass
class UnexpectedConfigEntriesException(Exception): pass


class Config(object):
    def __init__(self, path=None):
        self._path = path
        if self._path is None:
            self._path = self.default_name()

    @property
    def _absolute_path(self):
        return os.path.join(os.getcwd(), self._path)

    def read(self):
        if not os.path.exists(self._path):
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
        cls._write_to_file(cls.default_config(), path)

    def _write_backup(self, config):
        self._write_to_file(config, self.back_up_name())

    @staticmethod
    def _write_to_file(config, path):
        with open(path, mode="w") as f:
            json.dump(config, f, sort_keys=True, indent=4, separators=(',', ': '))

    def _config_from_file(self):
        with open(self._path, mode="r") as f:
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
        ending = "The config was updated and the previous config was backed up in %r." % self.back_up_name()
        if unexpected and missing:
            return "Parameter %s is unexpected while %s is missing from %r. %s" % \
                   (readable_list(unexpected), readable_list(missing), self._absolute_path, ending)
        if unexpected:
            return "Parameter %s is unexpected in %r. %s" % \
                   (readable_list(unexpected), self._absolute_path, ending)
        if missing:
            return "Parameter %s is missing from %r. %s" % \
                   (readable_list(missing), self._absolute_path, ending)

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
        return "%s.backup" % self._path

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
        cls._write_to_file(cls.default_config(ddd_name), path)

    def _raise_config_not_found_exception(self):
        raise BackendConfigNotFoundException(
            "Expected backend config '%s' to exist but it was not found." % self._absolute_path, self._absolute_path)


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
            "enable_rasa_nlu": False,
        }

    def _raise_config_not_found_exception(self):
        raise DddConfigNotFoundException(
            "Expected DDD config '%s' to exist but it was not found." % self._absolute_path, self._absolute_path)


class RasaConfig(Config):
    @staticmethod
    def default_name():
        return "rasa.config.json"

    @staticmethod
    def default_config():
        return {
            "enable_duckling": False,
            "duckling_url": "http://127.0.0.1:10090",
        }

    def _raise_config_not_found_exception(self):
        raise RasaConfigNotFoundException(
            "Expected RASA config '%s' to exist but it was not found." % self._absolute_path, self._absolute_path)


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
