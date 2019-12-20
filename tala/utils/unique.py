from collections import OrderedDict


def unique(elements):
    return list(OrderedDict.fromkeys(elements))
