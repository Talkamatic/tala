from __future__ import print_function

from tala.ddd.building.steps.abstract_build_step import AbstractBuildStep
from tala.nl.gf.auto_generator import AutoGenerator
from tala.nl.gf.rgl_gf_generator import RglGfFilesGenerator
from tala.nl.rasa.generating.generator import RasaGenerator
from tala.utils import chdir


class AbstractGenerateStep(AbstractBuildStep):
    _id = None
    _build_directory = None
    _AutoGeneratorClass = None

    def __init__(self, ddd, ignore_warnings, language_codes, verbose, ddd_root_directory, grammar_directory):
        super(AbstractGenerateStep, self).__init__(ddd, language_codes, ddd_root_directory, grammar_directory, verbose)
        self._ignore_warnings = ignore_warnings

    def build(self):
        with chdir.chdir(self._ddd_root_directory):
            with chdir.chdir(self._grammar_directory):
                for language_code in self._language_codes:
                    self._generate_grammars(language_code)
                    self._potentially_generate_rasa_model(language_code)

    def _potentially_generate_rasa_model(self, language_code):
        if not self._ddd.is_rasa_enabled:
            print("[%s] Not using RASA NLU, will not generate RASA models." % (language_code))
            return

        self._generate_rasa_nlu_model(language_code)

    def _generate_rasa_nlu_model(self, language_code):
        print("[%s] Generating model for RASA NLU." % (language_code))
        generator = RasaGenerator(self._ddd, language_code)
        generator.generate_and_write_to_file()
        print("[%s] Finished generating model for RASA NLU." % (language_code))

    def _generate_grammars(self, language_code):
        raise NotImplementedError()

    def _auto_generate_gf_grammar(self, AutoGeneratorClass, language_code):
        generator = AutoGeneratorClass(self._ddd, self._ignore_warnings, cwd=self._ddd_root_directory)
        generator.generate(language_code)
        generator.write_to_file(language_code)
        generator.clear()


class GenerateStepForGFGeneration(AbstractGenerateStep):
    _build_directory = "build"
    _AutoGeneratorClass = AutoGenerator

    def _generate_grammars(self, language_code):
        print("[%s] Generating grammar." % (language_code))
        self._auto_generate_gf_grammar(self._AutoGeneratorClass, language_code)
        print("[%s] Finished generating grammar." % (language_code))


class GenerateStepForHandcraftedGFFiles(AbstractGenerateStep):
    _build_directory = "build_handcrafted"

    def _generate_grammars(self, language_code):
        print("[%s] Using handcrafted grammar, will not generate." % (language_code))
        pass


class GenerateStepForGFRGLGeneration(GenerateStepForGFGeneration):
    _AutoGeneratorClass = RglGfFilesGenerator
