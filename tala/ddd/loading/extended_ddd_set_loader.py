from tala.ddd.loading.extended_ddd_loader import ExtendedDDDLoader
from tala.ddd.loading.ddd_set_loader import DDDSetLoader
from tala.utils.chdir import chdir


class ExtendedDDDSetLoader(DDDSetLoader):
    def __init__(self, ddd_manager, overridden_ddd_config_paths=None):
        super(ExtendedDDDSetLoader, self).__init__(overridden_ddd_config_paths)
        self._ddd_manager = ddd_manager

    def ddds_as_list(self, ddds, path=".", *args, **kwargs):
        with chdir(path):
            ddds_dict = self._load_ddds(ddds, *args, **kwargs)
            return list(ddds_dict.values())

    def _load_ddds(self, ddd_names, *args, **kwargs):
        ddds = {}
        configs = {}
        for ddd_name in ddd_names:
            configs[ddd_name] = self._ddd_config(ddd_name)

        for ddd_name in ddd_names:
            config = configs[ddd_name]
            ddds[ddd_name] = self._load_ddd(ddd_name, config, *args, **kwargs)
        return ddds

    def _load_ddd(self, *args, **kwargs):
        ddd_loader = ExtendedDDDLoader(self._ddd_manager, *args, **kwargs)
        return ddd_loader.load()

    def ensure_ddds_loaded(self, ddds, path=".", *args, **kwargs):
        with chdir(path):
            ddds = self._load_ddds(ddds, *args, **kwargs)
            for ddd in list(ddds.values()):
                self._ddd_manager.ensure_ddd_added(ddd)
