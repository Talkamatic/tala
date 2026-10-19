from tala.model.set import Set
from tala.utils import json_api
from tala.utils.as_json import AsJSONMixin
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.ddd.json_parser import NonCheckingJSONParser


class Commitments(AsSemanticExpressionMixin, AsJSONMixin):
    def __init__(self, content=None, meta_com=None, pcom=None, meta_pcom=None, previous_commitment_lifespan=30):
        if content is None:
            content = []
        if pcom is None:
            pcom = []
        if meta_com is None:
            meta_com = {}
        if meta_pcom is None:
            meta_pcom = {}
        self._backing_set = Set([item for item in content])
        self._meta_pcom = {k: v for k, v in meta_pcom.items()}
        self._meta_com = {k: v for k, v in meta_com.items()}
        self._pcom = Set([item for item in pcom])
        self._previous_commitment_lifespan = int(previous_commitment_lifespan)

    @classmethod
    def create_from_json(cls, input_json):
        parser = NonCheckingJSONParser()
        commitments = [parser.parse(commitment) for commitment in input_json["commitments_set"]["set"]]
        lifespan = int(input_json["commitment_lifespan"])
        meta_com = {parser.parse(elem["key"]): (elem["value"][0], elem["value"][1]) for elem in input_json["meta_com"]}
        pcom = [parser.parse(commitment) for commitment in input_json["pcom"]["set"]]
        meta_pcom = {
            parser.parse(elem["key"]): (elem["value"][0], int(elem["value"][1]))
            for elem in input_json["meta_pcom"]
        }
        return cls(commitments, meta_com, pcom, meta_pcom, lifespan)

    @property
    def meta_com(self):
        return self._meta_com

    @property
    def pcom(self):
        return self._pcom

    @property
    def meta_pcom(self):
        return self._meta_pcom

    def as_dict(self):
        return {
            "commitments_set": self._backing_set,
            "meta_com": [{
                "key": k,
                "value": [v[0], v[1]]
            } for k, v in self._meta_com.items()],
            "pcom": self._pcom,
            "meta_pcom": [{
                "key": k,
                "value": [v[0], v[1]]
            } for k, v in self._meta_pcom.items()],
            "commitment_lifespan": self._previous_commitment_lifespan
        }

    def as_json_api_dict(self, id_=None, type_="tdm.tis.commitments"):
        commitment_obj = json_api.JSONAPIObject(
            type_,
            id_ if id_ else str(id(self)),
            {"commitment_lifespan": int(self._previous_commitment_lifespan)},
        )
        commitment_obj.add_relationship(
            "commitments",
            self._backing_set.as_json_api_dict(type_="tdm.tis.set"),
        )
        commitment_obj.add_relationship(
            "previous_commitments",
            self._pcom.as_json_api_dict(type_="tdm.tis.set"),
        )
        commitment_obj.add_relationship(
            "meta_commitments",
            self._meta_list_as_json_api(self._meta_com, "meta_com"),
        )
        commitment_obj.add_relationship(
            "meta_previous_commitments",
            self._meta_list_as_json_api(self._meta_pcom, "meta_pcom"),
        )
        return commitment_obj.as_dict

    def _meta_list_as_json_api(self, meta_map, label):
        meta_container = json_api.JSONAPIObject(
            "tdm.tis.commitment_meta_list",
            f"commitments:{label}:{id(self)}",
        )
        for index, (proposition, meta) in enumerate(meta_map.items()):
            try:
                topmost_goal, turn_number = meta
            except (TypeError, ValueError):
                topmost_goal = None
                turn_number = None
            meta_entry = json_api.JSONAPIObject(
                "tdm.tis.commitment_meta",
                f"commitments:{label}:{id(self)}:{index}",
                {"turn_number": None if turn_number is None else int(turn_number)},
            )
            meta_entry.add_relationship("proposition", json_api.as_json_api_entry(proposition))
            meta_entry.add_relationship("topmost_goal", json_api.as_json_api_entry(topmost_goal))
            meta_container.append_relationship("entries", meta_entry.as_dict)
        return meta_container.as_dict

    @classmethod
    def create_from_json_api_data(cls, data, included):
        if data is None:
            return cls()
        commitments_data = included.get_data_for_relationship("commitments", data)
        previous_data = included.get_data_for_relationship("previous_commitments", data)
        meta_data = included.get_data_for_relationship("meta_commitments", data)
        meta_previous_data = included.get_data_for_relationship("meta_previous_commitments", data)
        commitments_set = Set.create_from_json_api_data(commitments_data, included)
        previous_set = Set.create_from_json_api_data(previous_data, included)
        meta_com = cls._meta_map_from_json_api(meta_data, included)
        meta_pcom = cls._meta_map_from_json_api(meta_previous_data, included)
        lifespan = data.get("attributes", {}).get("commitment_lifespan", 30)
        result = cls(list(commitments_set), meta_com, list(previous_set), meta_pcom, lifespan)
        return result

    @classmethod
    def _meta_map_from_json_api(cls, meta_list_data, included):
        if meta_list_data is None:
            return {}
        entries = included.get_data_for_relationship("entries", meta_list_data)
        if not entries:
            return {}
        try:
            entries[0]
        except (TypeError, KeyError, IndexError):
            entries = [entries]
        result = {}
        for entry in entries:
            if entry is None:
                continue
            proposition_data = included.get_data_for_relationship("proposition", entry)
            topmost_data = included.get_data_for_relationship("topmost_goal", entry)
            proposition = json_api.create_from_json_api_data(proposition_data, included)
            topmost_goal = json_api.create_from_json_api_data(topmost_data, included)
            turn_number = entry.get("attributes", {}).get("turn_number")
            result[proposition] = (topmost_goal, turn_number)
        return result

    def union(self, other):
        return self._backing_set.union(other)

    def add(self, proposition, turn_number=-1, topmost_goal=None):
        self._remove_incompatible_commitments(proposition)
        self._backing_set.add(proposition)
        self._meta_com[proposition] = (topmost_goal, turn_number)

    def _remove_incompatible_commitments(self, proposition):
        to_remove = []

        for commitment in self:
            if proposition.is_incompatible_with(commitment):
                to_remove.append(commitment)

        for commitment_to_remove in to_remove:
            self.remove(commitment_to_remove)

    def __iter__(self):
        return self._backing_set.__iter__()

    def remove(self, proposition):
        if proposition in self._meta_com:
            self._meta_pcom[proposition] = self._meta_com[proposition]
        self._backing_set.remove(proposition)
        self.pcom.add(proposition)

    def remove_if_exists(self, proposition):
        if proposition in self._backing_set:
            self.remove(proposition)

    def __str__(self):
        return str(self._backing_set)

    def __repr__(self):
        return repr(self._backing_set)

    def __eq__(self, other):
        return self._backing_set.__eq__(other)

    def is_subset_of(self, other):
        return self._backing_set.is_subset_of(other)

    def __len__(self):
        return len(self._backing_set)

    def should_purge_previous_commitments(self, current_turn_number):
        for fact in self.pcom:
            if fact in self._meta_pcom:
                (_, turn_number) = self._meta_pcom[fact]
                if int(turn_number) + self._previous_commitment_lifespan < current_turn_number:
                    return True
        return False

    def purge_previous_commitments(self, current_turn_number):
        # all exceptions in this method are swallowed.
        try:
            to_purge = []

            for fact in self.pcom:
                if fact in self._meta_pcom:
                    (_, turn_number) = self._meta_pcom[fact]

                    if int(turn_number) + self._previous_commitment_lifespan < current_turn_number:
                        to_purge.append(fact)

            for fact in to_purge:
                self.pcom.remove(fact)
                if fact in self._meta_pcom:
                    del self._meta_pcom[fact]
        except Exception:
            pass
