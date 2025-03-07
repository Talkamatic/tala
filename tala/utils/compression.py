import base64
import codecs
import json
import zlib
import binascii


def decompress_json(data):
    """
    decompress data, assuming that it was compressed with the compression function in this module - dumped
    into a json string, as bytes, zipped and base64-encoded.
    """
    return json.loads(decompress_string(data))


def ensure_decompressed_json(data):
    try:
        return decompress_json(data)
    except (AttributeError, zlib.error, binascii.Error, TypeError):
        return data


def compress_json(element_to_compress):
    """
    compress data: dump as JSON, create bytes object, zip it and encode as base64.

    """
    return compress_string(json.dumps(element_to_compress), 'utf-8')


def compress(element):
    return compress_json(element)


def decompress(data):
    return decompress_json(data)


def ensure_decompressed(data):
    return ensure_decompressed_json(data)


def decompress_string(data):
    """
    decompress data, assuming that it was compressed with the compression function in this module -
    string as bytes, zipped and base64-encoded.
    """
    decoded = codecs.decode(data.encode(), "base64")
    decompressed_bytes = zlib.decompress(decoded)
    return decompressed_bytes.decode('utf-8')


def ensure_decompressed_string(data):
    try:
        return decompress_string(data)
    except (AttributeError, zlib.error, binascii.Error, TypeError):
        return data


def compress_string(string_to_compress):
    """
    compress data: create bytes object, zip it and encode as base64.

    """
    bytes_to_compress = bytes(string_to_compress, 'utf-8')
    zipped = zlib.compress(bytes_to_compress, level=9)
    return base64.b64encode(zipped).decode()
