import os

from tala.utils.chdir import chdir
from tala.ddd.loading.ddd_loader import DDDLoader
from tala.ddd.parser import Parser

from tala.ddd.ddd_specific_components import DDDSpecificComponents
from tala.ddd.services.parameters.retriever import ParameterRetriever


class ComponentLoader(object):
    def __init__(self, ddd_component_manager, name, ddd_config, rerank_amount):
        ddd_loader = DDDLoader(name, ddd_config)
        self._ddd = ddd_loader.load()
        self._ddd_config = ddd_config
        self._ddd_component_manager = ddd_component_manager
        self._rerank_amount = rerank_amount

    def load(self):
        path = os.path.join(os.getcwd(), self._ddd.name)

        with chdir(self._ddd.name):
            parser = Parser(self._ddd.name, self._ddd.ontology, self._ddd.domain.name)
            parameter_retriever = ParameterRetriever(self._ddd.service_interface, self._ddd.ontology)

        components = DDDSpecificComponents(
            self._ddd,
            parameter_retriever,
            parser,
        )
        components.path = path
        return components
