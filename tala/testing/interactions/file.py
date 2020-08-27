import codecs
from fnmatch import fnmatch
import warnings

from tala.testing.interactions.compiler import InteractionTestCompiler
from tala.testing.interactions.named_test import InteractionTest


class InteractionTestingFile:
    def __init__(self, filename, tests):
        self.filename = filename
        self.tests = tests

    def add(self, name, interaction_events):
        test = InteractionTest(self.filename, name, interaction_events)
        self.tests.append(test)

    def __iter__(self):
        for test in self.tests:
            yield test

    def __getitem__(self, index):
        return self.tests[index]

    def __len__(self):
        return len(self.tests)

    def __repr__(self):
        return "InteractionTestingFile(filename=%s, tests=%r)" % (self.filename, self.tests)

    def pop_first(self):
        return self.tests.pop(0)

    def select_tests(self, patterns):
        warnings.warn(
            "This method modifies the tests internally in a destructive way. Use filter_tests_by_name() "
            "instead, which creates and returns a new list with the tests that match.", DeprecationWarning
        )
        self.tests = self.filter_tests_by_name(patterns)

    def filter_tests_by_name(self, patterns):
        filtered_tests = []
        for test in self.tests:
            for selected_test in patterns:
                if fnmatch(test.name, selected_test):
                    filtered_tests.append(test)
        return filtered_tests

    @staticmethod
    def _load_tests_from_file(path):
        with codecs.open(path, 'r', encoding='utf-8') as f:
            return InteractionTestCompiler().compile_interaction_tests(path, f)

    @staticmethod
    def from_path(path):
        tests = InteractionTestingFile._load_tests_from_file(path)
        return InteractionTestingFile(path, tests)
