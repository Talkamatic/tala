from datetime import datetime
import json
import threading

import requests
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient

from tala.utils import sse_client
from tala.utils.func import getenv, setup_logger

USR_TURN_METADATA = "USR_TURN_METADATA"
SYS_TURN_METADATA = "SYS_TURN_METADATA"


class DcrLogSender:
    def __init__(
        self,
        logger,
        dcr_client=None,
        dcr_endpoint=None,
        dcr_rule_id=None,
        dcr_stream_name=None,
    ):
        self._logger = logger
        self._dcr_endpoint = (
            dcr_endpoint if dcr_endpoint is not None else getenv("AZURE_DCR_CUSTOMER_LOG_ENDPOINT", default="")
        )
        self._dcr_rule_id = (
            dcr_rule_id if dcr_rule_id is not None else getenv("AZURE_DCR_CUSTOMER_LOG_RULE_ID", default="")
        )
        self._dcr_stream_name = (
            dcr_stream_name
            if dcr_stream_name is not None else getenv("AZURE_DCR_CUSTOMER_LOG_STREAM_NAME", default="")
        )
        self._dcr_endpoint = self._dcr_endpoint or ""
        self._dcr_rule_id = self._dcr_rule_id or ""
        self._dcr_stream_name = self._dcr_stream_name or ""
        if dcr_client is not None:
            self._dcr_client = dcr_client
        else:
            self._setup_data_collection_rule_client()

    def _setup_data_collection_rule_client(self):
        credential = DefaultAzureCredential()
        endpoint = str(self._dcr_endpoint or "")
        self._dcr_client = LogsIngestionClient(
            endpoint=endpoint,
            credential=credential,
            logging_enable=True,
        )

    def send_log_to_data_collection_rule(self, log_body):
        try:
            rule_id = str(self._dcr_rule_id or "")
            stream_name = str(self._dcr_stream_name or "")
            self._dcr_client.upload(
                rule_id=rule_id,
                stream_name=stream_name,
                logs=[log_body],
            )
        except HttpResponseError:
            pass
        except ServiceRequestError:
            pass


class CustomerStreamLogger(threading.Thread):
    def __init__(
        self,
        session_id,
        offer_id,
        offer_name,
        user_name,
        device_id,
        logger=None,
        sse_endpoint=None,
        dcr_client=None,
    ):
        super().__init__(daemon=True)
        self._logger = logger or setup_logger("customer-stream-logger")
        self._session_id = session_id
        self._offer_id = offer_id
        self._offer_name = offer_name
        self._user_name = user_name
        self._device_id = device_id
        if sse_endpoint:
            self._sse_endpoint = sse_endpoint
        else:
            self._sse_endpoint = getenv("SSE_BROKER_ENDPOINT_HTTPS")
        self._dcr_logger = DcrLogSender(self._logger, dcr_client=dcr_client)
        self._system_chunks = []
        self._sys_metadata = {}
        self._user_metadata = {}
        self._current_event = None
        self._stopped = threading.Event()

    def stop(self):
        self._stopped.set()

    def run(self):
        url = f"{self._sse_endpoint}/{self._session_id}"
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if self._stopped.is_set():
                        break
                    if not line:
                        continue
                    decoded_line = line.decode("utf-8")
                    self._process_line(decoded_line)
        except requests.RequestException:
            self._logger.exception(
                "customer stream logger failed to read stream",
                session_id=self._session_id,
            )
        self._stopped.set()
        self._logger.info("customer stream logger stopped", session_id=self._session_id)

    def _process_line(self, line):
        if line.startswith("event: "):
            event = line[len("event: "):]
            if event == sse_client.STREAMING_DONE:
                self._handle_streaming_done()
                return
            self._current_event = event
            return

        if line.startswith("data: ") and self._current_event:
            data = line[len("data: "):]
            self._handle_event(self._current_event, data)
            self._current_event = None

    def _handle_event(self, event, data):
        if event == sse_client.STREAMING_CHUNK:
            self._system_chunks.append(data)
            return
        if event == USR_TURN_METADATA:
            self._handle_user_metadata(data)
            return
        if event == SYS_TURN_METADATA:
            self._handle_system_metadata(data)
            return
        if event == sse_client.STREAMING_DONE:
            self._handle_streaming_done()

    def _handle_user_metadata(self, data):
        metadata = self._parse_json(data, event=USR_TURN_METADATA)
        if not metadata:
            return
        self._user_metadata = metadata
        log_body = self._build_user_log(metadata)
        if log_body:
            self._logger.info("customer stream user log", body=log_body)
            self._dcr_logger.send_log_to_data_collection_rule(log_body)

    def _handle_system_metadata(self, data):
        metadata = self._parse_json(data, event=SYS_TURN_METADATA)
        if not metadata:
            return
        self._sys_metadata = metadata

    def _handle_streaming_done(self):
        self._stopped.set()
        log_body = self._build_system_log()
        if log_body:
            self._logger.info("customer stream system log", body=log_body)
            self._dcr_logger.send_log_to_data_collection_rule(log_body)

    def _parse_json(self, data, event=None):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            self._logger.info(
                "customer stream logger received invalid json",
                session_id=self._session_id,
                event=event,
                data=data,
            )
            return None

    def _build_user_log(self, metadata):
        ddd_name = metadata.get("ddd_name")
        utterance = metadata.get("user_utterance")
        if not ddd_name or utterance is None:
            return None
        return {
            "device_id": self._device_id,
            "event": "request",
            "grouping_ddd": ddd_name,
            "moves": metadata.get("user_moves", []),
            "offer_id": self._offer_id,
            "offer_name": self._offer_name,
            "selected_interpretation": "",
            "session_id": self._session_id,
            "TimeGenerated": datetime.now().isoformat(),
            "turn": metadata.get("turn_count"),
            "username": self._user_name,
            "utterance": f"U> {utterance}",
        }

    def _build_system_log(self):
        ddd_name = self._sys_metadata.get("ddd_name") or self._user_metadata.get("ddd_name")
        if not ddd_name:
            return None
        utterance = "".join(self._system_chunks).strip()
        return {
            "device_id": self._device_id,
            "event": "response",
            "grouping_ddd": ddd_name,
            "moves": self._sys_metadata.get("system_moves", []),
            "offer_id": self._offer_id,
            "offer_name": self._offer_name,
            "selected_interpretation": self._sys_metadata.get(
                "selected_interpretation",
                "",
            ),
            "session_id": self._session_id,
            "TimeGenerated": datetime.now().isoformat(),
            "turn": self._sys_metadata.get("turn_count") or self._user_metadata.get("turn_count"),
            "username": self._user_name,
            "utterance": f"S> {utterance}",
        }
