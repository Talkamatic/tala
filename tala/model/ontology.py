import copy
import re
from typing import Iterable, Dict
import warnings

from tala.model.action import Action
from tala.model.error import OntologyError
from tala.model.individual import Individual, NegativeIndividual
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.polarity import Polarity
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition
from tala.model.question import YesNoQuestion, WhQuestion
from tala.model.sort import DomainSort, Sort, BuiltinSortRepository
from tala.utils.as_json import AsJSONMixin
from tala.utils.unique import unique
from tala.utils.json_api import JSONAPIObject, JSONAPIMixin


class IndividualExistsException(Exception):
    pass


class SortDoesNotExistException(Exception):
    pass


class ActionDoesNotExistException(Exception):
    pass


class PredicateDoesNotExistException(Exception):
    pass


class InvalidIndividualName(Exception):
    pass


class AmbiguousNamesException(Exception):
    pass


individual_name_matcher = re.compile(r"^[a-zA-Z0-9_\-\:]{1,}$")
SEMANTIC_OBJECT_TYPE = "ontology"


class DddOntology:
    pass


DEFAULT_ACTIONS = {"top", "up", "how"}


class Ontology(AsJSONMixin, JSONAPIMixin):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        def get_sorts(data, included):
            for sort in data["relationships"]["sorts"]["data"]:
                sort_data = included.get_object_from_relationship(sort)
                yield Sort.create_from_json_api_data(sort_data, included)

        def get_predicates(data, included):
            for predicate in data["relationships"]["predicates"]["data"]:
                predicate_data = included.get_object_from_relationship(predicate)
                yield Predicate.create_from_json_api_data(predicate_data, included)

        def get_individuals(data, included, sorts):
            for individual in data["relationships"]["individuals"]["data"]:
                individual_data = included.get_object_from_relationship(individual)
                individual = Individual.create_from_json_api_data(individual_data, included)
                yield individual.value, individual.sort

        def get_sort(name, sorts):
            for sort in sorts:
                if sort.name == name:
                    return sort

        def get_actions(data, included):
            for action in data["relationships"]["actions"]["data"]:
                action_data = included.get_object_from_relationship(action)
                yield action_data["attributes"]["name"]

        name = data["id"]
        sorts = list(get_sorts(data, included))
        predicates = list(get_predicates(data, included))
        individuals = {individual_name: sort for individual_name, sort in get_individuals(data, included, sorts)}
        actions = list(get_actions(data, included))
        return cls(name, sorts, predicates, individuals, actions)

    def __init__(
        self, name: str, sorts: Iterable[Sort], predicates: Iterable[Predicate], individuals: Dict[str, Sort],
        actions: Iterable[str]
    ):
        super(Ontology, self).__init__()
        self._name = name
        self._sorts = self._set_to_dict(sorts)
        self._predicates = self._set_to_dict(predicates)
        self._individuals = individuals
        self._original_individuals = copy.deepcopy(individuals)
        self._actions = DEFAULT_ACTIONS.union(actions)
        self._add_default_sorts()
        self._add_builtin_sorts_for_predicates()
        self._validate_individuals()
        self._validate_predicates()
        self._check_predicate_action_integrity()

    def as_json_api_dict(self):
        def create_relationship_data_and_include(resource_object):
            data = {"type": resource_object["type"], "id": resource_object["id"]}
            include = resource_object
            return data, include

        d = JSONAPIObject(
            "tala.model.ontology", self._name, {"name": self._name}, {
                "predicates": {
                    "data": []
                },
                "individuals": {
                    "data": []
                },
                "sorts": {
                    "data": []
                },
                "actions": {
                    "data": []
                }
            }, []
        )

        for predicate in self.predicates:
            predicate_data = predicate.as_json_api_dict()
            d.append_relationship("predicates", predicate_data)

        for individual in self.individuals_as_objects:
            individual_data = individual.as_json_api_dict()
            d.append_relationship("individuals", individual_data)

        for action in self.ddd_specific_actions:
            action_data = self.create_action(action).as_json_api_dict()
            d.append_relationship("actions", action_data)

        for sort in self.sorts:
            sort_data = sort.as_json_api_dict()
            d.append_relationship("sorts", sort_data)

        return d.as_dict

    def as_dict(self):
        json = super(Ontology, self).as_dict()
        json["_original_individuals"] = "<skipped>"
        json["semantic_object_type"] = SEMANTIC_OBJECT_TYPE
        json["_sorts"] = [sort.as_dict() for sort in self._sorts.values() if not sort.is_builtin()]
        return json

    def reset(self):
        self._individuals = copy.deepcopy(self._original_individuals)

    @property
    def name(self):
        return self._name

    @property
    def sorts(self):
        return [sort for _name, sort in self._sorts.items() if not sort.is_builtin()]

    @property
    def individuals(self):
        return self._individuals.items()

    @property
    def predicates(self):
        return [predicate for name, predicate in self._predicates.items()]

    @property
    def ddd_specific_actions(self):
        return self._actions.difference(DEFAULT_ACTIONS)

    def _set_to_dict(self, set_):
        dict_ = {}
        for item in set_:
            dict_[item.get_name()] = item
        return dict_

    def _validate_individuals(self):
        for name, sort in list(self._individuals.items()):
            self._validate_individual_name(name)
            self._validate_individual_sort(name, sort)

    def _validate_individual_name(self, name):
        if not individual_name_matcher.match(name):
            raise InvalidIndividualName("invalid individual name %r" % name)

    def _validate_individual_sort(self, name, sort):
        if sort not in list(self._sorts.values()):
            raise OntologyError("individual '%s' has unknown sort '%s' (%s)" % (name, sort.get_name(), self.__dict__))

    def _add_default_sorts(self):
        self._sorts["domain"] = DomainSort()

    def _add_builtin_sorts_for_predicates(self):
        for predicate in list(self._predicates.values()):
            self._add_builtin_sorts_for_predicate(predicate)

    def _add_builtin_sorts_for_predicate(self, predicate):
        sort = predicate.sort
        if sort.is_builtin() and sort not in self._sorts:
            self._sorts[sort.get_name()] = sort

    def _validate_predicates(self):
        for predicate in list(self._predicates.values()):
            if predicate.sort not in list(self._sorts.values()):
                raise OntologyError(
                    "predicate '%s' has unknown sort '%s' (sorts=%s)" %
                    (predicate.get_name(), predicate.sort, self._sorts)
                )

        for name in self._predicates.keys():
            if name in self._sorts.keys():
                raise AmbiguousNamesException(
                    f"Expected predicate and sort names to be unique but there is both a predicate and sort named "
                    f"'{name}' in ontology '{self.name}'"
                )

    def _check_predicate_action_integrity(self):
        for action in self._actions:
            if action in self._predicates:
                raise AmbiguousNamesException(
                    "Action '%s' is also a predicate name in %s ontology." % (action, self.name)
                )

    def get_sorts(self):
        return self._sorts

    def get_predicates(self):
        return self._predicates

    def get_actions(self):
        return self._actions

    @property
    def individuals_as_objects(self):
        return [Individual(self.name, value, sort) for value, sort in self._individuals.items()]

    def get_individuals(self):
        return self._individuals

    def get_individuals_of_sort(self, expected_sort):
        return [individual for individual, sort in list(self._individuals.items()) if sort.get_name() == expected_sort]

    def add_individual(self, name, sort_as_string):
        if name in list(self._individuals.keys()):
            raise IndividualExistsException("invididual %r already exists" % name)
        self._validate_name_and_add_individual(name, sort_as_string)

    def add_predicate(self, name, sort_as_string):
        if name in list(self._predicates.keys()):
            raise OntologyError(f"predicate '{name}' already exists")
        if self.has_sort(sort_as_string):
            sort = self.get_sort(sort_as_string)
        else:
            sort = BuiltinSortRepository.get_sort(sort_as_string)
        self._predicates[name] = Predicate(self.name, name, sort)

    def _validate_name_and_add_individual(self, name, sort_as_string):
        self._validate_individual_name(name)
        self._individuals[name] = self.get_sort(sort_as_string)

    def ensure_individual_exists(self, name, sort_as_string):
        if name not in list(self._individuals.keys()):
            self._validate_name_and_add_individual(name, sort_as_string)

    def get_name(self):
        return self.name

    def __str__(self):
        return self.name

    def get_sort(self, name):
        if not self.has_sort(name):
            raise SortDoesNotExistException("unknown sort '%s' in %s" % (name, self))
        else:
            return self._sorts[name]

    def get_predicate(self, name):
        try:
            return self._predicates[name]
        except KeyError:
            template = f'<predicate name="{name}" sort=" "/>'
            raise OntologyError(
                f"The predicate '{name}' is not known in ontology '{self}'. Known predicates: {[key for key in self._predicates.keys()]}. Missing predicate definition:\n  {template}"
            )

    def has_predicate(self, name):
        return name in list(self._predicates.keys())

    def has_sort(self, name):
        return name in list(self._sorts.keys())

    def is_predicate(self, object_):
        return object_ in list(self._predicates.values())

    def isPredicate(self, object_):
        warnings.warn(
            "Ontology.isPredicate() is deprecated. Use Ontology.is_predicate() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.is_predicate(object_)

    def individual_sort(self, value):
        def sort_of(value):
            if self._individual_is_of_enumerated_sort(value):
                return self._get_enumerated_individual_sort(value)
            return Sort.from_value(value)

        def names_of(sorts):
            return [sort.name for sort in sorts]

        sort = sort_of(value)
        if not self.predicates_contain_sort(sort.name):
            predicate_sorts = unique(names_of(self.predicate_sorts))
            raise OntologyError(
                "Expected one of the predicate sorts {} in ontology '{}', but got value '{}' of sort '{}'".format(
                    predicate_sorts, self.name, value, sort.name
                )
            )
        return sort

    def _individual_is_of_enumerated_sort(self, value):
        return value in self._individuals

    def _get_enumerated_individual_sort(self, value):
        try:
            return self._individuals[value]
        except KeyError:
            raise OntologyError("failed to get sort of unknown individual: " + str(value))

    def predicates_contain_sort(self, name):
        return name in [sort.get_name() for sort in self.predicate_sorts]

    @property
    def predicate_sorts(self):
        return unique(predicate.sort for predicate in sorted(self._predicates.values()))

    def is_action(self, value):
        return value in self._actions

    def create_lambda_abstracted_predicate_proposition(self, predicate):
        if not self.is_predicate(predicate):
            raise OntologyError("predicate %s is not valid in ontology %s" % (str(predicate), self.name))
        return LambdaAbstractedPredicateProposition(predicate, self.name)

    def create_action(self, action):
        if action not in self._actions:
            raise OntologyError("Expected one of %s but got %r" % (self._actions, action))
        return Action(action, self.name)

    def create_individual(self, value, sort=None):
        if sort is None:
            sort = self.individual_sort(value)

        value = self._normalize_and_assert_valid_individual_value(value, sort)
        return Individual(self.name, value, sort)

    def _normalize_and_assert_valid_individual_value(self, value, sort):
        if sort.is_dynamic():
            self._assume_value_of_dynamic_sort_is_valid()
            return value
        else:
            return self._normalize_and_assert_valid_individual_value_of_non_dynamic_sort(value, sort)

    def _assume_value_of_dynamic_sort_is_valid(self):
        pass

    def _normalize_and_assert_valid_individual_value_of_non_dynamic_sort(self, value, sort):
        if sort.is_builtin():
            return sort.normalize_value(value)
        else:
            self._assert_valid_individual_value_of_non_dynamic_custom_sort(value)
            return str(value)

    def _assert_valid_individual_value_of_non_dynamic_custom_sort(self, value):
        try:
            self.individual_sort(value)
        except OntologyError as error:
            raise OntologyError("failed to create individual with unknown value: " + str(error))

    def create_negative_individual(self, value):
        try:
            sort = self.individual_sort(value)
        except OntologyError:
            raise OntologyError("failed to create negative individual with unknown value: %r" % value)
        return NegativeIndividual(self.name, value, sort)

    def create_yes_no_question(self, predicate_name, individual_value):
        predicate = self.get_predicate(predicate_name)
        individual = self.create_individual(individual_value)
        proposition = self.create_predicate_proposition(predicate, individual)
        return YesNoQuestion(proposition)

    def create_wh_question(self, predicate_name):
        predicate = self.get_predicate(predicate_name)
        lambda_abstracted_prop = self.create_lambda_abstracted_predicate_proposition(predicate)
        return WhQuestion(lambda_abstracted_prop)

    def create_predicate_proposition(self, predicate, individual, polarity=Polarity.POS):
        proposition = PredicateProposition(predicate, individual, polarity)
        return proposition
