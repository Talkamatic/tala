from mock import Mock

from tala.model.grammar.intent import Intent
from tala.nl.generated_intent import GeneratedIntent


class TestGeneratedIntent(object):
    def setup(self):
        self._generated_intent = None
        self._mocked_intents = []
        self._result = None

    def test_only_unique_required_entities_are_returned_by_property(self):
        self.given_intent_with_entities(["entity 1", "entity 2"])
        self.given_intent_with_entities(["entity 1", "entity 3"])
        self.given_intent_with_entities(["entity 2", "entity 4"])
        self.given_created_generated_intent()
        self.when_accessing_required_entities()
        self.then_returned_entities_are(["entity 1", "entity 2", "entity 3", "entity 4"])

    def given_intent_with_entities(self, entities):
        intent = Mock(spec=Intent)
        intent.required_entities = entities
        self._mocked_intents.append(intent)

    def given_created_generated_intent(self):
        self._generated_intent = GeneratedIntent(name="mocked_intent", sources=self._mocked_intents, samples=[])

    def when_accessing_required_entities(self):
        self._result = self._generated_intent.required_entities

    def then_returned_entities_are(self, expected_entities):
        assert expected_entities == self._result, \
            "Expected {} to match {} but it didn't".format(expected_entities, self._result)

    def test_order_is_preserved_for_required_entities_returned_by_property(self):
        self.given_intent_with_entities(["entity 7", "entity 6"])
        self.given_intent_with_entities(["entity 5"])
        self.given_intent_with_entities(["entity 4", "entity 3", "entity 2"])
        self.given_intent_with_entities(["entity 1"])
        self.given_created_generated_intent()
        self.when_accessing_required_entities()
        self.then_returned_entities_are([
            "entity 7", "entity 6", "entity 5", "entity 4", "entity 3", "entity 2", "entity 1"
        ])
