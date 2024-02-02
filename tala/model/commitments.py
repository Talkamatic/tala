from tala.model.set import Set
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
