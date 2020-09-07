import os


class GrammarReader(object):
    @classmethod
    def read(cls, language_code, path=None):
        with open(cls.path(language_code, path), mode="rb") as grammar_file:
            grammar_source = grammar_file.read()
        return grammar_source

    @staticmethod
    def path(language_code, path=None):
        def relative_path(language_code, path):
            filename = "grammar_%s.xml" % language_code
            if path:
                return os.path.join(path, filename)
            return filename

        path = relative_path(language_code, path)
        return os.path.abspath(path)

    @classmethod
    def xml_grammar_exists_for_language(cls, language_code, path=None):
        return os.path.exists(cls.path(language_code, path))
