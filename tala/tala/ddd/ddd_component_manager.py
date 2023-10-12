from tala.ddd.json_parser import JSONDDDParser
from tala.ddd.parser import Parser
from tala.ddd.services.parameters.retriever import ParameterRetriever
from tala.ddd.ddd_specific_components import DDDSpecificComponents
from tala.ddd.domain_manager import DomainManager
from tala.model.semantic_logic import SemanticLogic


class DDDSpecificComponentsAlreadyExistsException(Exception):
    pass


class UnexpectedDomainException(Exception):
    pass


class UnexpectedOntologyException(Exception):
    pass


class UnexpectedDDDException(Exception):
    pass


class DDDComponentManager(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.ddd_names = []
        self.ddds_as_json = []
        self._components_of_ddds = {}
        self.ontologies = {}
        self.domains = {}
        self.domain_manager = DomainManager(self)
        self._ddds_of_domains = {}
        self._ddds_of_ontologies = {}
        self._semantic_logic = SemanticLogic(self)

    @property
    def semantic_logic(self):
        return self._semantic_logic

    def add(self, ddd_specific_components):
        if ddd_specific_components.name in self._components_of_ddds:
            raise DDDSpecificComponentsAlreadyExistsException(
                "Components for DDD '%s' already registered" % ddd_specific_components.name
            )
        self.add_ontology(ddd_specific_components.ontology)
        self._ddds_of_ontologies[ddd_specific_components.ontology] = ddd_specific_components
        self.add_domain(ddd_specific_components.domain)
        self._ddds_of_domains[ddd_specific_components.domain] = ddd_specific_components
        self._components_of_ddds[ddd_specific_components.name] = ddd_specific_components

    def ensure_ddd_components_added(self, ddd_components):
        if ddd_components.name not in self._components_of_ddds:
            self.add(ddd_components)

    def add_domain(self, domain):
        self.domains[domain.get_name()] = domain
        self.domain_manager.add(domain)

    def add_ontology(self, ontology):
        self.ontologies[ontology.get_name()] = ontology

    def get_components_for_all_ddds(self):
        return list(self._components_of_ddds.values())

    def get_ddd_specific_components(self, name):
        if name not in self._components_of_ddds and self.ddds_as_json:
            self._load_ddd(name)
        return self._components_of_ddds[name]

    def _load_ddd(self, name):
        if name not in self.ddd_names:
            raise UnexpectedDDDException(f"Expected one of the known DDDs {self.ddd_names}, but got '{name}'")
        if not self._is_loaded(name):
            ddd_as_json = self._get_ddd_as_json(name)
            self._parse_and_add(ddd_as_json)

    def load_ddd_for_ontology_name(self, name):
        for ddd_as_json in self.ddds_as_json:
            ontology_name = ddd_as_json["ontology"]["_name"]
            if ontology_name == name:
                self._parse_and_add(ddd_as_json)
                return
        raise UnexpectedDDDException(f"Expected ontology name of a known DDD ({self.ddd_names}), but got '{name}'")

    def _is_loaded(self, ddd_name):
        return ddd_name in self._components_of_ddds

    def add_ddds_as_json(self, ddd_names, ddds_as_json):
        self.ddd_names = ddd_names
        self.ddds_as_json = ddds_as_json

    def _get_ddd_as_json(self, name):
        for ddd in self.ddds_as_json:
            if name == ddd["ddd_name"]:
                return ddd

    def _parse_and_add(self, ddd_as_json):
        ddd = JSONDDDParser().parse(ddd_as_json)
        parameter_retriever = ParameterRetriever(ddd.service_interface, ddd.ontology)
        parser = Parser(ddd.name, ddd.ontology, ddd.domain.name)
        ddd_specific_components = DDDSpecificComponents(ddd, parameter_retriever, parser)
        self.add(ddd_specific_components)

    def get_domain(self, name):
        return self.domains[name]

    def get_ontology(self, name):
        if name not in self.ontologies:
            self.load_ddd_for_ontology_name(name)
        return self.ontologies[name]

    def get_ddd_specific_components_of_ontology(self, ontology):
        if ontology not in self._ddds_of_ontologies:
            raise UnexpectedOntologyException(
                "Expected to find '%s' among known ontologies %s but did not." %
                (ontology, list(self._ddds_of_ontologies.keys()))
            )
        return self._ddds_of_ontologies[ontology]

    def get_ddd_specific_components_of_ontology_name(self, ontology_name):
        if ontology_name not in self.ontologies:
            self.load_ddd_for_ontology_name(ontology_name)
        ontology = self.get_ontology(ontology_name)
        return self.get_ddd_specific_components_of_ontology(ontology)

    def reset_components_of_ddd(self, name):
        ddd_specific_components = self._components_of_ddds[name]
        ddd_specific_components.reset()
