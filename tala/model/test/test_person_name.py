# coding: utf-8

import unittest

from tala.model.person_name import PersonName


class PersonNameTestCase(unittest.TestCase):
    def test_unicode(self):
        self.when_get_unicode_string(PersonName("Åsa"))
        self.then_result_is('person_name(Åsa)')

    def when_get_unicode_string(self, person_name):
        self._actual_result = str(person_name)

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._actual_result)

    def test_repr(self):
        self.when_get_repr(PersonName("Åsa"))
        self.then_result_is("PersonName(%r)" % "Åsa")

    def when_get_repr(self, person_name):
        self._actual_result = repr(person_name)

    def test_str_does_not_crash_with_unicode_string(self):
        self.when_get_str_string(PersonName("Åsa"))
        self.then_result_is('person_name(Åsa)')

    def when_get_str_string(self, person_name):
        self._actual_result = str(person_name)
