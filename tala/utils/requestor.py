import uuid
import json
from threading import Event, Thread

import requests
from requests.exceptions import RequestException, ConnectTimeout
from tala.utils.func import getenv, setup_logger

REQUESTOR_URL = getenv("FUNCTION_ENDPOINT_REQUESTOR", "Define the Requestor function endpoint in the environment.")
CONNECTION_TIMEOUT = 3.05  # see requests documentation
READ_TIMEOUT = 60

DEFAULT_GPT_MODEL = getenv("DEFAULT_GPT_MODEL", "gpt-4o-2024-05-13")

TOP_PRIORITY = 1
HIGH_PRIORITY = 2
MEDIUM_PRIORITY = 10
LOW_PRIORITY = 200

MAX_NUM_CONNECTION_ATTEMPTS = 3

QUOTES = "'\""

requests_session = requests.Session()


class InvalidResponseError(Exception):
    pass


class ConnectionException(Exception):
    pass


class UnexpectedErrorException(Exception):
    pass


def unquote(possibly_quoted_string):
    def quoted(s):
        try:
            return s[0] in QUOTES and s[-1] in QUOTES
        except IndexError:
            return False

    if quoted(possibly_quoted_string):
        return possibly_quoted_string[1:len(possibly_quoted_string) - 1]
    return possibly_quoted_string


def make_request(endpoint, json_request, logger):
    def request(headers):
        logger.info(f"making request to: {endpoint}", body=json_request)
        try:
            attempt_no = 1
            success = False
            response_object = None
            while not success and attempt_no < MAX_NUM_CONNECTION_ATTEMPTS:
                try:
                    response_object = requests_session.post(
                        endpoint, json=json_request, headers=headers, timeout=(CONNECTION_TIMEOUT, READ_TIMEOUT)
                    )
                    response_object.raise_for_status()
                    success = True
                except ConnectTimeout:
                    logger.exception(
                        f"ConnectTimeout during request to {endpoint}. Attempt {attempt_no}/{MAX_NUM_CONNECTION_ATTEMPTS}."
                    )
                    logger.info(
                        f"ConnectTimeout during request to {endpoint}. Attempt {attempt_no}/{MAX_NUM_CONNECTION_ATTEMPTS}"
                    )
                attempt_no += 1
            return response_object
        except RequestException:
            logger.exception("Encountered exception during request")
            raise ConnectionException(f"Could not connect to {endpoint}")

    def decode(response_object):
        try:
            response = response_object.json()
            logger.debug("received response", body=response, endpoint=endpoint)
            return response
        except ValueError:
            logger.exception("Encountered exception when decoding response")
            raise InvalidResponseError(f"Expected a valid JSON response from service but got {response_object}.")

    def validate(response):
        if "error" in response:
            description = response["error"]["description"]
            logger.error("Received error from service", description=description)
            raise UnexpectedErrorException(description)

    headers = {'Content-type': 'application/json'}
    response_object = request(headers)

    response = decode(response_object)
    validate(response)
    return response


class GPTRequest:
    def __init__(
        self,
        logger=None,
        messages=None,
        temperature=0.1,
        max_tokens=50,
        max_retries=0,
        stop=None,
        default_gpt_response="[]",
        use_json=False,
        model=DEFAULT_GPT_MODEL,
        priority=MEDIUM_PRIORITY,
        request_id=None
    ):
        self.logger = logger if logger else setup_logger(__name__)
        self._request_id = request_id if request_id else str(uuid.uuid4())
        self._requestor_arguments = {
            "gpt_request": {
                "messages": messages if messages else [],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "max_retries": max_retries,
                "stop": stop if stop else [],
                "default_gpt_response": default_gpt_response,
                "use_json": use_json,
                "model": model
            },
            "priority": priority,
            "request_id": self._request_id
        }
        self._response = None
        self._done = Event()

    @property
    def response(self):
        self._done.wait()
        return self._response["response_body"]

    @property
    def json_response(self):
        try:
            return json.loads(self.response)
        except json.JSONDecodeError:
            self.logger.exception(
                "decoding response raised JSONDecodeError",
                response_content=self.response,
                gpt_max_tokens=self.max_tokens
            )
        except Exception as e:
            self.logger.info("json decoding response raised Exception", exception=e)

        self.logger.info("Returning default response", default_response=self.default_gpt_response)
        return json.loads(self.default_gpt_response)

    @property
    def text_response(self):
        return unquote(self.response)

    @property
    def default_gpt_response(self):
        return self._requestor_arguments["gpt_request"]["default_gpt_response"]

    @property
    def max_tokens(self):
        return self._requestor_arguments["gpt_request"]["max_tokens"]

    @property
    def messages(self):
        return self._requestor_arguments["gpt_request"]["messages"]

    @property
    def system_message(self):
        return self._requestor_arguments["gpt_request"]["messages"][0]

    def make(self):
        def do_request():
            self.logger.info("make request", request_id=self._request_id)
            try:
                self._response = make_request(REQUESTOR_URL, self._requestor_arguments, self.logger)
                self.logger.info("received response", request_id=self._request_id, response=self._response)
            except Exception:
                self._response = {}
                self.logger.exception()
            self._done.set()

        self.logger.info("Start request thread", request_id=self._request_id)
        Thread(target=do_request, daemon=True).start()

    def add_system_message(self, message):
        self._add_message("system", message)

    def _add_message(self, role, message):
        self._requestor_arguments["gpt_request"]["messages"].append({"role": role, "content": message})

    def add_messages(self, messages):
        self._requestor_arguments["gpt_request"]["messages"].extend(messages)

    def add_user_message(self, message):
        self._add_message("user", message)

    def add_assistant_message(self, message):
        self._add_message("assistant", message)

    def update_with_last_assistant_and_next_user_message(self, user_message):
        self.add_assistant_message(self.text_response)
        self.add_user_message(user_message)
        self._done.clear()
        self._response = None
