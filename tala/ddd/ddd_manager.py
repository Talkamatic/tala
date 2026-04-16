import warnings

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


class LegacyDddJsonFormatException(Exception):
    pass


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
            ontology_name = self._get_ontology_name(ddd_as_json)
            if ontology_name == name:
                self._parse_and_add(ddd_as_json)
                return
        raise UnexpectedDDDException(f"Expected ontology name of a known DDD ({self.ddd_names}), but got '{name}'")

    def _is_loaded(self, ddd_name):
        return ddd_name in self._ddds

    def add_ddds_as_json(self, ddd_names, ddds_as_json):
        self.ddd_names = ddd_names
        self.ddds_as_json = ddds_as_json

    def _is_json_api_format(self, ddd_as_json):
        return "data" in ddd_as_json

    def _is_legacy_format(self, ddd_as_json):
        return "ddd_name" in ddd_as_json or "ontology" in ddd_as_json

    def _warn_legacy_format(self, ddd_as_json):
        ddd_name = ddd_as_json.get("ddd_name", "<unknown>")
        warnings.warn(
            "Legacy DDD JSON format is deprecated and will be removed. "
            f"Regenerate the ODB using JSON:API (ddd='{ddd_name}').",
            DeprecationWarning,
            stacklevel=2,
        )

    def _get_ontology_name(self, ddd_as_json):
        if self._is_json_api_format(ddd_as_json):
            return ddd_as_json["data"]["relationships"]["ontology"]["data"]["id"]
        if self._is_legacy_format(ddd_as_json):
            self._warn_legacy_format(ddd_as_json)
            return ddd_as_json["ontology"]["_name"]
        raise LegacyDddJsonFormatException(
            "Unrecognized DDD JSON format; expected JSON:API or legacy shape."
        )

    def _get_ddd_as_json(self, name):
        for ddd_as_json in self.ddds_as_json:
            if self._is_json_api_format(ddd_as_json):
                if name == ddd_as_json["data"]["attributes"]["name"]:
                    return ddd_as_json
                continue
            if self._is_legacy_format(ddd_as_json):
                if name == ddd_as_json["ddd_name"]:
                    return ddd_as_json
                continue
        raise LegacyDddJsonFormatException(
            f"Unable to locate DDD '{name}' with JSON:API or legacy shape."
        )

    def _parse_and_add(self, ddd_as_json):
        if self._is_json_api_format(ddd_as_json):
            ddd = DDD.create_from_json_api_data(ddd_as_json)
        elif self._is_legacy_format(ddd_as_json):
            self._warn_legacy_format(ddd_as_json)
            ddd = JSONDDDParser().parse(ddd_as_json)
        else:
            raise LegacyDddJsonFormatException(
                "Unrecognized DDD JSON format; expected JSON:API or legacy shape."
            )
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
            "This object is not ontology specific, and has no ontology information: %s" % semantic_object
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
