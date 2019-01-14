class UnicodifyException(Exception):
    pass


def unicodify(object):
    if isinstance(object, (str, unicode)):
        return u"'%s'" % unicode(object)
    if isinstance(object, list):
        return _sequence_string(object)
    if isinstance(object, dict):
        return _dict_string(object)
    if isinstance(object, tuple):
        return _tuple_string(object)
    else:
        try:
            return unicode(object)
        except UnicodeDecodeError as exception:
            raise UnicodifyException("failed to unicodify object of class %s (%s)" % (object.__class__, exception))


def _sequence_string(sequence):
    return u"[%s]" % u", ".join([unicodify(item) for item in sequence])


def _dict_string(dict_):
    formatted_key_value_pairs = [(unicodify(key), unicodify(value)) for key, value in dict_.iteritems()]
    formatted_content = [u"%s: %s" % pair for pair in formatted_key_value_pairs]
    return u"{%s}" % u", ".join(formatted_content)


def _tuple_string(_tuple):
    return u"(%s)" % u", ".join([unicodify(item) for item in _tuple])
