from tala.model.proposition import ImplicationProposition, PredicateProposition
from tala.model.question import Question
from tala.utils.as_json import AsJSONMixin
from tala.utils.json_api import JSONAPIObject, JSONAPIMixin, get_attribute


class QueryBase(AsJSONMixin, JSONAPIMixin):
    def __init__(self, query):
        self._query = query

    @property
    def query(self):
        return self._query

    def __eq__(self, other):
        try:
            return self.__dict__ == other.__dict__
        except AttributeError:
            return False

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class ImplicationQuery(QueryBase):
    def __init__(self, query, implications):
        super().__init__(query)
        self._implications = implications

    @property
    def implications(self):
        return self._implications

    def as_json_api_dict(self):
        implication_object = JSONAPIObject("implication")
        implication_object.add_relationship("query", self.query.as_json_api_dict())
        for implication in self.implications:
            implication_object.append_relationship("content", implication.as_json_api_dict())
        return implication_object.as_dict

    @classmethod
    def create_from_json_api_data(cls, data, included):
        query_data = included.get_data_for_relationship("query", data)
        query = Question.create_from_json_api_data(query_data, included)

        implications = []
        for item in data["relationships"]["content"]["data"]:
            implication_object = included.get_object_from_relationship(item)
            implications.append(ImplicationProposition.create_from_json_api_data(implication_object, included))

        return cls(query, implications)


class EnumerationQuery(QueryBase):
    def __init__(self, query, enumeration_type, propositions):
        super().__init__(query)
        self._enumeration_type = enumeration_type
        self._propositions = propositions

    @property
    def enumeration_type(self):
        return self._enumeration_type

    @property
    def propositions(self):
        return self._propositions

    def as_json_api_dict(self):
        enumerator_object = JSONAPIObject("enumeration_query")
        enumerator_object.add_relationship("query", self.query.as_json_api_dict())
        enumerator_object.add_attribute("enumeration_type", self.enumeration_type)
        for proposition in self.propositions:
            enumerator_object.append_relationship("content", proposition.as_json_api_dict())
        return enumerator_object.as_dict

    @classmethod
    def create_from_json_api_data(cls, data, included):
        query_json = included.get_data_for_relationship("query", data)
        query = Question.create_from_json_api_data(query_json, included)

        enumeration_type = get_attribute("enumeration_type", data)
        propositions = []
        for item in data["relationships"]["content"]["data"]:
            prop_object = included.get_object_from_relationship(item)
            propositions.append(PredicateProposition.create_from_json_api_data(prop_object, included))

        return cls(query, enumeration_type, propositions)


class IteratorQuery(QueryBase):
    def __init__(self, query, limit, enumeration_type, propositions):
        super().__init__(query)
        self._limit = limit
        self._enumeration_type = enumeration_type
        self._propositions = propositions

    @property
    def limit(self):
        return self._limit

    @property
    def enumeration_type(self):
        return self._enumeration_type

    @property
    def propositions(self):
        return self._propositions

    def as_json_api_dict(self):
        iterator_object = JSONAPIObject("iterator")
        try:
            iterator_object.add_relationship("query", self.query.as_json_api_dict())
        except AttributeError:
            iterator_object.add_attribute("query", self.query)
        iterator_object.add_attribute("limit", self.limit)
        iterator_object.add_attribute("enumeration_type", self.enumeration_type)
        for proposition in self.propositions:
            iterator_object.append_relationship("content", proposition.as_json_api_dict())
        return iterator_object.as_dict

    @classmethod
    def create_from_json_api_data(cls, data, included):
        try:
            query_json = included.get_data_for_relationship("query", data)
            query = Question.create_from_json_api_data(query_json, included)
        except (AttributeError, TypeError, KeyError):
            query = get_attribute("query", data)
        limit = get_attribute("limit", data)
        enumeration_type = get_attribute("enumeration_type", data)
        propositions = []
        for item in data["relationships"]["content"]["data"]:
            prop_object = included.get_object_from_relationship(item)
            propositions.append(PredicateProposition.create_from_json_api_data(prop_object, included))
        return cls(query, limit, enumeration_type, propositions)


def create_query_from_json_api_data(query_data, included):
    if query_data["type"] == "implication":
        return ImplicationQuery.create_from_json_api_data(query_data, included)
    if query_data["type"] == "enumeration_query":
        return EnumerationQuery.create_from_json_api_data(query_data, included)
    if query_data["type"] == "iterator":
        return IteratorQuery.create_from_json_api_data(query_data, included)
    raise Exception(f"Type of query is not recognized: {query_data['type']}")


def create_query_from_dict(query_data):
    if "implications" in query_data:
        return ImplicationQuery(query_data["query"], query_data["implications"])
    if "limit" in query_data:
        enumeration_type = _get_enumeration_type(query_data)
        return IteratorQuery(
            query_data["query"],
            query_data["limit"],
            enumeration_type,
            query_data[enumeration_type],
        )
    enumeration_type = _get_enumeration_type(query_data)
    return EnumerationQuery(query_data["query"], enumeration_type, query_data[enumeration_type])


def _get_enumeration_type(query_data):
    for type_ in ["for_enumeration", "for_random_enumeration", "for_random_selection"]:
        if type_ in query_data:
            return type_
    raise Exception("Enumeration type is not recognized")
