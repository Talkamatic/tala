import base64
import codecs
import json
import zlib
import binascii
import warnings

# Compression


def compress_string(string_to_compress):
    """
    compress data: create bytes object, zip it and encode as base64.

    """
    bytes_to_compress = bytes(string_to_compress, 'utf-8')
    zipped = zlib.compress(bytes_to_compress, level=9)
    return base64.b64encode(zipped).decode()


def compress_json(element_to_compress):
    """
    compress data: dump as JSON, create bytes object, zip it and encode as base64.

    """
    return compress_string(json.dumps(element_to_compress))


def compress(element):
    warnings.warn(
        "tala.utils.compression.compress() is deprecated. Use tala.utils.compression.compress_json() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return compress_json(element)


# String decompression


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


# JSON decompression


def decompress_json(data):
    """
    decompress data, assuming that it was compressed with the compression function in this module - dumped
    into a json string, as bytes, zipped and base64-encoded.
    """
    return json.loads(decompress_string(data))


def decompress(data):
    warnings.warn(
        "tala.utils.compression.decompress() is deprecated. Use tala.utils.compression.decompress_json() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return decompress_json(data)


def ensure_decompressed_json(data):
    try:
        return decompress_json(data)
    except (AttributeError, zlib.error, binascii.Error, TypeError):
        return data


def ensure_decompressed(data):
    warnings.warn(
        "tala.utils.compression.ensure_decompressed() is deprecated. Use tala.utils.compression.ensure_decompressed_json() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return ensure_decompressed_json(data)
