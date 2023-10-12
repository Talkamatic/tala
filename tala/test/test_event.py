import unittest

from tala.event import Event
from tala.model.set import Set


class EventTests(unittest.TestCase):
    def test_input_event(self):
        event = Event(Event.PASSIVITY, "hello")
        self.assertEqual(Event.PASSIVITY, event.get_type())
        self.assertEqual("hello", event.get_content())

    def test_event_equality_for_input(self):
        event = Event(Event.PASSIVITY, "hello")
        identical_event = Event(Event.PASSIVITY, "hello")
        self.assertEqual(event, identical_event)

    def test_event_equality_for_interpretation(self):
        moves = Set(["move1", "move2"])
        event = Event(Event.INTERPRETATION, moves)
        identical_moves = Set(["move1", "move2"])
        identical_event = Event(Event.INTERPRETATION, identical_moves)
        self.assertEqual(event, identical_event)
        self.assertEqual(identical_event, event)
        self.assertFalse(event != identical_event)
        self.assertFalse(identical_event != event)

    def test_events_inequal_due_to_content(self):
        event = Event(Event.PASSIVITY, "hello")
        non_identical_event = Event(Event.PASSIVITY, "goodbye")
        self.assertNotEqual(event, non_identical_event)
        self.assertNotEqual(non_identical_event, event)

    def test_events_inequal_due_to_sender(self):
        event = Event(Event.PASSIVITY, "hello", sender="sender1")
        non_identical_event = Event(Event.PASSIVITY, "hello", sender="sender2")
        self.assertNotEqual(event, non_identical_event)
        self.assertNotEqual(non_identical_event, event)

    def test_events_inequal_due_to_reason(self):
        event = Event(Event.PASSIVITY, "hello", reason="reason1")
        non_identical_event = Event(Event.PASSIVITY, "hello", reason="reason2")
        self.assertNotEqual(event, non_identical_event)
        self.assertNotEqual(non_identical_event, event)

    def test_event_not_equals_none(self):
        event = Event(Event.PASSIVITY, "hello")
        self.assertNotEqual(None, event)

    def test_string_representation_for_non_empty_event(self):
        event = Event(Event.PASSIVITY, "hello")
        self.assertEqual("Event(PASSIVITY, 'hello', sender=None, reason=None)", str(event))

    def test_string_representation_for_empty_event(self):
        event = Event(Event.STOP)
        self.assertEqual("Event(STOP, None, sender=None, reason=None)", str(event))

    def test_is_internal(self):
        self.assertTrue(Event(Event.STOP).is_internal())
        self.assertFalse(Event(Event.PASSIVITY).is_internal())
