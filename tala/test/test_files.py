import pytest

from tala.ddd.files import ddd_files


class TestFiles:
    def setup_method(self):
        self._path = None
        self._result = None

    @pytest.mark.skip
    def test_ddd_files(self):
        self.given_path("tdm/ddds/person_name")
        self.when_fetching_ddd_files()
        self.then_returns([
            'tdm/ddds/person_name/__init__.py', 'tdm/ddds/person_name/ddd.config.json',
            'tdm/ddds/person_name/device.py', 'tdm/ddds/person_name/domain.xml',
            'tdm/ddds/person_name/grammar/__init__.py', 'tdm/ddds/person_name/grammar/grammar_eng.xml',
            'tdm/ddds/person_name/http_service.py', 'tdm/ddds/person_name/ontology.xml',
            'tdm/ddds/person_name/service_interface.xml', 'tdm/ddds/person_name/test/interaction_tests_eng.txt'
        ])

    def given_path(self, path):
        self._path = path

    def when_fetching_ddd_files(self):
        self._result = ddd_files(self._path)

    def then_returns(self, expected_result):
        actual_result = [str(actual) for actual in self._result]
        assert expected_result == sorted(actual_result), f"Expected {expected_result} but got {self._result}"
