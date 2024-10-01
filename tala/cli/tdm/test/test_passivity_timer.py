from unittest.mock import patch, ANY

from tala.cli.tdm import passivity_timer
from tala.cli.tdm.passivity_timer import PassivityTimer
from tala.utils.observable import Observer


class TestPassivityTimer(object):
    def setup_method(self):
        self._passivity_timer = PassivityTimer()
        self._MockTimer = None
        self._mocked_timer = None
        self._observer = None

    @patch("{}.Timer".format(passivity_timer.__name__, autospec=True))  # noqa: F522
    def test_start(self, MockTimer):
        self._given_mocked_timer(MockTimer)
        self._when_starting_timer_with(5.0)
        self._then_timer_was_started_with(5.0)

    def _given_mocked_timer(self, MockTimer):
        self._MockTimer = MockTimer
        self._mocked_timer = MockTimer.return_value

    def _when_starting_timer_with(self, duration):
        self._start_timer(duration)

    def _start_timer(self, duration=1.0):
        self._passivity_timer.start(duration)

    def _then_timer_was_started_with(self, expected_duration):
        self._MockTimer.assert_called_once_with(expected_duration, function=ANY)
        self._mocked_timer.start.assert_called_once()

    @patch("{}.Timer".format(passivity_timer.__name__, autospec=True))  # noqa: F522
    def test_stop(self, MockTimer):
        self._given_mocked_timer(MockTimer)
        self._given_started_timer()
        self._when_stopping_timer()
        self._then_timer_was_stopped()

    def _given_started_timer(self):
        self._start_timer()

    def _when_stopping_timer(self):
        self._passivity_timer.stop()

    def _then_timer_was_stopped(self):
        self._mocked_timer.cancel.assert_called_once()

    @patch("{}.Timer".format(passivity_timer.__name__, autospec=True))  # noqa: F522
    def test_stop_timer_when_not_started(self, MockTimer):
        self._given_mocked_timer(MockTimer)
        self._when_stopping_timer()
        self._then_no_exceptions_occur()

    def _then_no_exceptions_occur(self):
        pass

    @patch("{}.Timer".format(passivity_timer.__name__, autospec=True))  # noqa: F522
    def test_timer_updates_observer(self, MockTimer):
        self._given_mocked_timer(MockTimer)
        self._given_observer_added()
        self._given_started_timer()
        self._when_timer_triggers()
        self._then_observer_is_updated()

    def _given_observer_added(self):
        class PassivityTimerObserver(Observer):
            def __init__(self):
                self.updated_with = None

            def update(self, value):
                self.updated_with = value

        self._observer = PassivityTimerObserver()
        self._passivity_timer.add_observer(self._observer)

    def _when_timer_triggers(self):
        args, kwargs = self._MockTimer.call_args
        trigger_callback = kwargs["function"]
        trigger_callback()

    def _then_observer_is_updated(self):
        assert self._observer.updated_with == passivity_timer.PASSIVE
