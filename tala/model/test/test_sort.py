import unittest

from mock import patch
import pytest

from tala.model.ontology import Ontology, SortDoesNotExistException
from tala.model.predicate import Predicate
from tala.model.sort import StringSort, ImageSort, WebviewSort, BooleanSort, RealSort, CustomSort, IntegerSort, DateTimeSort, InvalidValueException, BuiltinSortRepository, UndefinedSort, DomainSort, BOOLEAN, INTEGER, DATETIME, REAL, STRING, IMAGE, DOMAIN, WEBVIEW
import tala.model.sort
from tala.model.image import Image
from tala.model.webview import Webview
from tala.model.date_time import DateTime
from tala.testing.utils import EqualityAssertionTestCaseMixin


class SortTestCase(unittest.TestCase):
    def setUp(self):
        self._sort = None
        self.ontology_name = None

    def _create_predicate(self, *args, **kwargs):
        return Predicate(self.ontology_name, *args, **kwargs)

    def when_normalize_value(self, value):
        self._actual_result = self._sort.normalize_value(value)

    def when_normalize_value_then_exception_is_raised(self, value, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            self._sort.normalize_value(value)

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._actual_result)


class SortTests(SortTestCase, EqualityAssertionTestCaseMixin):
    def setUp(self):
        self._create_ontology()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = set()
        sorts = {
            CustomSort(self.ontology_name, "city", dynamic=False),
            CustomSort(self.ontology_name, "city_type", dynamic=False),
        }
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_createSort(self):
        sort = self.ontology.get_sort("city")
        self.assertEquals("city", sort.get_name())

    def test_createSort_yields_exception_for_unknown_sort(self):
        with self.assertRaises(SortDoesNotExistException):
            self.ontology.get_sort("sdkjfhskdjf")

    def test_sort_unicode(self):
        self.assertEquals("Sort('city', dynamic=False)", unicode(CustomSort(self.ontology_name, "city")))

    def test_sort_equality(self):
        sort1 = self.ontology.get_sort("city")
        sort2 = self.ontology.get_sort("city")
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(sort1, sort2)

    def test_sort_inequality(self):
        sort1 = self.ontology.get_sort("city")
        sort2 = self.ontology.get_sort("city_type")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(sort1, sort2)

    def test_sorts_hashable(self):
        {self.ontology.get_sort("city"), RealSort()}


class StringSortTests(SortTestCase):
    def setUp(self):
        self._create_ontology()
        self._sort = StringSort()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("number_to_call", StringSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_string_individual(self):
        individual = self.ontology.create_individual('"a string"')
        self.assertEquals("a string", individual.getValue())
        self.assertEquals(StringSort(), individual.getSort())

    def test_string_individual_unicode(self):
        individual = self.ontology.create_individual(u'"a unicode string"')
        self.assertEquals(u"a unicode string", individual.getValue())
        self.assertEquals(StringSort(), individual.getSort())

    def test_string_individual_unicode_method(self):
        individual = self.ontology.create_individual('"a string"')
        self.assertEquals('"a string"', unicode(individual))

    def test_normalize_base_case(self):
        self.when_normalize_value("a string")
        self.then_result_is("a string")

    def test_exception_when_normalize_non_string_value(self):
        self.when_normalize_value_then_exception_is_raised(
            123, InvalidValueException, "Expected a string value but got 123 of type int."
        )


class ImageSortTests(SortTestCase):
    def setUp(self):
        self._create_ontology()
        self._sort = ImageSort()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("map", ImageSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_create_individual(self):
        individual = self.ontology.create_individual(Image("http://image.com/image.png"))
        self.assertEquals(Image("http://image.com/image.png"), individual.getValue())
        self.assertTrue(individual.getSort().is_image_sort())

    def test_is_not_dynamic(self):
        image_sort = ImageSort()
        self.assertFalse(image_sort.is_dynamic())

    def test_normalize_static_url_of_image_mime_type(self):
        self.when_normalize_value(Image("http://image.com/image.png"))
        self.then_result_is(Image("http://image.com/image.png"))

    @patch("%s.magic" % tala.model.sort.__name__)
    @patch("%s.urllib" % tala.model.sort.__name__)
    def test_normalize_dynamic_url_of_image_mime_type(self, mock_urllib, mock_magic):
        self.given_get_mime_type_of_url_returns(mock_magic, mock_urllib, "image/jpeg")
        self.when_normalize_value(Image("http://mock.domain/generate_image"))
        self.then_result_is(Image("http://mock.domain/generate_image"))

    def given_get_mime_type_of_url_returns(self, mock_magic, mock_urllib, mime_type):
        mock_urllib.urlretrieve.return_value = "mock_filepath", "mock_headers"
        mock_magic.from_file.return_value = mime_type

    def test_exception_when_normalize_non_url(self):
        self.when_normalize_value_then_exception_is_raised(
            Image("non_url"), InvalidValueException, "Expected an image URL but got 'non_url'."
        )

    def test_exception_when_normalize_non_image(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_image", InvalidValueException, "Expected an image object but got 'non_image'."
        )

    def test_exception_when_normalize_static_url_of_non_image_mime_type(self):
        self.when_normalize_value_then_exception_is_raised(
            Image("http://nonimage.com/nonimage.html"), InvalidValueException,
            "Expected an image URL but got 'http://nonimage.com/nonimage.html'."
        )

    @patch("%s.magic" % tala.model.sort.__name__)
    @patch("%s.urllib" % tala.model.sort.__name__)
    def test_exception_when_normalize_dynamic_url_of_non_image_mime_type(self, mock_urllib, mock_magic):
        self.given_get_mime_type_of_url_returns(mock_magic, mock_urllib, "text/html")
        self.when_normalize_value_then_exception_is_raised(
            Image("http://mock.domain/generate_html"), InvalidValueException,
            "Expected an image URL but got 'http://mock.domain/generate_html'."
        )


class WebviewSortTests(SortTestCase):
    def setUp(self):
        self._create_ontology()
        self._sort = WebviewSort()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("interactive_map", WebviewSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_create_individual(self):
        individual = self.ontology.create_individual(Webview("http://maps.com/map.html"))
        self.assertEquals(Webview("http://maps.com/map.html"), individual.getValue())
        self.assertEquals(WebviewSort(), individual.getSort())

    def test_is_not_dynamic(self):
        image_sort = WebviewSort()
        self.assertFalse(image_sort.is_dynamic())

    def test_normalize_base_case(self):
        self.when_normalize_value(Webview("http://maps.com/map.html"))
        self.then_result_is(Webview("http://maps.com/map.html"))

    def test_exception_when_normalize_non_webview_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_webview_value", InvalidValueException, "Expected a webview object but got 'non_webview_value'."
        )

    def test_exception_when_normalize_non_url(self):
        self.when_normalize_value_then_exception_is_raised(
            Webview("non_url"), InvalidValueException, "Expected a webview URL but got 'non_url'."
        )


class BooleanSortTestCase(SortTestCase):
    def setUp(self):
        self._create_ontology()
        self._sort = BooleanSort()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("need_visa", BooleanSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_create_individual(self):
        individual = self.ontology.create_individual(True)
        self.assertEqual(True, individual.getValue())
        self.assertEqual(BooleanSort(), individual.getSort())

    def test_normalize_true(self):
        self.when_normalize_value(True)
        self.then_result_is(True)

    def test_normalize_false(self):
        self.when_normalize_value(False)
        self.then_result_is(False)

    def test_exception_when_normalize_non_boolean_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_boolean_value", InvalidValueException, "Expected a boolean value but got 'non_boolean_value'."
        )


class IntegerSortTestCase(SortTestCase):
    def setUp(self):
        self._sort = IntegerSort()

    def test_normalize_base_case(self):
        self.when_normalize_value("123")
        self.then_result_is(123)

    def test_exception_when_normalize_non_integer_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_integer_value", InvalidValueException, "Expected an integer value but got 'non_integer_value'."
        )


class RealSortTestCase(SortTestCase):
    def setUp(self):
        self._sort = RealSort()

    def test_normalize_base_case(self):
        self.when_normalize_value("123.4")
        self.then_result_is(123.4)

    def test_exception_when_normalize_non_real_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_real_value", InvalidValueException, "Expected a real-number value but got 'non_real_value'."
        )


class DateTimeSortTestCase(SortTestCase):
    def setUp(self):
        self._sort = DateTimeSort()

    def test_normalize_base_case(self):
        self.when_normalize_value(DateTime("2018-03-20T22:00:00.000Z"))
        self.then_result_is(DateTime("2018-03-20T22:00:00.000Z"))

    def test_exception_when_normalize_datetime_object_with_non_iso8601_value(self):
        self.when_normalize_value_then_exception_is_raised(
            DateTime("non_iso8601_value"), InvalidValueException,
            "Expected a datetime value in ISO 8601 format but got 'non_iso8601_value'."
        )

    def test_exception_when_normalize_non_datetime_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_datetime_value", InvalidValueException, "Expected a datetime object but got 'non_datetime_value'."
        )


class TestBuiltinSortRepository(object):
    @pytest.mark.parametrize("name", [BOOLEAN, INTEGER, DATETIME, REAL, STRING, IMAGE, DOMAIN, WEBVIEW])
    def test_has_sort_true(self, name):
        self.when_invoking_has_sort(name)
        self.then_result_is(True)

    def when_invoking_has_sort(self, name):
        self._actual_result = BuiltinSortRepository.has_sort(name)

    def then_result_is(self, expected_result):
        assert expected_result == self._actual_result

    def test_has_sort_false(self):
        self.when_invoking_has_sort("undefined_sort")
        self.then_result_is(False)

    @pytest.mark.parametrize(
        "name,expected_class", [(BOOLEAN, BooleanSort), (INTEGER, IntegerSort), (DATETIME, DateTimeSort),
                                (REAL, RealSort), (STRING, StringSort), (IMAGE, ImageSort), (DOMAIN, DomainSort),
                                (WEBVIEW, WebviewSort)]
    )
    def test_get_sort_successful(self, name, expected_class):
        self.when_invoking_get_sort(name)
        self.then_result_is_instance_of(expected_class)

    def when_invoking_get_sort(self, name):
        self._actual_result = BuiltinSortRepository.get_sort(name)

    def then_result_is_instance_of(self, expected_class):
        assert expected_class == self._actual_result.__class__

    def test_get_sort_unsuccessful(self):
        self.when_invoking_get_sort_then_exception_is_raised(
            "undefined_sort", UndefinedSort, "Expected a built-in sort but got 'undefined_sort'."
        )

    def when_invoking_get_sort_then_exception_is_raised(self, name, expected_class, expected_message):
        with pytest.raises(expected_class) as excinfo:
            BuiltinSortRepository.get_sort(name)
        assert expected_message == str(excinfo.value)
