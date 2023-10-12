import datetime
import logging.config
import os

from structlog.processors import JSONRenderer, TimeStamper, StackInfoRenderer, format_exc_info, \
    ExceptionPrettyPrinter, KeyValueRenderer
from structlog.stdlib import add_log_level, filter_by_level, add_logger_name
import structlog

DEFAULT_LOG_LEVEL = logging.WARNING
TESTING_PROCESSORS = [
    filter_by_level,
    add_log_level,
    add_logger_name,
    TimeStamper(fmt="iso", key="time"),
    StackInfoRenderer(),
    format_exc_info,
    ExceptionPrettyPrinter(),
    KeyValueRenderer(sort_keys=True, repr_native_str=False),
]
STDOUT_HANDLER = {
    "stdout": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "plain",
    }
}


def get_logger():
    return structlog.get_logger("tdm")


def configure_file_logging(file_basename=None, level=None):
    if file_basename is None:
        file_basename = _log_basename("tdm")
    _ensure_log_folder_exists()
    filename = "logs/%s" % file_basename
    handlers = {
        "file": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": filename,
            "formatter": "plain",
            "mode": "w",
        }
    }
    return _configure_logging(handlers, level)


def configure_stdout_logging(level=None):
    return _configure_logging(STDOUT_HANDLER, level)


def configure_test_logging(level=None):
    level = level or logging.INFO
    return _configure_logging(STDOUT_HANDLER, level, processors=TESTING_PROCESSORS)


def _configure_logging(handlers, level=None, processors=None):
    level = level or DEFAULT_LOG_LEVEL
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=False),
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "handlers": list(handlers.keys()),
                "level": level,
                "propagate": False,
            },
        }
    })
    default_processors = [
        filter_by_level,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso", key="time"),
        StackInfoRenderer(),
        format_exc_info,
        JSONRenderer(sort_keys=True),
    ]
    processors = processors or default_processors
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _log_basename(prefix):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "%s_%s.log" % (prefix, timestamp)


def _ensure_log_folder_exists():
    try:
        os.mkdir("logs")
    except OSError:
        pass


def configure_and_get_test_logger():
    configure_file_logging("test_suite.log", level=logging.DEBUG)
    return structlog.get_logger("test_suite")
