class PersonName(object):
    def __init__(self, string):
        self._string = string

    @property
    def string(self):
        return self._string

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        are_equal = self.__eq__(other)
        if are_equal is NotImplemented:
            return NotImplemented
        return not are_equal

    def __unicode__(self):
        return "person_name(%s)" % self._string

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return 'PersonName(%r)' % self._string
