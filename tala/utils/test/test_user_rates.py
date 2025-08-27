import copy
import datetime
import json

import pytest

from tala.utils import user_rates_constants as constants
from tala.utils.user_rates import BuddyGeneratorUserRates, HandlerUserRates, OfferNotInDB

OFFER_USAGE_QUOTA = 500
AUTHOR_USAGE_QUOTA = 2500
AUTHOR_GENERATION_QUOTA = 30


class MockHandlerUserRates(HandlerUserRates):
    def __init__(self, table_client):
        self._table_client = table_client

    def _query_entities(self, key, value):
        entities = copy.deepcopy(self._table_client.query_entities(key, value))
        for entity in entities:
            self._load_json_fields(entity)
        return entities


class MockBuddyGeneratorUserRates(BuddyGeneratorUserRates):
    def __init__(self, table_client):
        self._table_client = table_client

    def _query_entities(self, key, value):
        entities = copy.deepcopy(self._table_client.query_entities(key, value))
        for entity in entities:
            self._load_json_fields(entity)
        return entities


class MockTableClient:
    def __init__(self, rate_entries):
        self._entries = rate_entries

    def query_entities(self, key, value):
        entities = []
        for entity in self._entries:
            if key in entity and entity[key] == value:
                entities.append(entity)
        return entities

    def create_entity(self, entity):
        self._entries.append(entity)

    def update_entity(self, entity):
        for original_entity in self._entries:
            if entity["RowKey"] == original_entity["RowKey"]:
                for key in entity:
                    original_entity[key] = entity[key]
                break


def create_rate_entry(handler_calls, offer_id, row_key):
    return {
        constants.PARTITION_KEY: constants.HANDLER_DATA,
        constants.ROW_KEY: row_key,
        constants.NUM_CALLS: handler_calls,
        constants.OFFER_ID: str(offer_id),
        constants.CALLS_LAST_PERIOD: json.dumps([]),
        constants.OFFER_AUTHOR_ID: '2',
        constants.OFFER_QUOTA: OFFER_USAGE_QUOTA
    }


def create_author_quota_entry(user_id, row_key):
    return {
        constants.PARTITION_KEY: constants.HANDLER_DATA,
        constants.ROW_KEY: row_key,
        constants.AUTHOR_ID: user_id,
        constants.AUTHOR_QUOTA: AUTHOR_USAGE_QUOTA
    }


class TestHandlerUserRates:
    def test_first_call(self):
        self.given_user_rates([(0, "offer-id-2", "id-2")])
        self.given_handler()
        self.when_increment_calls("offer-id-2")
        self.then_num_calls_are("offer-id-2", 1)

    def test_total_calls_incremented(self):
        self.given_user_rates([(499, "offer-id-1", "id_1")])
        self.given_handler()
        self.when_increment_calls("offer-id-1")
        self.then_num_calls_are("offer-id-1", 500)

    def given_user_rates(self, rate_entry_values):
        rates = [create_rate_entry(*values_tuple) for values_tuple in rate_entry_values]
        try:
            self._user_rates_table.extend(rates)
        except AttributeError:
            self._user_rates_table = rates

    def given_handler(self):
        try:
            self._handler = MockHandlerUserRates(MockTableClient(self._user_rates_table))
        except AttributeError:
            self._handler = MockHandlerUserRates(MockTableClient([]))

    def when_increment_calls(self, offer_id):
        self._handler.increment_num_calls(offer_id)

    def then_num_calls_are(self, offer_id, num_calls):
        entities = self._handler.query_offer_id(offer_id)
        assert num_calls == entities[0][constants.NUM_CALLS]

    def test_rate_increased(self):
        self.given_user_rates([(500, "offer-id-2", "id-2")])
        self.given_handler()
        self.when_increment_calls("offer-id-2")
        self.then_num_calls_last_hour_is("offer-id-2", 1)

    def test_entry_updated_with_new_field(self):
        self.given_user_rates([(0, "offer-id-1", "id_1")])
        self.given_field_removed(constants.CALLS_LAST_PERIOD)
        self.given_handler()
        self.when_increment_calls("offer-id-1")
        self.then_num_calls_last_hour_is("offer-id-1", 1)

    def given_field_removed(self, field_name):
        for item in self._user_rates_table:
            del item[field_name]

    def then_num_calls_last_hour_is(self, offer_id, num_calls):
        entities = self._handler.query_offer_id_and_garbage_collect(offer_id)
        assert num_calls == len(entities[0][constants.CALLS_LAST_PERIOD])

    def test_old_entries_garbage_collected(self):
        self.given_user_rates([(500, "offer-id-2", "id-2")])
        self.given_old_call(61)
        self.given_handler()
        self.when_increment_calls("offer-id-2")
        self.then_num_calls_last_hour_is("offer-id-2", 1)

    def given_old_call(self, age_in_minutes):
        now = datetime.datetime.now()
        delta = delta = datetime.timedelta(minutes=age_in_minutes)
        birth_time = now - delta
        self._user_rates_table[0][constants.CALLS_LAST_PERIOD] = json.dumps([birth_time.timestamp()])

    def test_younger_entries_not_garbage_collected(self):
        self.given_user_rates([(500, "offer-id-2", "id-2")])
        self.given_old_call(59)
        self.given_handler()
        self.when_increment_calls("offer-id-2")
        self.then_num_calls_last_hour_is("offer-id-2", 2)

    def test_offer_not_in_db(self):
        self.given_handler()
        with pytest.raises(OfferNotInDB):
            self.when_increment_calls("new_offer")

    def test_create_entity(self):
        self.given_handler()
        self.when_create_entity("new_offer", "new_ts_id", "new_user", OFFER_USAGE_QUOTA)
        self.then_incrementing_works_flawlessly("new_offer")

    def when_create_entity(self, offer_id, ts_dialogue_id, user_id, offer_quota):
        self._handler.create_entity(offer_id, ts_dialogue_id, user_id, offer_quota)

    def then_incrementing_works_flawlessly(self, offer_id):
        self._handler.increment_num_calls(offer_id)
        assert True

    def test_create_entity_author_usage_quota(self):
        self.given_handler()
        self.when_create_entity_author_quota("new_user", AUTHOR_USAGE_QUOTA)
        self.then_user_rates_contain_author_entry("new_user")

    def when_create_entity_author_quota(self, author_user_id, author_quota):
        self._handler.create_entity_author_quota(author_user_id, author_quota)

    def then_user_rates_contain_author_entry(self, author_user_id):
        entities = self._handler.query_author_user_id(author_user_id)
        assert author_user_id == entities[0][constants.AUTHOR_ID]

    def test_update_author_quota(self):
        self.given_author_in_user_rates([("author-user-id-2", "id-2")])
        self.given_handler()
        self.when_update_author_quota("author-user-id-2", 4000)
        self.then_author_quota_is("author-user-id-2", 4000)

    def when_update_author_quota(self, author_user_id, author_quota):
        self._handler.update_author_quota(author_user_id, author_quota)

    def then_author_quota_is(self, author_user_id, author_quota):
        entities = self._handler.query_author_user_id(author_user_id)
        assert author_quota == entities[0][constants.AUTHOR_QUOTA]

    def given_author_in_user_rates(self, author_rates_values):
        author_rates = [create_author_quota_entry(*values_tuple) for values_tuple in author_rates_values]
        try:
            self._user_rates_table.extend(author_rates)
        except AttributeError:
            self._user_rates_table = author_rates


def create_buddy_generator_rate_entry(num_calls, author_user_id, row_key, author_quota=None):
    return {
        constants.PARTITION_KEY: constants.BUDDY_GENERATOR_DATA,
        constants.ROW_KEY: row_key,
        constants.NUM_CALLS: num_calls,
        constants.AUTHOR_ID: author_user_id,
        constants.AUTHOR_QUOTA: author_quota if author_quota else AUTHOR_GENERATION_QUOTA
    }


class TestBuddyGeneratorUserRates:
    def test_first_call(self):
        self.given_user_rates([(0, "author-user-id-2", "id-2")])
        self.given_handler()
        self.when_increment_calls("author-user-id-2")
        self.then_num_calls_are("author-user-id-2", 1)

    def given_user_rates(self, rate_entry_values):
        rates = [create_buddy_generator_rate_entry(*values_tuple) for values_tuple in rate_entry_values]
        try:
            self._user_rates_table.extend(rates)
        except AttributeError:
            self._user_rates_table = rates

    def given_handler(self):
        try:
            self._handler = MockBuddyGeneratorUserRates(MockTableClient(self._user_rates_table))
        except AttributeError:
            self._handler = MockBuddyGeneratorUserRates(MockTableClient([]))

    def when_increment_calls(self, author_user_id):
        self._handler.increment_num_calls(author_user_id)

    def then_num_calls_are(self, author_user_id, num_calls):
        entities = self._handler.query_author_user_id(author_user_id)
        assert num_calls == entities[0][constants.NUM_CALLS]

    def test_create_entity(self):
        self.given_handler()
        self.when_create_entity("new_user", AUTHOR_GENERATION_QUOTA)
        self.then_user_rates_contain_author_entry("new_user")

    def when_create_entity(self, author_user_id, author_quota):
        self._handler.create_entity(author_user_id, author_quota)

    def then_user_rates_contain_author_entry(self, author_user_id):
        entities = self._handler.query_author_user_id(author_user_id)
        assert author_user_id == entities[0][constants.AUTHOR_ID]

    def test_update_author_quota(self):
        self.given_user_rates([(0, "author-user-id-2", "id-2")])
        self.given_handler()
        self.when_update_author_quota("author-user-id-2", 40)
        self.then_author_quota_is("author-user-id-2", 40)

    def when_update_author_quota(self, author_user_id, author_quota):
        self._handler.update_author_quota(author_user_id, author_quota)

    def then_author_quota_is(self, author_user_id, author_quota):
        entities = self._handler.query_author_user_id(author_user_id)
        assert author_quota == entities[0][constants.AUTHOR_QUOTA]
