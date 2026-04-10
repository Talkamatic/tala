from tala.testing.json_api_assertions import normalize_expected_json_api
from tala.utils import json_api


class DummyJSONAPI(json_api.JSONAPIMixin):
    def __init__(self, name):
        self.name = name

    @property
    def json_api_attributes(self):
        return ["name"]


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
                "meta": {
                    "version:id": "2"
                }
            },
            "included": []
        })

    def when_create_json_api(self, type_, id_=None):
        self._json_api = json_api.JSONAPIObject(type_, id_)

    def then_dict_is(self, data):
        expected = normalize_expected_json_api(data)
        assert expected == self._json_api.as_dict

    def test_create_object_with_id(self):
        self.when_create_json_api("some-type", "some-id")
        self.then_dict_is({
            "data": {
                "type": "some-type",
                "id": "some-id",
                "attributes": {},
                "relationships": {},
                "meta": {
                    "version:id": "2"
                }
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
                "meta": {
                    "version:id": "2"
                }
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
                    "meta": {
                        "version:id": "2"
                    }
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
                'meta': {
                    'version:id': '2'
                },
            },
            'included': [
                {
                    'attributes': {
                        'name': 'value',
                    },
                    'id': 'some-id',
                    'relationships': {},
                    'type': 'resource-type',
                    'meta': {
                        'version:id': '2'
                    },
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
                'meta': {
                    'version:id': '2'
                }
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
                'meta': {
                    'version:id': '2'
                }
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
                    'meta': {
                        'version:id': '2'
                    }
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
                'meta': {
                    'version:id': '2'
                }
            },
            'included': [{
                'attributes': {
                    'list-attribute': ['item']
                },
                'id': 'uuid_1',
                'relationships': {},
                'type': 'some-type',
                'meta': {
                    'version:id': '2'
                }
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
                    'meta': {
                        'version:id': '2'
                    },
                },
                'included': [
                    {
                        'attributes': {
                            'name': 'value',
                        },
                        'id': 'some-id',
                        'relationships': {},
                        'type': 'resource-type',
                        'meta': {
                            'version:id': '2'
                        },
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
                'meta': {
                    'version:id': '2'
                }
            },
            'included': [{
                'attributes': {
                    'name': 'value'
                },
                'id': 'some-id',
                'relationships': {},
                'type': 'resource-type',
                'meta': {
                    'version:id': '2'
                }
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
                'meta': {
                    'version:id': '2'
                }
            }]
        })


class TestJSONAPICompatibility:
    def test_create_object_from_dict_without_included(self):
        self.given_json_api_payload_without_included()

        self.when_creating_object_from_dict()

        self.then_included_is_empty()

    def test_has_relationship_for_list_and_to_one(self):
        self.given_json_api_object()
        self.given_list_relationship()
        self.given_to_one_relationship()

        self.when_checking_relationships()

        self.then_relationships_match()

    def test_get_data_for_relationship_variants(self):
        self.given_included_objects()
        self.given_relationships_for_data()

        self.when_loading_relationship_data()

        self.then_relationship_data_matches()

    def test_missing_relationships_returns_none(self):
        self.given_included_objects()
        self.given_data_without_relationships()

        self.when_loading_missing_relationship()

        self.then_missing_relationship_is_none()

    def test_default_json_api_id_collides(self):
        self.given_two_json_api_objects()

        self.when_including_resources()

        self.then_all_resources_are_present()

    def test_included_merge_and_type_resolution(self):
        self.given_included_with_same_id()
        self.given_relationship_with_type_variant()

        self.when_loading_included_relationship()

        self.then_included_is_merged()

    def test_create_object_without_relationships_or_attributes(self):
        self.given_json_api_payload_minimal()

        self.when_creating_object_from_dict()

        self.then_missing_fields_defaulted()

    def test_prefers_meta_version_over_legacy(self):
        self.given_payload_with_meta_and_legacy_version()

        self.when_creating_object_from_dict()

        self.then_version_is_meta()

    def test_accepts_legacy_version_when_meta_missing(self):
        self.given_payload_with_legacy_version_only()

        self.when_creating_object_from_dict()

        self.then_version_is_legacy()

    def given_json_api_payload_without_included(self):
        self._payload = {
            "data": {
                "type": "some-type",
                "id": "some-id",
                "attributes": {},
                "relationships": {},
            }
        }

    def given_json_api_payload_minimal(self):
        self._payload = {
            "data": {
                "type": "some-type",
                "id": "some-id",
            }
        }

    def given_two_json_api_objects(self):
        first = DummyJSONAPI("first").as_json_api_dict()["data"]
        second = DummyJSONAPI("second").as_json_api_dict()["data"]
        self._items = [first, second]

    def when_including_resources(self):
        self._included = json_api.IncludedObject(self._items)

    def then_all_resources_are_present(self):
        assert len(self._included.as_list) == 2

    def given_payload_with_meta_and_legacy_version(self):
        self._payload = {
            "data": {
                "type": "some-type",
                "id": "some-id",
                "meta": {
                    "version:id": "3"
                },
                "version:id": "2",
            }
        }

    def given_payload_with_legacy_version_only(self):
        self._payload = {
            "data": {
                "type": "some-type",
                "id": "some-id",
                "version:id": "2",
            }
        }

    def when_creating_object_from_dict(self):
        self._json_api = json_api.JSONAPIObject.create_from_dict(self._payload)

    def then_included_is_empty(self):
        assert self._json_api.as_dict["included"] == []

    def then_missing_fields_defaulted(self):
        assert self._json_api.as_dict["data"]["attributes"] == {}
        assert self._json_api.as_dict["data"]["relationships"] == {}

    def then_version_is_meta(self):
        version = self._json_api.as_dict["data"]["meta"]["version:id"]
        assert version == "3"

    def then_version_is_legacy(self):
        version = self._json_api.as_dict["data"]["meta"]["version:id"]
        assert version == "2"

    def given_json_api_object(self):
        self._json_api = json_api.JSONAPIObject("root")

    def given_list_relationship(self):
        self._json_api.relationships["items"] = {
            "data": [
                {
                    "type": "some",
                    "id": "one"
                },
                {
                    "type": "some",
                    "id": "two"
                },
            ]
        }

    def given_to_one_relationship(self):
        self._json_api.relationships["single"] = {"data": {"type": "other", "id": "only"}}

    def when_checking_relationships(self):
        self._has_item_one = self._json_api.has_relationship("items", "one")
        self._has_item_three = self._json_api.has_relationship("items", "three")
        self._has_single = self._json_api.has_relationship("single", "only")

    def then_relationships_match(self):
        assert self._has_item_one is True
        assert self._has_item_three is False
        assert self._has_single is True

    def given_included_objects(self):
        self._included = json_api.IncludedObject([
            {
                "type": "thing",
                "id": "a",
                "attributes": {},
                "relationships": {}
            },
            {
                "type": "thing",
                "id": "b",
                "attributes": {},
                "relationships": {}
            },
        ])

    def given_data_without_relationships(self):
        self._data = {}

    def given_relationships_for_data(self):
        self._data = {
            "relationships": {
                "to_many": {
                    "data": [
                        {
                            "type": "thing",
                            "id": "a"
                        },
                        {
                            "type": "thing",
                            "id": "b"
                        },
                    ]
                },
                "to_one": {
                    "data": {
                        "type": "thing",
                        "id": "a"
                    }
                },
                "empty": {
                    "data": None
                },
            }
        }

    def when_loading_relationship_data(self):
        self._to_many = self._included.get_data_for_relationship("to_many", self._data)
        self._to_one = self._included.get_data_for_relationship("to_one", self._data)
        self._empty = self._included.get_data_for_relationship("empty", self._data)

    def when_loading_missing_relationship(self):
        self._missing = self._included.get_data_for_relationship("missing", self._data)

    def then_relationship_data_matches(self):
        to_many_ids = []
        for item in self._to_many or []:
            getter = getattr(item, "get", None)
            if getter is None:
                assert False, "Expected included items to be dict-like"
            to_many_ids.append(getter("id"))
        if not to_many_ids:
            assert False, "Expected to_many relationship to resolve"
        assert to_many_ids == ["a", "b"]

        getter = getattr(self._to_one, "get", None)
        if getter is None:
            assert False, "Expected to_one relationship to resolve"
        to_one_id = getter("id")
        assert to_one_id == "a"
        assert self._empty is None

    def then_missing_relationship_is_none(self):
        assert self._missing is None

    def given_included_with_same_id(self):
        self._included = json_api.IncludedObject([
            {
                "type": "tala.model.domain.Domain",
                "id": "hello_world",
                "attributes": {
                    "name": "old"
                },
                "relationships": {
                    "plans": {
                        "data": []
                    }
                },
            },
            {
                "type": "tala.model.domain.Domain",
                "id": "hello_world",
                "attributes": {
                    "name": "new",
                    "extra": "x"
                },
                "relationships": {
                    "questions": {
                        "data": []
                    }
                },
            },
        ])

    def given_relationship_with_type_variant(self):
        self._data = {
            "relationships": {
                "domain": {
                    "data": {
                        "type": "tala.model.domain",
                        "id": "hello_world"
                    }
                },
            }
        }

    def when_loading_included_relationship(self):
        self._resolved_domain = self._included.get_data_for_relationship("domain", self._data)

    def then_included_is_merged(self):
        getter = getattr(self._resolved_domain, "get", None)
        if getter is None:
            assert False, "Expected merged included object"
        assert getter("attributes").get("name") == "new"
        assert getter("attributes").get("extra") == "x"
        assert "plans" in getter("relationships")
        assert "questions" in getter("relationships")
