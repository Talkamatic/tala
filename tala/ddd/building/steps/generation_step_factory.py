import os

from tala.ddd.building.steps.generation import GenerationStepForGeneratedGfFiles, GenerationStepForGfRglGeneratedFiles, \
    GenerationStepForHandcraftedGfFiles
from tala.ddd_utils import has_handcrafted_gf_grammar


class GenerationStepFactory(object):
    @staticmethod
    def create(ddd, language_codes, verbose, ignore_warnings):
        grammar_directory = "grammar"
        grammar_path = os.path.join(ddd.name, grammar_directory)
        handcrafted_gf = any([
            has_handcrafted_gf_grammar(ddd.name, lang, grammar_path)
            for lang in language_codes])
        if ddd.use_rgl:
            if handcrafted_gf:
                BuilderClass = GenerationStepForHandcraftedGfFiles
            else:
                BuilderClass = GenerationStepForGfRglGeneratedFiles
        else:
            if handcrafted_gf:
                BuilderClass = GenerationStepForHandcraftedGfFiles
            else:
                BuilderClass = GenerationStepForGeneratedGfFiles

        ddd_root_directory = os.path.join(os.getcwd(), ddd.name)
        return BuilderClass(
            ddd,
            ignore_warnings,
            language_codes,
            verbose,
            ddd_root_directory,
            grammar_directory
        )