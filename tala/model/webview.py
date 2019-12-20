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

    def __str__(self):
        return 'webview("%s")' % self.url

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return 17 * hash(str(self)) + 7 * hash(self.__class__.__name__)
