import unittest

from unittest.mock import patch

from tala.utils.chdir import chdir
from tala.config import BackendConfig, OverriddenDddConfig
from tala.ddd.loading import ddd_set_loader
from tala.ddd.loading.ddd_set_loader import DddNotFoundException, \
    OverriddenDddConfigNotFoundException
from tala.ddd.ddd_manager import DDDManager
from tala.log import logger
from tala.ddd.loading import extended_ddd_set_loader


class TestDDDSetLoader(unittest.TestCase):
    def setUp(self):
        self._ddd_manager = DDDManager()
        self._overridden_ddd_config_paths = None
        self.test_logger = logger.configure_and_get_test_logger()
        self._ddds = []
        self._result = None
        self._MockDddLoader = None

    def test_ensure_ddds_loaded(self):
        with chdir("ddds"):
            self._given_extended_ddd_set_loader_created()
            self._when_ensuring_ddds_loaded_from("mockup_travel.json")
            self._then_extended_ddd_loaded_for("mockup_travel")

    def _given_extended_ddd_set_loader_created(self):
        self._extended_ddd_set_loader = extended_ddd_set_loader.ExtendedDDDSetLoader(
            self._ddd_manager, self._overridden_ddd_config_paths
        )

    def _when_ensuring_ddds_loaded_from(self, config_path):
        config = BackendConfig(config_path).read()
        ddds = config["ddds"]
        self._extended_ddd_set_loader.ensure_ddds_loaded(ddds, rerank_amount=config["rerank_amount"])

    def _then_extended_ddd_loaded_for(self, ddd_name):
        extended_ddd = self._ddd_manager.get_ddd(ddd_name)
        self.assertTrue(extended_ddd.name == "mockup_travel")

    @patch("{}.DddConfig".format(ddd_set_loader.__name__))
    @patch("{}.ExtendedDDDLoader".format(extended_ddd_set_loader.__name__))
    def test_ddd_config_override(self, MockDddLoader, MockDddConfig):
        with chdir("ddds"):
            self._given_overridden_ddd_config_paths([OverriddenDddConfig("hello_world", "mock_config.json")])
            self._given_extended_ddd_set_loader_created()
            self._when_ensuring_ddds_loaded_from("hello_world.json")
            self._then_method_called_with(MockDddConfig, "mock_config.json")

    def _given_overridden_ddd_config_paths(self, overridden_ddd_config_paths):
        self._overridden_ddd_config_paths = overridden_ddd_config_paths

    def _then_method_called_with(self, method, argument):
        method.assert_called_with(argument)

    @patch("{}.DddConfig".format(ddd_set_loader.__name__))
    def test_non_existing_ddd_in_ddd_config_override_raises_exception(self, MockDddConfig):
        with chdir("ddds"):
            self._given_overridden_ddd_config_paths([OverriddenDddConfig("non_existing_ddd", "mock_config.json")])
            self._when_creating_ddd_set_loader_then_exception_is_raised_with_message_that_matches_regex(
                DddNotFoundException,
                "Expected overridden DDD 'non_existing_ddd' to exist in the working directory '.*', but it doesn't."
            )

    def _when_creating_ddd_set_loader_then_exception_is_raised_with_message_that_matches_regex(
        self, exception_class, expected_regex
    ):
        with self.assertRaisesRegex(exception_class, expected_regex):
            extended_ddd_set_loader.ExtendedDDDSetLoader(self._ddd_manager, self._overridden_ddd_config_paths)

    def test_non_existing_ddd_config_in_ddd_config_override_raises_exception(self):
        with chdir("ddds"):
            self._given_overridden_ddd_config_paths([OverriddenDddConfig("mockup_travel", "non_existing_config.json")])
            self._when_creating_ddd_set_loader_then_exception_is_raised_with_message_that_matches_regex(
                OverriddenDddConfigNotFoundException,
                "Expected DDD config '.*non_existing_config.json' to exist in DDD 'mockup_travel' but it was not found."
            )

    def _given_mock_ddd_loader(self, MockDddLoader):
        self._MockDddLoader = MockDddLoader

    def _given_ddds(self, *ddds):
        self._ddds = ddds

    def _when_loading_ddds_then_exception_is_raised_with_message_that_matches(self, ExpectedException, expected_regex):
        with self.assertRaisesRegex(ExpectedException, expected_regex):
            self._extended_ddd_set_loader.ensure_ddds_loaded(
                self._ddds, logger=self.test_logger, rerank_amount=BackendConfig.DEFAULT_RERANK_AMOUNT
            )
