from threading import Timer

from tala.utils.observable import Observable

PASSIVE = "PASSIVE"


class PassivityTimer(Observable):
    def __init__(self):
        Observable.__init__(self)
        self._timer = None

    def start(self, duration):
        self._timer = Timer(duration, function=lambda: self.set(PASSIVE))
        self._timer.start()

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
