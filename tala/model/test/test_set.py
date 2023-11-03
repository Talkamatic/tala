import unittest

from tala.model.set import Set
from tala.testing.utils import EqualityAssertionTestCaseMixin


class MockElement:
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "MockElement(%r)" % self._name


class SetTests(unittest.TestCase, EqualityAssertionTestCaseMixin):
    def test_set(self):
        testset = Set()
        testset.add("first")
        testset.add("second")
        self.assertEqual(len(testset), 2)

    def test_ininitialize_with_content(self):
        testset = Set(["first", "second"])
        self.assertEqual(len(testset), 2)

    def test_set_eq(self):
        testset1 = Set()
        testset1.add("first")
        testset1.add("second")
        testset2 = Set()
        testset2.add("second")
        testset2.add("first")
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(testset1, testset2)

    def test_set_non_equality(self):
        testset1 = Set()
        testset1.add("third")
        testset1.add("second")
        testset2 = Set()
        testset2.add("second")
        testset2.add("first")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(testset1, testset2)

    def test_empty_set_is_subset_of_any_set(self):
        testset = Set()
        testset.add("first")
        self.assertTrue(Set().is_subset_of(testset))

    def test_empty_set_is_subset_of_empty_set(self):
        testset = Set()
        self.assertTrue(Set().is_subset_of(testset))

    def test_single_elem_set_not_subset_of_empty_set(self):
        testset = Set()
        testset.add("first")
        self.assertFalse(testset.is_subset_of(Set()))

    def test_set_is_subset_of_itself(self):
        testset = Set()
        testset.add("first")
        self.assertTrue(testset.is_subset_of(testset))

    def test_subset_false_for_sets_with_empty_intersection(self):
        first_set = Set()
        first_set.add("first")
        second_set = Set()
        second_set.add("second")
        self.assertFalse(first_set.is_subset_of(second_set))

    def test_is_subset_of_true_for_sets_with_non_empty_intersection(self):
        first_set = Set()
        first_set.add("first")
        second_set = Set()
        second_set.add("first")
        second_set.add("second")
        self.assertTrue(first_set.is_subset_of(second_set))

    def test_empty_set_not_equals_none(self):
        empty_set = Set()
        self.assertNotEqual(None, empty_set)

    def test_empty_set_is_empty(self):
        testset = Set()
        self.assertEqual(0, len(testset))
        self.assertTrue(testset.is_empty())

    def test_non_empty_set_not_is_empty(self):
        testset = Set()
        testset.add("randomString")
        self.assertEqual(1, len(testset))
        self.assertFalse(testset.is_empty())

    def test_set_member_is_member(self):
        testset = Set()
        element = "kalle"
        testset.add(element)
        self.assertTrue(element in testset)

    def test_set_non_member_is_not_member(self):
        testset = Set()
        element = "kalle"
        self.assertFalse(element in testset)

    def test_set_iteration(self):
        testset = Set()
        testset.add("first")
        testset.add("second")
        comparisonset = set()
        for element in testset:
            comparisonset.add(element)
        self.assertTrue("first" in comparisonset)
        self.assertTrue("second" in comparisonset)

    def test_set_unicode(self):
        testset = Set()
        testset.add(MockElement("element"))
        self.assertEqual("{MockElement('element')}", str(testset))

        testset = Set()
        testset.add(MockElement("element1"))
        testset.add(MockElement("element2"))
        self.assertTrue(
            "{MockElement('element1'), MockElement('element2')}" == str(testset)
            or "{MockElement('element2'), MockElement('element1')}" == str(testset)
        )

    def test_set_property(self):
        set = Set()
        set.add("first")
        set.add("first")
        self.assertEqual(1, len(set))

    def test_remove_existing_element_from_single_element_set(self):
        set = Set(["first"])
        set.remove("first")
        self.assertEqual(0, len(set))

    def test_remove_existing_element(self):
        set = Set(["first", "second"])
        set.remove("first")
        expected_result = Set(["second"])
        self.assertEqual(expected_result, set)

    def test_remove_non_existing_element_yields_exception(self):
        set = Set(["first", "second"])
        with self.assertRaises(ValueError):
            set.remove("third")

    def test_remove_if_exists_for_existing_element(self):
        set = Set(["first", "second"])
        set.remove_if_exists("first")
        expected_result = Set(["second"])
        self.assertEqual(expected_result, set)

    def test_remove_if_exists_for_non_existing_element_has_no_effect(self):
        set = Set(["first", "second"])
        set.remove_if_exists("third")
        expected_result = Set(["first", "second"])
        self.assertEqual(expected_result, set)

    def test_union_with_empty_set(self):
        test_set = Set(["first", "second"])
        union = test_set.union(Set())
        self.assertEqual(test_set, union)

    def test_union_with_self(self):
        test_set = Set(["first", "second"])
        union = test_set.union(test_set)
        self.assertEqual(test_set, union)

    def test_union_with_empty_set_reflexive_1(self):
        test_set = Set(["first", "second"])
        union = Set().union(test_set)
        self.assertEqual(test_set, union)

    def test_union_with_empty_set_reflexive_2(self):
        first_list = ["first", "second"]
        second_list = ["third", "fourth"]
        first_set = Set(first_list)
        second_set = Set(second_list)
        union = first_set.union(second_set)
        first_list.extend(second_list)
        for item in first_list:
            self.assertTrue(item in union)

    def test_union_is_new_instance(self):
        first_set = Set()
        second_set = Set()
        union_set = first_set.union(second_set)
        first_set.add("dummy_item")
        self.assertEqual(Set(), union_set)

    def test_intersection_with_empty_set(self):
        first_set = Set()
        second_set = Set()
        intersection_set = first_set.intersection(second_set)
        self.assertEqual(first_set, intersection_set)

    def test_intersection_with_self(self):
        test_set = Set()
        intersection_set = test_set.intersection(test_set)
        self.assertEqual(test_set, intersection_set)

    def test_intersection_with_common_elements(self):
        first_set = Set([1, 2])
        second_set = Set([2, 3])
        intersection_set = first_set.intersection(second_set)

        expected_intersection = Set([2])
        self.assertEqual(expected_intersection, intersection_set)

    def test_intersection_disjoint_sets(self):
        first_set = Set([1])
        second_set = Set([2])
        intersection_set = first_set.intersection(second_set)
        expected_intersection_set = Set()
        self.assertEqual(intersection_set, expected_intersection_set)

    def test_set_in_set(self):
        set = Set()
        set_in_set = Set()
        set.add(set_in_set)

    def test_set_clear_then_add(self):
        set = Set()
        set.clear()
        set.add("first")

    def test_extend(self):
        test_set = Set(["first", "second"])
        extension = Set(["second", "third"])
        test_set.extend(extension)
        expected_result = Set(["first", "second", "third"])
        self.assertEqual(expected_result, test_set)
