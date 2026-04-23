import json
import os

from tala.model.ddd import DDD
from tala.ddd.ddd_xml_compiler import DDDXMLCompiler, DomainCompiler as DomainXmlCompiler
from tala.ddd.ddd_json_compiler import DDDJSONCompiler
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
        self._json_compiler = DDDJSONCompiler()
        self._ddd_bundle = None

    def _compile_ontology(self):
        bundle = self._load_ddd_bundle()
        if bundle is not None:
            ontology_args = self._json_compiler.compile_ontology({"ontology": self._bundle_node(bundle, "ontology")})
        else:
            resource = self._load_resource(self._ddd_file("ontology", "ontology.xml"))
            ontology_args = self._compile_resource(resource, self._json_compiler.compile_ontology,
                                                   self._xml_compiler.compile_ontology)
        ontology = Ontology(**ontology_args)
        return ontology

    def _compile_service_interface(self):
        bundle = self._load_ddd_bundle()
        if bundle is not None:
            service_interface = self._json_compiler.compile_service_interface(
                {"service_interface": self._bundle_node(bundle, "service_interface")}
            )
        else:
            resource = self._load_resource(self._ddd_file("service_interface", "service_interface.xml"))
            service_interface = self._compile_resource(resource, self._json_compiler.compile_service_interface,
                                                       self._xml_compiler.compile_service_interface)
        return service_interface

    def _compile_domain(self, ontology, parser, service_interface):
        domain_args = self._domain_as_dict(ontology, parser)
        domain = Domain(ontology=ontology, **domain_args)
        return domain

    def _domain_as_dict(self, ontology, parser):
        bundle = self._load_ddd_bundle()
        if bundle is not None:
            domain_as_dict = self._json_compiler.compile_domain(
                self._name, {"domain": self._bundle_node(bundle, "domain")}, ontology, parser
            )
        else:
            resource = self._load_resource(self._ddd_file("domain", "domain.xml"))
            domain_as_dict = self._compile_domain_resource(resource, ontology, parser)
        return domain_as_dict

    def _load_resource(self, resource_name):
        if os.path.exists(resource_name):
            if resource_name.endswith(".json"):
                with open(resource_name, "r", encoding="utf-8") as f:
                    return ("json", f.read())
            with open(resource_name, "rb") as f:
                return ("xml", f.read())
        raise DDDLoaderException("Expected '%s' to exist but it does not." % resource_name)

    def _find_domain_name(self):
        bundle = self._load_ddd_bundle()
        if bundle is not None:
            name = self._json_compiler.get_domain_name({"domain": self._bundle_node(bundle, "domain")})
        else:
            resource = self._load_resource(self._ddd_file("domain", "domain.xml"))
            name = self._get_domain_name(resource)
        return name

    def _get_domain_name(self, resource):
        kind, payload = resource
        if kind == "json":
            return self._json_compiler.get_domain_name(payload)
        return DomainXmlCompiler().get_name(payload)

    def _compile_resource(self, resource, json_compiler, xml_compiler):
        kind, payload = resource
        if kind == "json":
            return json_compiler(payload)
        return xml_compiler(payload)

    def _compile_domain_resource(self, resource, ontology, parser):
        kind, payload = resource
        if kind == "json":
            return self._json_compiler.compile_domain(self._name, payload, ontology, parser)
        return self._xml_compiler.compile_domain(self._name, payload, ontology, parser)

    def _ddd_file(self, key, default_name):
        files = self._ddd_config.get("ddd_files", {})
        return files.get(key, default_name)

    def _load_ddd_bundle(self):
        if self._ddd_bundle is not None:
            return self._ddd_bundle
        bundle_path = self._ddd_config.get("ddd_bundle")
        if not bundle_path:
            return None
        if not os.path.exists(bundle_path):
            raise DDDLoaderException("Expected '%s' to exist but it does not." % bundle_path)
        if not bundle_path.endswith(".json"):
            raise DDDLoaderException("Expected JSON bundle '%s'." % bundle_path)
        with open(bundle_path, "r", encoding="utf-8") as f:
            self._ddd_bundle = json.load(f)
        return self._ddd_bundle

    def _bundle_node(self, bundle, key):
        if key not in bundle:
            raise DDDLoaderException("Expected '%s' in DDD bundle but it was not found." % key)
        return bundle[key]

    def load(self):
        path = os.path.join(os.getcwd(), self._name)

        with chdir.chdir(self._name):
            ontology = self._compile_ontology()
            domain_name = self._find_domain_name()
            parser = Parser(self._name, ontology, domain_name)
            service_interface = self._compile_service_interface()
            domain = self._compile_domain(ontology, parser, service_interface)

        return DDD(self._name, ontology, domain, service_interface, path)
