import unittest

from tala.model.stack import StackSet, StackError, Stack
from tala.testing.utils import EqualityAssertionTestCaseMixin


class MockElement:
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "MockElement(%r)" % self._name


class StackTester(EqualityAssertionTestCaseMixin):
    def test_stacking(self):
        stack = self.create_stack()
        stack.push("first")
        stack.push("second")
        self.assertEqual(stack.pop(), "second")
        self.assertEqual(stack.pop(), "first")
        self.assertEqual(len(stack), 0)

    def test_initialize_with_content(self):
        stack = self.create_stack(["first", "second"])
        self.assertEqual(stack.pop(), "second")
        self.assertEqual(stack.pop(), "first")

    def test_equality_based_on_contents(self):
        stack1 = self.create_stack()
        stack1.push("first")
        stack1.push("second")
        stack2 = self.create_stack()
        stack2.push("first")
        stack2.push("second")
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(stack1, stack2)

    def test_top_on_empty_stack_raises_exception(self):
        stack = self.create_stack()
        self.assertRaises(StackError, stack.top)

    def test_top_returns_latest_stacked_element(self):
        stack = self.create_stack()
        stack.push("harry")
        element = "kalle"
        stack.push(element)
        self.assertEqual(element, stack.top())

    def test_newly_created_stack_is_empty(self):
        stack = self.create_stack()
        self.assertTrue(stack.is_empty())

    def test_non_empty_stack_is_not_empty(self):
        stack = self.create_stack()
        stack.push("randomString")
        self.assertFalse(stack.is_empty())

    def test_empty_stack_not_equals_none(self):
        empty_stack = self.create_stack()
        self.assertNotEqual(None, empty_stack)

    def test_pop_on_empty_stack_raises_exception(self):
        stack = self.create_stack()
        self.assertRaises(StackError, stack.pop)

    def test_is_top_succeeds_for_latest_stacked_element(self):
        stack = self.create_stack()
        stack.push("harry")
        element = "kalle"
        stack.push(element)
        self.assertTrue(stack.is_top(element))

    def test_is_top_on_empty_stack_returns_false(self):
        stack = self.create_stack()
        element = "kalle"
        self.assertFalse(stack.is_top(element))

    def test_is_top_for_non_top_element_returns_false(self):
        stack = self.create_stack()
        topElement = "kalle"
        stack.push(topElement)
        testElement = "nisse"
        self.assertFalse(stack.is_top(testElement))

    def test_iteration(self):
        stack = self.create_stack()
        stack.push("bottom")
        stack.push("top")
        list = []
        for element in stack:
            list.append(element)
        self.assertEqual(["top", "bottom"], list)

    def test_delete_element(self):
        stack = self.create_stack()
        stack.push("first")
        stack.push("second")
        stack.remove("first")
        self.assertTrue("first" not in stack)
        self.assertTrue("second" in stack)

    def test_pushing_stack_on_stack(self):
        lower_stack = self.create_stack()
        lower_stack.push("bottom")
        lower_stack.push("second_from_bottom")
        upper_stack = self.create_stack()
        upper_stack.push("second_from_top")
        upper_stack.push("top")
        expected_stack = self.create_stack()
        expected_stack.push("bottom")
        expected_stack.push("second_from_bottom")
        expected_stack.push("second_from_top")
        expected_stack.push("top")
        result_stack = lower_stack
        result_stack.push_stack(upper_stack)
        self.assertEqual(expected_stack, result_stack)


class TestStacks(unittest.TestCase, StackTester):
    def setUp(self):
        self.create_stack = Stack

    def test_string_representation(self):
        stack = Stack()
        stack.push(MockElement("bottom"))
        stack.push(MockElement("top"))
        self.assertEqual("Stack([MockElement('top'), MockElement('bottom')])", str(stack))


class TestStackSets(unittest.TestCase, StackTester):
    def setUp(self):
        self.create_stack = StackSet

    def test_string_representation(self):
        stack = StackSet()
        stack.push(MockElement("bottom"))
        stack.push(MockElement("top"))
        self.assertEqual("stackset([MockElement('top'), MockElement('bottom')])", str(stack))

    def test_stacking_two_identical_elements_leaves_only_one(self):
        stack = StackSet()
        stack.push("first")
        stack.push("first")
        self.assertEqual(1, len(stack))

    def test_stacking_an_element_a_second_time_leaves_it_at_top(self):
        stack = StackSet()
        stack.push("first")
        stack.push("second")
        stack.push("first")
        expected_stack = StackSet()
        expected_stack.push("second")
        expected_stack.push("first")

        self.assertEqual(expected_stack, stack)

    def test_remove_if_exists_for_existing_element(self):
        set = StackSet(["first", "second"])
        set.remove_if_exists("first")
        expected_result = StackSet(["second"])
        self.assertEqual(expected_result, set)

    def test_remove_if_exists_for_non_existing_element_has_no_effect(self):
        set = StackSet(["first", "second"])
        set.remove_if_exists("third")
        expected_result = StackSet(["first", "second"])
        self.assertEqual(expected_result, set)


class TestStackSetView(unittest.TestCase):
    def test_get_view_of_stack_set(self):
        self._given_a_stack_set([0, 1, 2])
        self._given_a_ONE_pass_filter()
        self._given_a_filtered_view_of_stack()
        self._when_peeking_top_of_view()
        self._then_return_value_is(1)

    def _given_a_stack_set(self, integers):
        self._stack_set = StackSet(integers)

    def _given_a_ONE_pass_filter(self):
        self._filter = lambda integer: integer == 1

    def _given_a_filtered_view_of_stack(self):
        self._view = self._stack_set.create_view(self._filter)

    def _when_peeking_top_of_view(self):
        self._result = self._view.top()

    def _then_return_value_is(self, expected_return_value):
        self.assertEqual(expected_return_value, self._result)

    def test_push_in_view_simple_case(self):
        self._given_a_stack_set([])
        self._given_a_positive_filter()
        self._given_a_filtered_view_of_stack()
        self._when_pushing_an_element_in_view()
        self._then_the_object_becomes_locally_and_globally_visible()

    def _given_a_positive_filter(self):
        self._filter = lambda element: element > 0

    def _when_pushing_an_element_in_view(self):
        self._view.push(42)

    def _then_the_object_becomes_locally_and_globally_visible(self):
        self.assertIn(42, self._stack_set)
        self.assertIn(42, self._view)

    def test_pushing_item_already_on_top_of_view_does_not_modify_stack(self):
        self._given_a_stack_set([0, 1, 2])
        self._given_a_ONE_pass_filter()
        self._given_a_filtered_view_of_stack()
        self._when_pushing_an_element_already_on_top_of_view()
        self._then_the_stack_is_unmodified()

    def _when_pushing_an_element_already_on_top_of_view(self):
        self._view.push(1)

    def _then_the_stack_is_unmodified(self):
        self.assertEqual(2, self._stack_set.top())

    def test_pop_in_view(self):
        self._given_a_stack_set([2, 1, 0, -1])
        self._given_a_positive_filter()
        self._given_a_filtered_view_of_stack()
        self._when_popping_an_element_in_view()
        self._then_the_object_is_locally_and_globally_removed()

    def _when_popping_an_element_in_view(self):
        self._view.pop()

    def _then_the_object_is_locally_and_globally_removed(self):
        self.assertNotIn(1, self._stack_set)
        self.assertNotIn(1, self._view)

    def test_iterate_in_view(self):
        self._given_a_stack_set([2, 1, 0, -1])
        self._given_a_positive_filter()
        self._given_a_filtered_view_of_stack()
        self._when_iteratively_generating_a_list_from_view()
        self._then_the_list_is([1, 2])

    def _when_iteratively_generating_a_list_from_view(self):
        self._integer_list = list(self._view.__iter__())

    def _then_the_list_is(self, elems):
        self.assertEqual(elems, self._integer_list)

    def test_length_of_view(self):
        self._given_a_stack_set([2, 1, 0, -1])
        self._given_a_positive_filter()
        self._given_a_filtered_view_of_stack()
        self._then_length_is(len([1, 2]))

    def _then_length_is(self, length):
        self.assertEqual(length, len(self._view))
