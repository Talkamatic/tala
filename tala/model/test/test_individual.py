from unittest.mock import Mock

from tala.model.individual import Individual
from tala.model.ontology import Ontology, OntologyError
from tala.model.predicate import Predicate
from tala.model.sort import RealSort, IntegerSort, StringSort, CustomSort, ImageSort, WebviewSort, DateTimeSort, \
    PersonNameSort, Sort
from tala.model.image import Image
from tala.model.webview import Webview
from tala.model.date_time import DateTime
from tala.testing.lib_test_case import LibTestCase


class IndividualTestBase(LibTestCase):
    def setUp(self):
        self._create_ontology()
        self._create_semantic_objects()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        self._city_sort = CustomSort(self.ontology_name, "city")
        sorts = {
            self._city_sort,
        }
        predicates = {
            self._create_predicate("price", RealSort()),
            self._create_predicate("number_of_passengers", IntegerSort()),
            self._create_predicate("map_to_show", ImageSort()),
            self._create_predicate("map_to_browse", WebviewSort()),
            self._create_predicate("departure_time", DateTimeSort()),
            self._create_predicate("comment", StringSort()),
            self._create_predicate("selected_city", self._city_sort),
            self._create_predicate("contact_to_call", PersonNameSort()),
        }
        individuals = {
            "paris": CustomSort(self.ontology_name, "city"),
            "london": CustomSort(self.ontology_name, "city"),
        }
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

        self.empty_ontology = Ontology("empty_ontology", {}, {}, {}, set())

    def _create_predicate(self, *args, **kwargs):
        return Predicate(self.ontology_name, *args, **kwargs)

    def _create_semantic_objects(self):
        self.sort_city = self.ontology.get_sort("city")
        self.individual_paris = self.ontology.create_individual("paris")
        self.individual_not_paris = self.ontology.create_negative_individual("paris")
        self.integer_individual = self.ontology.create_individual(1234, IntegerSort())
        self.string_individual = self.ontology.create_individual("a string")
        self.image_individual = self.ontology.create_individual(Image("http://mymap.com/map.png"))
        self.webview_individual = self.ontology.create_individual(Webview("http://mymap.com/map.html"))
        self.datetime_individual = self.ontology.create_individual(DateTime("2018-04-11T22:00:00.000Z"))


class IndividualTest(IndividualTestBase):
    def test_create_real_individual_with_ontology_with_real_type(self):
        self.ontology.create_individual(123.50)

    def test_create_real_individual_with_ontology_without_real_type(self):
        ontology_without_real_type = self.empty_ontology
        with self.assertRaises(OntologyError):
            ontology_without_real_type.create_individual(123.50)

    def test_create_integer_individual_with_ontology_with_integer_type(self):
        self.ontology.create_individual(123)

    def test_create_integer_individual_with_ontology_without_integer_type(self):
        with self.assertRaises(OntologyError):
            ontology_without_integer_type = self.empty_ontology
            ontology_without_integer_type.create_individual(123)

    def test_real_individual_unicode(self):
        real_individual = self.ontology.create_individual(1234.0)
        self.assertEqual("1234.0", str(real_individual))

    def test_integer_individual_unicode(self):
        self.assertEqual("1234", str(self.integer_individual))

    def test_string_individual_unicode(self):
        self.assertEqual('"a string"', str(self.string_individual))

    def test_image_individual_unicode(self):
        self.assertEqual('image("http://mymap.com/map.png")', str(self.image_individual))

    def test_webview_individual_unicode(self):
        self.assertEqual('webview("http://mymap.com/map.html")', str(self.webview_individual))

    def test_datetime_individual_unicode(self):
        self.assertEqual('datetime(2018-04-11T22:00:00.000Z)', str(self.datetime_individual))

    def test_create_individual(self):
        individual = self.ontology.create_individual("paris")
        self.assertEqual("paris", individual.value)

    def test_create_negative_individual(self):
        individual = self.ontology.create_negative_individual("paris")
        self.assertEqual("paris", individual.value)

    def test_create_invalid_individual(self):
        ontology_without_string_predicate = self.empty_ontology
        with (self.assertRaises(OntologyError)):
            ontology_without_string_predicate.create_individual("kalle")

    def test_create_invalid_negative_individual(self):
        ontology_without_string_predicate = self.empty_ontology
        with (self.assertRaises(OntologyError)):
            ontology_without_string_predicate.create_negative_individual("kalle")

    def test_get_sort(self):
        individual = self.ontology.create_individual("paris")
        self.assertEqual(self.sort_city, individual.sort)

    def test_equality(self):
        individual1 = self.ontology.create_individual("paris")
        individual2 = self.ontology.create_individual("paris")
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(individual1, individual2)

    def test_non_equality_due_to_value(self):
        other_individual = self.ontology.create_individual("london")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.individual_paris, other_individual)

    def test_non_equality_due_to_sort(self):
        other_individual = self.ontology.create_individual("paris", sort=StringSort())
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.individual_paris, other_individual)

    def test_non_equality_due_to_polarity(self):
        positive_individual = self.ontology.create_individual("paris")
        negative_individual = self.ontology.create_negative_individual("paris")
        self.assertNotEqual(positive_individual, negative_individual)
        self.assertNotEqual(negative_individual, positive_individual)

    def test_non_equality_with_non_individual(self):
        non_individual = "paris"
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.individual_paris, non_individual)

    def test_unicode_for_individual_of_custom_sort(self):
        self.assertEqual("paris", str(self.individual_paris))

    def test_unicode_for_negative_individual_of_custom_sort(self):
        self.assertEqual("~paris", str(self.individual_not_paris))

    def test_individual_is_positive(self):
        self.assertTrue(self.individual_paris.is_positive())

    def test_negative_individual_is_not_positive(self):
        self.assertFalse(self.individual_not_paris.is_positive())

    def test_individual_is_hashable(self):
        set_ = set()
        set_.add(self.individual_paris)

    def test_negative_individual_is_hashable(self):
        set_ = set()
        set_.add(self.individual_not_paris)

    def test_negate_positive_individual(self):
        self.assertFalse(self.individual_paris.negate().is_positive())

    def test_negate_negative_individual(self):
        self.assertTrue(self.individual_not_paris.negate().is_positive())

    def test_value_as_json_object(self):
        self.given_an_individual_of_mock_sort("mock_value")
        self.given_value_as_json_object_in_mock_sort_returns("mock_value", "mock_value_as_json_object")
        self.when_call_value_as_json_object_for_individual()
        self.then_result_is("mock_value_as_json_object")

    def given_an_individual_of_mock_sort(self, value):
        self._mock_sort = Mock(spec=Sort)
        self._individual = Individual("mock_ontology", value, self._mock_sort)

    def given_value_as_json_object_in_mock_sort_returns(self, expected_value, value_as_json_object):
        def mock_value_as_json_object(value):
            self.assertEqual(expected_value, value)
            return value_as_json_object

        self._mock_sort.value_as_json_object.side_effect = mock_value_as_json_object

    def when_call_value_as_json_object_for_individual(self):
        self._actual_result = self._individual.value_as_json_object()


class IsIndividualTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_individual_false(self):
        self.assertFalse(self.proposition_dest_city_paris.is_individual())

    def test_is_individual_true(self):
        self.assertTrue(self.individual_paris.is_individual())
