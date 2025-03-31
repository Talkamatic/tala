from tala.utils import json_api

uuid_counter = 0


def reset_mock_uuid():
    global uuid_counter
    uuid_counter = 0


def mock_uuid():
    global uuid_counter
    uuid_counter += 1
    return f"uuid_{uuid_counter}"


class TestJSONAPI:
    def setup_method(self):
        self._original_uuid = json_api.uuid.uuid4
        json_api.uuid.uuid4 = mock_uuid
        reset_mock_uuid()

    def teardown_method(self):
        json_api.uuid.uuid4 = self._original_uuid

    def test_create_object(self):
        self.when_create_json_api("some-type")
        self.then_dict_is({
            "data": {
                "type": "some-type",
                "id": "uuid_1",
                "attributes": {},
                "relationships": {},
                "version:id": "2"
            },
            "included": []
        })

    def when_create_json_api(self, type_, id_=None):
        self._json_api = json_api.JSONAPIObject(type_, id_)

    def then_dict_is(self, data):
        assert data == self._json_api.as_dict

    def test_create_object_with_id(self):
        self.when_create_json_api("some-type", "some-id")
        self.then_dict_is({
            "data": {
                "type": "some-type",
                "id": "some-id",
                "attributes": {},
                "relationships": {},
                "version:id": "2"
            },
            "included": []
        })

    def test_add_attribute(self):
        self.given_json_api_created()
        self.when_add_attribute("name", "value")
        self.then_dict_is({
            "data": {
                "type": "some-type",
                "id": "uuid_1",
                "attributes": {
                    "name": "value"
                },
                "relationships": {},
                "version:id": "2"
            },
            "included": []
        })

    def given_json_api_created(self, type_="some-type"):
        self._json_api = json_api.JSONAPIObject(type_)

    def when_add_attribute(self, name, value):
        self._json_api.add_attribute(name, value)

    def test_add_relationship(self):
        self.given_json_api_created("root-type")
        self.when_add_relationship(
            "included-data", {
                "data": {
                    "type": "resource-type",
                    "id": "some-id",
                    "attributes": {
                        "name": "value"
                    },
                    "relationships": {},
                    "version:id": "2"
                },
                "included": []
            }
        )
        self.then_dict_is({
            'data': {
                'attributes': {},
                'id': 'uuid_1',
                'relationships': {
                    'included-data': {
                        'data': {
                            'id': 'some-id',
                            'type': 'resource-type',
                        },
                    },
                },
                'type': 'root-type',
                'version:id': '2',
            },
            'included': [
                {
                    'attributes': {
                        'name': 'value',
                    },
                    'id': 'some-id',
                    'relationships': {},
                    'type': 'resource-type',
                    'version:id': '2',
                },
            ],
        })

    def when_add_relationship(self, name, data):
        self._json_api.add_relationship(name, data)

    def test_add_attribute_list(self):
        self.given_json_api_created()
        self.when_add_attribute("list-attribute", [])
        self.then_dict_is({
            'data': {
                'attributes': {
                    'list-attribute': []
                },
                'id': 'uuid_1',
                'relationships': {},
                'type': 'some-type',
                'version:id': '2'
            },
            'included': []
        })

    def test_append_attribute(self):
        self.given_json_api_created()
        self.when_append_attribute("list-attribute", "item")
        self.then_dict_is({
            'data': {
                'attributes': {
                    'list-attribute': ['item']
                },
                'id': 'uuid_1',
                'relationships': {},
                'type': 'some-type',
                'version:id': '2'
            },
            'included': []
        })

    def given_attribute_added(self, name, value):
        self._json_api.add_attribute(name, value)

    def when_append_attribute(self, name, value):
        self._json_api.append_attribute(name, value)

    def test_append_relationship(self):
        self.given_json_api_created()
        self.when_append_relationship(
            "list-relationship", {
                'data': {
                    'attributes': {
                        'list-attribute': ['item']
                    },
                    'id': 'uuid_1',
                    'relationships': {},
                    'type': 'some-type',
                    'version:id': '2'
                },
                'included': []
            }
        )
        self.then_dict_is({
            'data': {
                'attributes': {},
                'id': 'uuid_1',
                'relationships': {
                    'list-relationship': {
                        'data': [{
                            'id': 'uuid_1',
                            'type': 'some-type'
                        }]
                    }
                },
                'type': 'some-type',
                'version:id': '2'
            },
            'included': [{
                'attributes': {
                    'list-attribute': ['item']
                },
                'id': 'uuid_1',
                'relationships': {},
                'type': 'some-type',
                'version:id': '2'
            }]
        })

    def when_append_relationship(self, name, data):
        self._json_api.append_relationship(name, data)

    def test_add_resource_object_with_relationships(self):
        self.given_json_api_created("root-type")
        self.when_add_relationship(
            "root-included", {
                'data': {
                    'attributes': {},
                    'id': 'uuid_1',
                    'relationships': {
                        'included-data': {
                            'data': {
                                'id': 'some-id',
                                'type': 'resource-type',
                            },
                        },
                    },
                    'type': 'root-type',
                    'version:id': '2',
                },
                'included': [
                    {
                        'attributes': {
                            'name': 'value',
                        },
                        'id': 'some-id',
                        'relationships': {},
                        'type': 'resource-type',
                        'version:id': '2',
                    },
                ],
            }
        )
        self.then_dict_is({
            'data': {
                'attributes': {},
                'id': 'uuid_1',
                'relationships': {
                    'root-included': {
                        'data': {
                            'id': 'uuid_1',
                            'type': 'root-type'
                        }
                    }
                },
                'type': 'root-type',
                'version:id': '2'
            },
            'included': [{
                'attributes': {
                    'name': 'value'
                },
                'id': 'some-id',
                'relationships': {},
                'type': 'resource-type',
                'version:id': '2'
            }, {
                'attributes': {},
                'id': 'uuid_1',
                'relationships': {
                    'included-data': {
                        'data': {
                            'id': 'some-id',
                            'type': 'resource-type'
                        }
                    }
                },
                'type': 'root-type',
                'version:id': '2'
            }]
        })
