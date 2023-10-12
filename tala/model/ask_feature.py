import collections

from tala.utils.as_json import AsJSONMixin

SEMANTIC_OBJECT_TYPE = "ask_feature"


class AskFeature(collections.namedtuple("AskFeature", ["name", "kpq"]), AsJSONMixin):
    def __new__(cls, predicate_name, kpq=False):
        return super(AskFeature, cls).__new__(cls, predicate_name, kpq)

    def as_dict(self):
        return {"semantic_object_type": SEMANTIC_OBJECT_TYPE, "name": self.name, "kpq": self.kpq}
