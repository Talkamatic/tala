import importlib
import json
import uuid

CURRENT_FORMAT_VERSION = "2"


class NotImplementedException(BaseException):
    pass


def get_attribute(attribute_name, data):
    return data["attributes"][attribute_name]


def require_attributes(payload, label="payload"):
    try:
        data = payload["data"]
        attributes = data["attributes"]
    except (TypeError, KeyError):
        raise ValueError(f"Expected JSON:API {label} payload with data.attributes.")
    return attributes


def make_document(type_, id_, attributes, included=None, version=CURRENT_FORMAT_VERSION):
    data = {"type": type_, "id": id_, "attributes": attributes, "meta": {"version:id": version}}
    return {"data": data, "included": included or []}


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
        item = self._normalize_version_entry(item)
        type_ = item["type"]
        id_ = item["id"]

        if type_ not in self._data:
            self._data[type_] = {}
        if id_ not in self._data[type_]:
            self._data[type_][id_] = item
            return
        existing = self._data[type_][id_]
        self._data[type_][id_] = self._merge_included(existing, item)

    def _merge_included(self, existing, incoming):
        merged = dict(existing)
        attributes = dict(existing.get("attributes", {}))
        relationships = dict(existing.get("relationships", {}))
        try:
            attributes.update(incoming.get("attributes", {}))
        except AttributeError:
            pass
        try:
            relationships.update(incoming.get("relationships", {}))
        except AttributeError:
            pass
        merged.update(incoming)
        merged["attributes"] = attributes
        merged["relationships"] = relationships
        return merged

    def _normalize_version_entry(self, item):
        if not isinstance(item, dict):
            return item
        normalized = dict(item)
        attributes = normalized.get("attributes")
        meta = normalized.get("meta")
        version = normalized.get("version:id")

        if isinstance(attributes, dict) and "version:id" in attributes:
            if version is None:
                version = attributes.get("version:id")
            attributes = dict(attributes)
            attributes.pop("version:id", None)
            normalized["attributes"] = attributes

        if version is not None:
            if not isinstance(meta, dict):
                meta = {}
            else:
                meta = dict(meta)
            meta["version:id"] = version
            normalized["meta"] = meta
            normalized.pop("version:id", None)

        return normalized

    def _resolve_type(self, type_):
        if type_ in self._data:
            return type_
        try:
            base_type = type_.rsplit(".", 1)[0]
        except AttributeError:
            return None
        if base_type in self._data:
            return base_type
        matches = [candidate for candidate in self._data if candidate.startswith(f"{type_}.")]
        if len(matches) == 1:
            return matches[0]
        return None

    def get_object_from_relationship(self, key):
        try:
            type_ = key["type"]
            id_ = key["id"]
        except (TypeError, KeyError):
            return None
        resolved_type = self._resolve_type(type_)
        if resolved_type is None:
            return None
        return self._data.get(resolved_type, {}).get(id_)

    def get_data_for_relationship(self, relationship_name, data):
        try:
            relationships = data["relationships"]
        except (TypeError, KeyError):
            return None
        relationship = relationships.get(relationship_name, {})
        rel_data = relationship.get("data")
        if rel_data is None:
            return None
        try:
            rel_data[0]
        except (TypeError, KeyError, IndexError):
            return self.get_object_from_relationship(rel_data)
        return [self.get_object_from_relationship(item) for item in rel_data]

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
            try:
                target = self.__getattribute__(name)
            except AttributeError as exc:
                raise ValueError(f"JSON:API relationship '{name}' not found on {self.__class__.__name__}") from exc
            return as_json_api_entry(target)

        obj = JSONAPIObject(self.json_api_type, id_=self.json_api_id)
        for attribute in self.json_api_attributes:
            obj.add_attribute(attribute, self.__getattribute__(attribute))
        for relationship_name in self.json_api_relationships:
            relationship = get_relationship(relationship_name)
            obj.add_relationship(relationship_name, relationship)
        return obj.as_dict

    @property
    def json_api_type(self):
        type_ = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return type_

    @property
    def json_api_id(self):
        try:
            return self._json_api_id
        except AttributeError:
            new_id = f"{self.json_api_type}:{uuid.uuid4()}"
            try:
                setattr(self, "_json_api_id", new_id)
            except Exception:
                return self.json_api_type
            return new_id

    @property
    def json_api_version(self):
        return CURRENT_FORMAT_VERSION

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
        included = json_data.get("included", [])
        attributes = data.get("attributes", {})
        attr_version = None
        if isinstance(attributes, dict):
            attributes = dict(attributes)
            attr_version = attributes.pop("version:id", None)
        relationships = data.get("relationships", {})
        version = None
        try:
            version = data["meta"].get("version:id")
        except (TypeError, KeyError, AttributeError):
            version = None
        if not version:
            try:
                version = data["version:id"]
            except (TypeError, KeyError):
                version = None
        if not version and attr_version:
            version = attr_version
        if not version:
            version = CURRENT_FORMAT_VERSION

        return cls(data["type"], data["id"], attributes, relationships, included, version=version)

    def __init__(
        self, type_, id_=None, attributes=None, relationships=None, included=None, version=CURRENT_FORMAT_VERSION
    ):
        self.type_ = type_
        self.id_ = id_ if id_ else str(uuid.uuid4())
        self.attributes = attributes if attributes else {}
        self.relationships = relationships if relationships else {}
        self.included = IncludedObject(included if included else [])
        self.version = version

    def set_id(self, id_):
        self.id_ = id_

    def set_type(self, type_):
        self.type_ = type_

    def add_relationship(self, name, entry):
        if entry == []:
            self.relationships[name] = {"data": []}
            return

        data = entry.get("data")
        if data is None:
            self.relationships[name] = {"data": None}
            return

        try:
            data[0]
        except (TypeError, KeyError, IndexError):
            self.relationships[name] = {"data": {"type": data["type"], "id": data["id"]}}
        else:
            self.relationships[name] = {"data": [{"type": item["type"], "id": item["id"]} for item in data]}

        included = entry.get("included", [])
        try:
            for item in included:
                self.include(item)
        except TypeError:
            self.include(included)
        try:
            data[0]
        except (TypeError, KeyError, IndexError):
            self.include(data)
        else:
            for item in data:
                self.include(item)

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
            data = self.relationships[name]["data"]
            if data is None:
                return False
            try:
                data[0]
            except (TypeError, KeyError, IndexError):
                return data["id"] == id_
            for item in data:
                if item["id"] == id_:
                    return True
            return False

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
                "attributes": self.attributes,
                "relationships": self.relationships,
                "meta": {
                    "version:id": self.version,
                },
            },
            "included": self.included.as_list
        }

    @property
    def as_json(self):
        return json.dumps(self.as_dict, indent=4)


def _is_string_like(value):
    try:
        value.encode
        value.split
    except AttributeError:
        return False
    return True


def _is_move_like(value):
    is_move = getattr(value, "is_move", None)
    if callable(is_move):
        try:
            return is_move()
        except Exception:
            return False
    return False


def move_as_json_api_entry(move):
    return move.as_json_api_dict()


def as_json_api_entry(value):
    if value is None:
        return {"data": None, "included": []}
    if _is_string_like(value) or type(value) in (int, float, bool):
        scalar_obj = JSONAPIObject("tdm.tis.scalar", attributes={"value": value})
        return scalar_obj.as_dict
    obj_id = id(value)
    if obj_id in _JSON_API_ENTRY_STACK:
        raise ValueError(
            f"JSON:API serialization cycle detected for {value.__class__.__name__}"
        )
    _JSON_API_ENTRY_STACK.append(obj_id)
    try:
        if _is_move_like(value):
            return move_as_json_api_entry(value)
        as_json_api_dict = getattr(value, "as_json_api_dict", None)
        if callable(as_json_api_dict):
            try:
                return as_json_api_dict()
            except TypeError as exc:
                if not _is_argument_mismatch(exc):
                    raise
        items = getattr(value, "items", None)
        if callable(items):
            return map_as_json_api_entry(value)
        iterator = getattr(value, "__iter__", None)
        if callable(iterator) and not _is_string_like(value):
            try:
                value[0]
            except (TypeError, KeyError, IndexError):
                length = getattr(value, "__len__", None)
                if callable(length):
                    try:
                        if len(value) == 0:
                            return list_as_json_api_entry([])
                    except Exception:
                        pass
            else:
                return list_as_json_api_entry(value)
        raise ValueError(
            f"JSON:API serialization not implemented for {value.__class__.__module__}."
            f"{value.__class__.__name__}"
        )
    finally:
        _JSON_API_ENTRY_STACK.pop()


def list_as_json_api_entry(items, id_=None, type_="tdm.tis.list"):
    list_obj = JSONAPIObject(type_, id_=id_)
    if items is None:
        return list_obj.as_dict
    for item in items:
        list_obj.append_relationship("items", as_json_api_entry(item))
    return list_obj.as_dict


def map_as_json_api_entry(map_value, id_=None, type_="tdm.tis.map"):
    map_obj = JSONAPIObject(type_, id_=id_)
    if not map_value:
        return map_obj.as_dict
    for index, (key, value) in enumerate(map_value.items()):
        entry_id = f"map_entry:{id(map_value)}:{index}"
        if id_ is not None:
            entry_id = f"{id_}:entry:{index}"
        entry = JSONAPIObject("tdm.tis.map_entry", id_=entry_id)
        entry.add_relationship("key", as_json_api_entry(key))
        entry.add_relationship("value", as_json_api_entry(value))
        map_obj.append_relationship("entries", entry.as_dict)
    return map_obj.as_dict


def _coerce_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _move_kwargs_from_attributes(attributes):
    kwargs = {
        "understanding_confidence": _coerce_float(attributes.get("understanding_confidence")),
        "speaker": attributes.get("speaker"),
        "modality": attributes.get("modality"),
        "utterance": attributes.get("utterance"),
        "ddd_name": attributes.get("ddd"),
        "perception_confidence": _coerce_float(attributes.get("perception_confidence")),
    }
    if "weighted_understanding_confidence" in attributes:
        kwargs["weighted_understanding_confidence"] = _coerce_float(
            attributes.get("weighted_understanding_confidence")
        )
    return kwargs


def _content_from_relationship(entry, included):
    content_data = included.get_data_for_relationship("content", entry)
    if content_data is None:
        return None
    return create_from_json_api_data(content_data, included)


def _arguments_from_relationship(entry, included):
    args_data = included.get_data_for_relationship("arguments", entry)
    if args_data is None:
        return None
    parsed = create_from_json_api_data(args_data, included)
    if parsed is None:
        return []
    if isinstance(parsed, list):
        return parsed
    return [parsed]


def _create_icm_move(move_type, content, content_speaker, polarity, kwargs):
    from tala.model.move_icm import ICM

    icm_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in ("understanding_confidence", "speaker", "ddd_name", "perception_confidence")
    }

    if content is not None:
        if move_type == ICM.CARDINAL_SEQUENCING:
            try:
                content = int(content)
            except (TypeError, ValueError):
                pass
        move = ICM.create(
            move_type,
            content=content,
            content_speaker=content_speaker,
            polarity=polarity,
            **icm_kwargs,
        )
    else:
        move = ICM(move_type, polarity=polarity, **icm_kwargs)

    weighted = kwargs.get("weighted_understanding_confidence")
    if weighted is not None:
        move.weighted_understanding_confidence = weighted
    return move


def _create_move_from_json_api_data(entry, included):
    from tala.model.move_base import (
        Answer,
        Ask,
        Greet,
        Insult,
        InsultResponse,
        Mute,
        NoMove,
        Prereport,
        Quit,
        Report,
        Request,
        ThankYou,
        ThankYouResponse,
        Unmute,
        Move,
    )
    from tala.model.move_icm import ICM

    attributes = entry.get("attributes", {})
    move_type = attributes.get("move_type")
    if not move_type:
        return None

    kwargs = _move_kwargs_from_attributes(attributes)
    content = _content_from_relationship(entry, included)
    content_speaker = attributes.get("content_speaker")
    polarity = attributes.get("polarity")

    icm_types = {
        ICM.PER,
        ICM.ACC,
        ICM.UND,
        ICM.SEM,
        ICM.RERAISE,
        ICM.ACCOMMODATE,
        ICM.LOADPLAN,
        ICM.RESUME,
        ICM.CARDINAL_SEQUENCING,
        ICM.REPORT_INFERENCE,
    }
    if move_type in icm_types:
        return _create_icm_move(move_type, content, content_speaker, polarity, kwargs)

    if move_type == Move.ANSWER:
        return Answer(content, **kwargs)
    if move_type == Move.ASK:
        return Ask(content, **kwargs)
    if move_type == Move.REQUEST:
        return Request(content, **kwargs)
    if move_type == Move.REPORT:
        return Report(content, **kwargs)
    if move_type == Move.PREREPORT:
        arguments = _arguments_from_relationship(entry, included)
        if arguments is None:
            arguments = attributes.get("arguments") or []
        service_action = attributes.get("service_action")
        ontology_name = attributes.get("ontology_name")
        return Prereport(ontology_name, service_action, arguments)
    if move_type == Move.GREET:
        return Greet(**kwargs)
    if move_type == Move.THANK_YOU:
        return ThankYou(**kwargs)
    if move_type == Move.THANK_YOU_RESPONSE:
        return ThankYouResponse(**kwargs)
    if move_type == Move.INSULT:
        return Insult(**kwargs)
    if move_type == Move.INSULT_RESPONSE:
        return InsultResponse(**kwargs)
    if move_type == Move.MUTE:
        return Mute(**kwargs)
    if move_type == Move.UNMUTE:
        return Unmute(**kwargs)
    if move_type == Move.QUIT:
        return Quit(**kwargs)
    if move_type == Move.NO_MOVE:
        return NoMove(**kwargs)

    raise ValueError(f"Unsupported move_type '{move_type}' in JSON:API payload")


def _is_argument_mismatch(exc):
    message = str(exc)
    if "positional" in message and "given" in message:
        return True
    return "missing" in message and "required positional" in message


def _call_create_from_json_api_data(create_from_json_api_data, entry, included):
    try:
        return create_from_json_api_data(entry, included)
    except TypeError as exc:
        if not _is_argument_mismatch(exc):
            raise
    try:
        return create_from_json_api_data(entry)
    except TypeError as exc:
        if _is_argument_mismatch(exc):
            raise ValueError(
                f"JSON:API deserialization not implemented for {entry.get('type')}"
            )
        raise


def create_from_json_api_data(entry, included):
    if entry is None:
        return None
    try:
        entry[0]
    except (TypeError, KeyError, IndexError):
        pass
    else:
        return [create_from_json_api_data(item, included) for item in entry]
    try:
        type_ = entry["type"]
    except (TypeError, KeyError):
        return entry
    if type_ == "tdm.tis.scalar":
        return entry.get("attributes", {}).get("value")
    if type_ == "tdm.tis.openqueue":
        from tala.model.openqueue import OpenQueue
        return OpenQueue.create_from_json_api_data(entry, included)
    if type_ == "tdm.tis.set":
        from tala.model.set import Set
        return Set.create_from_json_api_data(entry, included)
    if type_ == "tdm.tis.stack":
        from tala.model.stack import Stack
        return Stack.create_from_json_api_data(entry, included)
    if type_ == "tdm.tis.stackset":
        from tala.model.stack import StackSet
        return StackSet.create_from_json_api_data(entry, included)
    if type_ == "tdm.tis.commitments":
        from tala.model.commitments import Commitments
        return Commitments.create_from_json_api_data(entry, included)
    if type_ == "tdm.tis.next_utterance":
        attributes = entry.get("attributes", {})
        moves_data = included.get_data_for_relationship("moves", entry)
        plan_item_data = included.get_data_for_relationship("plan_item", entry)
        alternatives = attributes.get("alternatives", [])
        parsed_alternatives = []
        for alternative in alternatives:
            try:
                alt_value = alternative.get("alt")
            except AttributeError:
                parsed_alternatives.append(alternative)
                continue
            alt_ref = alt_value
            try:
                alt_data = alt_ref.get("data")
            except AttributeError:
                alt_data = None
            if alt_data:
                alt_included = IncludedObject(alt_ref.get("included", []))
                alt_value = create_from_json_api_data(alt_data, alt_included)
            else:
                try:
                    alt_ref["type"]
                    alt_ref["id"]
                except (TypeError, KeyError):
                    alt_value = alt_ref
                else:
                    alt_entry = included.get_object_from_relationship(alt_ref)
                    if alt_entry is None:
                        raise ValueError(f"Missing included resource for alternative {alt_ref}")
                    alt_value = create_from_json_api_data(alt_entry, included)
            parsed_alternatives.append({"alt": alt_value, "predicted": alternative.get("predicted")})
        return {
            "moves": create_from_json_api_data(moves_data, included),
            "alternatives": parsed_alternatives,
            "plan_item": create_from_json_api_data(plan_item_data, included),
        }
    if type_ == "tdm.tis.latest_utterance":
        attributes = entry.get("attributes", {})
        moves_data = included.get_data_for_relationship("moves", entry)
        turn_content_data = included.get_data_for_relationship("turn_content", entry)
        return {
            "speaker": attributes.get("speaker"),
            "moves": create_from_json_api_data(moves_data, included),
            "turn_content": create_from_json_api_data(turn_content_data, included),
        }
    if type_ == "tala.model.plan":
        from tala.model.plan import Plan
        return Plan.create_from_json_api_data(entry, included)
    if type_ == "iterator_state":
        from tala.model.query import IteratorState
        return IteratorState.create_from_json_api_data(entry, included)
    if type_.startswith("tala.model.move"):
        return _create_move_from_json_api_data(entry, included)
    if type_ == "tdm.tis.map":
        entries = included.get_data_for_relationship("entries", entry)
        if not entries:
            return {}
        try:
            entries[0]
        except (TypeError, KeyError, IndexError):
            entries = [entries]
        result = {}
        for entry_item in entries:
            entry_value = create_from_json_api_data(entry_item, included)
            if isinstance(entry_value, dict) and "key" in entry_value:
                result[entry_value["key"]] = entry_value.get("value")
        return result
    if type_ == "tdm.tis.map_entry":
        key_data = included.get_data_for_relationship("key", entry)
        value_data = included.get_data_for_relationship("value", entry)
        return {
            "key": create_from_json_api_data(key_data, included),
            "value": create_from_json_api_data(value_data, included),
        }
    if type_ == "tdm.tis.list":
        items = included.get_data_for_relationship("items", entry)
        if items is None:
            return []
        try:
            items[0]
        except (TypeError, KeyError, IndexError):
            items = [items]
        return [create_from_json_api_data(item, included) for item in items if item is not None]
    if type_ in ("tala.model.action", "tala.model.action.Action"):
        from tala.model.action import Action
        return Action.create_from_json_api_data(entry, included)
    if type_ == "tala.event.Event":
        from tala.event import Event
        return Event.create_from_json_api_data(entry, included)
    if type_.startswith("tala.model.entity"):
        from tala.model.entity import Entity
        create_from_json_api_data_fn = getattr(Entity, "create_from_json_api_data", None)
        if callable(create_from_json_api_data_fn):
            return _call_create_from_json_api_data(create_from_json_api_data_fn, entry, included)
        attributes = entry.get("attributes", {})
        return Entity.create_from_json(attributes)
    try:
        module_name, class_name = type_.rsplit(".", 1)
    except ValueError:
        raise ValueError(f"JSON:API deserialization not implemented for {type_}")
    try:
        module = importlib.import_module(module_name)
    except Exception:
        raise ValueError(f"JSON:API deserialization not implemented for {type_}")
    target_cls = getattr(module, class_name, None)
    create_from_json_api_data_fn = getattr(target_cls, "create_from_json_api_data", None)
    if callable(create_from_json_api_data_fn):
        return _call_create_from_json_api_data(create_from_json_api_data_fn, entry, included)
    raise ValueError(f"JSON:API deserialization not implemented for {type_}")


_JSON_API_ENTRY_STACK = []
