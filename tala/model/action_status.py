class Done(object):
    def __eq__(self, other):
        return isinstance(other, Done)
