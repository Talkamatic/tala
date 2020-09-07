import os
import os.path
import shutil
import tempfile
import unittest

from mock import Mock, patch

from tala.backend.dependencies.for_generating import BackendDependenciesForGenerating
from tala.ddd.building.steps.abstract_build_step import AbstractBuildStep
import tala.ddd.building.ddd_builder_for_generating
from tala.ddd.building.ddd_builder_for_generating import DDDBuilderForGenerating
from tala.model.ddd import DDD


class TestDDDBuilderForGenerating(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TestDDDBuilderForGenerating")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._asr = None
        self._use_word_list_correction = False
        self._mocked_build_step = None
        self._mock_ddd = None
        self._ddd_name = None
        self._mocked_backend_dependencies = None
        self._language_codes = []
        self._ddds_builder = None

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    def _given_mocked_ddd(self):
        mock_ddd = Mock(spec=DDD)
        mock_ddd.name = self._ddd_name
        self._mock_ddd = mock_ddd

    def _given_ddd_name(self, name):
        self._ddd_name = name

    def _given_file_exists(self, path):
        self._ensure_dir_exists(os.path.dirname(path))
        with open(path, "w"):
            pass

    def _ensure_dir_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _given_language_codes(self, language_codes):
        self._language_codes = language_codes

    def _when_build_is_called(self):
        self._ddds_builder.build()

    def _given_mocked_backend_dependencies(self):
        backend_dependencies = Mock(spec=BackendDependenciesForGenerating)
        backend_dependencies.ddds = [self._mock_ddd]
        backend_dependencies.asr = self._asr
        backend_dependencies.use_word_list_correction = self._use_word_list_correction
        self._mocked_backend_dependencies = backend_dependencies

    def _given_ddds_builder_created(self):
        self._ddds_builder = DDDBuilderForGenerating(
            self._mocked_backend_dependencies, language_codes=self._language_codes
        )

    def _given_asr(self, asr):
        self._asr = asr

    @patch("{}.VerifyStepFactory".format(tala.ddd.building.ddd_builder_for_generating.__name__), autospec=True)
    def test_verify_invokes_build_on_verification_step(self, MockVerifyStepFactory):
        self._given_step_factory_creates_mocked_step(MockVerifyStepFactory)
        self._given_ddd_name("app")
        self._given_asr("none")
        self._given_mocked_ddd()
        self._given_mocked_backend_dependencies()
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_ddds_builder_created()
        self._when_calling_verify()
        self._then_build_is_invoked_on_step()

    def _given_step_factory_creates_mocked_step(self, MockStepFactory):
        self._mocked_build_step = Mock(spec=AbstractBuildStep)
        mocked_factory = MockStepFactory.return_value
        mocked_factory.create.return_value = self._mocked_build_step

    def _when_calling_verify(self):
        self._ddds_builder.verify()

    def _then_build_is_invoked_on_step(self):
        self._mocked_build_step.build.assert_called_once()

    @patch("{}.GenerateStepFactory".format(tala.ddd.building.ddd_builder_for_generating.__name__), autospec=True)
    def test_build_invokes_build_on_generate_step(self, MockGenerateStepFactory):
        self._given_step_factory_creates_mocked_step(MockGenerateStepFactory)
        self._given_ddd_name("app")
        self._given_asr("none")
        self._given_mocked_ddd()
        self._given_mocked_backend_dependencies()
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_ddds_builder_created()
        self._when_build_is_called()
        self._then_build_is_invoked_on_step()

    @patch("{}.GenerateStepFactory".format(tala.ddd.building.ddd_builder_for_generating.__name__), autospec=True)
    @patch("{}.CleanStepFactory".format(tala.ddd.building.ddd_builder_for_generating.__name__), autospec=True)
    def test_build_invokes_build_on_clean_step(self, MockCleanStepFactory, MockGenerateStepFactory):
        self._given_mocked_clean_step(MockCleanStepFactory)
        self._given_ddd_name("app")
        self._given_asr("none")
        self._given_mocked_ddd()
        self._given_mocked_backend_dependencies()
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_ddds_builder_created()
        self._when_build_is_called()
        self._then_build_is_invoked_on_step()

    def _given_mocked_clean_step(self, MockCleanStepFactory):
        self._mocked_build_step = MockCleanStepFactory.return_value.create.return_value
