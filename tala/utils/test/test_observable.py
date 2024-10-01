from unittest.mock import Mock
import unittest

from tala.utils.observable import Observable, Observer


class ObservableTests(unittest.TestCase):
    def test_add_observer_and_update_it(self):
        self.given_mocked_observer()
        self.given_observable()
        self.given_mocked_observer_added_to_observable()
        self.when_setting_value_in_observable("value")
        self.then_observer_was_updated_with("value")

    def given_mocked_observer(self):
        self._mock_observer = Mock(spec=Observer)

    def given_observable(self):
        self._observable = Observable()

    def given_mocked_observer_added_to_observable(self):
        self._observable.add_observer(self._mock_observer)

    def when_setting_value_in_observable(self, value):
        self._observable.set(value)

    def then_observer_was_updated_with(self, value):
        self._mock_observer.update.assert_called_once_with(value)

    def test_removed_observer_is_not_updated(self):
        self.given_mocked_observer()
        self.given_observable()
        self.given_mocked_observer_added_to_observable()
        self.given_mocked_observer_removed_from_observable()
        self.when_setting_value_in_observable("value")
        self.then_observer_was_not_updated()

    def given_mocked_observer_removed_from_observable(self):
        self._observable.remove_observer(self._mock_observer)

    def then_observer_was_not_updated(self):
        self._mock_observer.update.assert_not_called()

    def test_remove_observer_on_its_update(self):
        self.given_mocked_observer()
        self.given_observable()
        self.given_mocked_observer_added_to_observable()
        self.given_mocked_observer_removes_itself_from_observable_when_updated()
        self.when_setting_value_in_observable("value")
        self.then_there_was_no_exception()

    def given_mocked_observer_removes_itself_from_observable_when_updated(self):
        def remove_from_observable(value):
            self._observable.remove_observer(self._mock_observer)

        self._mock_observer.update.side_effect = remove_from_observable

    def then_there_was_no_exception(self):
        pass
