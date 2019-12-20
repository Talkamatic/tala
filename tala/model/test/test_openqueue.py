import unittest

from tala.model.openqueue import OpenQueue, OpenQueueError


class MockElement:
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "MockElement(%r)" % self._name


class OpenQueueTests(unittest.TestCase):
    def setUp(self):
        self.queue = OpenQueue()

    def test_first(self):
        self._given_an_element_enqueued("a")
        self._when_an_element_enqueued("b")
        self._first_returns("a")

    def _given_an_element_enqueued(self, elem):
        self.queue.enqueue(elem)

    def _when_an_element_enqueued(self, elem):
        self.queue.enqueue(elem)

    def _first_returns(self, element):
        actual_element = self.queue.first()
        self.assertEqual(element, actual_element)

    def test_is_first(self):
        self._given_an_element_enqueued("a")
        self._is_first("a")

    def _is_first(self, element):
        self.assertTrue(self.queue.is_first(element))

    def test_is_not_first_on_empty_queue(self):
        self._is_not_first("a")

    def _is_not_first(self, element):
        self.assertFalse(self.queue.is_first(element))

    def test_first_on_empty_queue_raises_exception(self):
        with self.assertRaises(OpenQueueError):
            self.queue.first()

    def test_last(self):
        self._given_an_element_enqueued("a")
        self._when_an_element_enqueued("b")
        self._last_returns("b")

    def _last_returns(self, element):
        actual_element = self.queue.last()
        self.assertEqual(element, actual_element)

    def test_size_0(self):
        self.assertEqual(0, len(self.queue))

    def test_size_1(self):
        self._given_an_element_enqueued("a")
        self.assertEqual(1, len(self.queue))

    def test_dequeue_returns_right_element(self):
        self._given_an_element_enqueued("a")
        self._dequeue_returns("a")

    def _dequeue_returns(self, element):
        actual_element = self.queue.dequeue()
        self.assertEqual(element, actual_element)

    def test_dequeue_deletes_element(self):
        self._given_an_element_enqueued("a")
        self._when_dequeue()
        self._queue_is_empty()

    def _when_dequeue(self):
        self.queue.dequeue()

    def _queue_is_empty(self):
        self.assertTrue(len(self.queue) == 0)

    def test_dequeue_on_empty_queue_raises_exception(self):
        with self.assertRaises(OpenQueueError):
            self.queue.dequeue()

    def test_delete(self):
        self._given_an_element_enqueued("a")
        self._given_an_element_enqueued("b")
        self._when_an_element_is_deleted("b")
        self._element_is_not_member("b")

    def _when_an_element_is_deleted(self, element):
        self.queue.remove(element)

    def _element_is_not_member(self, non_member):
        self.assertFalse(non_member in self.queue)

    def test_string_representation(self):
        self.queue.enqueue(MockElement("first"))
        self.queue.enqueue(MockElement("second"))
        self.assertEqual("OpenQueue(['#', MockElement('first'), MockElement('second')])", str(self.queue))

    def test_create_from_iterable(self):
        self.queue = OpenQueue(["a", "b", "c"])
        self.assertEqual("OpenQueue(['a', 'b', 'c', '#'])", str(self.queue))

    def test_shift(self):
        self.queue = OpenQueue(["a", "b", "c"])
        self.queue.init_shift()
        self.queue.shift()
        self.assertEqual("OpenQueue(['b', 'c', '#', 'a'])", str(self.queue))

    def test_fully_shifted(self):
        self.queue = OpenQueue(["a", "b", "c"])
        self.queue.init_shift()
        self.queue.shift()
        self.queue.shift()
        self.queue.shift()
        self.assertTrue(self.queue.fully_shifted())

    def test_dequeue_and_shift(self):
        self.queue = OpenQueue(["a", "b", "c"])
        self.queue.dequeue()
        self.queue.init_shift()
        self.queue.shift()
        self.assertEqual("OpenQueue(['c', '#', 'b'])", str(self.queue))

    def test_clear(self):
        self._given_an_element_enqueued("element")
        self._when_clear_is_called()
        self._object_is_emptied()

    def _when_clear_is_called(self):
        self.queue.clear()

    def _object_is_emptied(self):
        self.assertTrue(self.queue.is_empty())

    def test_empty_queues_are_equal(self):
        first_queue = OpenQueue()
        second_queue = OpenQueue()
        self.assertEqual(first_queue, second_queue)

    def test_empty_queue_not_equals_none(self):
        empty_queue = OpenQueue()
        self.assertNotEqual(None, empty_queue)

    def test_single_element_queues_are_equal(self):
        first_queue = OpenQueue(["a"])
        second_queue = OpenQueue(["a"])
        self.assertEqual(first_queue, second_queue)

    def test_single_element_queue_equal_to_shifted_single_element_queue(self):
        first_queue = OpenQueue(["a"])
        second_queue = OpenQueue(["a"])
        second_queue.shift()
        self.assertEqual(first_queue, second_queue)

    def test_unshifted_multi_element_queues_are_equal(self):
        first_queue = OpenQueue(["a", "b", "c"])
        second_queue = OpenQueue(["a", "b", "c"])
        self.assertEqual(first_queue, second_queue)

    def test_queue_not_equal_to_shifted_queue_1(self):
        first_queue = OpenQueue(["a", "b", "c"])
        second_queue = OpenQueue(["a", "b", "c"])
        second_queue.shift()
        self.assertNotEqual(first_queue, second_queue)

    def test_queue_not_equal_to_shifted_queue_2(self):
        first_queue = OpenQueue(["a", "b", "c"])
        second_queue = OpenQueue(["c", "a", "b"])
        second_queue.shift()
        self.assertNotEqual(first_queue, second_queue)

    def test_enqueue_first(self):
        queue = OpenQueue(["b"])
        queue.enqueue_first("a")
        self.assertEqual("a", queue.first())

    def test_remove_if_exists_for_existing_element(self):
        queue = OpenQueue(["first", "second"])
        queue.remove_if_exists("first")
        expected_result = OpenQueue(["second"])
        self.assertEqual(expected_result, queue)

    def test_remove_if_exists_for_non_existing_element_has_no_effect(self):
        queue = OpenQueue(["first", "second"])
        queue.remove_if_exists("third")
        expected_result = OpenQueue(["first", "second"])
        self.assertEqual(expected_result, queue)

    def test_set_property(self):
        self._given_an_element_enqueued("a")
        self._when_an_element_enqueued("a")
        self._first_returns("a")
        self._len_is(1)

    def _len_is(self, length):
        self.assertEqual(length, len(self.queue))

    def test_cancel_shift(self):
        queue = OpenQueue(["a", "b", "c"])
        queue.init_shift()
        queue.shift()
        queue.remove("b")
        queue.cancel_shift()
        expected_queue = OpenQueue(["a", "c"])
        self.assertEqual(expected_queue, queue)

    def test_cancel_shift_raises_exception_if_init_shift_not_called(self):
        queue = OpenQueue([])
        with self.assertRaises(OpenQueueError):
            queue.cancel_shift()

    def test_getitem(self):
        queue = OpenQueue(["a", "b", "c"])
        self.assertEqual("a", queue[0])
