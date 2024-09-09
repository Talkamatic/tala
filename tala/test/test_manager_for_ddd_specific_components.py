import unittest

from unittest.mock import Mock

from tala.ddd.ddd_manager import DDDManager, DDDAlreadyExistsException
from tala.ddd.services.service_interface import ServiceInterface
from tala.model.ddd import DDD
from tala.model.domain import Domain
from tala.model.ontology import Ontology
from tala.ddd.extended_ddd import ExtendedDDD
from tala.ddd.services.parameters.retriever import ParameterRetriever


class TestManagerForExtendedDDD(unittest.TestCase):
    def setUp(self):
        self.domain = None
        self.ontology = None
        self._mock_device_handler = None
        self._ddd_specific_components = None
        self._second_ddd_specific_components = None
        self._ddd_manager = None

    def _create_ddd(self, name="mockup_ddd"):
        return DDD(name, ontology=self.ontology, domain=self.domain, service_interface=Mock(spec=ServiceInterface))

    def _create_ddd_specific_components(self, ddd, device_class=None):
        return ExtendedDDD(ddd, parameter_retriever=Mock(spec=ParameterRetriever), parser=None)

    def test_get_domain(self):
        self._given_empty_manager_for_ddd_specific_components()
        self._given_mocked_ontology("MockupOntology")
        self._given_mocked_domain("MockupDomain")
        self._given_ddd_specific_components()
        self._given_ddd_specific_components_added()
        self._when_getting_domain("MockupDomain")
        self._then_it_equals_mocked_domain()

    def _given_mocked_domain(self, name="MockupDomain"):
        self.domain = self._create_mock_domain(name)

    def _create_mock_domain(self, name):
        domain = Mock(spec=Domain)
        domain.get_name.return_value = name
        domain.goals = {}
        return domain

    def _given_ddd_specific_components(self, name=None, device_class=None):
        ddd = self._create_ddd(name)
        self._ddd_specific_components = self._create_ddd_specific_components(ddd, device_class)

    def _given_second_ddd_specific_components(self, name=None, device_class=None):
        ddd = self._create_ddd(name)
        self._second_ddd_specific_components = self._create_ddd_specific_components(ddd, device_class)

    def _when_getting_domain(self, name):
        self._result = self._ddd_manager.get_domain(name)

    def _then_it_equals_mocked_domain(self):
        self.assertEqual(self._result, self.domain)

    def test_get_ontology(self):
        self._given_empty_manager_for_ddd_specific_components()
        self._given_mocked_ontology("MockupOntology")
        self._given_mocked_domain("MockupDomain")
        self._given_ddd_specific_components()
        self._given_ddd_specific_components_added()
        self._when_getting_ontology("MockupOntology")
        self._then_it_equals_mocked_ontology()

    def _given_mocked_ontology(self, name="MockupOntology"):
        self.ontology = self._create_mock_ontology(name)

    def _create_mock_ontology(self, name):
        ontology = Mock(spec=Ontology)
        ontology.get_individuals.return_value = {}
        ontology.get_name.return_value = name
        return ontology

    def _when_getting_ontology(self, name):
        self._result = self._ddd_manager.get_ontology(name)

    def _then_it_equals_mocked_ontology(self):
        self.assertEqual(self._result, self.ontology)

    def test_adding_duplicate_yields_exception(self):
        self._given_empty_manager_for_ddd_specific_components()
        self._given_mocked_ontology("MockupOntology")
        self._given_mocked_domain("MockupDomain")
        self._given_ddd_specific_components("ddd")
        self._given_ddd_specific_components_added()
        self._given_second_ddd_specific_components("ddd")
        self._when_adding_second_ddd_specific_components_again_then_exception_is_raised()

    def _when_adding_second_ddd_specific_components_again_then_exception_is_raised(self):
        with self.assertRaises(DDDAlreadyExistsException):
            self._given_second_ddd_specific_components_added()

    def _given_empty_manager_for_ddd_specific_components(self):
        self._ddd_manager = DDDManager()

    def _given_ddd_specific_components_added(self):
        self._ddd_manager.add(self._ddd_specific_components)

    def _given_second_ddd_specific_components_added(self):
        self._ddd_manager.add(self._second_ddd_specific_components)

    def _then_sorted_results_is(self, expected_result):
        self.assertEqual(expected_result, sorted(self._result))

    def test_get_ddd(self):
        self._given_mocked_ontology()
        self._given_mocked_domain()
        self._given_empty_manager_for_ddd_specific_components()
        self._given_ddd_specific_components("ddd")
        self._given_ddd_specific_components_added()
        self._when_getting_ddd_specific_components_for("ddd")
        self._then_ddd_specific_components_are_returned()

    def _when_getting_ddd_specific_components_for(self, ddd):
        self._result = self._ddd_manager.get_ddd(ddd)

    def _then_ddd_specific_components_are_returned(self):
        self.assertEqual(self._result, self._ddd_specific_components)

    def test_reset_ddd_resets_ontology(self):
        self._given_mocked_ontology()
        self._given_mocked_domain()
        self._given_empty_manager_for_ddd_specific_components()
        self._given_ddd_specific_components("ddd")
        self._given_ddd_specific_components_added()
        self._given_individual_added_to_ontology()
        self._when_ddd_is_reset_for("ddd")
        self._then_get_ddd_returns_ddd_with_unmodified_ontology("ddd")

    def _given_individual_added_to_ontology(self):
        self.ontology.add_individual("athens", "city")

    def _when_ddd_is_reset_for(self, ddd):
        self._ddd_manager.reset_ddd(ddd)

    def _then_get_ddd_returns_ddd_with_unmodified_ontology(self, ddd_name):
        ddd = self._ddd_manager.get_ddd(ddd_name)
        self.assertEqual(0, len(ddd.ontology.get_individuals()))

    def _then_result_is(self, expected):
        self.assertEqual(expected, self._result)
