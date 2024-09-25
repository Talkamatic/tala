from datetime import timedelta, datetime
import uuid
import time

from azure.data.tables import TableServiceClient

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
        self._table_client = table_service.get_table_client(table_name="UserRates")

    def query_user_id(self, user_id: str):
        return self._query_entities("UserID", user_id)

    def query_offer_id(self, offer_id: str):
        return self._query_entities("OfferID", offer_id)

    def _increment_calls(self, key: str, entity: dict):
        if entity:
            entity[key] += 1
            self._table_client.update_entity(entity)

    def _query_entities(self, key: str, value: str):
        filters = f"PartitionKey eq '{self.partition_key}' and {key} eq '{value}'"
        return list(self._table_client.query_entities(filters))


class HandlerUserRates(AbstractTableHandler):
    partition_key = "HandlerData"

    def create_entity(self, offer_id: str, user_id: str, offer_quota: int):
        self._table_client.create_entity(self._make_new_entity(offer_id, user_id, offer_quota))

    def create_entity_author_quota(self, user_id: str, author_quota: int):
        self._table_client.create_entity(self._make_new_entity_author_quota(user_id, author_quota))

    def query_offer_id_and_garbage_collect(self, offer_id: str, age_limit=DEFAULT_AGE_LIMIT):
        def garbage_collect(entity, age_limit=DEFAULT_AGE_LIMIT):
            to_remove = []
            now = datetime.now()
            for timestamp in entity.get("CallsLastPeriod", []):
                if datetime.fromtimestamp(timestamp) + timedelta(minutes=age_limit) < now:
                    to_remove.append(timestamp)
                else:
                    break
            for item in to_remove:
                entity["CallsLastPeriod"].remove(item)

        entities = self.query_offer_id(offer_id)
        for entity in entities:
            garbage_collect(entity, age_limit)
            self._table_client.update_entity(entity)
        return entities

    def increment_num_calls(self, offer_id, age_limit=DEFAULT_AGE_LIMIT):
        def increment_calls(entity):
            if entity["NumCalls"] < 0:
                pass
            else:
                entity["NumCalls"] += 1

        def log_call_in_last_period(entity):
            try:
                entity["CallsLastPeriod"].append(time.time())
            except KeyError:
                entity["CallsLastPeriod"] = [time.time()]

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
        self._table_client.update_entity(entity)

    def _make_new_entity(self, offer_id: str, user_id: str, offer_quota: int):
        return {
            "PartitionKey": self.partition_key,
            "RowKey": str(uuid.uuid4()),
            "NumCalls": 0,
            "CallsLastPeriod": [],
            "OfferID": offer_id,
            "UserID": user_id,
            "OfferQuota": offer_quota
        }

    def _make_new_entity_author_quota(self, user_id: str, author_quota: int):
        return {
            "PartitionKey": self.partition_key,
            "RowKey": str(uuid.uuid4()),
            "UserID": user_id,
            "AuthorQuota": author_quota
        }


class BuddyGeneratorUserRates(AbstractTableHandler):
    partition_key = "BuddyGeneratorData"

    def create_entity(self, user_id: str, author_quota: int):
        self._table_client.create_entity(self._make_new_entity(user_id, author_quota))

    def increment_num_calls(self, user_id: str):
        entities = self.query_user_id(user_id)
        self._increment_calls("NumCalls", entities[0])

    def _make_new_entity(self, user_id: str, author_quota: int):
        return {
            "PartitionKey": self.partition_key,
            "RowKey": str(uuid.uuid4()),
            "NumCalls": 0,
            "UserID": user_id,
            "AuthorQuota": author_quota
        }
