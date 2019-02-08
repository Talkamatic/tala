def can_convert_to_json(object_):
    if hasattr(object_, "can_convert_to_json"):
        return object_.can_convert_to_json
    return False


def convert_to_json(object_):
    if object_ is None:
        return None
    if object_ is True or object_ is False:
        return object_
    if isinstance(object_, list):
        return [convert_to_json(element) for element in object_]
    if isinstance(object_, set):
        return {
            "set": [convert_to_json(element) for element in object_]
        }
    if isinstance(object_, dict):
        return {str(key): convert_to_json(value) for key, value in object_.items()}
    if can_convert_to_json(object_):
        return object_.as_json()
    return unicode(object_)


class JSONLoggable(object):
    @property
    def can_convert_to_json(self):
        return True

    def as_json(self):
        dict_ = {}
        for key, value in self.__dict__.items():
            dict_[key] = convert_to_json(value)
        return dict_
