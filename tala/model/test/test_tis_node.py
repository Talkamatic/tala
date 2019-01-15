import unittest

import tala.model.set
from tala.model.tis_node import TISNode


class TISNodeTests(unittest.TestCase):
    def setUp(self):
        class TestNode(TISNode):
            def __init__(self):
                self.child1 = tala.model.set.Set()
                self.child2 = "string"

        class RecursiveTISNode(TISNode):
            def __init__(self):
                self.node1 = TestNode()
                self.node2 = TestNode()

        self.node = TestNode()
        self.recursive_node = RecursiveTISNode()

    def testTISNode_pretty_string_with_indent0(self):
        expected_string = "\n\tchild1: {}\n\tchild2: string"
        self.assertEquals(expected_string, self.node.pretty_string(0))

    def testTISNode_pretty_string_with_indent1(self):
        expected_string = "\n\t\tchild1: {}\n\t\tchild2: string"
        self.assertEquals(expected_string, self.node.pretty_string(1))

    def testTISNode_recursive_pretty_string(self):
        expected_string = "\n\tnode1: \n\t\tchild1: {}\n\t\tchild2: string\n\tnode2: \n\t\tchild1: {}\n\t\tchild2: string"
        self.assertEquals(expected_string, self.recursive_node.pretty_string(0))

    def testTISNode_pretty_string_base_case(self):
        expected_string = "\nchild1: {}\nchild2: string"
        self.assertEquals(expected_string, self.node.pretty_string_new([]))

    def testTISNode_pretty_string_recursive_case(self):
        expected_string = "\nnode1.child1: {}\nnode1.child2: string\nnode2.child1: {}\nnode2.child2: string"
        self.assertEquals(expected_string, self.recursive_node.pretty_string_new([]))
