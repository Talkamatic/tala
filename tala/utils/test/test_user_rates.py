import copy
import datetime

import pytest

from tala.utils.user_rates import HandlerUserRates, OfferNotInDB

OFFER_QUOTA = "500"


class MockHandlerUserRates(HandlerUserRates):
    def __init__(self, table_client):
        self._table_client = table_client

    def _query_entities(self, key, value):
        return copy.deepcopy(self._table_client.query_entities(key, value))


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


def generate_rate_entry(handler_calls, offer_id, row_key):
    return {
        'PartitionKey': 'HandlerData',
        'RowKey': row_key,
        'NumCalls': handler_calls,
        'OfferID': str(offer_id),
        'CallsLastPeriod': [],
        'UserID': '2'
    }


class TestQuota:
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
        rates = [generate_rate_entry(*values_tuple) for values_tuple in rate_entry_values]
        try:
            self._user_rates.extend(rates)
        except AttributeError:
            self._user_rates = rates

    def given_handler(self):
        try:
            self._handler = MockHandlerUserRates(MockTableClient(self._user_rates))
        except AttributeError:
            self._handler = MockHandlerUserRates(MockTableClient([]))

    def when_increment_calls(self, offer_id):
        self._handler.increment_num_calls(offer_id)

    def then_num_calls_are(self, offer_id, num_calls):
        entities = self._handler.query_offer_id(offer_id)
        assert num_calls == entities[0]["NumCalls"]

    def test_rate_increased(self):
        self.given_user_rates([(500, "offer-id-2", "id-2")])
        self.given_handler()
        self.when_increment_calls("offer-id-2")
        self.then_num_calls_last_hour_is("offer-id-2", 1)

    def test_entry_updated_with_new_field(self):
        self.given_user_rates([(0, "offer-id-1", "id_1")])
        self.given_field_removed("CallsLastPeriod")
        self.given_handler()
        self.when_increment_calls("offer-id-1")
        self.then_num_calls_last_hour_is("offer-id-1", 1)

    def given_field_removed(self, field_name):
        for item in self._user_rates:
            del item["CallsLastPeriod"]

    def then_num_calls_last_hour_is(self, offer_id, num_calls):
        entities = self._handler.query_offer_id_and_garbage_collect(offer_id)
        assert num_calls == len(entities[0]["CallsLastPeriod"])

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

        self._user_rates[0]["CallsLastPeriod"].append(birth_time.timestamp())

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
        self.when_create_entity("new_offer", "new_user", OFFER_QUOTA)
        self.then_incrementing_works_flawlessly("new_offer")

    def when_create_entity(self, offer_id, user_id, offer_quota):
        self._handler.create_entity(offer_id, user_id, offer_quota)

    def then_incrementing_works_flawlessly(self, offer_id):
        self._handler.increment_num_calls(offer_id)
        assert True
