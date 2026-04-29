import json
import os
import warnings

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
            ontology_args = self._compile_resource(
                resource, self._json_compiler.compile_ontology, self._xml_compiler.compile_ontology
            )
        ontology = Ontology(**ontology_args)
        return ontology

    def _compile_service_interface(self):
        bundle = self._load_ddd_bundle()
        if bundle is not None:
            service_interface = self._json_compiler.compile_service_interface({
                "service_interface": self._bundle_node(bundle, "service_interface")
            })
        else:
            resource = self._load_resource(self._ddd_file("service_interface", "service_interface.xml"))
            service_interface = self._compile_resource(
                resource, self._json_compiler.compile_service_interface, self._xml_compiler.compile_service_interface
            )
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
            self._maybe_warn_xml_usage(resource_name)
            with open(resource_name, "rb") as f:
                return ("xml", f.read())
        raise DDDLoaderException("Expected '%s' to exist but it does not." % resource_name)

    def _load_json_resource(self, resource_name):
        if os.path.exists(resource_name):
            with open(resource_name, "r", encoding="utf-8") as f:
                return json.load(f)
        raise DDDLoaderException("Expected '%s' to exist but it does not." % resource_name)

    def _json_bundle_name(self):
        return self._ddd_config.get("ddd_bundle")

    def _json_file_map(self):
        ddd_files = self._ddd_config.get("ddd_files")
        if not ddd_files:
            return {
                "ontology": "ontology.json",
                "domain": "domain.json",
                "service_interface": "service_interface.json",
            }
        try:
            ontology = ddd_files["ontology"]
            domain = ddd_files["domain"]
            service_interface = ddd_files["service_interface"]
        except (KeyError, TypeError):
            raise DDDLoaderException("Expected 'ddd_files' to define 'ontology', 'domain', and 'service_interface'.")
        if not ontology or not domain or not service_interface:
            raise DDDLoaderException(
                "Expected 'ddd_files' to define non-empty 'ontology', 'domain', and 'service_interface'."
            )
        return {
            "ontology": ontology,
            "domain": domain,
            "service_interface": service_interface,
        }

    def _has_split_json(self):
        json_files = self._json_file_map()
        if not all(path.endswith(".json") for path in json_files.values()):
            return False
        return all(os.path.exists(path) for path in json_files.values())

    def _compile_ontology_json(self, ontology_json):
        ontology_args = self._json_compiler.compile_ontology(ontology_json)
        return Ontology(**ontology_args)

    def _compile_service_interface_json(self, service_json):
        return self._json_compiler.compile_service_interface(service_json)

    def _compile_domain_json(self, domain_json, ontology, parser):
        domain_args = self._json_compiler.compile_domain(self._name, domain_json, ontology, parser)
        return Domain(ontology=ontology, **domain_args)

    def _find_domain_name_json(self, domain_json):
        name = self._json_compiler.get_domain_name(domain_json)
        return name

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
            bundle = json.load(f)
        if isinstance(bundle, dict) and "ddd" in bundle:
            bundle = bundle["ddd"]
        self._ddd_bundle = bundle
        return self._ddd_bundle

    def _bundle_node(self, bundle, key):
        if key not in bundle:
            raise DDDLoaderException("Expected '%s' in DDD bundle but it was not found." % key)
        return bundle[key]

    def _maybe_warn_xml_usage(self, resource_name):
        if not os.getenv("TALA_XML_WARN"):
            return
        if self._json_alternative_exists(resource_name):
            warnings.warn(
                "XML DDD files are deprecated when JSON alternatives exist. "
                "Configure a JSON bundle in ddd.config.json to migrate.",
                DeprecationWarning,
                stacklevel=2,
            )

    def _json_alternative_exists(self, resource_name):
        bundle_path = self._ddd_config.get("ddd_bundle")
        if bundle_path and os.path.exists(bundle_path):
            return True
        files = self._ddd_config.get("ddd_files", {})
        json_paths = [value for value in files.values() if isinstance(value, str) and value.endswith(".json")]
        for json_path in json_paths:
            if os.path.exists(json_path):
                return True
        candidate = os.path.splitext(resource_name)[0] + ".json"
        return os.path.exists(candidate)

    def load(self):
        path = os.path.join(os.getcwd(), self._name)

        with chdir.chdir(self._name):
            bundle_name = self._json_bundle_name()
            if bundle_name:
                ddd_json = self._load_ddd_bundle()
                ontology_json = {"ontology": ddd_json["ontology"]}
                domain_json = {"domain": ddd_json["domain"]}
                service_json = {"service_interface": ddd_json["service_interface"]}
                ontology = self._compile_ontology_json(ontology_json)
                domain_name = self._find_domain_name_json(domain_json)
                parser = Parser(self._name, ontology, domain_name)
                service_interface = self._compile_service_interface_json(service_json)
                domain = self._compile_domain_json(domain_json, ontology, parser)
            elif self._has_split_json():
                json_files = self._json_file_map()
                ontology_json = self._load_json_resource(json_files["ontology"])
                domain_json = self._load_json_resource(json_files["domain"])
                service_json = self._load_json_resource(json_files["service_interface"])
                ontology = self._compile_ontology_json(ontology_json)
                domain_name = self._find_domain_name_json(domain_json)
                parser = Parser(self._name, ontology, domain_name)
                service_interface = self._compile_service_interface_json(service_json)
                domain = self._compile_domain_json(domain_json, ontology, parser)
            else:
                ontology = self._compile_ontology()
                domain_name = self._find_domain_name()
                parser = Parser(self._name, ontology, domain_name)
                service_interface = self._compile_service_interface()
                domain = self._compile_domain(ontology, parser, service_interface)

        return DDD(self._name, ontology, domain, service_interface, path)
