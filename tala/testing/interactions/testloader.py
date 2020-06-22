import unittest

from tala.testing.interactions.testcase import InteractionTestingTestCase


class InteractionTestingLoader(object):
    def __init__(self, url):
        self._url = url

    def load_interaction_tests(self, interaction_testing_file, selected_tests=[]):
        suite = unittest.TestSuite()
        tests = interaction_testing_file.tests
        if selected_tests:
            tests = interaction_testing_file.filter_tests_by_name(selected_tests)
        for test in tests:
            test_case = self._create_test_case(test, self._url)
            suite.addTest(test_case)
        return suite

    def _create_test_case(self, test, environment_or_url):
        return InteractionTestingTestCase(test, environment_or_url)
