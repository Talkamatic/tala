import copy
from datetime import timedelta, datetime
import json
import uuid
import time

from azure.data.tables import TableServiceClient

from tala.utils import user_rates_constants as constants

DEFAULT_AGE_LIMIT = 60


class NoConnectionToDB(Exception):
    pass


class OfferNotInDB(Exception):
    pass


class AbstractTableHandler():
    def __init__(self, connection_str: str):
        try:
            table_service = TableServiceClient.from_connection_string(conn_str=connection_str)
        except Exception:
            raise NoConnectionToDB("Table Service Client could not be reached.")
        self._table_client = table_service.get_table_client(table_name=constants.USER_RATES)

    def query_user_id(self, user_id: str):
        return self._query_entities(constants.OFFER_AUTHOR_ID, user_id)

    def query_author_user_id(self, author_user_id: str):
        return self._query_entities(constants.AUTHOR_ID, author_user_id)

    def query_offer_id(self, offer_id: str):
        return self._query_entities(constants.OFFER_ID, offer_id)

    def update_author_quota(self, author_user_id: str, author_quota: int):
        entity = self.query_author_user_id(author_user_id)[0]
        entity[constants.AUTHOR_QUOTA] = author_quota
        self._update_entity(entity)

    def _create_entity(self, entity: dict):
        table_entity = self._dump_json_fields(copy.deepcopy(entity))
        self._table_client.create_entity(table_entity)

    def _dump_json_fields(self, entity: dict):
        for field in self.fields_to_jsonify:
            try:
                entity[field] = json.dumps(entity[field])
            except KeyError:
                pass
        return entity

    def _load_json_fields(self, entity: dict):
        for field in self.fields_to_jsonify:
            try:
                entity[field] = json.loads(entity[field])
            except KeyError:
                pass
        return entity

    def _increment_calls(self, key: str, entity: dict):
        if entity:
            entity[key] += 1
            self._update_entity(entity)

    def _query_entities(self, key: str, value: str):
        filters = f"PartitionKey eq '{self.partition_key}' and {key} eq '{value}'"
        entities = list(self._table_client.query_entities(filters))
        for entity in entities:
            self._load_json_fields(entity)
        return entities

    def _update_entity(self, entity: dict):
        table_entity = self._dump_json_fields(copy.deepcopy(entity))
        self._table_client.update_entity(table_entity)


class HandlerUserRates(AbstractTableHandler):
    partition_key = constants.HANDLER_DATA
    fields_to_jsonify = [constants.CALLS_LAST_PERIOD]

    def create_entity(self, offer_id: str, user_id: str, offer_quota: int):
        entity = self._make_new_entity(offer_id, user_id, offer_quota)
        self._create_entity(entity)

    def create_entity_author_quota(self, user_id: str, author_quota: int):
        entity = self._make_new_entity_author_quota(user_id, author_quota)
        self._create_entity(entity)

    def query_offer_id_and_garbage_collect(self, offer_id: str, age_limit=DEFAULT_AGE_LIMIT):
        def garbage_collect(entity, age_limit=DEFAULT_AGE_LIMIT):
            to_remove = []
            now = datetime.now()
            for timestamp in entity.get(constants.CALLS_LAST_PERIOD, []):
                if datetime.fromtimestamp(timestamp) + timedelta(minutes=age_limit) < now:
                    to_remove.append(timestamp)
                else:
                    break
            for item in to_remove:
                entity[constants.CALLS_LAST_PERIOD].remove(item)

        entities = self.query_offer_id(offer_id)
        for entity in entities:
            garbage_collect(entity, age_limit)
            self._update_entity(entity)
        return entities

    def increment_num_calls(self, offer_id, age_limit=DEFAULT_AGE_LIMIT):
        def increment_calls(entity):
            if entity[constants.NUM_CALLS] < 0:
                pass
            else:
                entity[constants.NUM_CALLS] += 1

        def log_call_in_last_period(entity):
            try:
                entity[constants.CALLS_LAST_PERIOD].append(time.time())
            except KeyError:
                entity[constants.CALLS_LAST_PERIOD] = [time.time()]

        def get_entry_for_offer_id(offer_id):
            try:
                return self.query_offer_id(offer_id)[0]
            except IndexError:
                raise OfferNotInDB(f"Offer {offer_id} was not found in DB")
            except TypeError:
                raise OfferNotInDB(f"Offer {offer_id} was not found in DB")

        entity = get_entry_for_offer_id(offer_id)
        increment_calls(entity)
        log_call_in_last_period(entity)
        self._update_entity(entity)

    def update_offer_quota(self, offer_id: str, offer_quota: int):
        entity = self.query_offer_id(offer_id)[0]
        entity[constants.OFFER_QUOTA] = offer_quota
        self._update_entity(entity)

    def _make_new_entity(self, offer_id: str, user_id: str, offer_quota: int):
        return {
            constants.PARTITION_KEY: self.partition_key,
            constants.ROW_KEY: str(uuid.uuid4()),
            constants.NUM_CALLS: 0,
            constants.CALLS_LAST_PERIOD: [],
            constants.OFFER_ID: offer_id,
            constants.OFFER_AUTHOR_ID: user_id,
            constants.OFFER_QUOTA: offer_quota
        }

    def _make_new_entity_author_quota(self, user_id: str, author_quota: int):
        return {
            constants.PARTITION_KEY: self.partition_key,
            constants.ROW_KEY: str(uuid.uuid4()),
            constants.AUTHOR_ID: user_id,
            constants.AUTHOR_QUOTA: author_quota
        }


class BuddyGeneratorUserRates(AbstractTableHandler):
    partition_key = constants.BUDDY_GENERATOR_DATA
    fields_to_jsonify = []

    def create_entity(self, user_id: str, author_quota: int):
        entity = self._make_new_entity(user_id, author_quota)
        self._create_entity(entity)

    def increment_num_calls(self, user_id: str):
        entities = self.query_author_user_id(user_id)
        self._increment_calls(constants.NUM_CALLS, entities[0])

    def _make_new_entity(self, author_user_id: str, author_quota: int):
        return {
            constants.PARTITION_KEY: self.partition_key,
            constants.ROW_KEY: str(uuid.uuid4()),
            constants.NUM_CALLS: 0,
            constants.AUTHOR_ID: author_user_id,
            constants.AUTHOR_QUOTA: author_quota
        }
