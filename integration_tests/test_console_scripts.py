import os
import re
import shutil
import subprocess
import tempfile

from pathlib import Path
import pytest

from tala.config import BackendConfig, DddConfig, RasaConfig
from tala.cli.console_formatting import BOLD, ENDC
from tala.cli import console_script
from tala.utils.chdir import chdir


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
        pattern = "Expected backend config '.*{config}' to exist but it was not found. To create it, " "run 'tala create-backend-config --filename .*{config}'\.".format(
            config=config_path
        )
        assert re.search(pattern, self._stderr) is not None

    def _then_stderr_contains_constructive_error_message_for_missing_ddd_config(self, config_path):
        pattern = "Expected DDD config '.*{config}' to exist but it was not found. To create it, " "run 'tala create-ddd-config --filename .*{config}'\.".format(
            config=config_path
        )
        assert re.search(pattern, self._stderr) is not None

    def _given_config_overrides_missing_parent(self, path):
        self._replace_in_file(path, '"overrides": null', '"overrides": "missing_parent.json"')

    def _replace_in_file(self, path, old, new):
        with path.open() as f:
            old_contents = f.read()
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
            (RasaConfig, "create-rasa-config"),
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
            (RasaConfig, "create-rasa-config"),
        ]
    )
    def test_create_config_with_path(self, ConfigClass, command):
        self._when_running_command("tala {} --filename my_ddd.config.json".format(command))
        self._then_config_contains_defaults(ConfigClass, "my_ddd.config.json")

    @pytest.mark.parametrize(
        "name,command", [
            ("backend", "create-backend-config"),
            ("DDD", "create-ddd-config"),
            ("RASA", "create-rasa-config"),
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
        "create-rasa-config",
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
            "\[eng\] RASA NLU is disabled, skipping its grammar verification.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def _then_stdout_matches(self, expected_pattern):
        assert re.match(expected_pattern,
                        self._stdout) is not None, "Expected stdout to match '{}' but got '{}'".format(
                            expected_pattern, self._stdout
                        )

    def test_stdout_when_verifying_boilerplate_ddd_with_rasa_enabled(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._given_rasa_config_created()
            self._when_running_command("tala verify")
        self._then_stdout_matches(
            "^Verifying models for DDD 'test_ddd'.\n"
            "\[eng\] Verifying grammar.\n"
            "\[eng\] Finished verifying grammar.\n"
            "\[eng\] Verifying grammar for RASA NLU.\n"
            "\[eng\] Finished verifying grammar for RASA NLU.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def _given_rasa_config_created(self):
        self._run_tala_with(["create-rasa-config"])

    def _given_enabled_rasa(self):
        self._replace_in_file(Path(DddConfig.default_name()), '"enable_rasa_nlu": false', '"enable_rasa_nlu": true')

    def test_stderr_when_verifying_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stderr_is_empty()

    def _then_stderr_is_empty(self):
        assert self._stderr == ""

    def test_stderr_when_verifying_boilerplate_ddd_with_rasa_enabled(self):
        def format_regular_expression_as_warning(regular_expression):
            return "{}{}{}".format(re.escape(BOLD), regular_expression, re.escape(ENDC))

        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._given_rasa_config_created()
            self._when_running_command("tala verify")
        self._then_stderr_matches_only(
            format_regular_expression_as_warning(
                "UserWarning: The support for RASA NLU is still in BETA. Talk gently. "
                "It is currently enabled in DDD 'test_ddd'.\n"
            )
        )

    def _then_stderr_matches_only(self, pattern):
        expected_pattern = "^{}$".format(pattern)
        match = re.match(expected_pattern, self._stderr)
        assert match is not None, "Expected pattern {!r} to match stderr {!r} but it didn't".format(
            expected_pattern, self._stderr
        )

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
            self._given_rasa_config_created()
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
