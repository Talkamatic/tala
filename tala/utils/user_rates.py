import uuid
from azure.data.tables import TableServiceClient


class NoConnectionToDB(Exception):
    pass


class TableHandler():
    def __init__(self, connection_str):
        try:
            table_service = TableServiceClient.from_connection_string(conn_str=connection_str)
        except Exception:
            raise NoConnectionToDB("Table Service Client could not be reached.")
        self._table_client = table_service.get_table_client(table_name="UserRates")

    def query_user_id(self, user_id: str):
        return self._query_entities_in_handler_data("UserID", user_id)

    def query_offer_id(self, offer_id: str):
        return self._query_entities_in_handler_data("OfferID", offer_id)

    def increment_num_calls_handler(self, offer_id: str):
        entities = self.query_offer_id(offer_id)
        self._increment_calls("NumCallsHandler", entities[0])

    def increment_num_calls_buddy_generator(self, offer_id: str):
        entities = self.query_offer_id(offer_id)
        self._increment_calls("NumCallsBuddyGenerator", entities[0])

    def create_entity(self, offer_id: str, user_id: str):
        entity = {
            "PartitionKey": "HandlerData",
            "RowKey": str(uuid.uuid4()),
            "NumCallsHandler": 0,
            "OfferID": offer_id,
            "UserID": user_id
        }
        return self._table_client.create_entity(entity)

    def _increment_calls(self, key: str, entity: dict):
        if entity:
            entity[key] += 1
            self._table_client.update_entity(entity)

    def _query_entities_in_handler_data(self, key: str, value: str):
        filters = f"PartitionKey eq 'HandlerData' and {key} eq '{value}'"
        return list(self._table_client.query_entities(filters))
