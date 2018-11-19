import unittest
import datetime
import logging

from mock import patch, Mock

from tala.log import logger


class TDMLoggerTests(unittest.TestCase):

    def setUp(self):
        self.logger = logger.create_logger("test_logger", "test_log.log")

    @patch("%s.datetime" % logger.__name__)
    @patch("%s.TDMLogger" % logger.__name__)
    def test_setup_logging(self, MockTDMLogger, mock_datetime):
        self.given_mock_tdm_logger(MockTDMLogger)
        self.given_datetime_now_returns(mock_datetime, datetime.datetime(2018, 2, 28, 10, 30, 50))
        self.when_setup_logging_is_invoked_with("mock_logger_name")
        self.then_return_value_is_tdm_logger_created_with(MockTDMLogger,
            "mock_logger_name",
            logging.DEBUG,
            "logs/mock_logger_name_2018-02-28T10-30-50.log",
            "full")

    def given_mock_tdm_logger(self, MockTDMLogger):
        self._mock_tdm_logger = Mock()
        MockTDMLogger.return_value = self._mock_tdm_logger

    def given_datetime_now_returns(self, mock_datetime, now):
        mock_datetime.datetime.now.return_value = now

    def when_setup_logging_is_invoked_with(self, logger_name):
        self._actual_return_value = logger.setup_logging(logger_name)

    def then_return_value_is_tdm_logger_created_with(self, MockTDMLogger, *args):
        MockTDMLogger.assert_called_once_with(*args)
        self.assertEquals(self._mock_tdm_logger, self._actual_return_value)
