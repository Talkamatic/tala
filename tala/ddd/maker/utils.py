import os
import shutil

DDD_MAKER_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(DDD_MAKER_PATH, "templates")


def write_template_to_file(target_path, template):
    with open(target_path, 'w') as target:
        template.seek(0)
        shutil.copyfileobj(template, target)
