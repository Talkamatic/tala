import os

from tala.ddd.building.steps.step_factory import CleanStepFactory, GenerateStepFactory, VerifyStepFactory
from tala.ddd.building.supported_asrs import SUPPORTED_ASRS
from tala.utils import chdir


class DDDsNotSpecifiedException(Exception):
    pass


class DDDNotFoundException(Exception):
    pass


class UnexpectedASRException(Exception):
    pass


class DDDBuilderForGenerating(object):
    def __init__(self, backend_dependencies, verbose=False, ignore_warnings=False, language_codes=None):
        super(DDDBuilderForGenerating, self).__init__()
        self._verbose = verbose
        self._ignore_warnings = ignore_warnings
        self._backend_dependencies = backend_dependencies
        self._language_codes = language_codes or self._backend_dependencies.supported_languages

        if self._backend_dependencies.asr not in SUPPORTED_ASRS:
            raise UnexpectedASRException(
                "Expected ASR as one of %s but got %r" % (SUPPORTED_ASRS, self._backend_dependencies.asr)
            )

        if not self._backend_dependencies.ddds:
            raise DDDsNotSpecifiedException("Expected DDDs to be specified in the backend config, but found none.")

        self.cwd = os.getcwd()
        self._cleaners = {}
        self._generators = {}
        self._verifiers = {}

        for ddd in self._backend_dependencies.ddds:
            if not os.path.exists(ddd.name):
                absolute_ddd_path = os.path.join(os.getcwd(), ddd.name)
                raise DDDNotFoundException("Expected a DDD at %r but found none." % absolute_ddd_path)
        for ddd in self._backend_dependencies.ddds:
            cleaner_factory = CleanStepFactory(ddd, self._language_codes, self._verbose, self._ignore_warnings)
            self._cleaners[ddd.name] = cleaner_factory.create()
            generator_factory = GenerateStepFactory(ddd, self._language_codes, self._verbose, self._ignore_warnings)
            self._generators[ddd.name] = generator_factory.create()
            verifier_factory = VerifyStepFactory(ddd, self._language_codes, self._verbose, self._ignore_warnings)
            self._verifiers[ddd.name] = verifier_factory.create()

    def build(self):
        for ddd in self._backend_dependencies.ddds:
            with chdir.chdir(ddd.name):
                print(("Generating models for DDD '{}'.".format(ddd.name)))
                self._cleaners[ddd.name].build()
                self._generators[ddd.name].build()
                print(("Finished generating models for DDD '{}'.".format(ddd.name)))

    def verify(self):
        for ddd_name, verifier in list(self._verifiers.items()):
            with chdir.chdir(ddd_name):
                verifier.build()
