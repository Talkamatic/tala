from collections import namedtuple

PROTOCOL_VERSION = "1.0"


class Session(namedtuple("Session", ["session_id"])):
    pass


class Context(namedtuple("Context", ["active_ddd", "facts", "invocation_id"])):
    pass
