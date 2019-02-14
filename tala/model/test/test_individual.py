from tala.model.ontology import Ontology, OntologyError
from tala.model.predicate import Predicate
from tala.model.sort import RealSort, IntegerSort, StringSort, CustomSort, ImageSort, WebviewSort, DateTimeSort
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
        }
        individuals = {
            "paris": CustomSort(self.ontology_name, "city"),
            "london": CustomSort(self.ontology_name, "city"),
        }
        actions = set([])
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

        self.empty_ontology = Ontology("empty_ontology", {}, {}, {}, set([]))

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
        self.assertEquals("1234.0", unicode(real_individual))

    def test_integer_individual_unicode(self):
        self.assertEquals("1234", unicode(self.integer_individual))

    def test_string_individual_unicode(self):
        self.assertEquals('"a string"', unicode(self.string_individual))

    def test_image_individual_unicode(self):
        self.assertEquals('image("http://mymap.com/map.png")', unicode(self.image_individual))

    def test_webview_individual_unicode(self):
        self.assertEquals(u'webview("http://mymap.com/map.html")', unicode(self.webview_individual))

    def test_datetime_individual_unicode(self):
        self.assertEquals('datetime(2018-04-11T22:00:00.000Z)', unicode(self.datetime_individual))

    def test_create_individual(self):
        individual = self.ontology.create_individual("paris")
        self.assertEquals("paris", individual.getValue())

    def test_create_negative_individual(self):
        individual = self.ontology.create_negative_individual("paris")
        self.assertEquals("paris", individual.getValue())

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
        self.assertEquals(self.sort_city, individual.getSort())

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
        self.assertEquals("paris", unicode(self.individual_paris))

    def test_unicode_for_negative_individual_of_custom_sort(self):
        self.assertEquals("~paris", unicode(self.individual_not_paris))

    def test_individual_is_positive(self):
        self.assertTrue(self.individual_paris.is_positive())

    def test_negative_individual_is_not_positive(self):
        self.assertFalse(self.individual_not_paris.is_positive())

    def test_hashing(self):
        s = set()
        s.add(self.individual_paris)

    def test_negate_positive_individual(self):
        self.assertFalse(self.individual_paris.negate().is_positive())

    def test_negate_negative_individual(self):
        self.assertTrue(self.individual_not_paris.negate().is_positive())


class ValueAsJsonObjectTestCase(IndividualTestBase):
    def test_custom_sort(self):
        self.when_get_value_as_json_object(self.individual_paris)
        self.then_result_is({"value": "paris"})

    def when_get_value_as_json_object(self, proposition):
        self._actual_result = proposition.value_as_json_object()

    def test_string(self):
        self.when_get_value_as_json_object(self.string_individual)
        self.then_result_is({"value": "a string"})

    def test_image(self):
        self.when_get_value_as_json_object(self.image_individual)
        self.then_result_is({"value": "http://mymap.com/map.png"})

    def test_webview(self):
        self.when_get_value_as_json_object(self.webview_individual)
        self.then_result_is({"value": "http://mymap.com/map.html"})

    def test_datetime(self):
        self.when_get_value_as_json_object(self.datetime_individual)
        self.then_result_is({"value": "2018-04-11T22:00:00.000Z"})


class IsIndividualTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_individual_false(self):
        self.assertFalse(self.proposition_dest_city_paris.is_individual())

    def test_is_individual_true(self):
        self.assertTrue(self.individual_paris.is_individual())
