import structlog
import time
import threading
import random
import uuid

import pytest

from tala.utils.sse_client import SSEClient, ChunkJoiner
from tala.utils.func import configure_stdout_logging, getenv

logger = structlog.get_logger(__name__)
log_level = getenv("LOG_LEVEL", default="DEBUG")
configure_stdout_logging(log_level)


class TestSSEClient:
    def setup_method(self):
        pass

    def test_creation(self):
        self.given_args_for_client_creation(["", logger, "some_endpoint", 443])
        self.when_sse_client_created()
        self.then_client_created_with(logger, "some_endpoint", 443, "name_base")

    def given_args_for_client_creation(self, args):
        self._sse_args = args

    def when_sse_client_created(self):
        self._sse_client = SSEClient(*self._sse_args)

    def then_client_created_with(self, logger, endpoint, port, name_base):
        assert self._sse_client.logger == logger
        assert self._sse_client._endpoint == endpoint
        assert self._sse_client._port == port

    @pytest.mark.parametrize("chunk", ["This is an unproblematic test utterance.", "Frölunda ", "Fr\u00f6lunda"])
    def test_stream_single_chunk(self, chunk):
        self.given_sse_client_started(
            "test_client", logger, "wss://tala-sse-ng-g6bpb0cncyc4htg3.swedencentral-01.azurewebsites.net", 443
        )
        self.given_session_id("test-session-id")
        self.when_chunk_streamed(chunk)
        self.then_everything_is_ok()

    def given_sse_client_started(self, name, logger, endpoint, port):
        self._client = SSEClient(name, logger, endpoint, port)
        self._client.start()

    def given_session_id(self, id_):
        self._session_id = id_ + str(uuid.uuid4())

    def when_chunk_streamed(self, chunk):
        self._client.open_session(self._session_id, None)
        self._client.set_persona(self._session_id, "some-persona")
        self._client.set_voice(self._session_id, "some-voice")
        self._client.stream_chunk(self._session_id, chunk)
        self._client.flush_stream(self._session_id)
        self._client.close_session(self._session_id)

    def then_everything_is_ok(self):
        assert True

    def test_multi_sessions_single_client_no_message_confusion(self):
        self.given_mocked_stream_to_frontend()
        self.given_single_client()
        self.when_client_streaming_to_num_sessions(10)
        self.then_all_streams_correct()

    def given_mocked_stream_to_frontend(self):
        def mocked_stream_to_frontend(_self, streamer_session, message):
            session_id = streamer_session["session_id"]
            if session_id not in self._streams:
                self._streams[session_id] = []
            self._streams[session_id].append(message)

        self._streams = {}
        SSEClient._stream_to_frontend = mocked_stream_to_frontend

    def given_single_client(self):
        print("create client")
        self._client = SSEClient(
            "some-id", logger, "wss://tala-sse-ng-g6bpb0cncyc4htg3.swedencentral-01.azurewebsites.net", 443
        )
        print("client created")

    def when_client_streaming_to_num_sessions(self, num_sessions):
        for i in range(0, num_sessions):
            session_id = f"session-{i}"
            print("open session for session id", session_id)
            self._client.open_session(session_id)

        for round in range(0, 4):
            print("round", round)
            for i in random.sample(range(0, num_sessions), num_sessions):
                print("stream to", i)
                self._client.stream_chunk(f"session-{i}", f"session-{i} ")

        for i in range(0, num_sessions):
            print("close stream", i)
            client = self._client
            client.flush_stream(f"session-{i}")
            client.end_stream(f"session-{i}")
            client.close_session(f"session-{i}")
            print("done")

    def then_all_streams_correct(self):
        for session_id, streamed in self._streams.items():
            for item in streamed:
                if item["event"] == "STREAMING_CHUNK":
                    assert session_id + " " == item["data"]


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
