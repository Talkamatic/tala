class Constants:
    ACTION = "action"
    SYS_ANSWER = "sys-answer"
    POSITIVE_SYS_ANSWER = "positive-sys-answer"
    NEGATIVE_SYS_ANSWER = "negative-sys-answer"
    PREDICATE = "predicate"
    USER_QUESTION = "user-question"
    SYS_QUESTION = "sys-question"
    ISSUE_TITLE = "issue-title"
    ACTION_TITLE = "action-title"
    ANSWER_COMBINATION = "answer-combination"
    REPORT_ENDED = "report-ended"
    REPORT_STARTED = "report-started"
    REPORT_FAILED = "report-failed"
    PREREPORT = "prereport"
    PRECONFIRM = "preconfirm"
    VALIDITY = "validity"
    INDIVIDUAL = "individual"
    STRING = "string"
    GREETING = "greeting"
    GRAMMAR = "grammar"
    SLOT = "slot"
    ONE_OF = "one-of"
    ITEM = "item"
    NP = "np"
    INDEFINITE = "indefinite"
    DEFINITE = "definite"
    VP = "vp"
    INFINITIVE = "infinitive"
    IMPERATIVE = "imperative"
    ING_FORM = "ing-form"
    OBJECT = "object"
    SELECTION = "selection"


class Node:
    def __init__(self, type_, parameters=None, children=None):
        self.type = type_
        if parameters is None:
            self.parameters = {}
        else:
            self.parameters = parameters
        if children is None:
            self.children = []
        else:
            self.children = children

    def __str__(self):
        return self._pretty_string()

    def _pretty_string(self, indentation=0):
        string = "%sNode(%s, %s)" % ("  " * indentation, self.type, self.parameters)
        if isinstance(self.children, list):
            if len(self.children) > 0:
                for child in self.children:
                    if isinstance(child, Node):
                        string += "\n%s" % (child._pretty_string(indentation + 1))
                    else:
                        string += "\n%s%r" % ("  " * (indentation + 1), child)
            else:
                string += " %s" % self.children
        else:
            string += "\n%s%s" % ("  " * (indentation + 1), self.children)
        return string

    def __repr__(self):
        return "Node(%s, %s, %r)" % (self.type, self.parameters, self.children)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return other.type == self.type and other.parameters == self.parameters and other.children == self.children
        else:
            return False

    def add_child(self, child):
        self.children.append(child)

    def get_child(self, type_, parameters={}):
        for child in self.children:
            if child.type == type_ and child.parameters == parameters:
                return child

    def get_single_child(self):
        if len(self.children) == 1:
            return self.children[0]
        else:
            raise Exception("expected this node to have a single child:\n%s" % self)
