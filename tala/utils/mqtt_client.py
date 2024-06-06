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

    @property
    def streamed(self):
        return self._streamed

    @session_id.setter
    def session_id(self, session_id):
        self._session_id = session_id

    @property
    def topic(self):
        return 'tm/id/' + self.session_id

    def stream_utterance(self, utterance):
        event = {"event": "STREAMING_CHUNK", "data": utterance}
        self._stream_to_frontend(event)
        self._streamed.append(utterance)

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
        self._client.publish(self.topic, json.dumps(message))
