import uuid
from azure.data.tables import TableServiceClient


class NoConnectionToDB(Exception):
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

    def increment_num_calls(self, offer_id: str):
        entities = self.query_offer_id(offer_id)
        self._increment_calls("NumCalls", entities[0])

    def _make_new_entity(self, offer_id: str, user_id: str, offer_quota: int):
        return {
            "PartitionKey": self.partition_key,
            "RowKey": str(uuid.uuid4()),
            "NumCalls": 0,
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
