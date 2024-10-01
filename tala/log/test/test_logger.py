import json
import logging
import os
import shutil
import tempfile

from unittest.mock import patch, ANY
import pytest
import structlog

from tala.log import logger


class TestLogger(object):
    def setup_method(self):
        self._log_filename = "mock_filename"
        self._temp_dir = tempfile.mkdtemp(prefix="LoggerTests")
        self._working_dir = os.getcwd()
        os.chdir(self._temp_dir)

    def teardown_method(self):
        os.chdir(self._working_dir)
        shutil.rmtree(self._temp_dir)

    @classmethod
    def tearDownClass(cls):
        structlog.reset_defaults()
        del logging.root.handlers[:]

    @patch("%s.TimeStamper" % logger.__name__)
    def test_configure_logger_configures_json_formatting(self, MockTimeStamper):
        self.given_timestamper_adds_timestamp(MockTimeStamper, "mock_timestamp")
        self.given_configured(logging.DEBUG)
        self.given_called_get_logger()
        self.when_invoke_debug("mock message", mock_key="mock_value")
        self.then_log_contains_json({
            "event": "mock message",
            "logger": "test_logger",
            "mock_key": "mock_value",
            "level": "debug",
            "time": "mock_timestamp"
        })

    def given_timestamper_adds_timestamp(self, MockTimeStamper, timestamp):
        def stamper(self, _, __, event_dict):
            event_dict["time"] = timestamp
            return event_dict

        MockTimeStamper.return_value = type("TimeStamper", (object, ), {"__call__": stamper})()

    def given_configured(self, level):
        logger.configure_file_logging(self._log_filename, level)

    def given_called_get_logger(self):
        self._logger = structlog.get_logger()

    def when_invoke_debug(self, message, **kwargs):
        self._logger.debug(message, **kwargs)

    def then_log_contains_json(self, expected_json):
        with open("logs/%s" % self._log_filename, "r") as log_file:
            actual_json = json.load(log_file)
        assert actual_json == expected_json

    @patch("%s.logging" % logger.__name__)
    def test_configure_file_logging_configures_file_handler(self, mock_logging):
        self.when_configuring_file_logging("mock_filename.log", "mock_log_level")
        self.then_stdlib_logging_is_configured_with_handlers(
            mock_logging, {
                "file": {
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "logs/mock_filename.log",
                    "formatter": "plain",
                    "mode": "w",
                }
            }
        )

    def when_configuring_file_logging(self, filename, level):
        logger.configure_file_logging(filename, level)

    def then_stdlib_logging_is_configured_with_handlers(self, mock_logging, expected_handlers):
        actual_config = mock_logging.config.dictConfig.call_args[0][0]
        actual_handlers = actual_config["handlers"]
        assert actual_handlers == expected_handlers

    @patch("%s.logging" % logger.__name__)
    @pytest.mark.parametrize(
        "actual_level,expected_level", [
            (None, logging.WARNING),
            (logging.DEBUG, logging.DEBUG),
            (logging.INFO, logging.INFO),
            (logging.WARNING, logging.WARNING),
            (logging.ERROR, logging.ERROR),
            (logging.CRITICAL, logging.CRITICAL),
        ]
    )
    def test_configure_file_logging_configures_level(self, mock_logging, actual_level, expected_level):
        self.when_configuring_file_logging("mock_filename.log", actual_level)
        self.then_stdlib_logging_is_configured_with(
            mock_logging, {
                "version": 1,
                "formatters": ANY,
                "handlers": ANY,
                "loggers": {
                    "": {
                        "handlers": ANY,
                        "level": expected_level,
                        "propagate": False,
                    },
                }
            }
        )

    def then_stdlib_logging_is_configured_with(self, mock_logging, expected_config):
        actual_config = mock_logging.config.dictConfig.call_args[0][0]
        assert actual_config == expected_config

    @patch("%s.logging" % logger.__name__)
    @pytest.mark.parametrize(
        "actual_level,expected_level", [
            (None, logging.WARNING),
            (logging.DEBUG, logging.DEBUG),
            (logging.INFO, logging.INFO),
            (logging.WARNING, logging.WARNING),
            (logging.ERROR, logging.ERROR),
            (logging.CRITICAL, logging.CRITICAL),
        ]
    )
    def test_configure_stdout_logging_configures_level(self, mock_logging, actual_level, expected_level):
        self.when_configuring_stdout_logging(actual_level)
        self.then_stdlib_logging_is_configured_with(
            mock_logging, {
                "version": 1,
                "formatters": ANY,
                "handlers": ANY,
                "loggers": {
                    "": {
                        "handlers": ANY,
                        "level": expected_level,
                        "propagate": False,
                    },
                }
            }
        )

    @patch("%s.logging" % logger.__name__)
    def test_configure_stdout_logging_configures_stdout_handler(self, mock_logging):
        self.when_configuring_stdout_logging("mock_log_level")
        self.then_stdlib_logging_is_configured_with_handlers(
            mock_logging,
            {"stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "plain",
            }}
        )

    def when_configuring_stdout_logging(self, level):
        logger.configure_stdout_logging(level)

    @patch("%s.JSONRenderer" % logger.__name__)
    @pytest.mark.parametrize(
        "configurer,args", [(logger.configure_file_logging, ["mock_filename"]), (logger.configure_stdout_logging, [])]
    )
    def test_configure_logger_configures_structlog_json_renderer(self, MockJSONRenderer, configurer, args):
        self.when_configuring(configurer, *args)
        self.then_structlog_is_configured_with_json_renderer(MockJSONRenderer, sort_keys=True)

    def when_configuring(self, configurer, *args):
        configurer(*args)

    def then_structlog_is_configured_with_json_renderer(self, JSONRenderer, **expected_kwargs):
        JSONRenderer.assert_called_once_with(**expected_kwargs)

    @patch("%s.TimeStamper" % logger.__name__)
    @pytest.mark.parametrize(
        "configurer,args", [(logger.configure_file_logging, ["mock_filename"]), (logger.configure_stdout_logging, [])]
    )
    def test_get_logger_configures_structlog_time_stamper(self, MockTimeStamper, configurer, args):
        self.when_configuring(configurer, *args)
        self.then_structlog_is_configured_with_timestamper(MockTimeStamper, fmt="iso", key="time")

    def then_structlog_is_configured_with_timestamper(self, TimeStamper, **expected_kwargs):
        TimeStamper.assert_called_once_with(**expected_kwargs)
