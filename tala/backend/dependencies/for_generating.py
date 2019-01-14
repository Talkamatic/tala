import warnings

from tala.backend.dependencies.abstract_backend_dependencies import AbstractBackendDependencies
from tala.config import RasaConfig
from tala.ddd.loading.ddd_set_loader import DDDSetLoader
from tala.model.sort import DATETIME, INTEGER


class BackendDependenciesForGenerating(AbstractBackendDependencies):
    def __init__(self, backend_args):
        super(BackendDependenciesForGenerating, self).__init__(backend_args)
        self._raw_rasa_config = None
        self._is_duckling_enabled = False
        self._duckling_url = None
        if any(self.ddds_with_rasa):
            self._raw_rasa_config = RasaConfig(backend_args.rasa_config).read()
            self._is_duckling_enabled = self._raw_rasa_config["enable_duckling"]
            self._duckling_url = self._raw_rasa_config["duckling_url"]

        if any(self.ddds_with_rasa) and not self.is_duckling_enabled:
            self._validate_compatibility_with_rasa_but_not_duckling()

        self._validate_compatibility_without_rasa()

    def _validate_compatibility_with_rasa_but_not_duckling(self):
        for ddd in self.ddds_with_rasa:
            if ddd.ontology.predicates_contain_sort(DATETIME):
                warnings.warn(
                    "DDD '{0}' contains predicates of the '{1}' sort, but duckling is disabled. "
                    "'{1}' entities won't be recognized in NLU.".format(ddd.name, DATETIME)
                )
            if ddd.ontology.predicates_contain_sort(INTEGER):
                warnings.warn(
                    "DDD '{0}' contains predicates of the '{1}' sort, but duckling is disabled. "
                    "Accuracy for '{1}' entities will be reduced in NLU.".format(ddd.name, INTEGER)
                )

    def _validate_compatibility_without_rasa(self):
        for ddd in self.ddds_without_rasa:
            if ddd.ontology.predicates_contain_sort(DATETIME):
                warnings.warn(
                    "DDD '{0}' contains predicates of the '{1}' sort, but RASA NLU is disabled. "
                    "'{1}' entities won't be recognized in NLU.".format(ddd.name, DATETIME)
                )

    def load_ddds(self, ddd_names):
        ddd_set_loader = self._create_ddd_set_loader()
        ddds = ddd_set_loader.ddds_as_list(ddd_names, languages=self.supported_languages)
        return ddds

    def _create_ddd_set_loader(self):
        return DDDSetLoader(self.overridden_ddd_config_paths)

    @property
    def is_duckling_enabled(self):
        return self._is_duckling_enabled

    @property
    def duckling_url(self):
        return self._duckling_url

    @property
    def ddds_without_rasa(self):
        return [ddd for ddd in self.ddds if not ddd.is_rasa_enabled]
