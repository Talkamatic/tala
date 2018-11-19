import os

from tala import utils
from tala.gf.naming import abstract_gf_filename, natural_language_gf_filename, semantic_gf_filename


def has_handcrafted_gf_grammar(ddd_name, language_code, path_to_grammar_folder):
    with utils.chdir(path_to_grammar_folder):
        exists = (os.path.exists(abstract_gf_filename(ddd_name)) or
                  os.path.exists(semantic_gf_filename(ddd_name)) or
                  os.path.exists(natural_language_gf_filename(ddd_name, language_code)))
        return exists


def path_to_grammar_build_folder(ddd_name, language_code, path):
    grammar_path = os.path.join(path, ddd_name, "grammar")
    is_handcrafted = has_handcrafted_gf_grammar(ddd_name, language_code, grammar_path)
    build_folder = "build_handcrafted" if is_handcrafted else "build"
    return os.path.join(grammar_path, build_folder)