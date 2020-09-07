import logging.config

from structlog.processors import JSONRenderer, TimeStamper, StackInfoRenderer, format_exc_info
from structlog.stdlib import add_log_level, filter_by_level, add_logger_name
import structlog

STDOUT_HANDLER = {
    "stdout": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "plain",
    }
}


def configure_stdout_logging(level=None):
    return _configure_logging(STDOUT_HANDLER, level)


def _configure_logging(handlers, level=None, processors=None):
    level = level
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
