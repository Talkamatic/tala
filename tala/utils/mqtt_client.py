import threading
import warnings
import json

import paho.mqtt.client as mqtt

from tala.utils import sse_client


class MQTTClientException(BaseException):
    pass


class MQTTClient(sse_client.AbstractSSEClient):
    def __init__(self, client_id_base, logger, endpoint, port=None):
        super().__init__(client_id_base, logger, endpoint, port)

        def on_connect(client, userdata, connect_flags, reason_code, properties):
            self.logger.info('CONNACK received', reason_code=reason_code, properties=properties)
            self._connected.set()

        self._connected = threading.Event()

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
            reconnect_on_failure=True,
            clean_session=True,
            client_id=self._client_id
        )
        self._client.on_connect = on_connect
        self._client.tls_set()

    def start(self):
        self.logger.info("connecting to", endpoint=self._endpoint, port=self._port)
        self._client.connect(self._endpoint, self._port)
        self._client.loop_start()

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


class ChunkJoiner(sse_client.ChunkJoiner):
    pass


class StreamIterator(sse_client.StreamIterator):
    pass
