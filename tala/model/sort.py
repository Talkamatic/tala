import iso8601
import urlparse
import mimetypes
import magic
import urllib

from tala.model.semantic_object import OntologySpecificSemanticObject, SemanticObject
from tala.model.image import Image
from tala.model.webview import Webview
from tala.model.date_time import DateTime

BOOLEAN = "boolean"
INTEGER = "integer"
DATETIME = "datetime"
REAL = "real"
STRING = "string"
IMAGE = "image"
DOMAIN = "domain"
WEBVIEW = "webview"


class Sort(SemanticObject):
    def __init__(self, name, dynamic=False):
        self._name = name
        self._dynamic = dynamic

    def get_name(self):
        return self._name

    @property
    def name(self):
        return self._name

    def is_dynamic(self):
        return self._dynamic

    def is_builtin(self):
        return False

    def is_boolean_sort(self):
        return self._name == BOOLEAN

    def is_datetime_sort(self):
        return self._name == DATETIME

    def is_real_sort(self):
        return self._name == REAL

    def is_integer_sort(self):
        return self._name == INTEGER

    def is_string_sort(self):
        return self._name == STRING

    def is_domain_sort(self):
        return self._name == DOMAIN

    def is_image_sort(self):
        return self._name == IMAGE

    def is_webview_sort(self):
        return self._name == WEBVIEW

    def __unicode__(self):
        return "Sort(%r, dynamic=%r)" % (self._name, self._dynamic)

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self._name, self._dynamic))

    def __eq__(self, other):
        try:
            return (other.get_name() == self.get_name() and other.is_dynamic() == self.is_dynamic())
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.get_name(), self.is_dynamic()))


class BuiltinSort(Sort):
    def is_builtin(self):
        return True

    def normalize_value(self, value):
        return value


class InvalidValueException(Exception):
    pass


class RealSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, REAL)

    def normalize_value(self, value):
        try:
            return float(value)
        except (ValueError, AttributeError, TypeError):
            raise InvalidValueException("Expected a real-number value but got '%s'." % value)


class IntegerSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, INTEGER)

    def normalize_value(self, value):
        try:
            return int(value)
        except (ValueError, AttributeError, TypeError):
            raise InvalidValueException("Expected an integer value but got '%s'." % value)


class StringSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, STRING)

    def normalize_value(self, value):
        if isinstance(value, basestring):
            return value
        else:
            raise InvalidValueException(
                "Expected a string value but got %s of type %s." % (value, value.__class__.__name__)
            )


class ImageSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, IMAGE)

    def normalize_value(self, value):
        if isinstance(value, Image):
            if isinstance(value.url,
                          (str, unicode)) and "http" in value.url and self._has_mime_type(value.url, "image"):
                return value
            else:
                raise InvalidValueException("Expected an image URL but got '%s'." % value.url)
        else:
            raise InvalidValueException("Expected an image object but got '%s'." % value)

    def _has_mime_type(self, value, expected_mime_type):
        mime_type = self._get_mime_type_from_url(value)
        if mime_type:
            return mime_type.startswith(expected_mime_type + "/")
        else:
            return False

    def _get_mime_type_from_url(self, url):
        path = urlparse.urlparse(url).path
        mime_type, mime_subtype = mimetypes.guess_type(path)
        if not mime_type:
            try:
                filepath, _ = urllib.urlretrieve(url)
            except IOError:
                return None
            print "filepath=", filepath
            mime_type = magic.from_file(filepath, mime=True)
        return mime_type


class WebviewSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, WEBVIEW)

    def normalize_value(self, value):
        if isinstance(value, Webview):
            if isinstance(value.url, (str, unicode)) and "http" in value.url:
                return value
            else:
                raise InvalidValueException("Expected a webview URL but got '%s'." % value.url)
        else:
            raise InvalidValueException("Expected a webview object but got '%s'." % value)


class BooleanSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, BOOLEAN)

    def normalize_value(self, value):
        if value is True or value is False:
            return value
        else:
            raise InvalidValueException("Expected a boolean value but got '%s'." % value)


class DomainSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, DOMAIN)


class DateTimeSort(BuiltinSort):
    def __init__(self):
        BuiltinSort.__init__(self, DATETIME)

    def normalize_value(self, value):
        if isinstance(value, DateTime):
            try:
                iso8601.parse_date(value.iso8601_string)
            except iso8601.ParseError:
                raise InvalidValueException(
                    "Expected a datetime value in ISO 8601 format but got '%s'." % value.iso8601_string
                )
            return value
        else:
            raise InvalidValueException("Expected a datetime object but got '%s'." % value)


class CustomSort(Sort, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, name, dynamic=False):
        Sort.__init__(self, name, dynamic=dynamic)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def __eq__(self, other):
        try:
            return (Sort.__eq__(self, other) and self.ontology_name == other.ontology_name)
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.ontology_name, Sort.__hash__(self)))


class BuiltinSortRepository(object):
    _repository = {
        BOOLEAN: BooleanSort(),
        INTEGER: IntegerSort(),
        DATETIME: DateTimeSort(),
        REAL: RealSort(),
        STRING: StringSort(),
        IMAGE: ImageSort(),
        DOMAIN: DomainSort(),
        WEBVIEW: WebviewSort()
    }

    @classmethod
    def has_sort(cls, name):
        return name in cls._repository

    @classmethod
    def get_sort(cls, name):
        if cls.has_sort(name):
            return cls._repository[name]
        else:
            raise UndefinedSort("Expected a built-in sort but got '%s'." % name)


class UndefinedSort(Exception):
    pass
