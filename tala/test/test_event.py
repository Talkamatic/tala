import unittest

from tala import event
from tala.model.set import Set


class EventTests(unittest.TestCase):
    def test_input_event(self):
        target_event = event.Event(event.PASSIVITY, "hello")
        self.assertEqual(event.PASSIVITY, target_event.type_)
        self.assertEqual("hello", target_event.content)

    def test_event_equality_for_input(self):
        target_event = event.Event(event.PASSIVITY, "hello")
        identical_event = event.Event(event.PASSIVITY, "hello")
        self.assertEqual(target_event, identical_event)

    def test_event_equality_for_interpretation(self):
        moves = Set(["move1", "move2"])
        target_event = event.Event(event.INTERPRETATION, moves)
        identical_moves = Set(["move1", "move2"])
        identical_event = event.Event(event.INTERPRETATION, identical_moves)
        self.assertEqual(target_event, identical_event)
        self.assertEqual(identical_event, target_event)
        self.assertFalse(target_event != identical_event)
        self.assertFalse(identical_event != target_event)

    def test_events_inequal_due_to_content(self):
        target_event = event.Event(event.PASSIVITY, "hello")
        non_identical_event = event.Event(event.PASSIVITY, "goodbye")
        self.assertNotEqual(target_event, non_identical_event)
        self.assertNotEqual(non_identical_event, target_event)

    def test_events_inequal_due_to_sender(self):
        target_event = event.Event(event.PASSIVITY, "hello", sender="sender1")
        non_identical_event = event.Event(event.PASSIVITY, "hello", sender="sender2")
        self.assertNotEqual(target_event, non_identical_event)
        self.assertNotEqual(non_identical_event, target_event)

    def test_events_inequal_due_to_reason(self):
        target_event = event.Event(event.PASSIVITY, "hello", reason="reason1")
        non_identical_event = event.Event(event.PASSIVITY, "hello", reason="reason2")
        self.assertNotEqual(target_event, non_identical_event)
        self.assertNotEqual(non_identical_event, target_event)

    def test_event_not_equals_none(self):
        target_event = event.Event(event.PASSIVITY, "hello")
        self.assertNotEqual(None, target_event)

    def test_string_representation_for_non_empty_event(self):
        target_event = event.Event(event.PASSIVITY, "hello")
        self.assertEqual("Event(PASSIVITY, 'hello', sender=None, reason=None)", str(target_event))
