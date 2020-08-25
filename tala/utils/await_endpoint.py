from datetime import datetime, timedelta
import time

import requests
from requests.exceptions import ConnectionError, ConnectTimeout


def await_endpoint(url, timeout=None):
    def connect():
        response = requests.get(url, timeout=timeout / 10)
        response.raise_for_status()

    def is_responding():
        try:
            connect()
            return True
        except (ConnectionError, ConnectTimeout):
            return False

    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout)
    while datetime.now() < end_time:
        if is_responding():
            return
        time.sleep(0.1)
        continue
    connect()
