from pathlib import Path

from tala.ddd.building.steps.clean import CleanStepForGFGeneration, CleanStepForHandcraftedGFFiles
from tala.ddd.building.steps.generate import GenerateStepForGFGeneration, GenerateStepForGFRGLGeneration, GenerateStepForHandcraftedGFFiles
from tala.ddd.building.steps.verify import VerifyStepForGFGeneration, VerifyStepForGFRGLGeneration, VerifyStepForHandcraftedGFFiles
from tala.ddd import utils


class AbstractStepFactory(object):
    def __init__(self, ddd, language_codes, verbose, ignore_warnings):
        self._ddd = ddd
        self._language_codes = language_codes
        self._verbose = verbose
        self._ignore_warnings = ignore_warnings

        self._grammar_directory = "grammar"
        grammar_path = Path.cwd() / self._ddd.name / self._grammar_directory
        self._has_handcrafted_gf_grammar = any(
            utils.has_handcrafted_gf_grammar(self._ddd.name, lang, str(grammar_path)) for lang in self._language_codes
        )

        self._ddd_root_directory = Path.cwd() / self._ddd.name

    def _create_step_for_gf_generation(self, *args, **kwargs):
        raise NotImplementedError()

    def _create_step_for_gf_rgl_generation(self, *args, **kwargs):
        raise NotImplementedError()

    def _create_step_for_handcrafted_gf_files(self, *args, **kwargs):
        raise NotImplementedError()

    def create(self):
        if self._has_handcrafted_gf_grammar:
            return self._create_step_for_handcrafted_gf_files()
        if self._ddd.use_rgl:
            return self._create_step_for_gf_rgl_generation()
        return self._create_step_for_gf_generation()

    def _create(self, class_):
        return class_(
            self._ddd, self._ignore_warnings, self._language_codes, self._verbose, str(self._ddd_root_directory),
            self._grammar_directory
        )


class CleanStepFactory(AbstractStepFactory):
    def _create_step_for_gf_generation(self):
        return self._create(CleanStepForGFGeneration)

    def _create_step_for_gf_rgl_generation(self):
        return self._create(CleanStepForGFGeneration)

    def _create_step_for_handcrafted_gf_files(self):
        return self._create(CleanStepForHandcraftedGFFiles)


class GenerateStepFactory(AbstractStepFactory):
    def _create_step_for_gf_generation(self):
        return self._create(GenerateStepForGFGeneration)

    def _create_step_for_gf_rgl_generation(self):
        return self._create(GenerateStepForGFRGLGeneration)

    def _create_step_for_handcrafted_gf_files(self):
        return self._create(GenerateStepForHandcraftedGFFiles)


class VerifyStepFactory(AbstractStepFactory):
    def _create_step_for_gf_generation(self):
        return self._create(VerifyStepForGFGeneration)

    def _create_step_for_gf_rgl_generation(self):
        return self._create(VerifyStepForGFRGLGeneration)

    def _create_step_for_handcrafted_gf_files(self):
        return self._create(VerifyStepForHandcraftedGFFiles)
