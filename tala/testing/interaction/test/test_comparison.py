from tala.testing.interaction.comparison import StringComparison


class TestStringComparison:
    def test_basic_comparison_success(self):
        self.given_actual_string("hej")
        self.given_expected_string("hej")
        self.when_comparing()
        self.then_comparison_is_successful()

    def given_actual_string(self, string):
        self._actual_string = string

    def given_expected_string(self, string):
        self._expected_string = string

    def when_comparing(self):
        self._comparison = StringComparison(self._actual_string, self._expected_string).match()

    def then_comparison_is_successful(self):
        assert self._comparison is not None
        assert self._comparison.group(0) == self._actual_string

    def test_basic_comparison_success_wildcard(self):
        self.given_actual_string("hej")
        self.given_expected_string("h*j")
        self.when_comparing()
        self.then_comparison_is_successful()

    def test_basic_comparison_failure(self):
        self.given_actual_string("haj")
        self.given_expected_string("hej")
        self.when_comparing()
        self.then_comparison_is_failing()

    def then_comparison_is_failing(self):
        assert self._comparison is None

    def test_basic_comparison_failure_wildcard(self):
        self.given_actual_string("haj")
        self.given_expected_string("he*")
        self.when_comparing()
        self.then_comparison_is_failing()

    def test_succesful_multi_alt_comparison(self):
        self.given_actual_string("hej")
        self.given_expected_string(["haj", "hej"])
        self.when_comparing()
        self.then_comparison_is_successful()

    def test_succesful_multi_alt_comparison_wildcard(self):
        self.given_actual_string("hej")
        self.given_expected_string(["*aj", "*ej"])
        self.when_comparing()
        self.then_comparison_is_successful()

    def test_failing_multi_alt_comparison(self):
        self.given_actual_string("huj")
        self.given_expected_string(["haj", "hej"])
        self.when_comparing()
        self.then_comparison_is_failing()

    def test_failing_multi_alt_comparison_wildcard(self):
        self.given_actual_string("huj")
        self.given_expected_string(["ha*", "he*"])
        self.when_comparing()
        self.then_comparison_is_failing()

    def test_basic_mismatch_output(self):
        self.given_actual_string("hej")
        self.given_expected_string("haj")
        self.when_getting_mismatch_description()
        self.then_mismatch_description_is('\nexpected: "haj"\n            ^\nbut got:  "hej"\n            ^')

    def when_getting_mismatch_description(self):

        comparison = StringComparison(self._actual_string, self._expected_string)
        comparison.match()
        self._mismatch = comparison.mismatch_description()

    def then_mismatch_description_is(self, expected):
        assert expected == self._mismatch

    def test_wildcard_mismatch_output(self):
        self.given_actual_string("hej")
        self.given_expected_string("ha*")
        self.when_getting_mismatch_description()
        self.then_mismatch_description_is('\nexpected: "ha*"\n            ^\nbut got:  "hej"\n            ^')

    def test_multi_alt_mismatch_output(self):
        self.given_actual_string("huj")
        self.given_expected_string(["haj", "hej"])
        self.when_getting_mismatch_description()
        self.then_mismatch_description_is('\nexpected: "hej"\n            ^\nbut got:  "huj"\n            ^')

    def test_multi_alt_wildcard_mismatch_output(self):
        self.given_actual_string("huj")
        self.given_expected_string(["ha*", "he*"])
        self.when_getting_mismatch_description()
        self.then_mismatch_description_is('\nexpected: "he*"\n            ^\nbut got:  "huj"\n            ^')
