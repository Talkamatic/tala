import logging
from tala.ddd.ddd_manager import DDDManager
from tala.ddd.loading.extended_ddd_set_loader import ExtendedDDDSetLoader
from tala.log.formats import TIS_LOGGING_COMPACT, TIS_LOGGING_FULL, TIS_LOGGING_AUTO
from tala.config import BackendConfig
from tala.utils.as_json import AsJSONMixin


class UnknownActiveDddException(Exception):
    pass


def create_odb_as_json(
    config, overridden_ddd_config_paths, should_greet, logged_tis_format, tis_update_format, log_to_stdout, log_level
):
    odb_as_json = {}

    raw_config = BackendConfig(config).read()

    odb_as_json["overridden_ddd_config_paths"] = overridden_ddd_config_paths
    odb_as_json["path"] = config or BackendConfig.default_name()
    odb_as_json["repeat_questions"] = raw_config["repeat_questions"]
    odb_as_json["ddd_names"] = raw_config["ddds"]
    odb_as_json["active_ddd_name"] = raw_config["active_ddd"]
    odb_as_json["rerank_amount"] = raw_config["rerank_amount"]
    odb_as_json["response_timeout"] = raw_config["response_timeout"]
    odb_as_json["confidence_thresholds"] = raw_config["confidence_thresholds"]
    odb_as_json["confidence_prediction_thresholds"] = raw_config["confidence_prediction_thresholds"]
    odb_as_json["short_timeout"] = raw_config["short_timeout"]
    odb_as_json["medium_timeout"] = raw_config["medium_timeout"]
    odb_as_json["long_timeout"] = raw_config["long_timeout"]
    odb_as_json["should_greet"] = should_greet
    odb_as_json["logged_tis_format"] = logged_tis_format
    odb_as_json["logged_tis_update_format"] = tis_update_format
    odb_as_json["log_to_stdout"] = log_to_stdout
    odb_as_json["log_level"] = log_level

    extended_ddds = load_ddds(odb_as_json["ddd_names"], overridden_ddd_config_paths, raw_config["rerank_amount"])

    odb_as_json["ddds"] = [extended_ddd.ddd.as_json_api_dict() for extended_ddd in extended_ddds]

    return odb_as_json


def load_ddds(ddd_names, overridden_config_paths, rerank_amount):
    ddd_manager = DDDManager()
    extended_ddd_set_loader = ExtendedDDDSetLoader(ddd_manager, overridden_config_paths)
    ddds = extended_ddd_set_loader.ddds_as_list(ddd_names, rerank_amount=rerank_amount)
    return ddds


class OrchestratedDomainBundle(AsJSONMixin):
    def __init__(self, argument_dict):
        self._overridden_ddd_config_paths = argument_dict["overridden_ddd_config_paths"]
        self._path = argument_dict["path"]
        self._repeat_questions = argument_dict["repeat_questions"]
        self._ddd_names = argument_dict["ddd_names"]
        self._rerank_amount = float(argument_dict["rerank_amount"])
        self._response_timeout = argument_dict["response_timeout"]
        self._confidence_thresholds = argument_dict["confidence_thresholds"]
        self._confidence_prediction_thresholds = argument_dict["confidence_prediction_thresholds"]
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

        for key in self._confidence_thresholds:
            self._confidence_thresholds[key] = float(self._confidence_thresholds[key])
        for key in self._confidence_prediction_thresholds:
            self._confidence_prediction_thresholds[key] = float(self._confidence_prediction_thresholds[key])

        if self._logged_tis_format == TIS_LOGGING_AUTO:
            log_level = logging.getLevelName(self._log_level)
            self._logged_tis_format = self._generate_tis_format_from_log_level(log_level)

        self.logger = None

    def as_dict(self):
        dict_ = {}

        dict_["overridden_ddd_config_paths"] = self._overridden_ddd_config_paths
        dict_["path"] = self._path
        dict_["repeat_questions"] = self._repeat_questions
        dict_["ddd_names"] = self._ddd_names
        dict_["active_ddd_name"] = self.active_ddd
        dict_["rerank_amount"] = self._rerank_amount
        dict_["response_timeout"] = self._response_timeout
        dict_["confidence_thresholds"] = self._confidence_thresholds
        dict_["confidence_prediction_thresholds"] = self._confidence_prediction_thresholds
        dict_["short_timeout"] = self._short_timeout
        dict_["medium_timeout"] = self._medium_timeout
        dict_["long_timeout"] = self._long_timeout
        dict_["should_greet"] = self._should_greet
        dict_["logged_tis_format"] = self._logged_tis_format
        dict_["logged_tis_update_format"] = self._logged_tis_update_format
        dict_["log_to_stdout"] = self._log_to_stdout
        dict_["log_level"] = self._log_level
        dict_["ddds"] = self.ddds_as_json

        return dict_

    def __repr__(self):
        return str(self.as_dict())

    @staticmethod
    def _generate_tis_format_from_log_level(log_level):
        if log_level == logging.DEBUG:
            return TIS_LOGGING_FULL
        return TIS_LOGGING_COMPACT

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
    def ddds(self):
        return self._ddds

    @ddds.setter
    def ddds(self, ddds):
        self._ddds = ddds

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
