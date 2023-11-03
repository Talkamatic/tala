from tala.model.error import OntologyError
from tala.model.predicate import Predicate
from tala.model.sort import CustomSort, IntegerSort, RealSort
from tala.testing.lib_test_case import LibTestCase


class PredicateTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_get_name(self):
        self.assertEqual("dest_city", self.predicate_dest_city.get_name())

    def test_create_invalid_predicate(self):
        with self.assertRaises(OntologyError):
            self.ontology.get_predicate("kalle")

    def test_getSort(self):
        predicate = self.ontology.get_predicate("dest_city")
        self.assertEqual(self.sort_city, predicate.sort)

    def test_feature_get_sort(self):
        predicate = self.ontology.get_predicate("dest_city_type")
        self.assertEqual(self.sort_city_type, predicate.sort)

    def test_is_feature_of_true(self):
        self.assertTrue(self.predicate_dest_city_type.is_feature_of(self.predicate_dest_city))

    def test_is_feature_of_false(self):
        self.assertFalse(self.predicate_dest_city.is_feature_of(self.predicate_dest_city_type))

    def test_allows_multiple_instances_false_by_default(self):
        arbirary_predicate = self.ontology.get_predicate("dest_city_type")
        self.assertFalse(arbirary_predicate.allows_multiple_instances())

    def test_allows_multiple_instances_true(self):
        multi_instance_predicate = self.ontology.get_predicate("passenger_type_to_add")
        self.assertTrue(multi_instance_predicate.allows_multiple_instances())

    def test_equality(self):
        predicate1 = Predicate(self.ontology_name, "dest_city", self._city_sort)
        predicate2 = Predicate(self.ontology_name, "dest_city", self._city_sort)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(predicate1, predicate2)

    def test_inequality_due_to_name(self):
        predicate1 = Predicate(self.ontology_name, "dest_city", self._city_sort)
        predicate2 = Predicate(self.ontology_name, "dept_city", self._city_sort)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(predicate1, predicate2)

    def test_inequality_due_to_sort(self):
        predicate1 = Predicate(self.ontology_name, "price", IntegerSort())
        predicate2 = Predicate(self.ontology_name, "price", RealSort())
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(predicate1, predicate2)

    def test_inequality_due_to_featurehood(self):
        predicate1 = Predicate(self.ontology_name, "dest_city_type", self._city_sort)
        predicate2 = Predicate(self.ontology_name, "dest_city_type", self._city_sort, feature_of_name="dest_city")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(predicate1, predicate2)

    def test_inequality_due_to_multiple_instances(self):
        predicate1 = Predicate(self.ontology_name, "dest_city", self._city_sort, multiple_instances=False)
        predicate2 = Predicate(self.ontology_name, "dest_city", self._city_sort, multiple_instances=True)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(predicate1, predicate2)

    def test_inequality_due_to_non_predicate(self):
        non_predicate = "means_of_transport"
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.predicate_dest_city, non_predicate)

    def test_inequality_due_to_ontology_name(self):
        sort_of_an_ontology = CustomSort("an_ontology", "a_sort")
        predicate1 = Predicate("an_ontology", "dest_city", sort_of_an_ontology)
        sort_of_other_ontology = CustomSort("other_ontology", "a_sort")
        predicate2 = Predicate("other_ontology", "dest_city", sort_of_other_ontology)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(predicate1, predicate2)

    def test_unicode(self):
        self.assertEqual("dest_city", str(self.predicate_dest_city))

    def test_hashable(self):
        s = set()
        s.add(self.predicate_dest_city)
