from tala.ddd.json_parser import JSONDDDParser
from tala.ddd.parser import Parser
from tala.ddd.services.parameters.retriever import ParameterRetriever
from tala.ddd.extended_ddd import ExtendedDDD
from tala.ddd.domain_manager import DomainManager
from tala.model.semantic_logic import SemanticLogic
from tala.model.ddd import DDD


class DDDAlreadyExistsException(Exception):
    pass


class UnexpectedDomainException(Exception):
    pass


class UnexpectedOntologyException(Exception):
    pass


class UnexpectedDDDException(Exception):
    pass


class SemanticObjectException(Exception):
    pass


def get_ddd_json_version(ddd_as_json):
    if "data" in ddd_as_json and "version:id" in ddd_as_json["data"]:
        return ddd_as_json["data"]["version:id"]
    return "1"


class DDDManager(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.ddd_names = []
        self.ddds_as_json = []
        self._ddds = {}
        self.ontologies = {}
        self.domains = {}
        self.domain_manager = DomainManager(self)
        self._ddds_of_domains = {}
        self._ddds_of_ontologies = {}
        self._semantic_logic = SemanticLogic(self)

    @property
    def semantic_logic(self):
        return self._semantic_logic

    def add(self, ddd):
        if ddd.name in self._ddds:
            raise DDDAlreadyExistsException("DDD '%s' already registered" % ddd.name)
        self.add_ontology(ddd.ontology)
        self._ddds_of_ontologies[ddd.ontology] = ddd
        self.add_domain(ddd.domain)
        self._ddds_of_domains[ddd.domain] = ddd
        self._ddds[ddd.name] = ddd

    def ensure_ddd_added(self, ddd):
        if ddd.name not in self._ddds:
            self.add(ddd)

    def add_domain(self, domain):
        self.domains[domain.get_name()] = domain
        self.domain_manager.add(domain)

    def add_ontology(self, ontology):
        self.ontologies[ontology.get_name()] = ontology

    def get_all_ddds(self):
        return list(self._ddds.values())

    def get_ddd(self, name):
        if name not in self._ddds and self.ddds_as_json:
            self._load_ddd(name)
        return self._ddds[name]

    def _load_ddd(self, name):
        if name not in self.ddd_names:
            raise UnexpectedDDDException(f"Expected one of the known DDDs {self.ddd_names}, but got '{name}'")
        if not self._is_loaded(name):
            ddd_as_json = self._get_ddd_as_json(name)
            self._parse_and_add(ddd_as_json)

    def load_ddd_for_ontology_name(self, name):
        for ddd_as_json in self.ddds_as_json:
            if get_ddd_json_version(ddd_as_json) == "2":
                ontology_name = ddd_as_json["data"]["relationships"]["ontology"]["data"]["id"]
            elif get_ddd_json_version(ddd_as_json) == "1":
                ontology_name = ddd_as_json["ontology"]["_name"]
            if ontology_name == name:
                self._parse_and_add(ddd_as_json)
                return
        raise UnexpectedDDDException(f"Expected ontology name of a known DDD ({self.ddd_names}), but got '{name}'")

    def _is_loaded(self, ddd_name):
        return ddd_name in self._ddds

    def add_ddds_as_json(self, ddd_names, ddds_as_json):
        self.ddd_names = ddd_names
        self.ddds_as_json = ddds_as_json

    def _get_ddd_as_json(self, name):
        for ddd_as_json in self.ddds_as_json:
            if get_ddd_json_version(ddd_as_json) == "2":
                if name == ddd_as_json["data"]["attributes"]["name"]:
                    return ddd_as_json
            if get_ddd_json_version(ddd_as_json) == "1":
                if name == ddd_as_json["ddd_name"]:
                    return ddd_as_json

    def _parse_and_add(self, ddd_as_json):
        if "data" in ddd_as_json and "version:id" in ddd_as_json["data"] and ddd_as_json["data"]["version:id"] == "2":
            ddd = DDD.create_from_json_api_data(ddd_as_json)
        else:
            ddd = JSONDDDParser().parse(ddd_as_json)
        parameter_retriever = ParameterRetriever(ddd.service_interface, ddd.ontology)
        parser = Parser(ddd.name, ddd.ontology, ddd.domain.name)
        extended_ddd = ExtendedDDD(ddd, parameter_retriever, parser)
        self.add(extended_ddd)

    def get_domain(self, name):
        return self.domains[name]

    def get_ontology(self, name):
        if name not in self.ontologies:
            self.load_ddd_for_ontology_name(name)
        return self.ontologies[name]

    def get_ontology_of(self, semantic_object):
        if semantic_object.is_ontology_specific():
            return self.get_ontology(semantic_object.ontology_name)
        raise SemanticObjectException(
            "This object is not ontology specific, and has no ontology information", semantic_object=semantic_object
        )

    def get_ddd_of_semantic_object(self, semantic_object):
        ontology = self.get_ontology_of(semantic_object)
        return self.get_ddd_of_ontology(ontology)

    def get_ddd_of_ontology(self, ontology):
        if ontology not in self._ddds_of_ontologies:
            raise UnexpectedOntologyException(
                "Expected to find '%s' among known ontologies %s but did not." %
                (ontology, list(self._ddds_of_ontologies.keys()))
            )
        return self._ddds_of_ontologies[ontology]

    def get_ddd_for_ontology_name(self, ontology_name):
        if ontology_name not in self.ontologies:
            self.load_ddd_for_ontology_name(ontology_name)
        ontology = self.get_ontology(ontology_name)
        return self.get_ddd_of_ontology(ontology)

    def reset_ddd(self, name):
        self._ddds[name].reset()
