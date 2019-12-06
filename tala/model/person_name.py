from tala.utils.equality import EqualityMixin


class PersonName(EqualityMixin):
    def __init__(self, string):
        self._string = string

    @property
    def string(self):
        return self._string

    def __unicode__(self):
        return "person_name(%s)" % self._string

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return 'PersonName(%r)' % self._string
