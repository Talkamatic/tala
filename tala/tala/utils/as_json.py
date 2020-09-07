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
