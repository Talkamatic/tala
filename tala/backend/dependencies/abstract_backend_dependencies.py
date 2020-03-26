from tala.config import BackendConfig

INACTIVE_SECONDS_ALLOWED_MIN = 60 * 60
INACTIVE_SECONDS_ALLOWED_MAX = 60 * 60 * 24 * 30


class InvalidConfigValue(Exception):
    pass


class AbstractBackendDependencies(object):
    def __init__(self, args):
        super(AbstractBackendDependencies, self).__init__()

        self._overridden_ddd_config_paths = args.overridden_ddd_config_paths
        if hasattr(args, "interpret_partially"):
            self._interpret_partially = args.interpret_partially
        else:
            self._interpret_partially = None
        self._raw_config = BackendConfig(args.config).read()
        self._path = args.config or BackendConfig.default_name()
        self._asr = self._raw_config["asr"]
        self._use_recognition_profile = self._raw_config["use_recognition_profile"]
        self._repeat_questions = self._raw_config["repeat_questions"]
        self._use_word_list_correction = self._raw_config["use_word_list_correction"]
        self._supported_languages = self._raw_config["supported_languages"]
        self._ddd_names = self._raw_config["ddds"]
        self._rerank_amount = self._raw_config["rerank_amount"]
        self._inactive_seconds_allowed = self._raw_config["inactive_seconds_allowed"]
        self._validate_inactive_seconds_allowed()
        self._response_timeout = self._raw_config["response_timeout"]

    def _validate_inactive_seconds_allowed(self):
        if self._inactive_seconds_allowed < INACTIVE_SECONDS_ALLOWED_MIN or self._inactive_seconds_allowed > INACTIVE_SECONDS_ALLOWED_MAX:
            raise InvalidConfigValue(
                "Expected inactive_seconds_allowed to be in the range %d-%d, but it was %d." %
                (INACTIVE_SECONDS_ALLOWED_MIN, INACTIVE_SECONDS_ALLOWED_MAX, self._inactive_seconds_allowed)
            )

    @property
    def raw_config(self):
        return self._raw_config

    @property
    def overridden_ddd_config_paths(self):
        return self._overridden_ddd_config_paths

    @property
    def interpret_partially(self):
        return self._interpret_partially

    @property
    def ddds(self):
        return self._ddds

    @ddds.setter
    def ddds(self, ddds):
        self._ddds = ddds

    @property
    def asr(self):
        return self._asr

    @property
    def use_recognition_profile(self):
        return self._use_recognition_profile

    @property
    def repeat_questions(self):
        return self._repeat_questions

    @property
    def use_word_list_correction(self):
        return self._use_word_list_correction

    @property
    def supported_languages(self):
        return self._supported_languages

    @property
    def ddd_names(self):
        return self._ddd_names

    @property
    def rerank_amount(self):
        return self._rerank_amount

    @property
    def inactive_seconds_allowed(self):
        return self._inactive_seconds_allowed

    @property
    def response_timeout(self):
        return self._response_timeout

    @property
    def path(self):
        return self._path
