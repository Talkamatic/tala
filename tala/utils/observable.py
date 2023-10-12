from copy import copy


class Observable(object):
    def __init__(self):
        self._observers = set()

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def set(self, value):
        for observer in copy(self._observers):
            observer.update(value)


class Observer(object):
    def update(self, value):
        raise NotImplementedError()
