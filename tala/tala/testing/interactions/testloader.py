from tala.testing.interactions.suite import TestSuite
from tala.testing.interactions.testcase import InteractionTestingTestCase


class InteractionTestingLoader(object):
    def __init__(self, url):
        self._url = url

    def load_interaction_tests(self, interaction_testing_file, selected_tests=None):
        suite = TestSuite(interaction_testing_file.filename)
        tests = interaction_testing_file.tests
        if selected_tests:
            tests = interaction_testing_file.filter_tests_by_name(selected_tests)
        for test in tests:
            test_case = InteractionTestingTestCase(test, self._url)
            suite.addTest(test_case)
        return suite
