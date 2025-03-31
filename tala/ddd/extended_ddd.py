from tala.utils.as_json import AsJSONMixin
from tala.utils.json_api import JSONAPIMixin


class ExtendedDDD(AsJSONMixin, JSONAPIMixin):
    """ This is in practice a DDD with the addition of a parameter retriever and a parser """
    def __init__(self, ddd, parameter_retriever, parser, path=None):
        super(ExtendedDDD, self).__init__()
        self._ddd = ddd
        self._parameter_retriever = parameter_retriever
        self._parser = parser
        self._path = path

    @property
    def parameter_retriever(self):
        return self._parameter_retriever

    @property
    def parser(self):
        return self._parser

    @property
    def path(self):
        return self._path

    @property
    def ddd(self):
        return self._ddd

    @property
    def name(self):
        return self.ddd.name

    @property
    def ontology(self):
        return self.ddd.ontology

    @property
    def domain(self):
        return self.ddd.domain

    @property
    def service_interface(self):
        return self.ddd.service_interface

    @property
    def language_codes(self):
        return self.ddd.language_codes

    def reset(self):
        self.ontology.reset()
        if self.parser is not None:
            self.parser.clear()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, (self.ddd, self.parameter_retriever, self.parser))

    def as_dict(self):
        return self.ddd.as_dict()

    def ensure_relevant_entities_added(self, entities):
        self.add_relevant_entities(entities)

    def add_relevant_entities(self, entities):
        for entity in entities:
            self._ensure_relevant_entity_added(entity)

    def _ensure_relevant_entity_added(self, entity):
        def entity_is_relevant():
            if not entity.ddd_name or self.name == entity.ddd_name:
                return self.ontology.has_sort(entity.sort)
            return False

        def is_entity_dynamic():
            sort = self.ontology.get_sort(entity.sort)
            return sort.is_dynamic()

        if entity_is_relevant() and is_entity_dynamic():
            self.ontology.ensure_individual_exists(entity.name, entity.sort)
