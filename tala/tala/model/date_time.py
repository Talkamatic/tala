from contextlib import contextmanager
import locale

import iso8601


@contextmanager
def setlocale(name):
    previous = locale.setlocale(locale.LC_ALL)
    try:
        yield locale.setlocale(locale.LC_ALL, name)
    finally:
        locale.setlocale(locale.LC_ALL, previous)


class DateTime(object):
    def __init__(self, iso8601_string):
        self._iso8601_string = iso8601_string

    @property
    def iso8601_string(self):
        return self._iso8601_string

    def __eq__(self, other):
        try:
            return other.iso8601_string == self.iso8601_string
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (other == self)

    def __str__(self):
        return "datetime(%s)" % self.iso8601_string

    def human_standard(self, locale="en_US.UTF-8"):
        if locale != "en_US.UTF-8":
            raise UnsupportedLocale("Expected a supported locale for datetime but got '%s'" % locale)
        datetime = iso8601.parse_date(self._iso8601_string)
        with setlocale(locale):
            human_standard_string = datetime.strftime("%m/%d/%Y %I:%M %p", )
        return human_standard_string

    def __repr__(self):
        return 'DateTime("%s")' % self._iso8601_string

    def __hash__(self):
        return 17 * hash(str(self)) + 7 * hash(self.__class__.__name__)


class UnsupportedLocale(Exception):
    pass
