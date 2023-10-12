from collections import namedtuple


class QueryResultFromService(
    namedtuple("QueryResultFromService", ["value", "confidence", "grammar_entry", "is_predicted"])
):
    def __new__(cls, value, confidence, grammar_entry=None, is_predicted=False):
        return super(QueryResultFromService, cls).__new__(cls, value, confidence, grammar_entry, is_predicted)


class QueryResultFromServiceManager(namedtuple("QueryResultFromServiceManager", ["proposition", "confidence"])):
    pass
