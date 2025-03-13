import structlog
import time
import threading
import random
import uuid

import pytest

from tala.utils.mqtt_client import MQTTClient, ChunkJoiner
from tala.utils.func import configure_stdout_logging, getenv

logger = structlog.get_logger(__name__)
log_level = getenv("LOG_LEVEL", default="DEBUG")
configure_stdout_logging(log_level)


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
        self.given_mqtt_client_started("test_client", logger, "tala-sse.azurewebsites.net", 443)
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
        self._client.set_persona("some-persona")
        self._client.set_voice("some-voice")
        self._client.stream_chunk(chunk)
        self._client.flush_stream()
        self._client.close_session()

    def then_everything_is_ok(self):
        assert True


class TestChunkJoiner:
    def test_single_chunk(self):
        self.given_joiner()
        self.given_chunks(["hej"])
        self.then_resulting_chunks_are(["hej"])

    def given_joiner(self):
        self._joiner = ChunkJoiner(logger)

    def given_chunks(self, chunks):
        def produce_chunks():
            for chunk in chunks:
                time.sleep(random.uniform(0.0, 0.2))
                self._joiner.add_chunk(chunk)
            self.when_end_chunks()

        self.producer_thread = threading.Thread(target=produce_chunks)
        self.producer_thread.start()

    def when_end_chunks(self):
        self._joiner.last_chunk_sent()

    def then_resulting_chunks_are(self, expected_chunks):
        self._result = list(self._joiner)
        assert len(expected_chunks) == len(self._result), f"{len(expected_chunks)} != {len(self._result)}"
        for expected, actual in zip(expected_chunks, self._result):
            assert expected == actual

    def test_two_chunks(self):
        self.given_joiner()
        self.given_chunks(["hej", " kalle"])
        self.then_resulting_chunks_are(["hej", " kalle"])

    def test_two_chunks_should_be_joined_if_no_initial_space(self):
        self.given_joiner()
        self.given_chunks(["hej", "san"])
        self.then_resulting_chunks_are(["hejsan"])

    def test_three_chunks_should_be_joined_if_no_initial_space(self):
        self.given_joiner()
        self.given_chunks(["hej", "san", "sa"])
        self.then_resulting_chunks_are(["hejsansa"])

    def test_two_chunks_should_be_joined_when_third_has_initial_space(self):
        self.given_joiner()
        self.given_chunks(["hej", "san", " sa", " kalle"])
        self.then_resulting_chunks_are(["hejsan", " sa", " kalle"])

    def test_naturalistic_gpt_output(self):
        self.given_joiner()
        self.given_chunks([
            "En", " lust", "j", "akt", " är", " en", " b", "åt", " som", " används", " för", " nö", "jes", "seg",
            "ling", ". "
        ])
        self.then_resulting_chunks_are([
            "En", " lustjakt", " är", " en", " båt", " som", " används", " för", " nöjessegling. "
        ])

    def test_ndg_system_case(self):
        self.given_joiner()
        self.given_chunks(["Har du några fler frågor? "])
        self.then_resulting_chunks_are(["Har du några fler frågor? "])

    def test_ndg_system_case_no_space(self):
        self.given_joiner()
        self.given_chunks(["Har du några fler frågor?"])
        self.then_resulting_chunks_are(["Har du några fler frågor?"])
