from tala.ddd.files import ddd_files


class TestFiles:
    def setup_method(self):
        self._path = None
        self._result = None

    def test_ddd_files(self):
        self.given_path("ddds/mockup_travel")
        self.when_fetching_ddd_files()
        self.then_returns([
            'ddds/mockup_travel/__init__.py', 'ddds/mockup_travel/ddd.config.json', 'ddds/mockup_travel/domain.xml',
            'ddds/mockup_travel/http_service/http_service.py', 'ddds/mockup_travel/ontology.xml',
            'ddds/mockup_travel/service_interface.xml', 'ddds/mockup_travel/test/__init__.py',
            'ddds/mockup_travel/test/interaction_tests.json'
        ])

    def given_path(self, path):
        self._path = path

    def when_fetching_ddd_files(self):
        self._result = ddd_files(self._path)

    def then_returns(self, expected_result):
        actual_result = [str(actual) for actual in self._result]
        assert expected_result == sorted(actual_result), f"Expected {expected_result} but got {self._result}"
