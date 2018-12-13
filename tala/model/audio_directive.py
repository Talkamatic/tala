class AudioDirective(object):
    PLAY = "PLAY"
    STOP = "STOP"

    def __init__(self, type):
        self._type = type

    @property
    def type(self):
        return self._type


class AudioPlayDirective(AudioDirective):
    def __init__(self, url, offset=0):
        super(AudioPlayDirective, self).__init__(AudioDirective.PLAY)
        self._url = url
        self._offset = offset

    @property
    def url(self):
        return self._url

    @property
    def offset(self):
        return self._offset

    def __eq__(self, other):
        return other.url == self.url and other.offset == self.offset

    def __repr__(self):
        return "AudioPlayDirective(%r, %r)" % (self.url, self.offset)


class AudioStopDirective(AudioDirective):
    def __init__(self):
        super(AudioStopDirective, self).__init__(AudioDirective.STOP)

    def __repr__(self):
        return "AudioStopDirective()"
