class Webview(object):
    def __init__(self, url):
        self._url = url

    @property
    def url(self):
        return self._url

    def __eq__(self, other):
        try:
            return other.url == self.url
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (other == self)

    def __unicode__(self):
        return u'webview("%s")' % self.url

    def __repr__(self):
        return unicode(self)
