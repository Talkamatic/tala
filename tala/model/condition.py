from tala.model.semantic_object import SemanticObject
from tala.model.predicate import Predicate
from tala.model.question import Question
from tala.utils import json_api as json_api_module

HAS_VALUE = "HasValue"
HAS_SHARED_VALUE = "HasSharedValue"
HAS_PRIVATE_VALUE = "HasPrivateValue"
IN_SHARED_COMMITMENTS = "InSharedCommitments"
IN_PRIVATE_BELIEFS = "InPrivateBeliefs"
IN_BELIEFS_OR_COMMITMENTS = "InBeliefsOrCommitments"
QUERY_HAS_MORE_ITEMS = "QueryHasMoreItems"
AND_CONDITION = "AndCondition"
OR_CONDITION = "OrCondition"
NOT_CONDITION = "NotCondition"

SEMANTIC_OBJECT_TYPE = "condition"


def create_condition(type_, parameter):
    if type_ == HAS_SHARED_VALUE:
        return HasSharedValue(parameter)
    if type_ == HAS_PRIVATE_VALUE:
        return HasPrivateValue(parameter)
    if type_ == IN_SHARED_COMMITMENTS:
        return InSharedCommitments(parameter)
    if type_ == IN_PRIVATE_BELIEFS:
        return InPrivateBeliefs(parameter)
    if type_ == IN_BELIEFS_OR_COMMITMENTS:
        return InBeliefsOrCommitments(parameter)
    if type_ == QUERY_HAS_MORE_ITEMS:
        return QueryHasMoreItems(parameter)
    if type_ == HAS_VALUE:
        return HasValue(parameter)
    if type_ == AND_CONDITION:
        return AndCondition(parameter)
    if type_ == OR_CONDITION:
        return OrCondition(parameter)
    if type_ == NOT_CONDITION:
        return NotCondition(parameter)


def create_from_json_api_data(condition_data, included):
    class_name = condition_data["attributes"]["condition_type"]
    target_cls = globals().get(class_name)
    return target_cls.create_from_json_api_data(condition_data, included)


class Condition(SemanticObject):
    def __init__(self, type_):
        self._type = type_

    @property
    def condition_type(self):
        return self._type

    def is_has_value_condition(self):
        return self.condition_type in [HAS_VALUE, HAS_SHARED_VALUE, HAS_PRIVATE_VALUE]

    def is_true_given_proposition_set(self, _):
        return False

    def __eq__(self, other):
        try:
            return self.condition_type == other.condition_type
        except AttributeError:
            return False

    def __repr__(self):
        return "Condition()"

    def as_dict(self):
        result = {"semantic_object_type": SEMANTIC_OBJECT_TYPE, "type": self.condition_type}
        return super().as_dict() | result


class HasValue(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        predicate_entry = included.get_object_from_relationship(data["relationships"]["predicate"]["data"])
        predicate = Predicate.create_from_json_api_data(predicate_entry, included)
        return cls(predicate)

    def __init__(self, predicate, type_=HAS_VALUE):
        super().__init__(type_)
        self._predicate = predicate

    @property
    def predicate(self):
        return self._predicate

    def is_true_given_proposition_set(self, proposition_set):
        for proposition in proposition_set:
            try:
                if proposition.predicate == self.predicate:
                    return True
            except AttributeError:
                pass
        return False

    def __eq__(self, other):
        try:
            equality = super().__eq__(other) and self.predicate == other.predicate
            return equality
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.predicate)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{self.predicate}"

    @property
    def json_api_attributes(self):
        return ["condition_type"]

    @property
    def json_api_relationships(self):
        return ["predicate"]


class HasSharedValue(HasValue):
    def __init__(self, predicate):
        super().__init__(predicate, HAS_SHARED_VALUE)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.shared.com)


class HasPrivateValue(HasValue):
    def __init__(self, predicate):
        super().__init__(predicate, HAS_PRIVATE_VALUE)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel)


class InPropositionSetCondition(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        proposition_entry = included.get_object_from_relationship(data["relationships"]["proposition"]["data"])
        proposition = json_api_module.create_from_json_api_data(proposition_entry, included)
        return cls(proposition)

    def __init__(self, proposition, type_):
        super().__init__(type_)
        self._proposition = proposition

    @property
    def proposition(self):
        return self._proposition

    def is_true_given_proposition_set(self, proposition_set):
        return self.proposition in proposition_set

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.proposition == other.proposition
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.proposition)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{self.proposition}"

    @property
    def json_api_attributes(self):
        return ["condition_type"]

    @property
    def json_api_relationships(self):
        return ["proposition"]


class InSharedCommitments(InPropositionSetCondition):
    def __init__(self, proposition):
        super().__init__(proposition, IN_SHARED_COMMITMENTS)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.shared.com)


class InPrivateBeliefs(InPropositionSetCondition):
    def __init__(self, proposition):
        super().__init__(proposition, IN_PRIVATE_BELIEFS)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel)


class InBeliefsOrCommitments(InPropositionSetCondition):
    def __init__(self, proposition):
        super().__init__(proposition, IN_BELIEFS_OR_COMMITMENTS)

    def is_true_given_tis(self, tis):
        return super().is_true_given_proposition_set(tis.private.bel) \
            or super().is_true_given_proposition_set(tis.shared.com)


def _evaluate_condition_for_tis(condition_obj, tis):
    try:
        return condition_obj.is_true_given_tis(tis)
    except AttributeError:
        return condition_obj.is_true_given_proposition_set(tis.shared.com) \
            or condition_obj.is_true_given_proposition_set(tis.private.bel)


def _parse_conditions_relationship(conditions_data, included):
    if conditions_data is None:
        return []
    try:
        conditions_data[0]
    except (TypeError, KeyError, IndexError):
        parsed = json_api_module.create_from_json_api_data(conditions_data, included)
        if parsed is None:
            return []
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    return [create_from_json_api_data(item, included) for item in conditions_data]


class AndCondition(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        conditions_data = included.get_data_for_relationship("conditions", data)
        conditions = _parse_conditions_relationship(conditions_data, included)
        return cls(conditions)

    def __init__(self, conditions):
        super().__init__(AND_CONDITION)
        self._conditions = list(conditions)

    @property
    def conditions(self):
        return self._conditions

    def is_true_given_tis(self, tis):
        return all(_evaluate_condition_for_tis(condition_obj, tis) for condition_obj in self.conditions)

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.conditions == other.conditions
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.conditions)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{id(self)}"

    @property
    def json_api_attributes(self):
        return ["condition_type"]

    @property
    def json_api_relationships(self):
        return ["conditions"]


class OrCondition(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        conditions_data = included.get_data_for_relationship("conditions", data)
        conditions = _parse_conditions_relationship(conditions_data, included)
        return cls(conditions)

    def __init__(self, conditions):
        super().__init__(OR_CONDITION)
        self._conditions = list(conditions)

    @property
    def conditions(self):
        return self._conditions

    def is_true_given_tis(self, tis):
        return any(_evaluate_condition_for_tis(condition_obj, tis) for condition_obj in self.conditions)

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.conditions == other.conditions
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.conditions)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{id(self)}"

    @property
    def json_api_attributes(self):
        return ["condition_type"]

    @property
    def json_api_relationships(self):
        return ["conditions"]


class NotCondition(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        condition_data = included.get_data_for_relationship("condition", data)
        condition_obj = json_api_module.create_from_json_api_data(condition_data, included)
        if isinstance(condition_obj, list):
            condition_obj = condition_obj[0] if condition_obj else None
        return cls(condition_obj)

    def __init__(self, condition_obj):
        super().__init__(NOT_CONDITION)
        self._condition = condition_obj

    @property
    def condition(self):
        return self._condition

    def is_true_given_tis(self, tis):
        return not _evaluate_condition_for_tis(self.condition, tis)

    def __eq__(self, other):
        try:
            return super().__eq__(other) and self.condition == other.condition
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.condition)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{id(self)}"

    @property
    def json_api_attributes(self):
        return ["condition_type"]

    @property
    def json_api_relationships(self):
        return ["condition"]


class QueryHasMoreItems(Condition):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        try:
            query = data["attributes"]["query"]
        except KeyError:
            query_entry = included.get_object_from_relationship(data["relationships"]["query"]["data"])
            query = Question.create_from_json_api_data(query_entry, included)
        return cls(query)

    def __init__(self, query, type_=QUERY_HAS_MORE_ITEMS):
        super().__init__(type_)
        self._query = query

    @property
    def query(self):
        return self._query

    def is_true_given_tis(self, tis):
        no_more_elements = tis.iterator_has_no_more_elements(self.query)
        reached_limit = tis.iterator_has_reached_limit(self.query)
        result = not (no_more_elements or reached_limit)
        return result

    def __eq__(self, other):
        try:
            equality = super().__eq__(other) and self.query == other.query
            return equality
        except AttributeError:
            return False

    def __repr__(self):
        return "{}({})".format(self.condition_type, self.query)

    @property
    def json_api_id(self):
        return f"{self.condition_type}:{self.query}"

    @property
    def json_api_attributes(self):
        if str(self.query) == self.query:
            return ["condition_type", "query"]
        else:
            return ["condition_type"]

    @property
    def json_api_relationships(self):
        if str(self.query) == self.query:
            return []
        else:
            return ["query"]
