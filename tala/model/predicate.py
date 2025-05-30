from tala.model.semantic_object import OntologySpecificSemanticObject
from tala.model.sort import Sort
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin


class Predicate(OntologySpecificSemanticObject, AsSemanticExpressionMixin):
    @classmethod
    def create_from_json_api_data(cls, predicate_entry, included):
        sort_entry = included.get_object_from_relationship(predicate_entry["relationships"]["sort"]["data"])
        sort = Sort.create_from_json_api_data(sort_entry, included)
        ontology_name = predicate_entry["attributes"]["ontology_name"]
        name = predicate_entry["attributes"]["name"]
        feature_of_name = predicate_entry["attributes"]["feature_of_name"]
        multiple_instances = predicate_entry["attributes"]["_multiple_instances"]
        return cls(ontology_name, name, sort, feature_of_name, multiple_instances)

    def __init__(self, ontology_name, name, sort, feature_of_name=None, multiple_instances=False):
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self.name = name
        self.sort = sort
        self.feature_of_name = feature_of_name
        self._multiple_instances = multiple_instances

    def get_name(self):
        return self.name

    def get_feature_of_name(self):
        return self.feature_of_name

    def is_feature_of(self, other):
        return self.feature_of_name == other.get_name()

    def allows_multiple_instances(self):
        return self._multiple_instances

    def is_predicate(self):
        return True

    @property
    def json_api_id(self):
        return f"{self.ontology_name}:{self.name}"

    @property
    def json_api_attributes(self):
        return ["ontology_name", "name", "feature_of_name", "_multiple_instances"]

    @property
    def json_api_relationships(self):
        return ["sort"]

    def __eq__(self, other):
        try:
            return other.get_name() == self.get_name() \
                and other.sort == self.sort \
                and other.get_feature_of_name() == self.get_feature_of_name() \
                and other.allows_multiple_instances() == self.allows_multiple_instances()
        except AttributeError:
            return False

    def __lt__(self, other):
        return self.name < other.name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.name, self.sort, self.feature_of_name, self._multiple_instances))

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return "%s%s" % (
            self.__class__.__name__, (self.name, self.sort, self.feature_of_name, self._multiple_instances)
        )
