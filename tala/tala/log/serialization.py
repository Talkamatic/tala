import pickle
import base64


def serialize(obj):
    return base64.b64encode(pickle.dumps(obj))


def unserialize(obj):
    return pickle.loads(base64.b64decode(obj))
