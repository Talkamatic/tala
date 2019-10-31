from collections import namedtuple, OrderedDict
from itertools import chain


class GeneratedIntent(namedtuple("GeneratedIntent", ["name", "sources", "samples"])):
    @property
    def required_entities(self):
        lists = [source.required_entities for source in self.sources]
        all_entities = chain(*lists)
        unique_entities = list(OrderedDict.fromkeys(all_entities))
        return unique_entities


class GeneratedBuiltinIntent(namedtuple("GeneratedBuiltinIntent", ["name", "samples"])):
    pass
