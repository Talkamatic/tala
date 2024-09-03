import json
import threading

import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, client_id, logger, endpoint, port=None):
        def on_connect(client, userdata, connect_flags, reason_code, properties):
            self.logger.info('CONNACK received', reason_code=reason_code, properties=properties)
            self._connected.set()

        self.logger = logger
        self._endpoint = endpoint
        self._port = int(port)
        self._connected = threading.Event()
        self._session_id = None
        self._request_id = None
        self._client_id = client_id

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
            reconnect_on_failure=True,
            clean_session=True,
            client_id=client_id
        )
        self._client.on_connect = on_connect
        self._client.tls_set()
        self._message_counter = 0
        self._streamed = []

    def start(self):
        self._client.connect(self._endpoint, self._port)
        self._client.loop_start()

    @property
    def session_id(self):
        return self._session_id

    @session_id.setter
    def session_id(self, session_id):
        self._session_id = session_id

    @property
    def request_id(self):
        return self._request_id

    @request_id.setter
    def request_id(self, request_id):
        self._request_id = request_id

    @property
    def streamed(self):
        return self._streamed

    @property
    def topics(self):
        yield f'tm/id/{self.session_id}'
        if self.request_id:
            yield f'tm/id/{self.session_id}-{self.request_id}'

    def stream_utterance(self, persona=None, voice=None, utterance="", status=None):
        self.set_persona(persona)
        self.set_voice(voice)
        self.stream_chunk(utterance + " ")

    def set_persona(self, persona):
        self._stream_to_frontend({"event": "STREAMING_SET_PERSONA", "data": persona if persona else ""})

    def set_voice(self, voice):
        self._stream_to_frontend({"event": "STREAMING_SET_VOICE", "data": voice if voice else ""})

    def stream_chunk(self, chunk):
        self._stream_to_frontend({"event": "STREAMING_CHUNK", "data": chunk})
        self._streamed.append(chunk)

    def prepare_stream(self):
        self._message_counter = 0
        self._streamed = []

    def end_stream(self):
        self._stream_to_frontend({"event": "STREAMING_DONE"})

    def _stream_to_frontend(self, message):
        self._message_counter += 1
        message |= {"id": f"{self._message_counter}_{self._client_id}"}
        self.logger.debug("streaming to frontend", message=message, session_id=self.session_id)
        self._connected.wait()
        for topic in self.topics:
            self._client.publish(topic, json.dumps(message))
