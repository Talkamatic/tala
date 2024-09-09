import unittest

from unittest.mock import Mock

from tala.ddd.extended_ddd import ExtendedDDD
from tala.ddd.parser import Parser
from tala.ddd.services.parameters.retriever import ParameterRetriever
from tala.ddd.services.service_interface import ServiceInterface
from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.ontology import Ontology


class TestExtendedDDD(unittest.TestCase):
    def setUp(self):
        self._extended_ddd = None
        self._mocked_ontology = None
        self._mocked_parser = None

    def test_reset_resets_ontology(self):
        self.given_mocked_ontology()
        self.given_extended_ddd_created()
        self.when_calling_reset()
        self.then_ontology_is_reset()

    def given_mocked_ontology(self, individuals=None):
        self._mocked_ontology = Mock(spec=Ontology)
        self._mocked_ontology.get_individuals.return_value = individuals or {}

    def given_extended_ddd_created(self):
        ddd = self._create_ddd()
        self._extended_ddd = self._create_extended_ddd(ddd)

    def _create_extended_ddd(self, ddd):
        return ExtendedDDD(ddd, parameter_retriever=Mock(spec=ParameterRetriever), parser=self._mocked_parser)

    def _create_ddd(self):
        return DDD(
            "a_ddd",
            ontology=self._mocked_ontology,
            domain=Mock(spec=Domain),
            service_interface=Mock(spec=ServiceInterface)
        )

    def when_calling_reset(self):
        self._extended_ddd.reset()

    def then_ontology_is_reset(self):
        self._mocked_ontology.reset.assert_called_once_with()

    def test_reset_clears_parser(self):
        self.given_mocked_ontology()
        self.given_mocked_parser()
        self.given_extended_ddd_created()
        self.when_calling_reset()
        self.then_parser_is_cleared()

    def given_mocked_parser(self):
        self._mocked_parser = Mock(spec=Parser)

    def then_parser_is_cleared(self):
        self._mocked_parser.clear.assert_called_once_with()
