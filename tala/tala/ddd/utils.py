import os

from tala.utils import chdir
from tala.nl.gf.naming import abstract_gf_filename, natural_language_gf_filename, semantic_gf_filename


def has_handcrafted_gf_grammar(ddd_name, language_code, path_to_grammar_folder):
    with chdir.chdir(path_to_grammar_folder):
        exists = (
            os.path.exists(abstract_gf_filename(ddd_name)) or os.path.exists(semantic_gf_filename(ddd_name))
            or os.path.exists(natural_language_gf_filename(ddd_name, language_code))
        )
        return exists


def path_to_grammar_build_folder(ddd_name, language_code, path):
    grammar_path = os.path.join(path, ddd_name, "grammar")
    is_handcrafted = has_handcrafted_gf_grammar(ddd_name, language_code, grammar_path)
    build_folder = "build_handcrafted" if is_handcrafted else "build"
    return os.path.join(grammar_path, build_folder)


class CacheMethod:
    def __init__(self, instance, method):
        self._method = method
        self._cache = {}

        def cached_method(*args):
            if args in self._cache:
                return self._cache[args]
            else:
                value = self._method.__call__(*args)
                self._cache[args] = value
                return value

        setattr(instance, method.__name__, cached_method)

    def __str__(self):
        return "CacheMethod(%s, _cache=%s)" % (self._method, self._cache)

    def clear(self):
        self._cache = {}
