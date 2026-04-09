import json

from tala.utils import customer_stream_logger


class FakeResponse:
    def __init__(self, lines):
        self._lines = lines
        self.closed = False

    def iter_lines(self):
        for line in self._lines:
            yield line

    def raise_for_status(self):
        return None

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class DcrClientStub:
    def __init__(self):
        self.upload_calls = []

    def upload(self, rule_id, stream_name, logs):
        self.upload_calls.append({
            "rule_id": rule_id,
            "stream_name": stream_name,
            "logs": logs,
        })


class TestCustomerStreamLogger:
    def test_logs_user_and_system_turns(self, monkeypatch):
        self.given_user_metadata({
            "ddd_name": "shopping",
            "user_moves": ["buy"],
            "user_utterance": "hi",
            "turn_count": 2,
        })
        self.given_system_metadata({
            "ddd_name": "shopping",
            "system_moves": ["confirm"],
            "turn_count": 2,
        })
        self.given_stream_events([
            ("USR_TURN_METADATA", self._user_metadata),
            ("STREAMING_CHUNK", "Hello "),
            ("STREAMING_CHUNK", "there"),
            ("SYS_TURN_METADATA", self._system_metadata),
            ("STREAMING_DONE", None),
        ])
        self.given_stream_response(monkeypatch)
        self.given_stream_environment(monkeypatch)
        self.given_dcr_client()
        self.given_logger_instance()

        self.when_logger_runs()

        self.then_stream_closed()
        self.then_logs_sent()
        self.then_user_log_is_expected()
        self.then_system_log_is_expected()

    def given_user_metadata(self, metadata):
        self._user_metadata = metadata

    def given_system_metadata(self, metadata):
        self._system_metadata = metadata

    def given_stream_events(self, events):
        lines = []
        for event, data in events:
            lines.append(f"event: {event}".encode("utf-8"))
            if data is None:
                continue
            if isinstance(data, dict):
                payload = json.dumps(data)
            else:
                payload = data
            lines.append(f"data: {payload}".encode("utf-8"))
        self._stream_lines = lines

    def given_stream_response(self, monkeypatch):
        self._response = FakeResponse(self._stream_lines)

        def fake_get(url, stream=True):
            return self._response

        monkeypatch.setattr(customer_stream_logger.requests, "get", fake_get)

    def given_stream_environment(self, monkeypatch):
        monkeypatch.setenv("SSE_BROKER_ENDPOINT_HTTPS", "https://example.test/event-sse")

    def given_dcr_client(self):
        self._dcr_client = DcrClientStub()

    def given_logger_instance(self):
        self._logger = customer_stream_logger.CustomerStreamLogger(
            session_id="session-1",
            offer_id="offer-1",
            offer_name="Offer",
            user_name="user-1",
            device_id="device-1",
            dcr_client=self._dcr_client,
        )

    def when_logger_runs(self):
        self._logger.run()

    def then_stream_closed(self):
        assert self._response.closed is True

    def then_logs_sent(self):
        assert len(self._dcr_client.upload_calls) == 2

    def then_user_log_is_expected(self):
        user_log = dict(self._dcr_client.upload_calls[0]["logs"][0])
        user_log.pop("TimeGenerated", None)
        assert user_log == {
            "device_id": "device-1",
            "event": "request",
            "grouping_ddd": "shopping",
            "moves": ["buy"],
            "offer_id": "offer-1",
            "offer_name": "Offer",
            "selected_interpretation": "",
            "session_id": "session-1",
            "turn": 2,
            "username": "user-1",
            "utterance": "U> hi",
        }

    def then_system_log_is_expected(self):
        system_log = dict(self._dcr_client.upload_calls[1]["logs"][0])
        system_log.pop("TimeGenerated", None)
        assert system_log == {
            "device_id": "device-1",
            "event": "response",
            "grouping_ddd": "shopping",
            "moves": ["confirm"],
            "offer_id": "offer-1",
            "offer_name": "Offer",
            "selected_interpretation": "",
            "session_id": "session-1",
            "turn": 2,
            "username": "user-1",
            "utterance": "S> Hello there",
        }
