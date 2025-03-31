import uuid
import json

CURRENT_FORMAT_VERSION = "2"


class NotImplementedException(BaseException):
    pass


def get_attribute(attribute_name, data):
    return data["attributes"][attribute_name]


def get_object_from_relationship(included, key):
    for item in included:
        if item["type"] == key["type"] and item["id"] == key["id"]:
            return item


class IncludedObject:
    def __init__(self, included_data):
        self._data = {}
        for item in included_data:
            self.include(item)

    def include(self, item):
        type_ = item["type"]
        id_ = item["id"]

        if type_ not in self._data:
            self._data[type_] = {}
        if id_ not in self._data[type_]:
            self._data[type_][id_] = item

    def get_object_from_relationship(self, key):
        return self._data[key["type"]][key["id"]]

    def get_data_for_relationship(self, relationship_name, data):
        return self.get_object_from_relationship(data["relationships"][relationship_name]["data"])

    @property
    def as_list(self):
        included = []
        for type_ in self._data:
            for id_ in self._data[type_]:
                included.append(self._data[type_][id_])
        return included


class JSONAPIMixin:
    @classmethod
    def create_from_json_api_string(cls, json_string):
        raise NotImplementedException("The method 'create_from_json_api_string' is not implemented.")

    @classmethod
    def create_from_json_api_data(cls, json_string):
        raise NotImplementedException("The method 'create_from_json_api_data' is not implemented.")

    @property
    def as_json_api_string(self):
        obj_as_dict = self.as_json_api_dict()

        obj_as_dict["included"] = sorted(obj_as_dict["included"], key=lambda d: f"{d['type']}{d['id']}")

        return json.dumps(obj_as_dict)
        # return json.dumps(obj_as_dict, indent=4)

    def as_json_api_dict(self):
        def get_relationship(name):
            target = self.__getattribute__(name)
            try:
                return target.as_json_api_dict()
            except AttributeError:
                return None

        obj = JSONAPIObject(self.json_api_type, self.json_api_id, {}, {}, [])
        for attribute in self.json_api_attributes:
            obj.add_attribute(attribute, self.__getattribute__(attribute))
        for relationship_name in self.json_api_relationships:
            relationship = get_relationship(relationship_name)
            if relationship:
                obj.add_relationship(relationship_name, relationship)
        return obj.as_dict

    @property
    def json_api_type(self):
        type_ = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return type_

    @property
    def json_api_id(self):
        return self.json_api_type

    @property
    def json_api_attributes(self):
        return []

    @property
    def json_api_relationships(self):
        return []


class JSONAPIObject:
    @classmethod
    def create_from_dict(cls, json_data):
        data = json_data["data"]
        included = json_data["included"]

        return cls(data["type"], data["id"], data["attributes"], data["relationships"], included)

    def __init__(self, type_, id_=None, attributes=None, relationships=None, included=None):
        self.type_ = type_
        self.id_ = id_ if id_ else str(uuid.uuid4())
        self.attributes = attributes if attributes else {}
        self.relationships = relationships if relationships else {}

        included = included if included else []
        self.included = IncludedObject(included)

    def set_id(self, id_):
        self.id_ = id_

    def set_type(self, type_):
        self.type_ = type_

    def add_relationship(self, name, entry):
        if entry == []:
            self.relationships[name] = {"data": []}
        else:
            self.relationships[name] = {"data": {"type": entry["data"]["type"], "id": entry["data"]["id"]}}
            if isinstance(entry["included"], dict):
                self.include(entry["included"])
            else:
                for item in entry["included"]:
                    self.include(item)
            self.include(entry["data"])

    def add_relationship_no_include(self, name, entry):
        self.relationships[name] = {"data": {"type": entry["data"]["type"], "id": entry["data"]["id"]}}

    def append_relationship(self, name, entry):
        if name not in self.relationships:
            self.relationships[name] = {"data": []}

        self.relationships[name]["data"].append({"type": entry["data"]["type"], "id": entry["data"]["id"]})
        for item in entry["included"]:
            self.include(item)
        self.include(entry["data"])

    def has_relationship(self, name, id_):
        if name in self.relationships:
            if type(self.relationships[name]["data"] is list):
                for item in self.relationships[name]["data"]:
                    if item["id"] == id_:
                        return True
                return False
            else:
                return self.relationships[name]["data"]["id"] == id_

    def add_attribute(self, name, entry):
        self.attributes[name] = entry

    def append_attribute(self, name, entry):
        if name not in self.attributes:
            self.attributes[name] = []

        self.attributes[name].append(entry)

    def include(self, data):
        if data:
            self.included.include(data)

    @property
    def as_dict(self):
        return {
            "data": {
                "type": self.type_,
                "id": self.id_,
                "version:id": "2",
                "attributes": self.attributes,
                "relationships": self.relationships
            },
            "included": self.included.as_list
        }

    @property
    def as_json(self):
        return json.dumps(self.as_dict, indent=4)
