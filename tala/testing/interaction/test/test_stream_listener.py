from tala.testing.interaction.stream_listener import StreamListener

import structlog

logger = structlog.get_logger("test-logger")


class TestStreamLitener:
    def test_quotes_in_streamed_chunk(self):
        self.given_stream_listener()
        self.given_chunk('this contains "quotes".')
        self.when_chunk_processed()
        self.then_chunk_available({"event": "STREAMING_CHUNK", "data": 'this contains "quotes".'})

    def given_stream_listener(self):
        self._listener = StreamListener("some-url", "some-session-id", logger)

    def given_chunk(self, chunk):
        self._chunk = chunk

    def when_chunk_processed(self):
        self._listener.process_line("event: STREAMING_CHUNK")
        self._listener.process_line(f"data: {self._chunk}")

    def then_chunk_available(self, expected_chunk):
        assert expected_chunk in self._listener.payload
