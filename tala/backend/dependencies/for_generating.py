import warnings

from tala.backend.dependencies.abstract_backend_dependencies import AbstractBackendDependencies
from tala.ddd.loading.ddd_set_loader import DDDSetLoader
from tala.model.sort import DATETIME, INTEGER


class BackendDependenciesForGenerating(AbstractBackendDependencies):
    def __init__(self, backend_args):
        super(BackendDependenciesForGenerating, self).__init__(backend_args)
        self.ddds = self.load_ddds(self._raw_config["ddds"])
        self._validate_rasa_compatibility()

    def _validate_rasa_compatibility(self):
        for ddd in self.ddds:
            if ddd.ontology.predicates_contain_sort(DATETIME):
                warnings.warn(
                    "DDD '{0}' contains predicates of sort '{1}'. "
                    "Note that the builtin NLU can not recognize them. "
                    "For best coverage, use a properly configured Rasa NLU.".format(ddd.name, DATETIME)
                )
            if ddd.ontology.predicates_contain_sort(INTEGER):
                warnings.warn(
                    "DDD '{0}' contains predicates of sort '{1}'. "
                    "Note that the builtin NLU has limitations with this sort. "
                    "For best coverage, use a properly configured Rasa NLU.".format(ddd.name, INTEGER)
                )

    def load_ddds(self, ddd_names):
        ddd_set_loader = self._create_ddd_set_loader()
        ddds = ddd_set_loader.ddds_as_list(ddd_names, languages=self.supported_languages)
        return ddds

    def _create_ddd_set_loader(self):
        return DDDSetLoader(self.overridden_ddd_config_paths)
