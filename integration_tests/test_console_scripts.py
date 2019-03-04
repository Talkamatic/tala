import os
import re
import shutil
import subprocess
import tempfile

from pathlib import Path
import pytest

from tala.config import BackendConfig, DddConfig, DeploymentsConfig
from tala.cli import console_script
from tala.utils.chdir import chdir


class UnexpectedContentsException(Exception):
    pass


class TempDirTestCase(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TalaIntegrationTest")
        self._working_dir = os.getcwd()
        os.chdir(self._temp_dir)

    def teardown(self):
        os.chdir(self._working_dir)
        shutil.rmtree(self._temp_dir)


class ConsoleScriptTestCase(TempDirTestCase):
    def setup(self):
        super(ConsoleScriptTestCase, self).setup()
        self._process = None

    def _given_created_ddd_in_a_target_dir(self):
        self._create_ddd()

    def _create_ddd(self):
        self._run_tala_with(["create-ddd", "--target-dir", "test_root", "test_ddd"])

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
        self._process = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return self._process.communicate()

    def _then_stderr_contains_constructive_error_message_for_missing_backend_config(self, config_path):
        pattern = "Expected backend config '.*{config}' to exist but it was not found. To create it, " \
                  "run 'tala create-backend-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _then_stderr_contains_constructive_error_message_for_missing_ddd_config(self, config_path):
        pattern = "Expected DDD config '.*{config}' to exist but it was not found. To create it, " \
                  "run 'tala create-ddd-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _given_config_overrides_missing_parent(self, path):
        self._replace_in_file(path, '"overrides": null', '"overrides": "missing_parent.json"')

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

    def _then_file_contains(self, filename, expected_string):
        actual_content = self._read_file(filename)
        assert expected_string in actual_content

    def _read_file(self, filename):
        with open(filename) as f:
            actual_content = f.read()
        return actual_content

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
        assert re.search(expected_pattern, string) is not None, "Expected string to match '{}' but got '{}'".format(
            expected_pattern, string
        )


class TestCreateDDD(ConsoleScriptTestCase):
    def test_create(self):
        self._when_creating_a_ddd()
        self._then_result_is_successful()

    def _when_creating_a_ddd(self):
        self._create_ddd()


class TestVersionIntegration(ConsoleScriptTestCase):
    def test_version(self):
        self._when_checking_tala_version()
        self._then_result_is_a_version_number()

    def _when_checking_tala_version(self):
        process = subprocess.Popen(["tala version"], stdout=subprocess.PIPE, shell=True)
        stdout, _ = process.communicate()
        self._result = stdout

    def _then_result_is_a_version_number(self):
        base_version = r"[0-9]+\.[0-9]+(\.[0-9]+)*"
        dev_version_suffix = r"\.dev[0-9]+\+[a-z0-9]+"
        dirty_version_suffix = r"\.d[0-9]{8}"

        release_version_regexp = base_version
        dev_version_regexp = base_version + dev_version_suffix
        dirty_version_regexp = base_version + dev_version_suffix + dirty_version_suffix

        is_version_regexp = r"(?:%s|%s|%s)" % (release_version_regexp, dev_version_regexp, dirty_version_regexp)

        assert re.search(is_version_regexp, self._result) is not None


class TestBackendConfigCreationIntegration(ConsoleScriptTestCase):
    def test_create_config_without_path_or_ddd(self):
        self._when_running_command("tala create-backend-config")
        self._then_backend_config_has_active_ddd(BackendConfig.default_name(), "")

    def test_create_backend_config_without_ddd(self):
        self._when_running_command("tala create-backend-config --filename test.config.json")
        self._then_backend_config_has_active_ddd("test.config.json", "")

    def _then_backend_config_has_active_ddd(self, config_path, expected_active_ddd):
        config = BackendConfig(config_path).read()
        assert expected_active_ddd == config["active_ddd"]

    def test_create_backend_config_with_ddd(self):
        self._when_running_command("tala create-backend-config --filename test.config.json --ddd test_ddd")
        self._then_backend_config_has_active_ddd("test.config.json", "test_ddd")


class TestConfigFileIntegration(ConsoleScriptTestCase):
    @pytest.mark.parametrize(
        "ConfigClass,command", [
            (BackendConfig, "create-backend-config"),
            (DddConfig, "create-ddd-config"),
            (DeploymentsConfig, "create-deployments-config"),
        ]
    )
    def test_create_config_without_path(self, ConfigClass, command):
        self._when_running_command("tala {}".format(command))
        self._then_config_contains_defaults(ConfigClass, ConfigClass.default_name())

    def _then_config_contains_defaults(self, ConfigClass, name):
        expected_config = ConfigClass.default_config()
        actual_config = ConfigClass(name).read()
        assert expected_config == actual_config

    @pytest.mark.parametrize(
        "ConfigClass,command", [
            (BackendConfig, "create-backend-config"),
            (DddConfig, "create-ddd-config"),
            (DeploymentsConfig, "create-deployments-config"),
        ]
    )
    def test_create_config_with_path(self, ConfigClass, command):
        self._when_running_command("tala {} --filename my_ddd.config.json".format(command))
        self._then_config_contains_defaults(ConfigClass, "my_ddd.config.json")

    @pytest.mark.parametrize(
        "name,command", [
            ("backend", "create-backend-config"),
            ("DDD", "create-ddd-config"),
            ("deployments", "create-deployments-config"),
        ]
    )
    def test_exception_raised_if_config_file_already_exists(self, name, command):
        self._given_config_was_created_with([command, "--filename", "test.config.json"])
        self._when_running_command("tala {} --filename test.config.json".format(command))
        self._then_stderr_contains(
            "Expected to be able to create {} config file 'test.config.json' but it already exists.".format(name)
        )

    def _given_config_was_created_with(self, arguments):
        self._run_tala_with(arguments)

    @pytest.mark.parametrize("command", [
        "create-backend-config",
        "create-ddd-config",
        "create-deployments-config",
    ])
    def test_config_file_not_overwritten(self, command):
        self._given_file_contains("test.config.json", "unmodified_mock_content")
        self._when_running_command("tala {} --filename test.config.json".format(command))
        self._then_file_contains("test.config.json", "unmodified_mock_content")

    @pytest.mark.parametrize("command", [
        "tala verify --config non_existing_config.json",
    ])
    def test_missing_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_backend_config("non_existing_config.json")

    @pytest.mark.parametrize("command", [
        "tala verify",
    ])
    def test_missing_parent_backend_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._given_config_overrides_missing_parent(Path(BackendConfig.default_name()))
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_backend_config("missing_parent.json")

    @pytest.mark.parametrize("command", [
        "tala verify",
    ])
    def test_missing_parent_ddd_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_config_overrides_missing_parent(Path(DddConfig.default_name()))
        with self._given_changed_directory_to_target_dir():
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_ddd_config("missing_parent.json")


class TestVerifyIntegration(ConsoleScriptTestCase):
    def setup(self):
        super(TestVerifyIntegration, self).setup()

    def test_that_verifying_boilerplate_ddd_succeeds(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_verifying()
        self._then_result_is_successful()

    def _when_verifying(self):
        self._run_tala_with(["verify"])

    def test_stdout_when_verifying_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stdout_matches(
            "^Verifying models for DDD 'test_ddd'.\n"
            "\[eng\] Verifying grammar.\n"
            "\[eng\] Finished verifying grammar.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def test_stdout_when_verifying_boilerplate_ddd_with_rasa_enabled(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stdout_matches(
            "^Verifying models for DDD 'test_ddd'.\n"
            "\[eng\] Verifying grammar.\n"
            "\[eng\] Finished verifying grammar.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def _given_enabled_rasa(self):
        self._replace_in_file(
            Path(DddConfig.default_name()), '"rasa_nlu": {}', '"rasa_nlu": {"eng": {"url": "mock-url", "config": {}}}'
        )

    def test_stderr_when_verifying_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stderr_is_empty()

    def _then_stderr_is_empty(self):
        assert self._stderr == ""

    def test_verify_creates_no_build_folders(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_there_are_no_build_folders()

    def _then_there_are_no_build_folders(self):
        ddd_folder = Path("test_root") / "test_ddd" / "grammar"
        build_folders = [path for path in ddd_folder.iterdir() if path.is_dir() and path.name.startswith("build")]
        assert not any(build_folders), "Expected no build folders but got {}".format(build_folders)

    def test_verify_creates_no_build_folders_with_rasa_enabled(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_there_are_no_build_folders()

    def test_verify_returncode_with_schema_violation(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_schema_violation_in_ontology()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_returncode_signals_error()

    def _given_schema_violation_in_ontology(self):
        self._replace_in_file(Path("ontology.xml"), "ontology", "hello")

    def _then_returncode_signals_error(self):
        assert self._process.returncode != 0

    def test_verify_stderr_with_schema_violation(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_schema_violation_in_ontology()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stderr_contains(
            "Expected ontology.xml compliant with schema but it's in violation: "
            "Element 'hello': "
            "No matching global declaration available for the validation root., line 2"
        )


class TestInteractIntegration(ConsoleScriptTestCase):
    def test_stderr_when_interacting_with_unknown_environment(self):
        self._given_created_deployments_config()
        self._when_running_command("tala interact my-made-up-environment")
        self._then_stderr_contains(
            "UnexpectedEnvironmentException: "
            "Expected one of the known environments [u'dev'] but got 'my-made-up-environment'"
        )

    def _given_created_deployments_config(self):
        self._run_tala_with(["create-deployments-config"])


class TestGenerateRASAIntegration(ConsoleScriptTestCase):
    def setup(self):
        super(TestGenerateRASAIntegration, self).setup()

    def test_that_generating_boilerplate_ddd_succeeds(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_generating()
        self._then_result_is_successful()

    def _when_generating(self):
        self._run_tala_with(["generate-rasa", "test_ddd", "eng"])

    def test_stdout_when_generating_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_ontology_contains("""
<ontology name="TestDddOntology">
  <action name="call"/>
</ontology>""")
            self._given_grammar_contains(
                """
<grammar>
  <action name="top">main menu</action>
  <action name="up">go back</action>
  <action name="call">call</action>
  <request action="call"><utterance>make a call</utterance></request>
</grammar>"""
            )
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate-rasa test_ddd eng")
        self._then_stdout_matches(
            'language: "en"\n'
            '\n'
            'pipeline: "spacy_sklearn"\n'
            '\n'
            'data: |\n'
            '  ## intent:test_ddd:action::call\n'
            '  - make a call\n'
            '\n'
            '  ## intent:test_ddd:NEGATIVE\n'
            '- aboard\n'
            '- about\n'
        )

    def _given_ontology_contains(self, new_content):
        old_content = """
<ontology name="TestDddOntology">
</ontology>"""
        self._replace_in_file(Path("ontology.xml"), old_content, new_content)

    def _given_grammar_contains(self, new_content):
        old_content = """
<grammar>
</grammar>"""
        self._replace_in_file(Path("grammar") / "grammar_eng.xml", old_content, new_content)

    def test_generating_for_unknown_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate-rasa unknown-ddd eng")
        self._then_stderr_matches("UnexpectedDDDException: Expected DDD 'unknown-ddd' to exist but it didn't")

    def test_generating_for_unknown_language(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate-rasa test_ddd unknown-language")
        self._then_stderr_matches(
            "tala generate-rasa\: error\: argument language\: invalid choice\: 'unknown-language'"
        )
