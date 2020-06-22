from tala.testing.interactions.base_test import BaseInteractionTest


class InteractionTest(BaseInteractionTest):
    def __init__(self, file_name, test_name, turns):
        self._file_name = file_name
        self._test_name = test_name
        self._turns = turns

    @property
    def filename(self):
        return self._file_name

    @property
    def name(self):
        return self._test_name

    @property
    def turns(self):
        return self._turns
