class UnicodifyException(Exception):
    pass


def unicodify(object):
    if isinstance(object, str):
        return "'%s'" % str(object)
    if isinstance(object, list):
        return _sequence_string(object)
    if isinstance(object, dict):
        return _dict_string(object)
    if isinstance(object, tuple):
        return _tuple_string(object)
    else:
        try:
            return str(object)
        except UnicodeDecodeError as exception:
            raise UnicodifyException("failed to unicodify object of class %s (%s)" % (object.__class__, exception))


def _sequence_string(sequence):
    return "[%s]" % ", ".join([unicodify(item) for item in sequence])


def _dict_string(dict_):
    formatted_key_value_pairs = [(unicodify(key), unicodify(value)) for key, value in list(dict_.items())]
    formatted_content = ["%s: %s" % pair for pair in formatted_key_value_pairs]
    return "{%s}" % ", ".join(formatted_content)


def _tuple_string(_tuple):
    return "(%s)" % ", ".join([unicodify(item) for item in _tuple])
