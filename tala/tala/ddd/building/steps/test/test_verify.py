import os
import os.path
import shutil
import tempfile

from mock import Mock, patch, call
import pytest

from tala.ddd.building.steps import verify
from tala.ddd.building.steps.verify import VerifyStepForGFGeneration, VerifyStepForGFRGLGeneration
from tala.model.ddd import DDD


class TestVerifyStepsForGFGeneration(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TestVerify")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._verify_step = None
        self._mock_ddd = None
        self._ddd_name = None
        self._language_codes = []
        self._mocked_auto_generator = None

    def teardown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    @pytest.mark.parametrize("step", [
        VerifyStepForGFGeneration,
        VerifyStepForGFRGLGeneration,
    ])
    def test_verify_does_not_create_build_directories(self, step):
        with self._patched_auto_generator(step) as MockAutoGenerator:
            self._given_mocked_auto_generator(MockAutoGenerator)
            self._given_ddd_name("MockDDD")
            self._given_mocked_ddd()
            self._given_language_codes(["eng"])
            self._given_file_exists("MockDDD/grammar/grammar_eng.xml")
            self._given_step_created(step)
            self._when_calling_build()
            self._then_files_have_not_been_written_by_auto_generator()

    def _patched_auto_generator(self, step):
        return patch("{}.{}._AutoGeneratorClass".format(verify.__name__, step.__name__), autospec=True)

    def _given_mocked_auto_generator(self, MockAutoGenerator):
        self._mocked_auto_generator = MockAutoGenerator.return_value

    def _given_ddd_name(self, name):
        self._ddd_name = name

    def _given_mocked_ddd(self):
        mock_ddd = Mock(spec=DDD)
        mock_ddd.name = self._ddd_name
        self._mock_ddd = mock_ddd

    def _given_language_codes(self, language_codes):
        self._language_codes = language_codes

    def _given_file_exists(self, path):
        self._ensure_dir_exists(os.path.dirname(path))
        with open(path, "w"):
            pass

    def _ensure_dir_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _given_step_created(self, VerifyStep):
        ignore_warnings = True
        verbose = False
        self._verify_step = VerifyStep(
            self._mock_ddd, ignore_warnings, self._language_codes, verbose, self._ddd_name, "grammar"
        )

    def _when_calling_build(self):
        self._verify_step.build()

    def _then_files_have_not_been_written_by_auto_generator(self):
        self._mocked_auto_generator.write_to_file.assert_not_called()

    @pytest.mark.parametrize("step", [
        VerifyStepForGFGeneration,
        VerifyStepForGFRGLGeneration,
    ])
    def test_verify_generates_gf_grammars(self, step):
        with self._patched_auto_generator(step) as MockAutoGenerator:
            self._given_mocked_auto_generator(MockAutoGenerator)
            self._given_ddd_name("MockDDD")
            self._given_mocked_ddd()
            self._given_language_codes(["eng", "sv"])
            self._given_file_exists("MockDDD/grammar/grammar_eng.xml")
            self._given_step_created(step)
            self._when_calling_build()
            self._then_gf_grammars_have_been_generated_for(["eng", "sv"])

    def _then_gf_grammars_have_been_generated_for(self, expected_languages):
        expected_calls = [call(language) for language in expected_languages]
        self._mocked_auto_generator.generate.assert_has_calls(expected_calls)
