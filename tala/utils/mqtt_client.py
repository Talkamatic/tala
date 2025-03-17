import json
import threading
import queue
import uuid
import warnings

import requests
import paho.mqtt.client as mqtt

STREAMING_DONE = "STREAMING_DONE"
STREAMING_SET_PERSONA = "STREAMING_SET_PERSONA"
STREAMING_SET_VOICE = "STREAMING_SET_VOICE"
STREAMING_CHUNK = "STREAMING_CHUNK"
TIMEOUT = 5.0


class MQTTClientException(BaseException):
    pass


class MQTTClient:
    def __init__(self, client_id_base, logger, endpoint, port=None):
        def on_connect(client, userdata, connect_flags, reason_code, properties):
            self.logger.info('CONNACK received', reason_code=reason_code, properties=properties)
            self._connected.set()

        self._setup_logger(logger)
        self._endpoint = endpoint
        self._port = int(port)
        self._connected = threading.Event()
        self._session_id = None
        self._client_id = f"{client_id_base}-{str(uuid.uuid4())}"

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
            reconnect_on_failure=True,
            clean_session=True,
            client_id=self._client_id
        )
        self._client.on_connect = on_connect
        self._client.tls_set()
        self._message_counter = 0
        self._streamed = []

    def _setup_logger(self, logger):
        self._base_logger = logger
        self._set_logger(logger)

    def _set_logger(self, logger):
        self.logger = logger

    def _reset_logger(self):
        self._set_logger(self._base_logger)

    def start(self):
        self.logger.info("connecting to", endpoint=self._endpoint, port=self._port)
        self._client.connect(self._endpoint, self._port)
        self._client.loop_start()

    @property
    def session_id(self):
        return self._session_id

    @property
    def streamed(self):
        return self._streamed

    @property
    def client_id(self):
        return self._client_id

    @property
    def topic(self):
        return f'tm/id/{self.session_id}'

    def prepare_session(self, session_id, s_and_r_dict=None):
        warnings.warn(
            "MQTTClient.prepare_session() is deprecated. Use MQTTClient.open_session instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.open_session(session_id, s_and_r_dict)

    def open_session(self, session_id, s_and_r_dict=None, logger=None):
        if logger:
            self._set_logger(logger)
        self._session_id = session_id
        self._search_and_replace_dict = s_and_r_dict if s_and_r_dict else {}
        self.logger.info("open_session", client_id=self.client_id, session_id=self.session_id)
        self._message_counter = 0
        self._streamed = []
        self._prepare_streamer_thread()

    def _apply_dictionary(self, chunk):
        def key_matches_beginning_of_chunk(key, chunk):
            return chunk.startswith(f"{key} ")

        def key_matches_middle_of_chunk(key, chunk):
            chunk_ends = [" ", ".", ",", "!", "?"]
            for end in chunk_ends:
                search_term = f" {key}{end}"
                if search_term in chunk:
                    return search_term

        def key_matches_end_of_chunk(key, chunk):
            return chunk.endswith(f" {key}")

        if chunk in self._search_and_replace_dict:
            self.logger.info("Matched entire chunk", chunk=chunk)
            return self._search_and_replace_dict[chunk]
        for key in self._search_and_replace_dict:
            if key_matches_beginning_of_chunk(key, chunk):
                self.logger.info("Matched beginning of chunk", key=key, chunk=chunk)
                chunk = chunk.replace(key, self._search_and_replace_dict[key], 1)
            match = key_matches_middle_of_chunk(key, chunk)
            while match:
                self.logger.info("Matched middle of chunk", key=key, chunk=chunk)
                chunk = chunk.replace(key, self._search_and_replace_dict[key], 1)
                match = key_matches_middle_of_chunk(key, chunk)
            if key_matches_end_of_chunk(key, chunk):
                self.logger.info("Matched end of chunk", key=key, chunk=chunk)
                chunk = chunk.replace(key, self._search_and_replace_dict[key], 1)
        return chunk

    def _prepare_streamer_thread(self):
        def stream_chunks():
            self._streaming_exception = None
            for chunk in self._chunk_joiner:
                try:
                    chunk = self._apply_dictionary(chunk)
                    self._stream_to_frontend({"event": STREAMING_CHUNK, "data": chunk})
                    self._streamed.append(chunk)
                except Exception as e:
                    self._streaming_exception = e
                    self.logger.exception("Exception raised in streamer thread")

        self._chunk_joiner = ChunkJoiner(self.logger)
        self.streamer_thread = threading.Thread(target=stream_chunks)
        self.streamer_thread.start()

    def stream_utterance(self, persona=None, voice=None, utterance=""):
        self.set_persona(persona)
        self.set_voice(voice)
        self.stream_chunk(utterance + " ")

    def set_persona(self, persona):
        self._stream_to_frontend({"event": STREAMING_SET_PERSONA, "data": persona if persona else ""})

    def set_voice(self, voice):
        self._stream_to_frontend({"event": STREAMING_SET_VOICE, "data": voice if voice else ""})

    def _stream_to_frontend(self, message):
        def remove_final_space(message):
            if "data" in message:
                message["data"] = message["data"].strip()
            return message

        self._message_counter += 1
        self.logger.debug(
            "MQTT Client streaming to frontend", message=message, session_id=self.session_id, client_id=self.client_id
        )
        self._connected.wait()
        self.logger.debug("publish message", message=message, session_id=self.session_id, client_id=self.client_id)
        self._client.publish(self.topic, json.dumps(message))

    def stream_chunk(self, chunk):
        self._chunk_joiner.add_chunk(chunk)

    def flush_stream(self):
        self.logger.info("flushing stream")
        self._chunk_joiner.last_chunk_sent()
        self.streamer_thread.join(3.0)
        if self.streamer_thread.is_alive():
            self.logger.warn("Streamer thread is still alive!", streamed=self._streamed)

    def end_stream(self):
        self.logger.info("ending stream")
        self._stream_to_frontend({"event": STREAMING_DONE})

    def finalize_session(self):
        warnings.warn(
            "MQTTClient.finalize_session() is deprecated. Use MQTTClient.close_session() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.close_session()

    def close_session(self):
        if self._streaming_exception:
            raise MQTTClientException(
                f"{self._streaming_exception} was raised during streaming in {self.session_id}. Streamed: {self._streamed}."
            )
        self.logger.info("close session", client_id=self.client_id, session_id=self.session_id)
        self.logger.info("Streamed in session", num_messages=self._message_counter, streamed=self._streamed)
        self._reset_logger()
        self._session_id = None


class StreamIterator:
    def __init__(self, session_id, logger):
        self.logger = logger
        self.url = f'https://tala-event-sse.azurewebsites.net/event-sse/{session_id}'
        self.response = None
        self.iterator = None

        self._current_event = None
        self._session_id = session_id
        self._stream = None

    def wait_for_message(self, expected_message):
        next_message = self.get_next_message()
        if json.loads(expected_message) != json.loads(next_message):
            self.logger.info("received unexpected message", expected=expected_message, received=next_message)
            raise MQTTClientException(f"Expected '{expected_message}', but received '{next_message}'.")
        else:
            self.logger.info("received expected message", message=next_message)

    @property
    def session_id(self):
        return self._session_id

    def start_stream(self):
        """Start the streaming connection and prepare the iterator."""
        self.response = requests.get(self.url, stream=True)
        self.response.raise_for_status()  # Ensure the response is successful
        self.iterator = self.response.iter_lines()

    def get_next_message(self):
        """Retrieve the next message from the stream."""
        if self.iterator is None:
            raise RuntimeError("Stream has not been started. Call start_stream() first.")
        try:
            item = self._get_next_item()
            return item
        except StopIteration:
            return None

    def close_stream(self):
        if self.response:
            self.response.close()
            self.response = None

    def _get_next_item(self):
        def is_event(line):
            return line.startswith("event: ")

        def is_data(line):
            return line.startswith("data: ")

        def extract_event(line):
            return line[len("event: "):]

        def extract_data(line):
            return line[len("data: "):]

        while True:
            line = next(self.iterator).decode('utf-8')
            if is_event(line):
                event = extract_event(line)
                if event == STREAMING_DONE:
                    self.close_stream()
                    return f'{{"event": "{event}"}}'
                elif event in [STREAMING_CHUNK, STREAMING_SET_PERSONA, STREAMING_SET_VOICE]:
                    while True:
                        next_line = next(self.iterator).decode('utf-8')
                        if is_data(next_line):
                            data = extract_data(next_line)
                            return f'{{"event": "{event}", "data": "{data.strip()}"}}'


class ChunkJoiner:
    """
    Iterates over segments put together from chunks received in the queue. A segment is not made available until we know
    that it's a complete segment. To be considered complete segment means that the next chunk starts with a space, or
    that someone called last_chunk_sent().
    """
    def __init__(self, logger):
        self.logger = logger
        self._chunk_queue = queue.Queue()
        self._received_last_chunk = threading.Event()
        self._next_chunk = None
        self._collected_chunks = []

    def add_chunk(self, chunk):
        self._chunk_queue.put(chunk)

    def last_chunk_sent(self):
        self._received_last_chunk.set()

    def __next__(self):
        return self._get_next_segment()

    def _get_next_segment(self):
        self._collected_chunks = []
        self._collect_chunks()
        if self._collected_chunks:
            next_segment = "".join(self._collected_chunks)
            self.logger.info("Joiner collected segment", next_segment=next_segment)
            return next_segment
        else:
            self.logger.info("No chunks collected, stopping iteration")
            raise StopIteration

    def _collect_chunks(self):
        def waiting_for_first_chunk():
            return self._collected_chunks == []

        def add_next_chunk_to_collected_chunks():
            self._collected_chunks.append(self._next_chunk)
            self._next_chunk = None

        def next_chunk_belongs_to_this_segment():
            return not self._next_chunk.startswith(" ")

        def handle_possible_last_chunk():
            try:
                self._next_chunk = self._chunk_queue.get_nowait()
                if self._next_chunk:
                    self.logger.info("there was a last chunk to handle.")
                    add_next_chunk_to_collected_chunks()
            except queue.Empty:
                pass

        while not self._complete_segment_collected():
            try:
                if not self._next_chunk:
                    self._next_chunk = self._chunk_queue.get(timeout=0.05)

                if waiting_for_first_chunk() or next_chunk_belongs_to_this_segment():
                    add_next_chunk_to_collected_chunks()

            except queue.Empty:
                if self._received_last_chunk.is_set():
                    self.logger.info("received last chunk")
                    handle_possible_last_chunk()
                    break

    def _complete_segment_collected(self):
        def next_chunk_was_not_needed_to_complete_this_segment():
            return self._collected_chunks and self._next_chunk

        def collected_chunks_end_with_space():
            return self._collected_chunks and self._collected_chunks[-1].endswith(" ")

        return next_chunk_was_not_needed_to_complete_this_segment() or collected_chunks_end_with_space()

    def __iter__(self):
        return self
