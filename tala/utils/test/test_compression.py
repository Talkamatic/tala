import pytest

from tala.utils import compression

UNCOMPRESSED_STRING = "kalle"
COMPRESSED_STRING = 'eNrLTszJSQUABiECCg=='

UNCOMPRESSED_JSON = {"name": "kalle"}
COMPRESSED_JSON = "eNqrVspLzE1VslJQyk7MyUlVqgUAMToFhQ=="


class TestStringCompression:
    def test_compress_string_base_case(self):
        self.given_string(UNCOMPRESSED_STRING)
        self.when_compress_string()
        self.then_compressed_string_is(COMPRESSED_STRING)

    def given_string(self, string):
        self._string = string

    def when_compress_string(self):
        self._compressed_string = compression.compress_string(self._string)

    def then_compressed_string_is(self, string):
        assert self._compressed_string == COMPRESSED_STRING

    def test_decompress_compressed_string_base_case(self):
        self.given_compressed_string(COMPRESSED_STRING)
        self.when_decompress_string()
        self.then_decompressed_string_is(UNCOMPRESSED_STRING)

    def given_compressed_string(self, string):
        self._compressed_string = string

    def when_decompress_string(self):
        self._decompressed_string = compression.decompress_string(self._compressed_string)

    def then_decompressed_string_is(self, string):
        assert self._decompressed_string == UNCOMPRESSED_STRING

    @pytest.mark.parametrize("data", [UNCOMPRESSED_STRING, COMPRESSED_STRING])
    def test_ensure_decompress(self, data):
        self.given_data(data)
        self.when_ensure_decompress_string()
        self.then_decompressed_string_is(UNCOMPRESSED_STRING)

    def given_data(self, string):
        self._possibly_compressed_string = string

    def when_ensure_decompress_string(self):
        self._decompressed_string = compression.ensure_decompressed_string(self._possibly_compressed_string)


class TestJSONCompression:
    def test_compress_json_dict_base_case(self):
        self.given_json(UNCOMPRESSED_JSON)
        self.when_compress_json()
        self.then_compressed_json_is(COMPRESSED_JSON)

    def given_json(self, json_dict):
        self._json = json_dict

    def when_compress_json(self):
        self._compressed_json = compression.compress_json(self._json)

    def then_compressed_json_is(self, json_dict):
        assert self._compressed_json == json_dict

    def test_decompress_compressed_json_base_case(self):
        self.given_compressed_json(COMPRESSED_JSON)
        self.when_decompress_json()
        self.then_decompressed_json_is(UNCOMPRESSED_JSON)

    def given_compressed_json(self, json_dict):
        self._compressed_json = json_dict

    def when_decompress_json(self):
        self._decompressed_json = compression.decompress_json(self._compressed_json)

    def then_decompressed_json_is(self, json_dict):
        assert self._decompressed_json == json_dict

    @pytest.mark.parametrize("data", [UNCOMPRESSED_JSON, COMPRESSED_JSON])
    def test_ensure_decompress(self, data):
        self.given_data(data)
        self.when_ensure_decompress_json()
        self.then_decompressed_json_is(UNCOMPRESSED_JSON)

    def given_data(self, json_dict):
        self._possibly_compressed_json = json_dict

    def when_ensure_decompress_json(self):
        self._decompressed_json = compression.ensure_decompressed_json(self._possibly_compressed_json)
