import json
import threading
import queue
import uuid

import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, client_id_base, logger, endpoint, port=None):
        def on_connect(client, userdata, connect_flags, reason_code, properties):
            self.logger.info('CONNACK received', reason_code=reason_code, properties=properties)
            self._connected.set()

        self.logger = logger
        self._endpoint = endpoint
        self._port = int(port)
        self._connected = threading.Event()
        self._session_id = None
        self._request_id = None
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

    def start(self):
        self.logger.info("connecting to", endpoint=self._endpoint, port=self._port)
        self._client.connect(self._endpoint, self._port)
        self._client.loop_start()

    @property
    def session_id(self):
        return self._session_id

    @property
    def request_id(self):
        return self._request_id

    @property
    def streamed(self):
        return self._streamed

    @property
    def topics(self):
        yield f'tm/id/{self.session_id}'
        if self.request_id:
            yield f'tm/id/{self.session_id}-{self.request_id}'

    def prepare_session(self, session_id, request_id=None, s_and_r_dict=None):
        self.open_session(session_id, request_id, s_and_r_dict)

    def open_session(self, session_id, request_id=None, s_and_r_dict=None):
        self._session_id = session_id
        self._request_id = request_id
        self._search_and_replace_dict = s_and_r_dict if s_and_r_dict else {}
        self.logger.info(
            "prepare_session", client_id=self._client_id, session_id=self.session_id, request_id=self.request_id
        )
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
            return self._search_and_replace_dict[chunk]
        for key in self._search_and_replace_dict:
            if key_matches_beginning_of_chunk(key, chunk):
                chunk = chunk.replace(key, self._search_and_replace_dict[key], 1)
            match = key_matches_middle_of_chunk(key, chunk)
            while match:
                replacement = match.replace(key, chunk)
                chunk.replace(match, replacement)
                match = key_matches_middle_of_chunk(key, chunk)
            if key_matches_end_of_chunk(key, chunk):
                chunk = chunk.replace(key, self._search_and_replace_dict[key], 1)
        return chunk

    def _prepare_streamer_thread(self):
        def stream_chunks():
            for chunk in self._chunk_joiner:
                chunk = self._apply_dictionary(chunk)
                self._stream_to_frontend({"event": "STREAMING_CHUNK", "data": chunk})
                self._streamed.append(chunk)

        self._chunk_joiner = ChunkJoiner()
        self.streamer_thread = threading.Thread(target=stream_chunks)
        self.streamer_thread.start()

    def stream_utterance(self, persona=None, voice=None, utterance=""):
        self.set_persona(persona)
        self.set_voice(voice)
        self.stream_chunk(utterance + " ")

    def set_persona(self, persona):
        self._stream_to_frontend({"event": "STREAMING_SET_PERSONA", "data": persona if persona else ""})

    def set_voice(self, voice):
        self._stream_to_frontend({"event": "STREAMING_SET_VOICE", "data": voice if voice else ""})

    def _stream_to_frontend(self, message):
        self._message_counter += 1
        message |= {"id": f"{self._message_counter}_{self._client_id}"}
        self.logger.debug("streaming to frontend", message=message, session_id=self.session_id)
        self._connected.wait()
        for topic in self.topics:
            self._client.publish(topic, json.dumps(message))

    def stream_chunk(self, chunk):
        self._chunk_joiner.add_chunk(chunk)

    def flush_stream(self):
        self._chunk_joiner.last_chunk_sent()
        self.streamer_thread.join()

    def end_stream(self):
        self._stream_to_frontend({"event": "STREAMING_DONE"})

    def finalize_session(self):
        self.close_session()

    def close_session(self):
        self.logger.info(
            "finalizing session", client_id=self._client_id, session_id=self.session_id, request_id=self.request_id
        )
        self.logger.info("Streamed in session", num_messages=self._message_counter, streamed=self._streamed)
        self._session_id = None
        self._request_id = None


class ChunkJoiner:
    """
    Iterates over words put together from chunks received in the queue. A word is not made available until we know
    that it's a complete word. To be considered complete word means that the next chunk starts with a space, or
    that someone called last_chunk_sent().
    """
    def __init__(self):
        self._chunk_queue = queue.Queue()
        self._received_last_chunk = threading.Event()
        self.flushed = threading.Event()
        self._next_chunk = None
        self._collected_chunks = []

    def add_chunk(self, chunk):
        self._chunk_queue.put(chunk)

    def last_chunk_sent(self):
        self._received_last_chunk.set()

    def __next__(self):
        return self._get_next_word()

    def _get_next_word(self):
        self._collected_chunks = []
        self._get_word()
        if self._collected_chunks:
            return "".join(self._collected_chunks)
        else:
            self.flushed.set()
            raise StopIteration

    def _get_word(self):
        def waiting_for_first_part_of_word():
            return not self._collected_chunks

        def get_next_chunk_from_queue():
            self._next_chunk = self._chunk_queue.get(timeout=0.1)

        def add_next_chunk_to_collected_chunks():
            self._collected_chunks.append(self._next_chunk)
            self._next_chunk = None

        def next_chunk_belongs_to_this_word():
            return not self._next_chunk.startswith(" ")

        def handle_possible_last_chunk():
            try:
                self._next_chunk = self._chunk_queue.get_nowait()
                if self._next_chunk:
                    print("This happened!")
                    add_next_chunk_to_collected_chunks()
            except queue.Empty:
                pass

        while not self._complete_word_collected():
            try:
                if not self._next_chunk:
                    get_next_chunk_from_queue()

                if waiting_for_first_part_of_word():
                    add_next_chunk_to_collected_chunks()
                elif next_chunk_belongs_to_this_word():
                    add_next_chunk_to_collected_chunks()

            except queue.Empty:
                if self._received_last_chunk.is_set():
                    handle_possible_last_chunk()
                    break

    def _complete_word_collected(self):
        def next_chunk_not_needed_to_complete_this_word():
            return self._collected_chunks and self._next_chunk

        def collected_chunks_end_with_space():
            return self._collected_chunks and self._collected_chunks[-1].endswith(" ")

        return next_chunk_not_needed_to_complete_this_word() or collected_chunks_end_with_space()

    def __iter__(self):
        return self
