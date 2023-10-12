import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from tala.cli import console_script
from tala.utils.chdir import chdir


class UnexpectedContentsException(Exception):
    pass


class TempDirTestMixin:
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TalaIntegrationTest")
        self._working_dir = os.getcwd()
        os.chdir(self._temp_dir)

    def teardown(self):
        os.chdir(self._working_dir)
        shutil.rmtree(self._temp_dir)


class ConsoleScriptTestMixin(TempDirTestMixin):
    def setup(self):
        super().setup()
        self._process = None

    def _given_created_ddd_in_a_target_dir(self, name=None):
        self._create_ddd(name)

    def _create_ddd(self, name=None):
        name = name or "test_ddd"
        self._run_tala_with(["create-ddd", "--target-dir", "test_root", name])

    def _given_changed_directory_to_target_dir(self):
        return chdir("test_root")

    def _given_changed_directory_to_ddd_folder(self):
        return chdir("test_root/test_ddd")

    def _then_result_is_successful(self):
        def assert_no_error_occured():
            pass

        assert_no_error_occured()

    def _when_running_command(self, command_line):
        self._stdout, self._stderr = self._run_command(command_line)

    def _run_tala_with(self, args):
        console_script.main(args)

    def _run_command(self, command_line):
        self._process = subprocess.Popen(
            command_line.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = self._process.communicate()
        return stdout, stderr

    def _then_stderr_contains_constructive_error_message_for_missing_backend_config(self, config_path):
        pattern = "Expected backend config '.*{config}' to exist but it was not found. To create it, " \
                  r"run 'tala create-backend-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _then_stderr_contains_constructive_error_message_for_missing_ddd_config(self, config_path):
        pattern = "Expected DDD config '.*{config}' to exist but it was not found. To create it, " \
                  r"run 'tala create-ddd-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _given_config_overrides_missing_parent(self, path):
        self._set_in_config_file(path, "overrides", "missing_parent.json")

    def _set_in_config_file(self, path, key, value):
        with path.open(mode="r") as f:
            config = json.load(f)
        config[key] = value
        with path.open(mode="w") as f:
            string = json.dumps(config)
            f.write(str(string))

    def _then_file_contains(self, filename, expected_string):
        actual_content = self._read_file(filename)
        assert expected_string in actual_content

    def _read_file(self, filename):
        with open(filename) as f:
            actual_content = f.read()
        return actual_content

    def _then_stdout_contains(self, string):
        assert string in self._stdout, f"Expected {string} in stdout but got {self._stdout}"

    def _then_stderr_contains(self, string):
        assert string in self._stderr

    def _given_file_contains(self, filename, string):
        f = open(filename, "w")
        f.write(string)
        f.close()

    def _then_stdout_matches(self, expected_pattern):
        self._assert_matches(expected_pattern, self._stdout)

    def _then_stderr_matches(self, expected_pattern):
        self._assert_matches(expected_pattern, self._stderr)

    @staticmethod
    def _assert_matches(expected_pattern, string):
        assert re.search(
            expected_pattern, string
        ) is not None, f"Expected string to match '{expected_pattern}' but got '{string}'"

    def _given_ontology_contains(self, new_content):
        old_content = """
<ontology name="TestDddOntology">
</ontology>"""
        self._replace_in_file(Path("ontology.xml"), old_content, new_content)

    def _replace_in_file(self, path, old, new):
        with path.open() as f:
            old_contents = f.read()
        if old not in old_contents:
            raise UnexpectedContentsException(
                "Expected to find string to be replaced '{}' in '{}' but got '{}'".format(old, str(path), old_contents)
            )
        new_contents = old_contents.replace(old, new)
        with path.open("w") as f:
            f.write(new_contents)

    def _given_domain_contains(self, new_content):
        old_content = """
<domain name="TestDddDomain" is_super_domain="true">
  <goal type="perform" action="top">
    <plan>
      <forget_all/>
      <findout type="goal"/>
    </plan>
  </goal>
</domain>"""
        self._replace_in_file(Path("domain.xml"), old_content, new_content)

    def _given_rgl_is_disabled(self):
        config = Path("ddd.config.json")
        self._replace_in_file(config, '"use_rgl": true', '"use_rgl": false')

    def _given_rgl_is_enabled(self):
        config = Path("ddd.config.json")
        self._replace_in_file(config, '"use_rgl": false', '"use_rgl": true')
