import structlog

from tala.utils.mqtt_client import MQTTClient
from tala.utils.func import configure_stdout_logging, getenv

logger = structlog.get_logger(__name__)
log_level = getenv("LOG_LEVEL", default="DEBUG")
configure_stdout_logging(log_level)


class TestMQTTClient(object):
    def setup_method(self):
        pass

    def test_creation(self):
        self.given_args_for_client_creation(["", logger, "some_endpoint", 443])
        self.when_mqtt_client_created()
        self.then_client_created_with(logger, "some_endpoint", 443, "name_base")

    def given_args_for_client_creation(self, args):
        self._mqtt_args = args

    def when_mqtt_client_created(self):
        self._mqtt_client = MQTTClient(*self._mqtt_args)

    def then_client_created_with(self, logger, endpoint, port, name_base):
        assert self._mqtt_client.logger == logger
        assert self._mqtt_client._endpoint == endpoint
        assert self._mqtt_client._port == port

    def test_creation_with_client_id(self):
        self.given_args_for_client_creation(["cliend_id", logger, "some_endpoint", 443])
        self.when_mqtt_client_created()
        self.then_client_id_is("cliend_id")

    def then_client_id_is(self, id_):
        assert self._mqtt_client._client_id == id_
