import collections

from tala.utils.as_json import AsJSONMixin
from tala.utils.json_api import JSONAPIMixin

SEMANTIC_OBJECT_TYPE = "ask_feature"


class AskFeature(collections.namedtuple("AskFeature", ["name", "kpq"]), AsJSONMixin, JSONAPIMixin):
    @classmethod
    def create_from_json_api_dict(cls, ask_feature_data, included):
        name = ask_feature_data["attributes"]["name"]
        kpq = ask_feature_data["attributes"]["kpq"]
        return cls(name, kpq)

    def __new__(cls, predicate_name, kpq=False):
        return super(AskFeature, cls).__new__(cls, predicate_name, kpq)

    def as_dict(self):
        return {"semantic_object_type": SEMANTIC_OBJECT_TYPE, "name": self.name, "kpq": self.kpq}

    @property
    def json_api_id(self):
        return f"{self.name}:{self.kpq}"

    @property
    def json_api_attributes(self):
        return ["name", "kpq"]

    @property
    def json_api_relationships(self):
        return []
