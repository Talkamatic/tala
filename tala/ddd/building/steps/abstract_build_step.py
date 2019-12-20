class AbstractBuildStep(object):
    def __init__(self, ddd, language_codes, ddd_root_directory, grammar_directory, verbose):
        self._ddd = ddd
        self._name = ddd.name
        self._language_codes = language_codes
        self._ddd_root_directory = ddd_root_directory
        self._grammar_directory = grammar_directory
        self._verbose = verbose

    def build(self):
        raise NotImplementedError()

    def _log_command(self, cmd):
        if self._verbose:
            print(("calling %r" % cmd))
