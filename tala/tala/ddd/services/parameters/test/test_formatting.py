import unittest

from tala.ddd.services.parameters.formatting import ParameterBindingsFormatter
from tala.ddd.services.parameters.binding import SingleInstanceParameterBinding
from tala.ddd.services.service_interface import ServiceParameter


class FormattingTestCase(unittest.TestCase):
    def test_to_proposition_list_base_case(self):
        self.given_bindings([
            SingleInstanceParameterBinding(ServiceParameter("mock_predicate_name"), "mock_value", "mock_proposition")
        ])
        self.when_to_proposition_list_is_called()
        self.then_result_is(["mock_proposition"])

    def given_bindings(self, bindings):
        self._bindings = bindings

    def then_result_is(self, expected_result):
        self.assertEqual(expected_result, self._actual_result)

    def when_to_proposition_list_is_called(self):
        self._actual_result = ParameterBindingsFormatter.to_proposition_list(self._bindings)

    def test_to_proposition_list_excludes_optional_unbound_propositions(self):
        self.given_bindings([
            SingleInstanceParameterBinding(
                ServiceParameter("mock_predicate_name", is_optional=True), value=None, proposition=None
            )
        ])
        self.when_to_proposition_list_is_called()
        self.then_result_is([])

    def test_to_values_base_case(self):
        self.given_bindings([
            SingleInstanceParameterBinding(ServiceParameter("mock_predicate_name"), "mock_value", "mock_proposition")
        ])
        self.when_to_values_is_called()
        self.then_result_is(["mock_value"])

    def when_to_values_is_called(self):
        self._actual_result = ParameterBindingsFormatter.to_values(self._bindings)

    def test_result_has_values_includes_optional_unknown_facts(self):
        self.given_bindings([
            SingleInstanceParameterBinding(
                ServiceParameter("dest_city", is_optional=True), value=None, proposition=None
            )
        ])
        self.when_to_values_is_called()
        self.then_result_is([None])
