import structlog
from urllib.parse import urlparse
import uuid

import pytest

from tala.utils.mqtt_client import MQTTClient
from tala.utils.func import configure_stdout_logging, getenv

logger = structlog.get_logger(__name__)
log_level = getenv("LOG_LEVEL", default="DEBUG")
configure_stdout_logging(log_level)


def resolve_mqtt_endpoint():
    endpoint = str(getenv("SSE_BROKER_ENDPOINT_MQTT", default="") or "")
    if endpoint:
        return endpoint
    https_endpoint = str(getenv("SSE_BROKER_ENDPOINT_HTTPS", default="") or "")
    if not https_endpoint:
        return ""
    parsed = urlparse(https_endpoint)
    if parsed.netloc:
        return parsed.netloc
    return https_endpoint.replace("https://", "").replace("http://", "").split("/")[0]


class TestMQTTClient:
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
        self.given_args_for_client_creation(["client_id", logger, "some_endpoint", 443])
        self.when_mqtt_client_created()
        self.then_client_id_matches("client_id")

    def then_client_id_matches(self, id_):
        assert self._mqtt_client._client_id.startswith(f"{id_}-")

    @pytest.mark.parametrize("chunk", ["This is an unproblematic test utterance.", "Frölunda ", "Fr\u00f6lunda"])
    def test_stream_single_chunk(self, chunk):
        self.given_streamer_endpoint()
        self.given_mqtt_client_started("test_client", logger, self._endpoint, 443)
        self.given_session_id("test-session-id")
        self.when_chunk_streamed(chunk)
        self.then_everything_is_ok()

    def given_mqtt_client_started(self, name, logger, endpoint, port):
        self._client = MQTTClient(name, logger, endpoint, port)
        self._client.start()

    def given_session_id(self, id_):
        self._session_id = id_ + str(uuid.uuid4)

    def when_chunk_streamed(self, chunk):
        self._client.open_session(self._session_id, None)
        self._client.set_persona(self._session_id, "some-persona")
        self._client.set_voice(self._session_id, "some-voice")
        self._client.stream_chunk(self._session_id, chunk)
        self._client.flush_stream(self._session_id)
        self._client.close_session(self._session_id)

    def then_everything_is_ok(self):
        assert True

    def given_streamer_endpoint(self):
        self._endpoint = resolve_mqtt_endpoint()
        assert self._endpoint, "SSE_BROKER_ENDPOINT_MQTT or SSE_BROKER_ENDPOINT_HTTPS not set"
