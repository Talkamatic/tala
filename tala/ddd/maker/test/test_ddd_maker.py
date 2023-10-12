import os
import shutil
import unittest
import tempfile

from tala.ddd.maker import ddd_maker


class TestDddMaker(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TestDddMaker")
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    def test_custom_target_dir(self):
        self._given_target_dir_specified()
        self._when_make_is_called()
        self._then_everything_is_created()

    def test_default_target_dir(self):
        self._given_default_target_dir()
        self._when_make_is_called()
        self._then_everything_is_created()

    def _then_everything_is_created(self):
        self._base_dir_is_created()
        self._domain_is_created()
        self._ontology_is_created()
        self._service_interface_is_created()
        self._backend_config_is_created()
        self._ddd_config_is_created()
        self._interaction_tests_are_created()

    def _given_target_dir_specified(self):
        self._target_dir = "%s/mock_ddd" % self._temp_dir

    def _given_default_target_dir(self):
        os.chdir(self._temp_dir)
        self._target_dir = "."

    def _when_make_is_called(self):
        ddd_maker.DddMaker("ddd", use_rgl=True, target_dir=self._target_dir).make()
        os.chdir(self._target_dir)

    def _base_dir_is_created(self):
        self.assertTrue(os.path.exists("ddd"))

    def _domain_is_created(self):
        self.assertTrue(os.path.exists("ddd/domain.xml"))

    def _ontology_is_created(self):
        self.assertTrue(os.path.exists("ddd/ontology.xml"))

    def _service_interface_is_created(self):
        self.assertTrue(os.path.exists("ddd/service_interface.xml"))

    def _ddd_config_is_created(self):
        self.assertTrue(os.path.exists("ddd/ddd.config.json"))

    def _backend_config_is_created(self):
        self.assertTrue(os.path.exists("backend.config.json"))

    def _interaction_tests_are_created(self):
        self.assertTrue(os.path.exists("ddd/test/interaction_tests_sem.txt"))
