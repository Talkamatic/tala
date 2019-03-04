import os
import os.path
import shutil
import tempfile

from mock import Mock

from tala.ddd.building.steps.generate import AbstractGenerateStep
from tala.model.ddd import DDD


class TestAbstractGenerateStep(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TestGenerate")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._generate_step = None
        self._mock_ddd = None
        self._ddd_name = None
        self._language_codes = []

    def teardown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    def test_build_generates_grammars(self):
        self._given_ddd_name("MockDDD")
        self._given_mocked_ddd()
        self._given_language_codes(["eng"])
        self._given_file_exists("MockDDD/grammar/grammar_eng.py")
        self._given_generate_step_created()
        self._given_mocked_generate_grammars_method()
        self._when_calling_build()
        self._then_generate_grammars_is_invoked_with_arguments("eng")

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

    def _given_generate_step_created(self):
        ignore_warnings = True
        verbose = False
        self._generate_step = AbstractGenerateStep(
            self._mock_ddd, ignore_warnings, self._language_codes, verbose, self._ddd_name, "grammar"
        )

    def _given_mocked_generate_grammars_method(self):
        self._generate_step._generate_grammars = Mock()

    def _when_calling_build(self):
        self._generate_step.build()

    def _then_generate_grammars_is_invoked_with_arguments(self, *expected_args):
        self._generate_step._generate_grammars.assert_called_once_with(*expected_args)
