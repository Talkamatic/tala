import logging
import uuid
from tala.ddd.ddd_manager import DDDManager
from tala.ddd.loading.extended_ddd_set_loader import ExtendedDDDSetLoader
from tala.log.formats import TIS_LOGGING_COMPACT, TIS_LOGGING_FULL, TIS_LOGGING_AUTO
from tala.config import BackendConfig
from tala.utils.as_json import AsJSONMixin
from tala.utils import json_api


class UnknownActiveDddException(Exception):
    pass


_LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _resolve_odb_id(path):
    return path or str(uuid.uuid4())


def _make_odb_document(payload):
    odb_id = _resolve_odb_id(payload["path"])
    return json_api.make_document("tdm.orchestrated_domain_bundle", f"odb:{odb_id}", payload)


def create_odb_as_json(
    config, overridden_ddd_config_paths, should_greet, logged_tis_format, tis_update_format, log_to_stdout, log_level
):
    odb = OrchestratedDomainBundle.from_backend_config(
        config,
        overridden_ddd_config_paths,
        should_greet,
        logged_tis_format,
        tis_update_format,
        log_to_stdout,
        log_level,
    )
    return odb.as_json()


def load_ddds(ddd_names, overridden_config_paths, rerank_amount):
    ddd_manager = DDDManager()
    extended_ddd_set_loader = ExtendedDDDSetLoader(ddd_manager, overridden_config_paths)
    ddds = extended_ddd_set_loader.ddds_as_list(ddd_names, rerank_amount=rerank_amount)
    return ddds


class OrchestratedDomainBundle(AsJSONMixin):
    @classmethod
    def from_backend_config(
        cls,
        config,
        overridden_ddd_config_paths,
        should_greet,
        logged_tis_format,
        logged_tis_update_format,
        log_to_stdout,
        log_level,
    ):
        raw_config = BackendConfig(config).read()
        ddd_names = _validate_ddd_names(raw_config["ddds"])
        _validate_active_ddd_name(raw_config["active_ddd"], ddd_names)
        extended_ddds = load_ddds(ddd_names, overridden_ddd_config_paths, raw_config["rerank_amount"])
        attributes = {
            "overridden_ddd_config_paths": overridden_ddd_config_paths,
            "path": config or BackendConfig.default_name(),
            "repeat_questions": raw_config["repeat_questions"],
            "ddd_names": ddd_names,
            "active_ddd_name": raw_config["active_ddd"],
            "rerank_amount": raw_config["rerank_amount"],
            "response_timeout": raw_config["response_timeout"],
            "confidence_thresholds": raw_config["confidence_thresholds"],
            "confidence_prediction_thresholds": raw_config["confidence_prediction_thresholds"],
            "short_timeout": raw_config["short_timeout"],
            "medium_timeout": raw_config["medium_timeout"],
            "long_timeout": raw_config["long_timeout"],
            "should_greet": should_greet,
            "logged_tis_format": logged_tis_format,
            "logged_tis_update_format": logged_tis_update_format,
            "log_to_stdout": log_to_stdout,
            "log_level": log_level,
            "ddds": [extended_ddd.ddd.as_json_api_dict() for extended_ddd in extended_ddds],
        }
        return cls(_make_odb_document(attributes))

    def __init__(self, argument_dict):
        argument_dict = self._require_json_api_attributes(argument_dict)
        self._overridden_ddd_config_paths = argument_dict["overridden_ddd_config_paths"]
        self._path = argument_dict["path"]
        self._repeat_questions = argument_dict["repeat_questions"]
        self._ddd_names = _validate_ddd_names(argument_dict["ddd_names"])
        self._rerank_amount = float(argument_dict["rerank_amount"])
        self._response_timeout = argument_dict["response_timeout"]
        self._confidence_thresholds = self._coerce_float_dict(
            argument_dict["confidence_thresholds"], "confidence_thresholds"
        )
        self._confidence_prediction_thresholds = self._coerce_float_dict(
            argument_dict["confidence_prediction_thresholds"], "confidence_prediction_thresholds"
        )
        self._short_timeout = float(argument_dict["short_timeout"])
        self._medium_timeout = float(argument_dict["medium_timeout"])
        self._long_timeout = float(argument_dict["long_timeout"])
        self._should_greet = argument_dict["should_greet"]
        self._logged_tis_format = argument_dict["logged_tis_format"]
        self._logged_tis_update_format = argument_dict["logged_tis_update_format"]
        self._log_to_stdout = argument_dict["log_to_stdout"]
        self._log_level = argument_dict["log_level"]

        self.ddds_as_json = argument_dict["ddds"]

        self._active_ddd_name = argument_dict["active_ddd_name"]
        _validate_active_ddd_name(self._active_ddd_name, self._ddd_names)

        if self._logged_tis_format == TIS_LOGGING_AUTO:
            log_level = self._normalize_log_level(self._log_level)
            self._logged_tis_format = self._generate_tis_format_from_log_level(log_level)

        self.logger = None

    def as_dict(self):
        return self._as_json_api_dict()

    def as_json(self):
        return self._as_json_api_dict()

    def _as_json_api_dict(self):
        payload = self._odb_dict()
        return _make_odb_document(payload)

    def _odb_dict(self):
        return {
            "overridden_ddd_config_paths": self._overridden_ddd_config_paths,
            "path": self._path,
            "repeat_questions": self._repeat_questions,
            "ddd_names": self._ddd_names,
            "active_ddd_name": self.active_ddd,
            "rerank_amount": self._rerank_amount,
            "response_timeout": self._response_timeout,
            "confidence_thresholds": self._confidence_thresholds,
            "confidence_prediction_thresholds": self._confidence_prediction_thresholds,
            "short_timeout": self._short_timeout,
            "medium_timeout": self._medium_timeout,
            "long_timeout": self._long_timeout,
            "should_greet": self._should_greet,
            "logged_tis_format": self._logged_tis_format,
            "logged_tis_update_format": self._logged_tis_update_format,
            "log_to_stdout": self._log_to_stdout,
            "log_level": self._log_level,
            "ddds": self.ddds_as_json,
        }

    def _require_json_api_attributes(self, argument_dict):
        return json_api.require_attributes(argument_dict, "ODB")

    def __repr__(self):
        return str(self.as_dict())

    @staticmethod
    def _generate_tis_format_from_log_level(log_level):
        if log_level == logging.DEBUG:
            return TIS_LOGGING_FULL
        return TIS_LOGGING_COMPACT

    @staticmethod
    def _normalize_log_level(log_level):
        try:
            return int(log_level)
        except (TypeError, ValueError):
            pass
        name = str(log_level).upper()
        name_level = _LOG_LEVELS.get(name)
        if name_level is not None:
            return name_level
        try:
            return int(logging.getLevelName(name))
        except (TypeError, ValueError):
            return logging.INFO

    @staticmethod
    def _coerce_float_dict(values, label):
        try:
            items = values.items()
        except AttributeError as exc:
            raise ValueError(f"Expected '{label}' to be a mapping of numbers.") from exc
        result = {}
        for key, value in items:
            try:
                result[key] = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Expected '{label}' values to be numbers; got {value!r} for '{key}'.") from exc
        return result

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @property
    def active_ddd(self):
        return self._active_ddd_name

    @active_ddd.setter
    def active_ddd(self, active_ddd_name):
        self._active_ddd_name = active_ddd_name

    @property
    def should_greet(self):
        return self._should_greet

    @property
    def logged_tis_format(self):
        return self._logged_tis_format

    @property
    def logged_tis_update_format(self):
        return self._logged_tis_update_format

    @property
    def log_to_stdout(self):
        return self._log_to_stdout

    @property
    def log_level(self):
        return self._log_level

    @property
    def confidence_thresholds(self):
        return self._confidence_thresholds

    @property
    def confidence_prediction_thresholds(self):
        return self._confidence_prediction_thresholds

    @property
    def overridden_ddd_config_paths(self):
        return self._overridden_ddd_config_paths

    @property
    def ddds_as_json(self):
        return self._ddds_as_json

    @ddds_as_json.setter
    def ddds_as_json(self, ddds_as_json):
        try:
            self._ddds_as_json = list(ddds_as_json)
        except TypeError as exc:
            raise ValueError("Expected 'ddds' to be a list of JSON:API DDD payloads.") from exc

    @property
    def ddds(self):
        return self.ddds_as_json

    @ddds.setter
    def ddds(self, ddds):
        self.ddds_as_json = ddds

    @property
    def repeat_questions(self):
        return self._repeat_questions

    @property
    def ddd_names(self):
        return self._ddd_names

    @property
    def rerank_amount(self):
        return self._rerank_amount

    @property
    def response_timeout(self):
        return self._response_timeout

    @property
    def path(self):
        return self._path

    @property
    def short_timeout(self):
        return self._short_timeout

    @property
    def medium_timeout(self):
        return self._medium_timeout

    @property
    def long_timeout(self):
        return self._long_timeout


def _validate_active_ddd_name(active_ddd_name, ddd_names):
    if not active_ddd_name or active_ddd_name == "none":
        return
    if active_ddd_name not in ddd_names:
        raise UnknownActiveDddException(
            f"Active DDD '{active_ddd_name}' is not in configured DDDs {ddd_names}."
        )


def _validate_ddd_names(ddd_names):
    try:
        names = list(ddd_names)
    except TypeError as exc:
        raise ValueError("Expected 'ddd_names' to be a non-empty list.") from exc
    if not names:
        raise ValueError("Expected 'ddd_names' to contain at least one DDD.")
    return names
