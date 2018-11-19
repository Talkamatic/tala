import datetime
import json
import logging
import os

LOG_FORMATS = {
    "full": u"%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "comparable": u"%(name)s - %(levelname)s - %(message)s"
}

DEBUG = "DEBUG"
ANALYTICS = "ANALYTICS"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"

VALID_LOG_LEVELS = [
    DEBUG,
    ANALYTICS,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
]

logger = None

ANALYTICS_LOG_LEVEL = 15


def setup_logging(logger_name, prefix=None, log_format="full"):
    global logger
    if prefix is None:
        prefix = logger_name
    logger = _configure_root_logger(logger_name, prefix, log_format)
    return logger


def _configure_root_logger(logger_name, prefix, log_format):
    _ensure_log_folder_exists()
    logger = TDMLogger(logger_name, logging.DEBUG, _log_path(prefix), log_format)
    return logger


def _log_path(prefix):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "logs/%s_%s.log" % (prefix, timestamp)


def _ensure_log_folder_exists():
    try:
        os.mkdir("logs")
    except OSError as directory_already_exists_exception:
        pass

def create_logger(logger_name, file_basename, log_format="full"):
    _ensure_log_folder_exists()
    filename = "logs/%s" % file_basename
    logger = TDMLogger(logger_name, logging.DEBUG, filename, log_format)
    return logger


def get_test_logger():
    global logger
    if logger is None:
        logger = setup_logging("test_suite", "test_suite.log")
    return logger


class TDMLogger(logging.Logger):
    def __init__(self, logger_name, threshold, filename, log_format):
        logging.Logger.__init__(self, logger_name)
        logging.addLevelName(ANALYTICS_LOG_LEVEL, ANALYTICS)
        self.custom_setup(threshold, filename, log_format)

    def custom_setup(self, threshold, filename, log_format):
        self.setLevel(threshold)
        logging_handler = logging.FileHandler(filename, mode="w")
        formatter = logging.Formatter(LOG_FORMATS[log_format])
        logging_handler.setFormatter(formatter)
        self.propagate = False
        self.addHandler(logging_handler)

    def analytics(self, info_str, tdm_object):
        self.log(ANALYTICS_LOG_LEVEL, "%s - %s" % (info_str, tdm_object))
