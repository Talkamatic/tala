from tala.model.semantic_object import SemanticObject
from tala.model.openqueue import OpenQueue
from tala.model.set import Set
from tala.model.stack import Stack
from tala.model.tis_node import TISNode


def can_convert_to_json(object_):
    def anyinstanceof(object_, types):
        return any(isinstance(object_, type) for type in types)

    return anyinstanceof(object_, [Stack, TISNode, SemanticObject, Set, OpenQueue])