import sys
import unittest

from tala.testing.interactions.file import InteractionTestingFile
from tala.testing.interactions.testcase import InteractionTestingTestCase
from tala.testing.endurance.named_test import EnduranceInteractionTest


class EnduranceTestRunner(object):
    FAILURE_EXIT_CODE = 5

    def __init__(self, test_files, duration, environment_or_url):
        self._tests = self._all_tests_from_files(test_files)
        self._duration = duration
        self._environment_or_url = environment_or_url
        self._endurance_interaction_test = EnduranceInteractionTest(self._tests, self._duration)

    @staticmethod
    def _all_tests_from_files(test_files):
        test_files = [InteractionTestingFile.from_path(test_file) for test_file in test_files]
        for test_file in test_files:
            for test in test_file.tests:
                yield test

    def run(self):
        test_case = InteractionTestingTestCase(self._endurance_interaction_test,
                                               self._environment_or_url)
        suite = unittest.TestSuite()
        suite.addTest(test_case)
        successful = self._run(suite)
        if not successful:
            sys.exit(self.FAILURE_EXIT_CODE)

    @staticmethod
    def _run(suite):
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        successful = result.wasSuccessful()
        return successful

    def stop(self):
        self._endurance_interaction_test.stop()
