import os

from tala.config import DddConfig, DddConfigNotFoundException
from tala.ddd.loading.ddd_loader import DDDLoader
from tala.utils.chdir import chdir


class DddNotFoundException(Exception):
    pass


class OverriddenDddConfigNotFoundException(Exception):
    pass


class DDDSetLoader(object):
    def __init__(self, overridden_ddd_config_paths=None):
        self._overridden_ddd_configs = overridden_ddd_config_paths or []
        self._validate_that_ddds_in_overridden_ddd_configs_exist()
        self._validate_that_configs_in_overridden_ddd_configs_exist()

    def _validate_that_ddds_in_overridden_ddd_configs_exist(self):
        for overridden_config in self._overridden_ddd_configs:
            if not os.path.exists(overridden_config.ddd_name):
                raise DddNotFoundException(
                    "Expected overridden DDD '%s' to exist in the working directory '%s', but it doesn't." %
                    (overridden_config.ddd_name, os.getcwd())
                )

    def _validate_that_configs_in_overridden_ddd_configs_exist(self):
        for overridden_config in self._overridden_ddd_configs:
            with chdir(overridden_config.ddd_name):
                try:
                    DddConfig(overridden_config.path).read()
                except DddConfigNotFoundException:
                    raise OverriddenDddConfigNotFoundException(
                        "Expected DDD config '%s' to exist in DDD '%s' but it was not found." %
                        (overridden_config.path, overridden_config.ddd_name)
                    )

    def ddds_as_list(self, ddds, path=".", *args, **kwargs):
        with chdir(path):
            return list(self._load_ddds(ddds, *args, **kwargs))

    def _load_ddds(self, ddd_names, *args, **kwargs):
        configs = {}
        for ddd_name in ddd_names:
            configs[ddd_name] = self._ddd_config(ddd_name)

        for ddd_name in ddd_names:
            config = configs[ddd_name]
            yield self._load_ddd(ddd_name, config, *args, **kwargs)

    def _load_ddd(self, *args, **kwargs):
        ddd_loader = DDDLoader(*args, **kwargs)
        return ddd_loader.load()

    def _ddd_config(self, ddd_name):
        for overridden_config in self._overridden_ddd_configs:
            if overridden_config.ddd_name == ddd_name:
                with chdir(ddd_name):
                    return DddConfig(overridden_config.path).read()
        with chdir(ddd_name):
            return DddConfig().read()
