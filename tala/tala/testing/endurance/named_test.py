import copy
import random
import sys
import time

from tala.testing.interactions.base_test import BaseInteractionTest


class MissingTurnsException(Exception):
    pass


class EnduranceInteractionTest(BaseInteractionTest):
    def __init__(self, all_tests, duration):
        self._all_tests = list(all_tests)
        self._start_time = time.time()
        self._duration = duration
        self._is_requested_to_stop = False

    @property
    def _end_time(self):
        if self._duration <= 0:
            return sys.maxsize
        else:
            return self._start_time + self._duration

    @property
    def filename(self):
        return self.__class__.__name__

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def turns(self):
        while not self._is_requested_to_stop and time.time() < self._end_time:
            next_test = self._prepare_next_test()
            for turn in next_test.turns:
                yield turn

    def _prepare_next_test(self):
        next_test = self._randomly_sampled_test()
        self._remove_first_turn_if_type_is_system(next_test)
        if not next_test.turns:
            raise MissingTurnsException("Expected turns but found none in test '%s' of '%s'" %
                                        (next_test.name, next_test.filename))
        return next_test

    @staticmethod
    def _remove_first_turn_if_type_is_system(next_test):
        first_turn = next_test.turns[0]
        if first_turn.is_system_output_turn:
            next_test.turns.pop(0)

    def _randomly_sampled_test(self):
        random_test = random.choice(self._all_tests)
        if not random_test.turns:
            raise MissingTurnsException("Expected turns but found none in test '%s' of '%s'" %
                                        (random_test.name, random_test.filename))
        return copy.copy(random_test)

    def stop(self):
        self._is_requested_to_stop = True
