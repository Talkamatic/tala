import os
import os.path
import shutil
import tempfile

from mock import Mock, ANY, patch
import pytest

from tala.ddd.building.steps.generate import GenerateStepForHandcraftedGFFiles, GenerateStepForGFRGLGeneration, GenerateStepForGFGeneration
from tala.ddd.building.steps.verify import VerifyStepForGFGeneration, VerifyStepForGFRGLGeneration, VerifyStepForHandcraftedGFFiles
from tala.ddd.building.steps import step_factory
from tala.ddd.building.steps.step_factory import GenerateStepFactory, VerifyStepFactory
from tala.model.ddd import DDD


class TestStepFactories(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="DddBuilderTestCase")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._ddd_name = None
        self._mock_ddd = None
        self._language_codes = []
        self._actual_step = None
        self._step_factory = None

    def teardown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    @patch("{}.utils".format(step_factory.__name__), autospec=True)
    @patch("{}.VerifyStepForGFGeneration".format(step_factory.__name__), autospec=True)
    def test_created_verification_step_is_returned(self, MockVerificationStepForGFGeneration, mocked_utils):
        self._given_ddd_name("app")
        self._given_mocked_ddd(use_rgl=False)
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_no_handcrafted_gf_files(mocked_utils)
        self._given_step_factory_created(VerifyStepFactory)
        self._when_creating_step()
        self._then_step_is_returned(MockVerificationStepForGFGeneration)

    def _given_mocked_ddd(self, use_rgl=False):
        mock_ddd = Mock(spec=DDD)
        mock_ddd.name = self._ddd_name
        mock_ddd.use_rgl = use_rgl
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

    def _given_no_handcrafted_gf_files(self, mocked_utils):
        mocked_utils.has_handcrafted_gf_grammar.return_value = False

    def _given_step_factory_created(self, class_):
        self._step_factory = class_(self._mock_ddd, self._language_codes, verbose=False, ignore_warnings=False)

    def _when_creating_step(self):
        self._actual_step = self._step_factory.create()

    def _then_step_is_returned(self, expected_step):
        assert self._actual_step == expected_step.return_value

    @patch("{}.utils".format(step_factory.__name__), autospec=True)
    @patch("{}.GenerateStepForGFGeneration".format(step_factory.__name__), autospec=True)
    def test_created_generation_step_is_returned(self, MockGenerationStepForGFGeneration, mocked_utils):
        self._given_ddd_name("app")
        self._given_mocked_ddd(use_rgl=False)
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_no_handcrafted_gf_files(mocked_utils)
        self._given_step_factory_created(GenerateStepFactory)
        self._when_creating_step()
        self._then_step_is_returned(MockGenerationStepForGFGeneration)

    @pytest.mark.parametrize(
        "StepFactory,ExpectedStep", [
            (VerifyStepFactory, VerifyStepForGFGeneration),
            (GenerateStepFactory, GenerateStepForGFGeneration),
        ]
    )
    @patch("{}.utils".format(step_factory.__name__), autospec=True)
    def test_creating_step_for_gf_generation(self, mocked_utils, StepFactory, ExpectedStep):
        self._given_ddd_name("app")
        self._given_mocked_ddd(use_rgl=False)
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_no_handcrafted_gf_files(mocked_utils)
        with self._given_expected_step(ExpectedStep) as MockExpectedStep:
            self._given_step_factory_created(StepFactory)
            self._when_creating_step()
            self._then_step_is_created_with_expected_parameters(MockExpectedStep)

    def _given_expected_step(self, ExpectedStep):
        return patch("{}.{}".format(step_factory.__name__, ExpectedStep.__name__), autospec=True)

    def _then_step_is_created_with_expected_parameters(self, MockExpectedStep):
        MockExpectedStep.assert_called_once_with(self._mock_ddd, False, self._language_codes, False, ANY, "grammar")

    @pytest.mark.parametrize(
        "StepFactory,ExpectedStep", [
            (VerifyStepFactory, VerifyStepForGFRGLGeneration),
            (GenerateStepFactory, GenerateStepForGFRGLGeneration),
        ]
    )
    @patch("{}.utils".format(step_factory.__name__), autospec=True)
    def test_verify_creates_step_for_gf_rgl_generation(self, mocked_utils, StepFactory, ExpectedStep):
        self._given_ddd_name("app")
        self._given_mocked_ddd(use_rgl=True)
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_no_handcrafted_gf_files(mocked_utils)
        with self._given_expected_step(ExpectedStep) as MockExpectedStep:
            self._given_step_factory_created(StepFactory)
            self._when_creating_step()
            self._then_step_is_created_with_expected_parameters(MockExpectedStep)

    @pytest.mark.parametrize(
        "StepFactory,ExpectedStep", [
            (VerifyStepFactory, VerifyStepForHandcraftedGFFiles),
            (GenerateStepFactory, GenerateStepForHandcraftedGFFiles),
        ]
    )
    @patch("{}.utils".format(step_factory.__name__), autospec=True)
    def test_verify_creates_step_for_handcrafted_grammar(self, mocked_utils, StepFactory, ExpectedStep):
        self._given_ddd_name("app")
        self._given_mocked_ddd(use_rgl=False)
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_handcrafted_gf_files(mocked_utils)
        with self._given_expected_step(ExpectedStep) as MockExpectedStep:
            self._given_step_factory_created(StepFactory)
            self._when_creating_step()
            self._then_step_is_created_with_expected_parameters(MockExpectedStep)

    def _given_handcrafted_gf_files(self, mocked_utils):
        mocked_utils.has_handcrafted_gf_grammar.return_value = True
