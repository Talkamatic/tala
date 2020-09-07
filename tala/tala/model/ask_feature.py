import collections


class AskFeature(collections.namedtuple("AskFeature", ["name", "kpq"])):
    def __new__(cls, predicate_name, kpq=False):
        return super(AskFeature, cls).__new__(cls, predicate_name, kpq)
