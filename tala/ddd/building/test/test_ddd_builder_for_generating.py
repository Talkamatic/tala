import os
import os.path
import shutil
import tempfile
import unittest

from mock import Mock

from tala.backend.dependencies.for_generating import BackendDependenciesForGenerating
from tala.ddd.ddd import DDD
from tala.ddd.building.ddd_builder_for_generating import DDDBuilderForGenerating


class TestDDDBuilderForGenerating(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.mkdtemp(prefix="DddBuilderTestCase")
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)
        self._asr = None
        self._use_word_list_correction = False

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    def test_auto_generator_invoked(self):
        self._given_ddd_name("app")
        self._given_asr("none")
        self._given_mocked_ddd(is_rasa_enabled=False)
        self._given_mocked_backend_dependencies()
        self._given_file_exists("app/grammar/grammar_eng.py")
        self._given_language_codes(["eng"])
        self._given_ddds_builder_created()
        self._given_mocked_build_grammars_method()
        self._given_mocked_generate_grammars_method()
        self._when_build_is_called()
        self._then_generate_grammars_is_invoked_with_arguments("eng")

    def _given_mocked_build_grammars_method(self):
        for trainer in self._ddds_builder._trainers.values():
            trainer._build_grammar = Mock()

    def _given_mocked_generate_grammars_method(self):
        for generator in self._ddds_builder._generators.values():
            generator._generate_grammars = Mock()

    def _given_mocked_ddd(self, is_rasa_enabled):
        mock_ddd = Mock(spec=DDD)
        mock_ddd.name = self._ddd_name
        mock_ddd.is_rasa_enabled = is_rasa_enabled
        self._mock_ddd = mock_ddd

    def _given_ddd_name(self, name):
        self._ddd_name = name

    def _given_file_exists(self, path):
        self._ensure_dir_exists(os.path.dirname(path))
        with open(path, "w") as f:
            pass

    def _ensure_dir_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _given_language_codes(self, language_codes):
        self._language_codes = language_codes

    def _when_build_is_called(self):
        self._ddds_builder.build()

    def _then_generate_grammars_is_invoked_with_arguments(self, *expected_args):
        auto_generators = [generator._generate_grammars for generator in self._ddds_builder._generators.values()]
        first_auto_generator = auto_generators[0]
        first_auto_generator.assert_called_once_with(*expected_args)

    def _given_mocked_backend_dependencies(self):
        backend_dependencies = Mock(spec=BackendDependenciesForGenerating)
        backend_dependencies.ddds = [self._mock_ddd]
        backend_dependencies.asr = self._asr
        backend_dependencies.use_word_list_correction = self._use_word_list_correction
        self._mocked_backend_dependencies = backend_dependencies

    def _given_ddds_builder_created(self):
        self._ddds_builder = DDDBuilderForGenerating(
            self._mocked_backend_dependencies,
            language_codes=self._language_codes
        )

    def _given_asr(self, asr):
        self._asr = asr
