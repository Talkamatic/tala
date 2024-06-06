import base64
import codecs
import json
import zlib


def decompress(data):
    """
    decompress data, assuming that it was compressed with the compression function in this module - dumped
    into a json string, as bytes, zipped and base64-encoded.
    """
    decoded = codecs.decode(data.encode(), "base64")
    decompressed_bytes = zlib.decompress(decoded)
    json_str = decompressed_bytes.decode('utf-8')
    return json.loads(json_str)


def ensure_decompressed(data):
    try:
        return decompress(data)
    except AttributeError:
        return data


def compress(element_to_compress):
    """
    compress data: dump as JSON, create bytes object, zip it and encode as base64.

    """
    bytes_to_compress = bytes(json.dumps(element_to_compress), 'utf-8')
    zipped = zlib.compress(bytes_to_compress, level=9)
    return base64.b64encode(zipped).decode()
