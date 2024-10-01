import unittest

from unittest.mock import Mock

from tala.model.proposition import Proposition
from tala.model.validation_result import ValidationResult, ValidationSuccess, ValidationFailure


class TestBase(unittest.TestCase):
    def setUp(self):
        self._validation_object = None
        self._result = None

    def when_accessing_is_successful(self):
        self._result = self._validation_object.is_successful

    def then_result_is(self, expected_result):
        self.assertEqual(self._result, expected_result)

    def when_calling_repr(self):
        self._result = repr(self._validation_object)


class ValidationResultTests(TestBase):
    def test_creation(self):
        self.given_created_object()
        self.when_accessing_is_successful_then_exception_is_raised_matching(
            NotImplementedError, "This property needs to be implemented in a subclass"
        )

    def given_created_object(self):
        self._validation_object = ValidationResult()

    def when_accessing_is_successful_then_exception_is_raised_matching(self, expected_exception, expected_message):
        with self.assertRaisesRegex(expected_exception, expected_message):
            self._result = self._validation_object.is_successful


class ValidationSuccessTests(TestBase):
    def test_is_successful_property_of_successful_result(self):
        self.given_created_object()
        self.when_accessing_is_successful()
        self.then_result_is(True)

    def given_created_object(self):
        self._validation_object = ValidationSuccess()

    def test_repr_of_successful_result(self):
        self.given_created_object()
        self.when_calling_repr()
        self.then_result_is("ValidationSuccess()")

    def test_eq_on_identical_objects(self):
        self.when_equaling(ValidationSuccess(), ValidationSuccess())
        self.then_result_is(True)

    def test_eq_on_instance_of_other_class(self):
        self.when_equaling(ValidationSuccess(), "non_validation_result")
        self.then_result_is(False)

    def when_equaling(self, first, second):
        self._result = first == second

    def test_ne_on_identical_objects(self):
        self.when_testing_not_equals(ValidationSuccess(), ValidationSuccess())
        self.then_result_is(False)

    def when_testing_not_equals(self, first, second):
        self._result = first != second

    def test_ne_on_instance_of_other_class(self):
        self.when_testing_not_equals(ValidationSuccess(), "non_validation_result")
        self.then_result_is(True)

    def test_ne_on_failure(self):
        self.when_testing_not_equals(ValidationSuccess(), ValidationFailure("a_reason", Mock(spec=Proposition)))
        self.then_result_is(True)

    def test_uniqueness_of_identical_objects(self):
        self.when_checking_length_of({ValidationSuccess(), ValidationSuccess()})
        self.then_result_is(1)

    def when_checking_length_of(self, validation_results):
        self._result = len(validation_results)

    def test_uniqueness_of_different_objects(self):
        self.when_checking_length_of({ValidationSuccess(), ValidationFailure("a_reason", Mock(spec=Proposition))})
        self.then_result_is(2)


class ValidationFailureTests(TestBase):
    def setUp(self):
        super(ValidationFailureTests, self).setUp()
        self._invalid_parameters = None
        self._first = None
        self._second = None

    def test_is_successful_property_of_failed_result(self):
        self.given_created_failed_result_with(invalidity_reason="a_reason", invalid_parameters="mock_parameter_set")
        self.when_accessing_is_successful()
        self.then_result_is(False)

    def given_created_failed_result_with(self, invalidity_reason, invalid_parameters=None):
        self._validation_object = self._create_failed_result(invalidity_reason, invalid_parameters)

    def _create_failed_result(self, invalidity_reason, invalid_parameters=None):
        invalid_parameters = invalid_parameters or "mock_parameter_set"
        return ValidationFailure(invalidity_reason=invalidity_reason, invalid_parameters=invalid_parameters)

    def test_repr_of_failed_result(self):
        self.given_created_failed_result_with("a_reason", "mock_parameter_set")
        self.when_calling_repr()
        self.then_result_is("ValidationFailure('a_reason', 'mock_parameter_set')")

    def test_invalidity_reason_property(self):
        self.given_created_failed_result_with("a_reason")
        self.when_accessing_invalidity_reason()
        self.then_result_is("a_reason")

    def when_accessing_invalidity_reason(self):
        self._result = self._validation_object.invalidity_reason

    def test_invalid_parameters_property(self):
        self.given_created_failed_result_with("a_reason", "mock_parameter_set")
        self.when_accessing_invalid_parameters()
        self.then_result_is("mock_parameter_set")

    def when_accessing_invalid_parameters(self):
        self._result = self._validation_object.invalid_parameters

    def test_eq_on_identical_objects(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second(self._create_failed_result("a_reason"))
        self.when_equaling_first_and_second()
        self.then_result_is(True)

    def given_first(self, first):
        self._first = first

    def given_second(self, second):
        self._second = second

    def given_created_two_identical_validation_failures(self):
        self._first = self._create_failed_result("a_reason")
        self._second = self._create_failed_result("a_reason")

    def when_equaling_first_and_second(self):
        self._result = self._first == self._second

    def test_eq_on_instance_of_other_class(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second("mock_non_validation_result")
        self.when_equaling_first_and_second()
        self.then_result_is(False)

    def test_ne_on_identical_objects(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second(self._create_failed_result("a_reason"))
        self.when_testing_not_equals_on_first_and_second()
        self.then_result_is(False)

    def when_testing_not_equals_on_first_and_second(self):
        self._result = self._first != self._second

    def test_ne_on_instance_of_other_class(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second("mock_non_validation_result")
        self.when_testing_not_equals_on_first_and_second()
        self.then_result_is(True)

    def test_ne_on_success(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second(ValidationSuccess())
        self.when_testing_not_equals_on_first_and_second()
        self.then_result_is(True)

    def test_uniqueness_of_identical_objects(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second(self._create_failed_result("a_reason"))
        self.when_checking_length_of_first_and_second()
        self.then_result_is(1)

    def when_checking_length_of_first_and_second(self):
        self._result = len({self._first, self._second})

    def test_uniqueness_of_different_objects(self):
        self.given_first(self._create_failed_result("a_reason"))
        self.given_second(self._create_failed_result("another_reason"))
        self.when_checking_length_of_first_and_second()
        self.then_result_is(2)
