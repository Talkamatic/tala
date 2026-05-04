import uuid

from tala.cli.interact import console


class StubClient:
    def __init__(self, url, session_response=None):
        self.url = url
        self._session_response = session_response
        self.start_session_calls = []
        self.text_calls = []
        self.speech_calls = []
        self.passive_calls = []
        self.semantic_calls = []
        self.call_order = []

    def start_session(self, session_data):
        self.call_order.append("start")
        self.start_session_calls.append(session_data)
        response_session = self._session_response
        if response_session is None:
            response_session = session_data or {}
        return {"session": response_session, "output": {"utterance": "started"}}

    def request_text_input(self, utterance, session):
        self.text_calls.append((utterance, session))
        return {"session": session or {}, "output": {"utterance": "ok"}}

    def request_speech_input(self, hypotheses, session):
        self.speech_calls.append((hypotheses, session))
        return {"session": session or {}, "output": {"utterance": "ok"}}

    def request_semantic_input(self, interpretations, session, entities=None):
        self.call_order.append("semantic")
        self.semantic_calls.append((interpretations, session, entities))
        return {"session": session or {}, "output": {"utterance": "ok"}}

    def request_passivity(self, session):
        self.passive_calls.append(session)
        return {"session": session or {}, "output": {"utterance": ""}}


class StubClientWithHttpError(StubClient):
    class DummyResponse:
        def __init__(self, text):
            self.text = text

    class DummyException(Exception):
        def __init__(self, message, response):
            super().__init__(message)
            self.response = response

    def __init__(self, url, response_text):
        super().__init__(url)
        self._response_text = response_text

    def start_session(self, session_data):
        response = self.DummyResponse(self._response_text)
        raise self.DummyException("boom", response)


class TestTDMConsole:
    def setup_method(self):
        self._output_lines = []
        self._input_lines = []
        self._client = None
        self._runner = None

    def given_console_input(self, lines):
        self._input_lines = list(lines)

    def given_client(self, client):
        self._client = client

    def given_console(self, **kwargs):
        iterator = iter(self._input_lines)

        def input_func():
            return next(iterator)

        def output_func(message=""):
            self._output_lines.append(message)

        def client_factory(url):
            return self._client

        self._runner = console.TDMConsole(
            "http://example",
            client_cls=client_factory,
            input_func=input_func,
            output_func=output_func,
            **kwargs,
        )

    def when_running_console(self):
        self._runner.run()

    def then_session_started_with(self, expected):
        assert len(self._client.start_session_calls) == 1
        assert self._client.start_session_calls[0] == expected

    def then_session_started_count_is(self, expected):
        assert len(self._client.start_session_calls) == expected

    def then_semantic_move_is(self, ddd, move):
        assert len(self._client.semantic_calls) == 1
        interpretations = self._client.semantic_calls[0][0]
        assert len(interpretations) == 1
        interpretation = interpretations[0]
        assert interpretation.moves[0].ddd == ddd
        assert interpretation.moves[0].semantic_expression == move
        assert interpretation.utterance == ""

    def then_no_session_id_sent(self):
        assert "session_id" not in self._client.start_session_calls[0]

    def then_text_request_session_id_is(self, expected):
        assert len(self._client.text_calls) == 1
        assert self._client.text_calls[0][1]["session_id"] == expected

    def then_speech_request_sent(self, utterance):
        assert len(self._client.speech_calls) == 1
        hypotheses = self._client.speech_calls[0][0]
        assert hypotheses[0].utterance == utterance

    def then_speech_request_session_id_is(self, expected):
        assert len(self._client.speech_calls) == 1
        assert self._client.speech_calls[0][1]["session_id"] == expected

    def then_passivity_sent_count_is(self, expected):
        assert len(self._client.passive_calls) == expected

    def then_output_contains(self, expected):
        assert any(expected in line for line in self._output_lines)

    def test_session_prefix_generates_session_id(self, monkeypatch):
        fixed_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
        monkeypatch.setattr(console.uuid, "uuid4", lambda: fixed_uuid)
        self.given_client(StubClient("http://example"))
        self.given_console_input(["/start", "/quit"])
        self.given_console(session_prefix="cli", device_id="device-1")
        self.when_running_console()
        self.then_session_started_with({
            "device_id": "device-1",
            "session_id": "cli-11111111-1111-1111-1111-111111111111",
        })

    def test_backend_generated_session_id_used_for_requests(self):
        self.given_client(
            StubClient("http://example", session_response={
                "session_id": "backend-id",
                "device_id": "device"
            })
        )
        self.given_console_input(["hello", "/quit"])
        self.given_console(device_id="device")
        self.when_running_console()
        self.then_no_session_id_sent()
        self.then_speech_request_session_id_is("backend-id")

    def test_session_command_is_not_supported(self):
        self.given_client(StubClient("http://example", session_response={"session_id": "backend-id"}))
        self.given_console_input(["/session new-id", "hello", "/quit"])
        self.given_console()
        self.when_running_console()
        self.then_no_session_id_sent()
        assert len(self._client.speech_calls) == 1

    def test_auto_start_defaults_to_true(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["/quit"])
        self.given_console()
        self.when_running_console()
        self.then_session_started_count_is(1)

    def test_auto_start_can_be_disabled(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["/quit"])
        self.given_console(auto_start=False)
        self.when_running_console()
        self.then_session_started_count_is(0)

    def test_ddd_entry_move_sent_after_start(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["/quit"])
        self.given_console(ddd="grouping_1")
        self.when_running_console()
        assert self._client.call_order == ["start", "semantic"]
        self.then_semantic_move_is("grouping_1", console.DEFAULT_DDD_ENTRY_MOVE)

    def test_prefixed_move_input_sends_semantic_request(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["grouping_1:request(top)", "/quit"])
        self.given_console(auto_start=False)
        self.when_running_console()
        self.then_semantic_move_is("grouping_1", "request(top)")

    def test_http_error_body_is_reported(self):
        self.given_client(StubClientWithHttpError("http://example", "backend error details"))
        self.given_console_input(["/quit"])
        self.given_console()
        self.when_running_console()
        self.then_output_contains("body: backend error details")

    def test_http_error_body_with_hypotheses_hint(self):
        response_text = "KeyError: 'hypotheses'"
        self.given_client(StubClientWithHttpError("http://example", response_text))
        self.given_console_input(["/quit"])
        self.given_console()
        self.when_running_console()
        self.then_output_contains("hint: try --input-mode speech")

    def test_input_mode_speech_sends_hypotheses(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["hello", "/quit"])
        self.given_console(input_mode="speech")
        self.when_running_console()
        self.then_speech_request_sent("hello")

    def test_input_mode_text_sends_text_request(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["hello", "/quit"])
        self.given_console(input_mode="text")
        self.when_running_console()
        assert len(self._client.text_calls) == 1

    def test_empty_line_sends_passivity(self):
        self.given_client(StubClient("http://example"))
        self.given_console_input(["", "/quit"])
        self.given_console(auto_start=False)
        self.when_running_console()
        self.then_passivity_sent_count_is(1)
