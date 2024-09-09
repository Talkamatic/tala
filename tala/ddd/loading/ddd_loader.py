import os

from tala.model.ddd import DDD
from tala.ddd.ddd_xml_compiler import DDDXMLCompiler, DomainCompiler as DomainXmlCompiler
from tala.ddd.parser import Parser
from tala.model.domain import Domain
from tala.model.ontology import Ontology
from tala.utils import chdir


class DDDLoaderException(Exception):
    pass


class DDDLoader(object):
    def __init__(self, name, ddd_config):
        super(DDDLoader, self).__init__()
        self._name = name
        self._ddd_config = ddd_config
        self._xml_compiler = DDDXMLCompiler()

    def _compile_ontology(self):
        ontology_xml = self._load_xml_resource("ontology.xml")
        ontology_args = self._xml_compiler.compile_ontology(ontology_xml)

        return Ontology(**ontology_args)

    def _compile_service_interface(self):
        service_interface_xml = self._load_xml_resource("service_interface.xml")
        return self._xml_compiler.compile_service_interface(service_interface_xml)

    def _compile_domain(self, ontology, parser, service_interface):
        domain_args = self._domain_as_dict(ontology, parser)
        return Domain(ontology=ontology, **domain_args)

    def _domain_as_dict(self, ontology, parser):
        domain_xml = self._load_xml_resource("domain.xml")
        domain_as_dict = self._xml_compiler.compile_domain(self._name, domain_xml, ontology, parser)
        return domain_as_dict

    def _load_xml_resource(self, resource_name):
        if os.path.exists(resource_name):
            with open(resource_name, "rb") as f:
                return f.read()
        else:
            raise DDDLoaderException("Expected '%s' to exist but it does not." % resource_name)

    def _find_domain_name(self):
        domain_xml = self._load_xml_resource("domain.xml")
        name = DomainXmlCompiler().get_name(domain_xml)
        return name

    def load(self):
        path = os.path.join(os.getcwd(), self._name)

        with chdir.chdir(self._name):
            ontology = self._compile_ontology()
            domain_name = self._find_domain_name()
            parser = Parser(self._name, ontology, domain_name)
            service_interface = self._compile_service_interface()
            domain = self._compile_domain(ontology, parser, service_interface)

        return DDD(self._name, ontology, domain, service_interface, path)
