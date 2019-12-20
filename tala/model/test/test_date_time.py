import unittest

from tala.model.date_time import DateTime


class DateTimeTestCase(unittest.TestCase):
    def test_unicode(self):
        self.when_get_unicode_string(DateTime("2018-04-11T22:00:00.000Z"))
        self.then_result_is('datetime(2018-04-11T22:00:00.000Z)')

    def when_get_unicode_string(self, date_time):
        self._actual_result = str(date_time)

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._actual_result)

    def test_human_standard(self):
        self.when_get_human_standard(DateTime("2018-04-11T22:00:00.000Z"))
        self.then_result_is("04/11/2018 10:00 PM")

    def when_get_human_standard(self, date_time):
        self._actual_result = date_time.human_standard()

    def test_repr(self):
        self.when_get_repr(DateTime("2018-04-11T22:00:00.000Z"))
        self.then_result_is('DateTime("2018-04-11T22:00:00.000Z")')

    def when_get_repr(self, date_time):
        self._actual_result = repr(date_time)
