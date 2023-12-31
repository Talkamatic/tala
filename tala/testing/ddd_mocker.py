import os
import shutil
import sys
import tempfile
import unittest

from tala.config import BackendConfig, DddConfig


class DddMockingTestCase(unittest.TestCase):
    def setUp(self):
        self._working_dir = os.getcwd()
        temp_dir = tempfile.mkdtemp(prefix="DddMockingTestCase")
        os.chdir(temp_dir)
        self._temp_dir = os.getcwd()
        self._exception_occurred = False
        self._mock_ddd_config = DddConfig.default_config(use_rgl=True)
        self._mock_backend_config = BackendConfig.default_config(active_ddd="mockup_app", ddds=["mockup_app"])

    def tearDown(self):
        os.chdir(self._working_dir)
        if self._exception_occurred:
            if "--keep-temp-dir" in sys.argv:
                print(("NOTE: Temp dir %s kept for debugging. It needs to be deleted manually." % self._temp_dir))
            else:
                self._delete_temp_dir()
                print("NOTE: Temp dir deleted. To keep the temp dir for debugging, "
                      "run again with --keep-temp-dir")
        else:
            self._delete_temp_dir()

    def _delete_temp_dir(self):
        shutil.rmtree(self._temp_dir)

    def _given_ontology_py_file(self, path):
        content = """
from tala.model.ontology import DddOntology
class MockupOntology(DddOntology):
  sorts = {}
  predicates = {}
  individuals = {}
  actions = set()
"""
        self.create_mockup_file(path, content)

    def _given_domain_py_file(self, path):
        content = """
from tala.model.domain import DddDomain
class MockupDomain(DddDomain):
  plans = []
"""
        self.create_mockup_file(path, content)

    def create_mockup_domain_file(self, path="mockup_app/domain.xml"):
        content = """
<domain name="MockupDomain"/>
"""
        self.create_mockup_file(path, content)

    def _given_domain_xml_file(self, path, domain_name="MockupDomain"):
        content = '<domain name="%s"/>' % domain_name
        self.create_mockup_file(path, content)

    def _given_service_interface_xml_file(self, path):
        content = '<service_interface/>'
        self.create_mockup_file(path, content)

    def _given_ontology_xml_file(self, path):
        content = '<ontology name="MockupOntology"/>'
        self.create_mockup_file(path, content)

    def _given_mocked_ddd_config(self, **kwargs):
        if "use_rgl" not in kwargs:
            kwargs["use_rgl"] = True
        self._mock_ddd_config = DddConfig.default_config(**kwargs)

    def _given_mocked_backend_config(self, **kwargs):
        self._mock_backend_config = BackendConfig.default_config(**kwargs)

    def create_mockup_file(self, relative_path, content):
        container_directory = os.path.dirname(relative_path)
        self._ensure_dir_exists(container_directory)
        with open(relative_path, "w") as f:
            f.write(content)

    def _ensure_dir_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
