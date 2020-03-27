from io import StringIO
import os
import re

from tala.config import BackendConfig, DddConfig
from tala.ddd.maker import utils
from tala.utils import chdir


class UnexpectedCharactersException(Exception):
    pass


class DddMaker(object):
    def __init__(self, ddd_name, use_rgl, target_dir="."):
        self._validate(ddd_name)
        self._ddd_name = ddd_name
        self._use_rgl = use_rgl
        self._class_name_prefix = self.directory_to_class_name(ddd_name)
        self._target_dir = target_dir

    @staticmethod
    def directory_to_class_name(directory_name):
        name_with_capitalized_words = directory_name.title()
        class_name = re.sub("[_]", "", name_with_capitalized_words)
        return class_name

    @staticmethod
    def _validate(name):
        if re.match(r'^[0-9a-zA-Z_]+$', name) is None:
            raise UnexpectedCharactersException(
                f"Expected only alphanumeric ASCII and underscore characters in DDD name '{name}', but found others."
            )

    def make(self):
        self._ensure_target_dir_exists()
        self._create_ddd_module()
        self._create_domain_skeleton_file()
        self._create_ontology_skeleton_file()
        self._create_service_interface_skeleton_file()
        self._create_configs()
        self._create_grammar()
        self._create_test_directory()
        self._create_interaction_tests()
        self._create_word_list()

    def _ensure_target_dir_exists(self):
        if not os.path.exists(self._target_dir):
            os.mkdir(self._target_dir)

    def _create_ddd_module(self):
        ddd_path = self._ddd_path()
        if not os.path.exists(ddd_path):
            os.makedirs(ddd_path)
        self._create_empty_file("__init__.py")

    def _create_configs(self):
        with chdir.chdir(self._target_dir):
            BackendConfig.write_default_config(ddd_name=self._ddd_name)
            with chdir.chdir(self._ddd_name):
                DddConfig.write_default_config(use_rgl=self._use_rgl)

    def _create_ontology_skeleton_file(self):
        self._create_skeleton_file("ontology_template.xml", "ontology.xml")

    def _create_domain_skeleton_file(self):
        self._create_skeleton_file("domain_template.xml", "domain.xml")

    def _create_service_interface_skeleton_file(self):
        self._create_skeleton_file("service_interface_template.xml", "service_interface.xml")

    def _create_grammar(self):
        grammar_path = os.path.join(self._ddd_path(), "grammar")
        if not os.path.exists(grammar_path):
            os.makedirs(grammar_path)
        self._create_empty_file("grammar/__init__.py")
        self._create_skeleton_file("grammar_eng_template.xml", "grammar/grammar_eng.xml")

    def _ddd_path(self):
        return os.path.join(self._target_dir, self._ddd_name)

    def _create_empty_file(self, filename):
        path = os.path.join(self._ddd_path(), filename)
        open(path, 'w').close()

    def _create_test_directory(self):
        os.mkdir("%s/%s/test" % (self._target_dir, self._ddd_name))

    def _create_interaction_tests(self):
        self._create_skeleton_file("interaction_tests_eng_template.txt", "test/interaction_tests_eng.txt")

    def _create_skeleton_file(self, template_filename, ddd_relative_path, language="eng"):
        target = os.path.join(self._ddd_path(), ddd_relative_path)
        content = self._template_from_file(template_filename, language)
        utils.write_template_to_file(target, content)

    def _create_word_list(self):
        utils.create_word_list_boilerplate(self._ddd_path())

    def _template_from_file(self, filename, language):
        path = os.path.join(utils.TEMPLATES_PATH, filename)
        content = StringIO()
        with open(path) as template:
            for line in template:
                line = line.replace('__app__', self._ddd_name)
                line = line.replace('__lang__', language)
                line = line.replace('__App__', self._class_name_prefix)
                content.write(line)
        return content
