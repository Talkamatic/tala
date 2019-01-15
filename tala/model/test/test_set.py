import unittest

import tala.model
from tala.testing.utils import EqualityAssertionTestCaseMixin


class MockElement:
    def __init__(self, name):
        self._name = name

    def __unicode__(self):
        return "MockElement(%r)" % self._name


class SetTests(unittest.TestCase, EqualityAssertionTestCaseMixin):
    def testSet(self):
        testset = tala.model.set.Set()
        testset.add("first")
        testset.add("second")
        self.assertEquals(len(testset), 2)

    def test_ininitialize_with_content(self):
        testset = tala.model.set.Set(["first", "second"])
        self.assertEquals(len(testset), 2)

    def testSetEq(self):
        testset1 = tala.model.set.Set()
        testset1.add("first")
        testset1.add("second")
        testset2 = tala.model.set.Set()
        testset2.add("second")
        testset2.add("first")
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(testset1, testset2)

    def test_set_non_equality(self):
        testset1 = tala.model.set.Set()
        testset1.add("third")
        testset1.add("second")
        testset2 = tala.model.set.Set()
        testset2.add("second")
        testset2.add("first")
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(testset1, testset2)

    def test_empty_set_is_subset_of_any_set(self):
        testset = tala.model.set.Set()
        testset.add("first")
        self.assertTrue(tala.model.set.Set().is_subset_of(testset))

    def test_empty_set_is_subset_of_empty_set(self):
        testset = tala.model.set.Set()
        self.assertTrue(tala.model.set.Set().is_subset_of(testset))

    def test_single_elem_set_not_subset_of_empty_set(self):
        testset = tala.model.set.Set()
        testset.add("first")
        self.assertFalse(testset.is_subset_of(tala.model.set.Set()))

    def test_set_is_subset_of_itself(self):
        testset = tala.model.set.Set()
        testset.add("first")
        self.assertTrue(testset.is_subset_of(testset))

    def test_subset_false_for_sets_with_empty_intersection(self):
        first_set = tala.model.set.Set()
        first_set.add("first")
        second_set = tala.model.set.Set()
        second_set.add("second")
        self.assertFalse(first_set.is_subset_of(second_set))

    def test_is_subset_of_true_for_sets_with_non_empty_intersection(self):
        first_set = tala.model.set.Set()
        first_set.add("first")
        second_set = tala.model.set.Set()
        second_set.add("first")
        second_set.add("second")
        self.assertTrue(first_set.is_subset_of(second_set))

    def test_empty_set_not_equals_none(self):
        empty_set = tala.model.set.Set()
        self.assertNotEquals(None, empty_set)

    def testEmptySetisEmpty(self):
        testset = tala.model.set.Set()
        self.assertEquals(0, len(testset))
        self.assertTrue(testset.isEmpty())

    def testNonEmptySetNotisEmpty(self):
        testset = tala.model.set.Set()
        testset.add("randomString")
        self.assertEquals(1, len(testset))
        self.assertFalse(testset.isEmpty())

    def testSetMemberIsMember(self):
        testset = tala.model.set.Set()
        element = "kalle"
        testset.add(element)
        self.assertTrue(element in testset)

    def testSetNonMemberIsNotMember(self):
        testset = tala.model.set.Set()
        element = "kalle"
        self.assertFalse(element in testset)

    def testSetIteration(self):
        testset = tala.model.set.Set()
        testset.add("first")
        testset.add("second")
        comparisonset = set()
        for element in testset:
            comparisonset.add(element)
        self.assertTrue("first" in comparisonset)
        self.assertTrue("second" in comparisonset)

    def testTypedSet(self):
        testset = tala.model.set.Set(str)
        testset.add("foo")

    def testTypedSetTypeError(self):
        testset = tala.model.set.Set(int)
        exception_raised = False
        try:
            testset.add("foo")
        except TypeError:
            exception_raised = True
        self.assertTrue(exception_raised)

    def testSetunicode(self):
        testset = tala.model.set.Set()
        testset.add(MockElement("element"))
        self.assertEquals("{MockElement('element')}", unicode(testset))

        testset = tala.model.set.Set()
        testset.add(MockElement("element1"))
        testset.add(MockElement("element2"))
        self.assertTrue(
            "{MockElement('element1'), MockElement('element2')}" == unicode(testset)
            or "{MockElement('element2'), MockElement('element1')}" == unicode(testset)
        )

    def test_set_property(self):
        set = tala.model.set.Set()
        set.add("first")
        set.add("first")
        self.assertEquals(1, len(set))

    def test_remove_existing_element_from_single_element_set(self):
        set = tala.model.set.Set(["first"])
        set.remove("first")
        self.assertEquals(0, len(set))

    def test_remove_existing_element(self):
        set = tala.model.set.Set(["first", "second"])
        set.remove("first")
        expected_result = tala.model.set.Set(["second"])
        self.assertEquals(expected_result, set)

    def test_remove_non_existing_element_yields_exception(self):
        set = tala.model.set.Set(["first", "second"])
        with self.assertRaises(Exception):
            set.remove("third")

    def test_remove_if_exists_for_existing_element(self):
        set = tala.model.set.Set(["first", "second"])
        set.remove_if_exists("first")
        expected_result = tala.model.set.Set(["second"])
        self.assertEquals(expected_result, set)

    def test_remove_if_exists_for_non_existing_element_has_no_effect(self):
        set = tala.model.set.Set(["first", "second"])
        set.remove_if_exists("third")
        expected_result = tala.model.set.Set(["first", "second"])
        self.assertEquals(expected_result, set)

    def test_union_with_empty_set(self):
        test_set = tala.model.set.Set(["first", "second"])
        union = test_set.union(tala.model.set.Set())
        self.assertEquals(test_set, union)

    def test_union_with_self(self):
        test_set = tala.model.set.Set(["first", "second"])
        union = test_set.union(test_set)
        self.assertEquals(test_set, union)

    def test_union_with_empty_set_reflexive_1(self):
        test_set = tala.model.set.Set(["first", "second"])
        union = tala.model.set.Set().union(test_set)
        self.assertEquals(test_set, union)

    def test_union_with_empty_set_reflexive_2(self):
        first_list = ["first", "second"]
        second_list = ["third", "fourth"]
        first_set = tala.model.set.Set(first_list)
        second_set = tala.model.set.Set(second_list)
        union = first_set.union(second_set)
        first_list.extend(second_list)
        for item in first_list:
            self.assertTrue(item in union)

    def test_union_is_new_instance(self):
        first_set = tala.model.set.Set()
        second_set = tala.model.set.Set()
        union_set = first_set.union(second_set)
        first_set.add("dummy_item")
        self.assertEquals(tala.model.set.Set(), union_set)

    def test_intersection_with_empty_set(self):
        first_set = tala.model.set.Set()
        second_set = tala.model.set.Set()
        intersection_set = first_set.intersection(second_set)
        self.assertEquals(first_set, intersection_set)

    def test_intersection_with_self(self):
        test_set = tala.model.set.Set()
        intersection_set = test_set.intersection(test_set)
        self.assertEquals(test_set, intersection_set)

    def test_intersection_with_common_elements(self):
        first_set = tala.model.set.Set([1, 2])
        second_set = tala.model.set.Set([2, 3])
        intersection_set = first_set.intersection(second_set)

        expected_intersection = tala.model.set.Set([2])
        self.assertEquals(expected_intersection, intersection_set)

    def test_intersection_disjoint_sets(self):
        first_set = tala.model.set.Set([1])
        second_set = tala.model.set.Set([2])
        intersection_set = first_set.intersection(second_set)
        expected_intersection_set = tala.model.set.Set()
        self.assertEquals(intersection_set, expected_intersection_set)

    def test_set_in_set(self):
        set = tala.model.set.Set()
        set_in_set = tala.model.set.Set()
        set.add(set_in_set)

    def test_set_clear_then_add(self):
        set = tala.model.set.Set()
        set.clear()
        set.add("first")

    def test_extend(self):
        test_set = tala.model.set.Set(["first", "second"])
        extension = tala.model.set.Set(["second", "third"])
        test_set.extend(extension)
        expected_result = tala.model.set.Set(["first", "second", "third"])
        self.assertEquals(expected_result, test_set)
