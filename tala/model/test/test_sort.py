from unittest.mock import patch
import pytest

from tala.model.ontology import Ontology, SortDoesNotExistException
from tala.model.predicate import Predicate
from tala.model.sort import Sort, StringSort, ImageSort, WebviewSort, BooleanSort, RealSort, CustomSort, IntegerSort, \
    DateTimeSort, InvalidValueException, BuiltinSortRepository, UndefinedSort, DomainSort, PersonNameSort, BOOLEAN, \
    INTEGER, DATETIME, PERSON_NAME, REAL, STRING, IMAGE, DOMAIN, WEBVIEW, UnsupportedValue
import tala.model.sort
from tala.model.image import Image
from tala.model.webview import Webview
from tala.model.date_time import DateTime
from tala.model.person_name import PersonName
from tala.testing.utils import EqualityAssertionTestCaseMixin


class SortTestCase(object):
    def setup_method(self):
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
        assert expected_result == self._actual_result

    def given_sort(self, sort):
        self._sort = sort

    def when_call_value_as_basic_type(self, value):
        self._actual_result = self._sort.value_as_basic_type(value)

    def when_call_value_from_basic_type(self, basic_value):
        self._actual_result = self._sort.value_from_basic_type(basic_value)

    def when_call_value_as_json_object(self, value):
        self._actual_result = self._sort.value_as_json_object(value)

    def when_call_grammar_entry(self, value, language_code):
        self._actual_result = self._sort.grammar_entry(value, language_code)


class TestSort(SortTestCase, EqualityAssertionTestCaseMixin):
    def setup_method(self):
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
        assert "city" == sort.get_name()

    def test_createSort_yields_exception_for_unknown_sort(self):
        with pytest.raises(SortDoesNotExistException):
            self.ontology.get_sort("sdkjfhskdjf")

    def test_sort_unicode(self):
        assert "Sort('city', dynamic=False)" == str(CustomSort(self.ontology_name, "city"))

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

    def test_value_as_basic_type_returns_value_by_default(self):
        self.given_sort(CustomSort(self.ontology_name, "city", dynamic=False))
        self.when_call_value_as_basic_type("mock_value")
        self.then_result_is("mock_value")

    def test_value_from_basic_type_returns_basic_value_by_default(self):
        self.given_sort(CustomSort(self.ontology_name, "city", dynamic=False))
        self.when_call_value_from_basic_type("mock_value")
        self.then_result_is("mock_value")

    @pytest.mark.parametrize(
        "value,expected_sort", [(123.50, RealSort()), (123, IntegerSort()),
                                (Image("http://www.internet.org/image.png"), ImageSort()),
                                (Webview("http://maps.com/map.html"), WebviewSort())]
    )
    def test_from_value_returns_expected_sort(self, value, expected_sort):
        self.when_call_from_value(value)
        self.then_result_is(expected_sort)

    def when_call_from_value(self, value):
        self._actual_result = Sort.from_value(value)

    def test_from_value_raises_exception_for_unsupported_value(self):
        with pytest.raises(UnsupportedValue, match="Expected a supported value but got 'None'"):
            self.when_call_from_value(None)

    @patch("{}.Sort.value_as_basic_type".format(tala.model.sort.__name__))
    def test_value_as_json_object_uses_value_as_basic_type(self, mock_value_as_basic_type):
        self.given_a_sort()
        self.when_call_value_as_json_object("mock_value")
        self.then_result_is({"value": mock_value_as_basic_type.return_value})

    def given_a_sort(self, name="mock_name"):
        self._sort = Sort(name)


class TestStringSort(SortTestCase):
    def setup_method(self):
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
        assert "a string" == individual.value
        assert StringSort() == individual.sort

    def test_string_individual_unicode(self):
        individual = self.ontology.create_individual('"a unicode string"')
        assert "a unicode string" == individual.value
        assert StringSort() == individual.sort

    def test_string_individual_unicode_method(self):
        individual = self.ontology.create_individual('"a string"')
        assert '"a string"' == str(individual)

    def test_normalize_base_case(self):
        self.when_normalize_value("a string")
        self.then_result_is("a string")

    def test_exception_when_normalize_non_string_value(self):
        self.when_normalize_value_then_exception_is_raised(
            123, InvalidValueException, "Expected a string value but got 123 of type int."
        )


class TestImageSort(SortTestCase):
    def setup_method(self):
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
        assert Image("http://image.com/image.png") == individual.value
        assert individual.sort.is_image_sort()

    def test_is_not_dynamic(self):
        image_sort = ImageSort()
        assert not image_sort.is_dynamic()

    def test_normalize_static_url_of_image_mime_type(self):
        self.when_normalize_value(Image("http://image.com/image.png"))
        self.then_result_is(Image("http://image.com/image.png"))

    @patch("%s.mimetypes" % tala.model.sort.__name__)
    @patch("%s.urllib" % tala.model.sort.__name__)
    def test_normalize_dynamic_url_of_image_mime_type(self, mock_urllib, mock_mimetypes):
        self.given_get_mime_type_of_url_returns(mock_mimetypes, mock_urllib, "image/jpeg")
        self.given_urllib_parsed_path_is(mock_urllib, "/generate_image")
        self.when_normalize_value(Image("http://mock.domain/generate_image"))
        self.then_result_is(Image("http://mock.domain/generate_image"))

    def given_get_mime_type_of_url_returns(self, mock_mimetypes, mock_urllib, mime_type):
        mock_urllib.request.urlretrieve.return_value = "mock_filepath", "mock_headers"
        mock_mimetypes.guess_type.return_value = mime_type, None

    def given_urllib_parsed_path_is(self, mock_urllib, path):
        mock_urllib.parse.urlparse.return_value.path = path

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

    @patch(f"{tala.model.sort.__name__}.mimetypes")
    @patch(f"{tala.model.sort.__name__}.urllib")
    def test_exception_when_normalize_dynamic_url_of_non_image_mime_type(self, mock_urllib, mock_mimetypes):
        self.given_get_mime_type_of_url_returns(mock_mimetypes, mock_urllib, "text/html")
        self.given_urllib_parsed_path_is(mock_urllib, "/generate_html")
        self.when_normalize_value_then_exception_is_raised(
            Image("http://mock.domain/generate_html"), InvalidValueException,
            "Expected an image URL but got 'http://mock.domain/generate_html'."
        )

    def test_value_as_basic_type(self):
        self.when_call_value_as_basic_type(Image("http://image.com/image.png"))
        self.then_result_is("http://image.com/image.png")

    def test_value_from_basic_type(self):
        self.when_call_value_from_basic_type("http://image.com/image.png")
        self.then_result_is(Image("http://image.com/image.png"))


class TestWebviewSort(SortTestCase):
    def setup_method(self):
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
        assert Webview("http://maps.com/map.html") == individual.value
        assert WebviewSort() == individual.sort

    def test_is_not_dynamic(self):
        image_sort = WebviewSort()
        assert not image_sort.is_dynamic()

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

    def test_value_as_basic_type(self):
        self.when_call_value_as_basic_type(Webview("http://maps.com/map.html"))
        self.then_result_is("http://maps.com/map.html")

    def test_value_from_basic_type(self):
        self.when_call_value_from_basic_type("http://maps.com/map.html")
        self.then_result_is(Webview("http://maps.com/map.html"))


class TestBooleanSort(SortTestCase):
    def setup_method(self):
        self._create_ontology()
        self._sort = BooleanSort()

    def _create_ontology(self):
        self.ontology_name = "mockup_ontology"
        predicates = {self._create_predicate("need_visa", BooleanSort())}
        sorts = set()
        individuals = {}
        actions = set()
        self.ontology = Ontology(self.ontology_name, sorts, predicates, individuals, actions)

    def test_created_individual_has_expected_value(self):
        self.given_created_individual_with_argument(True)
        self.when_call_getValue_of_individual()
        self.then_result_is(True)

    def given_created_individual_with_argument(self, value):
        self._individual = self.ontology.create_individual(value)

    def when_call_getValue_of_individual(self):
        self._actual_result = self._individual.value

    def test_created_individual_has_expected_sort(self):
        self.given_created_individual_with_argument(True)
        self.when_call_getSort_of_individual()
        self.then_result_is(BooleanSort())

    def when_call_getSort_of_individual(self):
        self._actual_result = self._individual.sort

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


class TestIntegerSort(SortTestCase):
    def setup_method(self):
        self._sort = IntegerSort()

    def test_normalize_base_case(self):
        self.when_normalize_value("123")
        self.then_result_is(123)

    def test_exception_when_normalize_non_integer_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_integer_value", InvalidValueException, "Expected an integer value but got 'non_integer_value'."
        )


class TestRealSort(SortTestCase):
    def setup_method(self):
        self._sort = RealSort()

    def test_normalize_base_case(self):
        self.when_normalize_value("123.4")
        self.then_result_is(123.4)

    def test_exception_when_normalize_non_real_value(self):
        self.when_normalize_value_then_exception_is_raised(
            "non_real_value", InvalidValueException, "Expected a real-number value but got 'non_real_value'."
        )


class TestDateTimeSort(SortTestCase):
    def setup_method(self):
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

    def test_value_as_basic_type(self):
        self.when_call_value_as_basic_type(DateTime("2018-03-20T22:00:00.000Z"))
        self.then_result_is("2018-03-20T22:00:00.000Z")

    def test_value_from_basic_type(self):
        self.when_call_value_from_basic_type("2018-03-20T22:00:00.000Z")
        self.then_result_is(DateTime("2018-03-20T22:00:00.000Z"))


class TestPersonName(SortTestCase):
    def setup_method(self):
        self._sort = PersonNameSort()

    def test_normalize_base_case(self):
        self.when_normalize_value(PersonName("John"))
        self.then_result_is(PersonName("John"))

    def test_normalize_from_string(self):
        self.when_normalize_value("John")
        self.then_result_is(PersonName("John"))

    def test_exception_when_normalize_non_person_name_value(self):
        self.when_normalize_value_then_exception_is_raised(
            10, InvalidValueException, "Expected a person name object but got 10 of type int."
        )

    def test_value_as_basic_type(self):
        self.when_call_value_as_basic_type(PersonName("John"))
        self.then_result_is("John")

    def test_value_from_basic_type(self):
        self.when_call_value_from_basic_type("John")
        self.then_result_is(PersonName("John"))


class TestBuiltinSortRepository(object):
    @pytest.mark.parametrize("name", [BOOLEAN, INTEGER, DATETIME, PERSON_NAME, REAL, STRING, IMAGE, DOMAIN, WEBVIEW])
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
                                (WEBVIEW, WebviewSort), (PERSON_NAME, PersonNameSort)]
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
