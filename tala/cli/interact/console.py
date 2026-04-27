import argparse
import json
import uuid

from tala.model.common import Modality
from tala.model.input_hypothesis import InputHypothesis
from tala.model.interpretation import Interpretation
from tala.model.user_move import DDDSpecificUserMove
from tala.utils.tdm_client import TDMClient

DEFAULT_DEVICE_ID = "tala-cli"
DEFAULT_DDD_ENTRY_MOVE = "request(top)"
DEFAULT_INPUT_MODE = "speech"
INPUT_MODE_TEXT = "text"
INPUT_MODE_SPEECH = "speech"


class TDMConsole:
    def __init__(
        self,
        url,
        device_id=DEFAULT_DEVICE_ID,
        session_id=None,
        session_prefix=None,
        auto_start=True,
        ddd=None,
        input_mode=DEFAULT_INPUT_MODE,
        show_moves=False,
        raw_output=False,
        client_cls=TDMClient,
        input_func=input,
        output_func=print,
    ):
        self._url = url
        self._device_id = device_id
        self._show_moves = show_moves
        self._raw_output = raw_output
        self._auto_start = auto_start
        self._ddd = ddd
        self._ddd_entered = False
        self._input_mode = input_mode
        self._input = input_func
        self._output = output_func
        self._session_id = session_id
        if session_id and session_prefix:
            raise ValueError("--session and --session-prefix cannot be used together")
        if session_prefix:
            self._session_id = self._create_prefixed_session_id(session_prefix)
        self._client = client_cls(url)
        self._session = None
        self._started = False

    def run(self):
        self._emit("TDM CLI ready. Type /quit to exit.")
        self._emit("Use /start to begin, or enter text directly.")
        self._emit("Semantic moves: <ddd>:request(top)")
        if self._auto_start:
            self._emit("auto-starting session")
            self._start_session()
        while True:
            try:
                line = self._input()
            except (EOFError, StopIteration):
                break
            if line is None:
                break
            line = line.strip()
            if not line:
                self._handle_passive()
                continue
            if line.startswith("/"):
                if not self._handle_command(line):
                    break
            else:
                self._handle_utterance(line)

    def _create_prefixed_session_id(self, prefix):
        return f"{prefix}-{uuid.uuid4()}"

    def _handle_command(self, line):
        parts = line[1:].split()
        if not parts:
            return True
        command = parts[0]
        args = parts[1:]
        if command in ("quit", "exit"):
            return False
        if command == "start":
            self._start_session()
            return True
        if command == "passive":
            self._handle_passive()
            return True
        if command == "device":
            self._handle_device(args)
            return True
        if command == "raw":
            self._raw_output = not self._raw_output
            self._emit(f"raw: {'on' if self._raw_output else 'off'}")
            return True
        self._emit(f"unknown command: /{command}")
        return True

    def _handle_device(self, args):
        if not args:
            self._emit(f"device: {self._device_id}")
            return
        if self._started:
            self._emit("device id locked after session start")
            return
        self._device_id = " ".join(args)

    def _handle_passive(self):
        if not self._ensure_session_started():
            return
        self._send_request(self._client.request_passivity, self._session)

    def _handle_utterance(self, utterance):
        prefixed_move = self._split_prefixed_move(utterance)
        if prefixed_move:
            ddd, move = prefixed_move
            self._handle_semantic_move(ddd, move)
            return
        if not self._ensure_session_started():
            return
        if self._input_mode == INPUT_MODE_SPEECH:
            hypotheses = [InputHypothesis(utterance, 1.0)]
            self._send_request(self._client.request_speech_input, hypotheses, self._session)
        else:
            self._send_request(self._client.request_text_input, utterance, self._session)

    def _handle_semantic_move(self, ddd, move):
        if not self._ensure_session_started():
            return
        interpretation = Interpretation([DDDSpecificUserMove(ddd, move, 1.0, 1.0)], Modality.OTHER, utterance="")
        self._send_request(self._client.request_semantic_input, [interpretation], self._session)

    def _ensure_session_started(self):
        if self._started:
            return True
        response = self._start_session()
        return response is not None

    def _start_session(self):
        if self._started:
            self._emit("session already started")
            return None
        session_data = self._build_session_data()
        self._session = dict(session_data)
        response = self._send_request(self._client.start_session, session_data)
        if response is not None:
            self._started = True
            self._maybe_enter_ddd()
        return response

    def _maybe_enter_ddd(self):
        if not self._ddd or self._ddd_entered:
            return
        self._ddd_entered = True
        self._emit(f"entering ddd: {self._ddd}")
        self._handle_semantic_move(self._ddd, DEFAULT_DDD_ENTRY_MOVE)

    def _build_session_data(self):
        session_data = {"device_id": self._device_id}
        if self._session_id:
            session_data["session_id"] = self._session_id
        return session_data

    def _send_request(self, func, *args):
        try:
            response = func(*args)
        except Exception as exc:
            response = getattr(exc, "response", None)
            if response is not None:
                body = getattr(response, "text", None)
                if body:
                    self._emit(f"error: {exc} | body: {body}")
                    if "KeyError" in body and "hypotheses" in body:
                        self._emit("hint: try --input-mode speech for this backend")
                    return None
            self._emit(f"error: {exc}")
            return None
        self._handle_response(response)
        return response

    def _handle_response(self, response):
        self._update_session(response)
        output = response.get("output") if isinstance(response, dict) else None
        if isinstance(output, dict) and "utterance" in output:
            self._emit(str(output["utterance"]))
        if self._show_moves and isinstance(output, dict) and output.get("moves") is not None:
            moves_json = json.dumps(output["moves"], ensure_ascii=True)
            self._emit(f"moves: {moves_json}")
        if self._raw_output:
            raw_json = json.dumps(response, indent=2, sort_keys=True, ensure_ascii=True)
            self._emit(raw_json)

    def _update_session(self, response):
        if not isinstance(response, dict):
            return
        incoming = response.get("session")
        if not isinstance(incoming, dict):
            return
        if self._session is None:
            self._session = dict(incoming)
        else:
            for key, value in incoming.items():
                if key == "session_id" and self._session_id and value != self._session_id:
                    continue
                self._session[key] = value
        if self._session_id is None and "session_id" in incoming:
            self._session_id = incoming["session_id"]

    def _split_prefixed_move(self, line):
        if ":" not in line:
            return None
        ddd, remainder = line.split(":", 1)
        if not ddd or not remainder:
            return None
        if remainder.startswith(("ask(", "answer(", "request(", "report(", "icm:")):
            return ddd, remainder
        return None

    def _emit(self, message):
        self._output(message)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Terminal chat client for TDM backends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  tala-interact https://host/interact/<id>\n"
            "  tala-interact https://host/interact/<id> --ddd grouping_1\n"
            "  tala-interact https://host/interact/<id> --no-auto-start\n"
            "  tala-interact https://host/interact/<id> --input-mode text\n"
            "\n"
            "scripting:\n"
            "  printf \"/start\\n\\nhello\\n/quit\\n\" | tala-interact https://host/interact/<id>\n"
            "  printf \"/start\\ngrouping_1:request(top)\\n/quit\\n\" | tala-interact https://host/interact/<id>\n"
            "  cat <<'EOF' | tala-interact https://host/interact/<id> --ddd grouping_1\n"
            "  /start\n"
            "\n"
            "  grouping_1:request(top)\n"
            "  /quit\n"
            "  EOF\n"
            "\n"
            "commands:\n"
            "  /start  start session\n"
            "  /quit   exit\n"
            "  /raw    toggle raw responses\n"
            "  /device <id>  set device id before start\n"
            "  /passive  send passivity (empty line also sends passivity)\n"
            "\n"
            "notes:\n"
            "  empty line triggers passivity\n"
            "  semantic move format: <ddd>:request(top)\n"
            "\n"
            "scripting notes:\n"
            "  use scripting to replay deterministic flows and reproduce issues\n"
            "  useful for smoke tests, regressions, and cross-environment comparisons\n"
            "  works with semantic moves (DDD-prefixed) and passivity (blank line)\n"
        ),
    )
    parser.add_argument("url", help="TDM interact endpoint URL")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Device identifier")
    parser.add_argument("--ddd", help="DDD to enter after session start")
    parser.add_argument(
        "--input-mode",
        choices=[INPUT_MODE_TEXT, INPUT_MODE_SPEECH],
        default=DEFAULT_INPUT_MODE,
        help="Input mode for utterances",
    )
    parser.add_argument("--show-moves", action="store_true", help="Print output moves after each reply")
    parser.add_argument("--raw", dest="raw_output", action="store_true", help="Print raw responses")
    parser.add_argument("--auto-start", dest="auto_start", action="store_true", help="Auto-start session")
    parser.add_argument("--no-auto-start", dest="auto_start", action="store_false", help="Disable auto-start")
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument("--session", help="Explicit session id to use")
    session_group.add_argument("--session-prefix", help="Prefix for a generated session id")
    parser.set_defaults(auto_start=True)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    console = TDMConsole(
        args.url,
        device_id=args.device_id,
        session_id=args.session,
        session_prefix=args.session_prefix,
        auto_start=args.auto_start,
        ddd=args.ddd,
        input_mode=args.input_mode,
        show_moves=args.show_moves,
        raw_output=args.raw_output,
    )
    console.run()


if __name__ == "__main__":
    main()
