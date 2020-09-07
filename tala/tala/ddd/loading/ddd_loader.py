import os
import warnings

from tala.model.ddd import DDD
from tala.ddd.loading.python_module_loader import PythonModuleLoader, DddLoaderException
from tala.ddd.ddd_py_compiler import DddPyCompiler, DomainCompiler as DomainPyCompiler
from tala.ddd.ddd_xml_compiler import DddXmlCompiler, DomainCompiler as DomainXmlCompiler
from tala.ddd.parser import Parser
from tala.ddd.services.service_interface import ServiceInterface
from tala.ddd.services.service_interface_from_device import ServiceInterfaceFromDevice
from tala.model.grammar.grammar import Grammar, GrammarForRGL
from tala.ddd.grammar.reader import GrammarReader
from tala.ddd.grammar.parser import GrammarParser
from tala.model.domain import Domain, DddDomain
from tala.model.ontology import Ontology, DddOntology
from tala.utils import chdir


class DDDLoader(object):
    def __init__(self, name, ddd_config, languages):
        super(DDDLoader, self).__init__()
        self._name = name
        self._ddd_config = ddd_config
        self._languages = languages
        self._py_compiler = DddPyCompiler()
        self._xml_compiler = DddXmlCompiler()

    def _load_grammar(self, language_code):
        if GrammarReader.xml_grammar_exists_for_language(language_code, path="grammar"):
            grammar_string = GrammarReader.read(language_code, path="grammar")
            grammar_path = GrammarReader.path(language_code, path="grammar")
            grammar_root = GrammarParser.parse(grammar_string)
            if self._ddd_config["use_rgl"]:
                return GrammarForRGL(grammar_root, grammar_path)
            else:
                return Grammar(grammar_root, grammar_path)
        return None

    def _compile_ontology(self):
        if os.path.exists("ontology.xml"):
            ontology_xml = self._load_xml_resource("ontology.xml")
            ontology_args = self._xml_compiler.compile_ontology(ontology_xml)
        elif os.path.exists("ontology.py"):
            warnings.warn("ontology.py is deprecated. Convert it to an ontology.xml instead.", DeprecationWarning)
            ontology_class = PythonModuleLoader(self._name).load_py_module_class("ontology.py", DddOntology)
            ontology_args = self._py_compiler.compile_ontology(ontology_class)
        else:
            raise DddLoaderException("neither .py nor .xml ontology found")

        return Ontology(**ontology_args)

    def _compile_service_interface(self):
        if not os.path.exists("service_interface.xml"):
            empty_service_interface = ServiceInterface([], [], [], [])
            suggestion = ServiceInterfaceFromDevice.to_xml(empty_service_interface)
            raise DddLoaderException(
                "Expected 'service_interface.xml' to exist but it does not. Start by adding an empty one:\n\n%s\n" %
                suggestion
            )
        service_interface_xml = self._load_xml_resource("service_interface.xml")
        return self._xml_compiler.compile_service_interface(service_interface_xml)

    def _compile_domain(self, ontology, parser, service_interface):
        domain_args = self._domain_as_dict(ontology, parser, service_interface)
        return Domain(ontology=ontology, **domain_args)

    def _domain_as_dict(self, ontology, parser, service_interface):
        if os.path.exists("domain.xml"):
            domain_xml = self._load_xml_resource("domain.xml")
            domain_as_dict = self._xml_compiler.compile_domain(
                self._name, domain_xml, ontology, parser, service_interface
            )
        elif os.path.exists("domain.py"):
            domain_class = PythonModuleLoader(self._name).load_py_module_class("domain.py", DddDomain)
            domain_as_dict = self._py_compiler.compile_domain(self._name, domain_class, ontology, parser)
        else:
            raise DddLoaderException("neither .py nor .xml domain found")
        return domain_as_dict

    def _load_xml_resource(self, resource_name):
        if os.path.exists(resource_name):
            with open(resource_name, "rb") as f:
                return f.read()
        else:
            raise DddLoaderException("Expected '%s' to exist but it does not" % resource_name)

    def _find_domain_name(self):
        if os.path.exists("domain.xml"):
            domain_xml = self._load_xml_resource("domain.xml")
            name = DomainXmlCompiler().get_name(domain_xml)
        elif os.path.exists("domain.py"):
            warnings.warn("domain.py is deprecated. Convert it to a domain.xml instead.", DeprecationWarning)
            domain_class = PythonModuleLoader(self._name).load_py_module_class("domain.py", DddDomain)
            name = DomainPyCompiler().get_name(domain_class)
        else:
            raise DddLoaderException("neither .py nor .xml domain found")
        return name

    def load(self):
        path = os.path.join(os.getcwd(), self._name)

        with chdir.chdir(self._name):
            ontology = self._compile_ontology()
            grammars = {}
            for language_code in self._languages:
                grammar = self._load_grammar(language_code)
                grammars[language_code] = grammar

            domain_name = self._find_domain_name()
            parser = Parser(self._name, ontology, domain_name)
            service_interface = self._compile_service_interface()
            domain = self._compile_domain(ontology, parser, service_interface)

        ddd = self._create_ddd(ontology, domain, service_interface, grammars)
        ddd.path = path
        return ddd

    def _create_ddd(self, ontology, domain, service_interface, grammars):
        return DDD(
            self._name, ontology, domain, self._ddd_config["rasa_nlu"], service_interface, grammars, self._languages,
            self._ddd_config["use_rgl"]
        )
