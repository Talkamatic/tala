import os
import shutil
from io import StringIO
import warnings

from tala.config import DddConfig
from tala.utils import chdir

DDD_MAKER_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(DDD_MAKER_PATH, "templates")


def write_template_to_file(target_path, template):
    with open(target_path, 'w') as target:
        template.seek(0)
        shutil.copyfileobj(template, target)


def word_list_template():
    content = StringIO()
    with open(os.path.join(TEMPLATES_PATH, "word_list_template.txt"), 'r') as template:
        shutil.copyfileobj(template, content)
    return content


def word_list_filename(path_to_ddd):
    with chdir.chdir(path_to_ddd):
        ddd_config = DddConfig().read()
    filename = ddd_config["word_list"]
    return filename


def create_word_list_boilerplate(path_to_ddd):
    filename = word_list_filename(path_to_ddd)
    target_path = os.path.join(path_to_ddd, filename)
    template = word_list_template()
    write_template_to_file(target_path, template)


def potentially_create_word_list_boilerplate(path_to_ddd):
    filename = word_list_filename(path_to_ddd)
    word_list_path = os.path.join(path_to_ddd, filename)
    if not os.path.exists(word_list_path):
        create_word_list_boilerplate(path_to_ddd)
        ddd_name = os.path.basename(path_to_ddd)
        message = "The word list for %r is missing. It was created at %s." % (ddd_name, word_list_path)
        warnings.warn(message)
