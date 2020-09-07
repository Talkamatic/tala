from tala.ddd.building.steps.abstract_build_step import AbstractBuildStep
from tala.nl.gf.auto_generator import AutoGenerator
from tala.nl.gf.rgl_gf_generator import RglGfFilesGenerator
from tala.utils import chdir


class AbstractVerifyStep(AbstractBuildStep):
    _id = None
    _build_directory = None
    _AutoGeneratorClass = None

    def __init__(self, ddd, ignore_warnings, language_codes, verbose, ddd_root_directory, grammar_directory):
        super(AbstractVerifyStep, self).__init__(ddd, language_codes, ddd_root_directory, grammar_directory, verbose)
        self._ignore_warnings = ignore_warnings

    def build(self):
        with chdir.chdir(self._ddd_root_directory):
            print("Verifying models for DDD '%s'." % self._name)
            with chdir.chdir(self._grammar_directory):
                for language_code in self._language_codes:
                    self._verify_grammars(language_code)
            print("Finished verifying models for DDD '%s'." % self._name)

    def _verify_grammars(self, language_code):
        raise NotImplementedError()

    def _verify_gf_grammar(self, AutoGeneratorClass, language_code):
        generator = AutoGeneratorClass(self._ddd, self._ignore_warnings, cwd=self._ddd_root_directory)
        generator.generate(language_code)
        generator.clear()


class VerifyStepForGFGeneration(AbstractVerifyStep):
    _build_directory = "build"
    _id = "generated"
    _AutoGeneratorClass = AutoGenerator

    def _verify_grammars(self, language_code):
        print("[%s] Verifying grammar." % (language_code))
        self._verify_gf_grammar(self._AutoGeneratorClass, language_code)
        print("[%s] Finished verifying grammar." % (language_code))


class VerifyStepForHandcraftedGFFiles(AbstractVerifyStep):
    _build_directory = "build_handcrafted"
    _id = "handcrafted"

    def _verify_grammars(self, language_code):
        print("[%s] Using handcrafted grammar, will not verify." % (language_code))
        pass


class VerifyStepForGFRGLGeneration(VerifyStepForGFGeneration):
    _AutoGeneratorClass = RglGfFilesGenerator
