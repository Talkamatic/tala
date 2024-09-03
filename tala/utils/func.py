import logging.config
import re
import os

from structlog.processors import JSONRenderer, TimeStamper, StackInfoRenderer, format_exc_info
from structlog.stdlib import add_log_level, filter_by_level, add_logger_name
import structlog


class EnvironmentVariableNotDefinedException(Exception):
    pass


def getenv(key, default=None):
    value = os.getenv(key, default)
    if value:
        return value
    if default is None:
        raise EnvironmentVariableNotDefinedException(
            f"Expected environment variable '{key}' to be defined but it wasn't"
        )


class FuncBase:
    def _setup_logger(self, request, logger):
        def get_session_id():
            try:
                return request["session"]["session_id"]
            except KeyError:
                return "unknown-session-id"

        def get_device_id():
            try:
                return request["session"]["device_id"]
            except KeyError:
                return "unknown-device-id"

        self.logger = logger.bind(session_id=get_session_id(), device_id=get_device_id())


def configure_stdout_logging(level=None):
    structlog.configure(
        processors=[
            filter_by_level,
            add_log_level,
            add_logger_name,
            TimeStamper(fmt="iso", key="time"),
            StackInfoRenderer(),
            format_exc_info,
            JSONRenderer(sort_keys=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=False),
            },
            "access-json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.add_logger_name,
                    TimeStamper(fmt="iso", key="time"),
                    StackInfoRenderer(),
                    format_exc_info,
                    combined_logformat,
                ],
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "plain",
            },
            "access": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "access-json",
            },
        },
        "loggers": {
            "": {
                "handlers": ["stdout"],
                "level": level,
                "propagate": False,
            },
            "gunicorn.access": {
                "handlers": ["access"],
                "level": level,
                "propagate": False,
            },
        }
    })  # yapf: disable


def combined_logformat(logger, name, event_dict):
    if event_dict.get('logger') == "gunicorn.access":
        message = event_dict['event']

        parts = [
            r'(?P<host>\S+)',  # host %h
            r'\S+',  # indent %l (unused)
            r'(?P<user>\S+)',  # user %u
            r'\[(?P<time>.+)\]',  # time %t
            r'"(?P<request>.+)"',  # request "%r"
            r'(?P<status>[0-9]+)',  # status %>s
            r'(?P<size>\S+)',  # size %b (careful, can be '-')
            r'"(?P<referer>.*)"',  # referer "%{Referer}i"
            r'"(?P<agent>.*)"',  # user agent "%{User-agent}i"
        ]
        pattern = re.compile(r'\s+'.join(parts) + r'\s*\Z')
        m = pattern.match(message)
        result = m.groupdict()

        if result["user"] == "-":
            result["user"] = None

        result["status"] = int(result["status"])

        if result["size"] == "-":
            result["size"] = 0
        else:
            result["size"] = int(result["size"])

        if result["referer"] == "-":
            result["referer"] = None

        event_dict.update(result)
        event_dict["event"] = "endpoint accessed"

    return event_dict