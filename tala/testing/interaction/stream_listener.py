import json
import requests
import threading
import time

TIMEOUT = 2.0


class StreamListener(threading.Thread):
    def __init__(self, session_id):
        self.current_data = None
        self.current_event = None
        self.stream_started = threading.Event()
        self._please_stop = threading.Event()
        self._stopped = threading.Event()
        self._session_id = session_id
        self._streaming_started = None
        self._streaming_ended = None
        super().__init__(daemon=True)

    def run(self):
        self._streamed_messages = []
        response = requests.get(f'https://tala-event-sse.azurewebsites.net/event-sse/{self._session_id}', stream=True)
        self.stream_started.set()
        for line in response.iter_lines():
            if line:  # filter out keep-alive new lines
                decoded_line = line.decode('utf-8')
                self.process_line(decoded_line)
            if self._please_stop.is_set():
                break
        self._stopped.set()

    def process_line(self, line):
        def is_event():
            return line.startswith("event: ")

        def is_data():
            return line.startswith("data: ")

        def extract_event():
            return line[len("event: "):]

        def extract_data():
            return line[len("data: "):]

        if is_event():
            self.current_event = extract_event()
        if is_data() and self.current_event:
            self.current_data = extract_data()
            self.create_event_and_store()

    def create_event_and_store(self):
        try:
            if self.current_event == "STREAMING_CLEAR":
                json_event = f'{{"event": "{self.current_event}"}}'
            if self.current_event == "STREAMING_DONE":
                json_event = f'{{"event": "{self.current_event}"}}'
                self._streaming_ended = time.time()
                self.please_stop()
            if self.current_event == "STREAMING_CHUNK":
                if not bool(self._streaming_started):
                    self._streaming_started = time.time()

                json_event = f'{{"event": "{self.current_event}", "data": "{self.current_data}"}}'
            if json_event:
                self._streamed_messages.append(json.loads(json_event))
        except UnboundLocalError:
            pass
        self.current_event = None

    def please_stop(self):
        self._please_stop.set()

    @property
    def payload(self):
        self._stopped.wait(TIMEOUT)
        return self._streamed_messages

    @property
    def system_utterance(self):
        utterance = ""
        for item in self.payload:
            try:
                utterance += item["data"]
            except KeyError:
                pass
        return utterance.strip()

    @property
    def streaming_started(self):
        return self._streaming_started

    @property
    def streaming_ended(self):
        return self._streaming_ended
