from copy import copy

from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


def json_semantic_expression_of(object_):
    return {"semantic_expression": object_.as_semantic_expression()}


def convert_to_json(object_, verbose=True):
    if object_ is None:
        return None
    if object_ is True or object_ is False:
        return object_
    if isinstance(object_, list):
        return [convert_to_json(element, verbose) for element in object_]
    if isinstance(object_, set):
        return {"set": [convert_to_json(element, verbose) for element in object_]}
    if isinstance(object_, dict):
        return {str(key): convert_to_json(value, verbose) for key, value in list(object_.items())}
    if not verbose and isinstance(object_, AsSemanticExpressionMixin):
        return json_semantic_expression_of(object_)
    if isinstance(object_, AsJSONMixin):
        dict_ = object_.as_dict()
        json = convert_to_json(dict_, verbose)
        if isinstance(object_, AsSemanticExpressionMixin):
            json.update(json_semantic_expression_of(object_))
        return json
    return str(object_)


def convert_to_human_readable_json(object_, _memo=None):
    if object_ is None:
        return None
    if object_ is True or object_ is False:
        return object_

    if _memo is None:
        _memo = {}
    object_id = id(object_)
    if object_id in _memo:
        return _memo[object_id]

    if isinstance(object_, list):
        result = []
        _memo[object_id] = result
        result.extend([convert_to_human_readable_json(element, _memo) for element in object_])
        return result
    if isinstance(object_, set):
        result = {"set": []}
        _memo[object_id] = result
        result["set"].extend([convert_to_human_readable_json(element, _memo) for element in object_])
        return result
    if isinstance(object_, dict):
        if "semantic_expression" in object_:
            result = convert_to_human_readable_json(object_["semantic_expression"], _memo)
            _memo[object_id] = result
            return result
        result = {}
        _memo[object_id] = result
        for key, value in object_.items():
            result[str(key)] = convert_to_human_readable_json(value, _memo)
        return result
    if isinstance(object_, AsSemanticExpressionMixin):
        result = json_semantic_expression_of(object_)
        _memo[object_id] = result
        return result
    if isinstance(object_, AsJSONMixin):
        dict_ = object_.as_dict()
        result = convert_to_human_readable_json(dict_, _memo)
        _memo[object_id] = result
        return result

    result = str(object_)
    _memo[object_id] = result
    return result


class AsJSONMixin(object):
    @property
    def can_convert_to_json(self):
        return True

    def as_json(self):
        return convert_to_json(self, verbose=True)

    def as_compact_json(self):
        return convert_to_json(self, verbose=False)

    def as_dict(self):
        return copy(self.__dict__)

    def as_readable_json(self):
        return convert_to_human_readable_json(self)
