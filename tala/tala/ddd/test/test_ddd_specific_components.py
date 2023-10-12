import unittest

from mock import Mock

from tala.ddd.ddd_specific_components import DDDSpecificComponents
from tala.ddd.parser import Parser
from tala.ddd.services.parameters.retriever import ParameterRetriever
from tala.ddd.services.service_interface import ServiceInterface
from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.ontology import Ontology


class TestDdd(unittest.TestCase):
    def setUp(self):
        self._ddd_specific_components = None
        self._mocked_ontology = None
        self._mocked_parser = None

    def test_reset_resets_ontology(self):
        self.given_mocked_ontology()
        self.given_ddd_and_components_created()
        self.when_calling_reset()
        self.then_ontology_is_reset()

    def given_mocked_ontology(self, individuals=None):
        self._mocked_ontology = Mock(spec=Ontology)
        self._mocked_ontology.get_individuals.return_value = individuals or {}

    def given_ddd_and_components_created(self):
        ddd = self._create_ddd()
        self._ddd_specific_components = self._create_ddd_components(ddd)

    def _create_ddd_components(self, ddd):
        return DDDSpecificComponents(ddd, parameter_retriever=Mock(spec=ParameterRetriever), parser=self._mocked_parser)

    def _create_ddd(self):
        return DDD(
            "a_ddd",
            ontology=self._mocked_ontology,
            domain=Mock(spec=Domain),
            service_interface=Mock(spec=ServiceInterface)
        )

    def when_calling_reset(self):
        self._ddd_specific_components.reset()

    def then_ontology_is_reset(self):
        self._mocked_ontology.reset.assert_called_once_with()

    def test_reset_clears_parser(self):
        self.given_mocked_ontology()
        self.given_mocked_parser()
        self.given_ddd_and_components_created()
        self.when_calling_reset()
        self.then_parser_is_cleared()

    def given_mocked_parser(self):
        self._mocked_parser = Mock(spec=Parser)

    def then_parser_is_cleared(self):
        self._mocked_parser.clear.assert_called_once_with()
