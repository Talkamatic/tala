import os
import shutil

from tala.ddd.building.steps.abstract_build_step import AbstractBuildStep
from tala.utils import chdir


class AbstractCleanStep(AbstractBuildStep):
    _build_directory = None

    def __init__(self, ddd, ignore_warnings, language_codes, verbose, ddd_root_directory, grammar_directory):
        super(AbstractCleanStep, self).__init__(ddd, language_codes, ddd_root_directory, grammar_directory, verbose)
        self._ignore_warnings = ignore_warnings

    def build(self):
        with chdir.chdir(self._ddd_root_directory):
            with chdir.chdir(self._grammar_directory):
                self._create_empty_build_directories()

    def _create_empty_build_directories(self):
        for language_code in self._language_codes:
            self._create_empty_build_directory(language_code, self._build_directory)

    def _create_empty_build_directory(self, language_code, directory_name):
        directory = "%s/%s" % (directory_name, language_code)
        print("[%s] Cleaning build directory '%s'..." % (language_code, directory), end="")
        self._clean_directory(directory)
        print("Done.")

    def _clean_directory(self, directory):
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=True)
        os.makedirs(directory)


class CleanStepForGFGeneration(AbstractCleanStep):
    _build_directory = "build"


class CleanStepForHandcraftedGFFiles(AbstractCleanStep):
    _build_directory = "build_handcrafted"
