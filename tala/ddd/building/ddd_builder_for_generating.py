import os

from tala.ddd.building.steps.generation_step_factory import GenerationStepFactory
from tala.constants.supported_asrs import SUPPORTED_ASRS
from tala import utils


class DDDsNotSpecifiedException(Exception): pass


class DDDNotFoundException(Exception): pass


class UnexpectedASRException(Exception): pass


class DDDBuilderForGenerating(object):
    def __init__(self,
                 backend_dependencies,
                 verbose=False,
                 ignore_warnings=False,
                 language_codes=None):
        super(DDDBuilderForGenerating, self).__init__()
        self._verbose = verbose
        self._ignore_warnings = ignore_warnings
        self._backend_dependencies = backend_dependencies
        self._language_codes = language_codes or self._backend_dependencies.supported_languages

        if self._backend_dependencies.asr not in SUPPORTED_ASRS:
            raise UnexpectedASRException(
                "Expected ASR as one of %s but got %r" % (SUPPORTED_ASRS, self._backend_dependencies.asr))

        if not self._backend_dependencies.ddds:
            raise DDDsNotSpecifiedException("Expected DDDs to be specified in the backend config, but found none.")

        self.cwd = os.getcwd()
        self._generators = {}
        self._trainers = {}

        for ddd in self._backend_dependencies.ddds:
            if not os.path.exists(ddd.name):
                absolute_ddd_path = os.path.join(os.getcwd(), ddd.name)
                raise DDDNotFoundException("Expected a DDD at %r but found none." % absolute_ddd_path)
        for ddd in self._backend_dependencies.ddds:
            generator = GenerationStepFactory.create(ddd, self._language_codes, self._verbose, self._ignore_warnings)
            self._generators[ddd.name] = generator

    def generate(self):
        for ddd_name, generator in self._generators.iteritems():
            with utils.chdir(ddd_name):
                generator.build()

    def build(self):
        self.generate()